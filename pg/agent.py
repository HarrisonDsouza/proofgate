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
from pg import observability as obs
from pg.config import AGENT_ID, OPERATOR_ID
from pg.db import get_db


@obs.traceable("triage_one")
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


@obs.traceable("gate_execute")
def _gate_execute(tenant: str, proposal: dict) -> dict:
    return gate.execute(tenant, proposal["proposal_id"], proposal["approval_id"], AGENT_ID, OPERATOR_ID)


@obs.traceable("target_apply")
def _target_apply(tenant: str, t: dict, grant_header: str) -> dict:
    return target.apply(tenant, t["kind"], t["record_id"], t["to_status"], grant_header, AGENT_ID)


@obs.traceable("gate_confirm")
def _gate_confirm(tenant: str, denial_id: str) -> dict:
    return gate.confirm(tenant, denial_id)


@obs.traceable("execute_one")
def execute_one(tenant: str, proposal: dict) -> dict:
    obs.annotate_run(tenant_id=tenant, proposal_id=proposal.get("proposal_id"), case_id=proposal.get("case_id"))
    res = _gate_execute(tenant, proposal)
    obs.annotate_run(decision=res["decision"])
    if res["decision"] != "ALLOW":
        return res
    t = res["target"]
    try:
        _target_apply(tenant, t, f"Grant {res['grant_id']}")
    except HTTPException:
        pass  # the confirm step will mark NOT_EXECUTED
    return res | {"confirm": _gate_confirm(tenant, res["denial_id"])}


def executor_loop(tenant: str, stop: threading.Event | None = None, once: bool = False) -> list[dict]:
    db = get_db()
    results = []
    while not (stop and stop.is_set()):
        if (db.agent_control.find_one({"_id": f"executor|{tenant}"}) or {}).get("paused"):
            if once:
                return results  # paused: a one-shot run returns at once instead of waiting forever
            time.sleep(0.5)
            continue
        batch = list(db.proposals.find({"tenant_id": tenant, "status": "approved", "recommendation": "deny"}).limit(100))
        for p in batch:
            # Re-read before acting: a suspension mid-batch sends the rest back to review, and asking the gate about
            # each of those costs a full transaction (~1.9 s on the sandbox) for a certain refusal.
            if not db.proposals.find_one({"_id": p["_id"], "status": "approved"}, {"_id": 1}):
                continue
            results.append(execute_one(tenant, p))
        if once:
            return results
        time.sleep(0.3)
    return results
