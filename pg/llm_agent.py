"""Claude triage agent (S6): the LLM proposes, code decides.

Claude reads one claim's evidence and the tenant's policy clauses, then calls one tool, `submit_triage`.
Code then checks the proposal: the evidence ids must exist in the case, their hashes are taken from the
case (never from the model), and the clause must be a real clause for this tenant. Anything wrong, slow
(>8 s), refused or missing a key falls back to the deterministic rule in pg.agent.triage.

Claude never sees grants, never calls the target system and never approves anything: the proposal still
waits for a human review and the Atlas gate.
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timezone

from pg import agent
from pg.config import OPERATOR_ID, settings
from pg.db import get_db
from pg.observability import LLM_CALLS, traceable

log = logging.getLogger("pg.llm_agent")
DEFAULT_MODEL = "claude-opus-5-5"
TIMEOUT_S = 8.0

SUBMIT_TOOL = {
    "name": "submit_triage",
    "description": "Submit your triage proposal for this claim. Call it exactly once.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["recommendation", "cited_evidence_ids", "clause_id", "rationale"],
        "properties": {
            "recommendation": {"type": "string", "enum": ["deny", "pay"]},
            "cited_evidence_ids": {"type": "array", "items": {"type": "string"},
                                   "description": "Evidence ids (e.g. E1, E3) a human reviewer must read to check your proposal."},
            "clause_id": {"type": "string", "description": "The policy clause id your proposal relies on, e.g. MP-004."},
            "rationale": {"type": "string", "description": "One or two plain sentences a reviewer can check against the cited evidence."},
        },
    },
}

SYSTEM = (
    "You triage health-insurance claims for a payer. You only propose; a licensed human reviewer must read every "
    "document you cite before anything happens, and code checks your proposal. Recommend 'deny' only when the "
    "evidence shows the billed service needed a prior authorization and none is on file; otherwise recommend 'pay'. "
    "Cite the evidence a reviewer needs to verify your reasoning (usually the claim line and the prior-auth record). "
    "Pick the single most relevant clause from the list. Use the submit_triage tool to answer."
)


def _model() -> str:
    return settings.llm_model or DEFAULT_MODEL


def _prompt(case: dict, clauses: list[dict]) -> str:
    ev = "\n".join(f"[{e['evidence_id']}] {e['label']}: {e['content']}" for e in case["evidence"])
    cl = "\n".join(f"{c['clause_id']}: {c['text']}" for c in clauses)
    return (f"Claim {case['case_id']} ({case['specialty']}), billed ${case['billed_amount']}.\n\n"
            f"Evidence:\n{ev}\n\nPolicy clauses:\n{cl}")


def _validate(case: dict, clauses: list[dict], out: dict) -> dict:
    """Code decides what the proposal says: ids must exist, hashes come from the case, the clause must be real."""
    ev = {e["evidence_id"]: e for e in case["evidence"]}
    ids = [i for i in dict.fromkeys(out.get("cited_evidence_ids") or []) if i in ev]
    if not ids or len(ids) != len(set(out.get("cited_evidence_ids") or [])):
        raise ValueError("cited evidence not in case")
    clause_ids = {c["clause_id"] for c in clauses}
    if out.get("clause_id") not in clause_ids:
        raise ValueError("unknown clause")
    if out.get("recommendation") not in ("deny", "pay"):
        raise ValueError("bad recommendation")
    rationale = str(out.get("rationale", "")).strip()[:600]
    if not rationale:
        raise ValueError("empty rationale")
    return {"recommendation": out["recommendation"], "rationale": rationale,
            "cited_evidence": [{"evidence_id": i, "hash": ev[i]["hash"]} for i in ids],
            "cited_clauses": [out["clause_id"]]}


@traceable("agent.triage_llm")
def _ask_claude(case: dict, clauses: list[dict]) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=TIMEOUT_S, max_retries=0)
    resp = client.messages.create(
        model=_model(),
        max_tokens=2000,
        system=SYSTEM,
        output_config={"effort": "low"},
        tools=[SUBMIT_TOOL],
        tool_choice={"type": "auto"},
        messages=[{"role": "user", "content": _prompt(case, clauses)}],
    )
    if resp.stop_reason == "refusal":
        raise ValueError("model refused")
    call = next((b for b in resp.content if b.type == "tool_use" and b.name == "submit_triage"), None)
    if call is None:
        raise ValueError(f"no tool call (stop_reason={resp.stop_reason})")
    return dict(call.input)


def triage(case: dict, clauses: list[dict]) -> tuple[dict, str, str | None]:
    """Returns (proposal fields, proposer, fallback_reason). proposer is 'llm:<model>' or 'rules-v1'."""
    if not settings.anthropic_api_key:
        return agent.triage(case, clauses), "rules-v1", "no ANTHROPIC_API_KEY"
    try:
        out = _validate(case, clauses, _ask_claude(case, clauses))
        LLM_CALLS.labels("triage", "true").inc()
        return out, f"llm:{_model()}", None
    except Exception as e:  # any failure: the deterministic rule decides what to propose
        LLM_CALLS.labels("triage", "false").inc()
        reason = f"{type(e).__name__}: {str(e)[:120]}"
        log.warning("llm triage fell back to rules: %s", reason)
        return agent.triage(case, clauses), "rules-v1", reason


def triage_new_claims(tenant: str, n: int = 3, seed: int | None = None) -> dict:
    """Simulate n newly arriving claims and have the agent triage each. Seed data and the eval stay on rules."""
    from seed.generate import make_case

    db = get_db()
    clauses = list(db.policy_clauses.find({"tenant_id": tenant}, {"_id": 0}))
    existing = db.cases.count_documents({"tenant_id": tenant})
    rng = random.Random(seed if seed is not None else existing * 7919 + 1)
    now = datetime.now(timezone.utc)
    out = []
    for k in range(max(1, min(n, 5))):
        c = make_case(rng, tenant, existing + k + 1, "orthopedics", now)
        c["case_id"] = c["case_id"].replace("CLM-", "CLM-N")  # new arrivals never collide with seeded ids
        fields, proposer, why = triage(c, clauses)
        prop = {"tenant_id": tenant, "proposal_id": c["case_id"].replace("CLM", "P"), "case_id": c["case_id"],
                "action_type": "claim_denial", "agent_id": "triage-agent-v1", "model_version": proposer,
                "proposer": proposer, "fallback_reason": why, "operator_id": OPERATOR_ID, **fields,
                "status": "pending_review", "requeue_reasons": [], "created_at": now}
        db.cases.insert_one(c)
        db.target_records.insert_one({"tenant_id": tenant, "kind": "claim", "record_id": c["case_id"], "status": "PENDING",
                                      "history": [], "reopened_for": []})
        db.proposals.insert_one(prop)
        out.append({"case_id": c["case_id"], "recommendation": fields["recommendation"], "proposer": proposer,
                    "cited": [e["evidence_id"] for e in fields["cited_evidence"]], "clause": fields["cited_clauses"],
                    "rationale": fields["rationale"], "fallback_reason": why})
    return {"model": _model(), "key_set": bool(settings.anthropic_api_key), "claims": out}
