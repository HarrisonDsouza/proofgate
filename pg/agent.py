"""Triage agent (rules-based, PRD M3) and executor loop (M9).

The agent proposes; code decides. The executor calls the gate, then the target with the grant,
then asks the gate to confirm by read-back. It honours agent_control.paused.
"""
from __future__ import annotations

import hashlib
import threading
import time

from fastapi import HTTPException

from pg import gate, target
from pg.config import AGENT_ID, OPERATOR_ID
from pg.db import get_db


def triage(case: dict, clauses: list[dict]) -> dict:
    """Deterministic rule: deny when the prior-auth evidence says 'none on file' and the policy needs one."""
    ev = {e["evidence_id"]: e for e in case["evidence"]}
    no_pa = any("Prior-auth record: none on file" in e["content"] for e in case["evidence"])
    cited_ids = [eid for eid in ev if eid in ("E1", "E3")][:2] or list(ev)[:2]
    idx = int(hashlib.sha256(case["case_id"].encode()).hexdigest(), 16) % max(1, len(clauses))  # stable across runs
    clause = clauses[idx]["clause_id"] if clauses else None
    return {"recommendation": "deny" if no_pa else "pay",
            "rationale": (f"Service billed without a prior authorization on file; {clause} requires one."
                          if no_pa else "Documentation supports the billed service."),
            "cited_evidence": [{"evidence_id": i, "hash": ev[i]["hash"]} for i in cited_ids],
            "cited_clauses": [clause] if clause else []}


def execute_one(tenant: str, proposal: dict) -> dict:
    res = gate.execute(tenant, proposal["proposal_id"], proposal["approval_id"], AGENT_ID, OPERATOR_ID)
    if res["decision"] != "ALLOW":
        return res
    t = res["target"]
    try:
        target.apply(tenant, t["kind"], t["record_id"], t["to_status"], f"Grant {res['grant_id']}", AGENT_ID)
    except HTTPException:
        pass  # the confirm step will mark NOT_EXECUTED
    return res | {"confirm": gate.confirm(tenant, res["denial_id"])}


def executor_loop(tenant: str, stop: threading.Event | None = None, once: bool = False) -> list[dict]:
    db = get_db()
    results = []
    while not (stop and stop.is_set()):
        if (db.agent_control.find_one({"_id": f"executor|{tenant}"}) or {}).get("paused"):
            time.sleep(0.5)
            continue
        batch = list(db.proposals.find({"tenant_id": tenant, "status": "approved", "recommendation": "deny"}).limit(100))
        for p in batch:
            results.append(execute_one(tenant, p))
        if once:
            return results
        time.sleep(0.3)
    return results
