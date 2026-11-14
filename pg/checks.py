"""Pure gate logic: G1-G8 and server-side dwell crediting. No I/O.

The transaction in gate.py gathers the inputs and records the output; every decision rule
lives here so it can be property-tested. Thresholds always come from the policy document.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

HEARTBEAT_MAX_GAP_MS = 7000
INTERACTION_WINDOW_MS = 15000


def credit_heartbeat(last_hb_at: datetime, now: datetime, visible: bool, interacted_within_ms: int) -> int:
    """PRD M4: credit min(gap, 7 s) only if the tab is visible, there was input in the last 15 s,
    and the gap since the last heartbeat is <= 7 s. Everything else is idle (0)."""
    if not visible or interacted_within_ms > INTERACTION_WINDOW_MS:
        return 0
    gap = int((now - last_hb_at).total_seconds() * 1000)
    if gap < 0 or gap > HEARTBEAT_MAX_GAP_MS:
        return 0
    return gap


def _check(rule: str, ok: bool, observed: Any, required: Any, detail: str = "") -> dict:
    return {"rule": rule, "pass": bool(ok), "observed": observed, "required": required, "detail": detail}


def evaluate(*, approval: dict | None, proposal: dict, case: dict, policy: dict, reviewer: dict | None,
             reviewer_state: dict, active_suspension: bool, paused: bool, window_count: int,
             now: datetime, tenant_id: str) -> tuple[bool, list[dict]]:
    """Return (allow, checks). Fail closed: any missing input is a failed check."""
    r = policy["rules"]
    checks: list[dict] = []
    baseline_only = bool(r.get("baseline_only_existence"))

    # G1 approval for this case, unconsumed
    g1 = bool(approval) and approval.get("tenant_id") == tenant_id and approval.get("case_id") == proposal["case_id"] \
        and approval.get("proposal_id") == proposal["proposal_id"] and approval.get("status") == "submitted" \
        and proposal.get("status") == "approved" and proposal.get("approval_id") == approval.get("approval_id")
    checks.append(_check("G1_APPROVAL_FOR_CASE", g1, approval.get("status") if approval else None, "submitted",
                         "" if g1 else "no unconsumed approval for this proposal, or proposal not in approved state"))
    if baseline_only:  # policy v0: the "approval exists" baseline used in the evaluation
        return g1, checks
    if not approval or not reviewer:
        checks.append(_check("G3_CREDENTIAL", False, None, "reviewer on file", "unknown reviewer"))
        return False, checks

    # G2 not suspended, executor not paused
    g2 = not reviewer_state.get("suspended") and not active_suspension and not paused
    checks.append(_check("G2_NOT_SUSPENDED", g2, {"suspended": reviewer_state.get("suspended"), "paused": paused},
                         {"suspended": False}, "" if g2 else "reviewer suspended or executor paused"))

    # G3 credential valid, specialty match, snapshot equals current record
    exp = reviewer.get("license_expires_at")
    unexpired = exp is not None and exp > now
    spec_ok = (not r.get("require_specialty_match", True)) or reviewer.get("specialty") == case.get("specialty")
    snap = approval.get("credential_snapshot", {})
    snap_ok = snap.get("license_no") == reviewer.get("license_no") and snap.get("specialty") == reviewer.get("specialty")
    g3 = unexpired and spec_ok and snap_ok
    checks.append(_check("G3_CREDENTIAL", g3,
                         {"license_expires_at": str(exp), "specialty": reviewer.get("specialty")},
                         {"unexpired": True, "specialty": case.get("specialty")},
                         "" if g3 else "expired licence, specialty mismatch, or changed credential"))

    # G4 every cited hash was viewed AND still equals the case's current evidence hash
    current = {e["evidence_id"]: e["hash"] for e in case.get("evidence", [])}
    viewed = set(approval.get("evidence_hashes_viewed", []))
    missing = [c["evidence_id"] for c in proposal.get("cited_evidence", [])
               if c["hash"] not in viewed or current.get(c["evidence_id"]) != c["hash"]]
    g4 = not missing
    checks.append(_check("G4_EVIDENCE_COVERAGE", g4, len(proposal.get("cited_evidence", [])) - len(missing),
                         len(proposal.get("cited_evidence", [])), "" if g4 else f"cited {','.join(missing)} not opened"))

    # G5 total active dwell and per-item floor on cited items
    dwell = int(approval.get("active_dwell_ms", 0))
    per_item = {v["evidence_id"]: int(v.get("active_ms", 0)) for v in approval.get("views", [])}
    short_items = [c["evidence_id"] for c in proposal.get("cited_evidence", [])
                   if per_item.get(c["evidence_id"], 0) < r["min_item_active_ms"]]
    g5 = dwell >= r["min_active_dwell_ms"] and not short_items
    checks.append(_check("G5_DWELL", g5, dwell, r["min_active_dwell_ms"],
                         "" if g5 else f"active dwell {dwell / 1000:.1f} s < {r['min_active_dwell_ms'] / 1000:.0f} s floor"
                         + (f"; items under {r['min_item_active_ms'] / 1000:.0f} s: {','.join(short_items)}" if short_items else "")))

    # G6 rate window
    g6 = window_count < r["rate_max_approvals"]
    checks.append(_check("G6_RATE", g6, window_count, f"< {r['rate_max_approvals']} per {r['rate_window_ms'] // 1000} s",
                         "" if g6 else "approval rate over policy limit"))

    # G7 proposal freshness
    age = int((now - proposal["created_at"]).total_seconds() * 1000)
    g7 = age <= r["max_proposal_age_ms"]
    checks.append(_check("G7_FRESHNESS", g7, age, r["max_proposal_age_ms"], "" if g7 else "proposal too old; re-review"))

    # G8 separation of duties
    g8 = approval["reviewer_id"] not in {proposal.get("operator_id"), proposal.get("agent_id")}
    checks.append(_check("G8_SEPARATION_OF_DUTIES", g8, approval["reviewer_id"],
                         f"not {proposal.get('operator_id')}", "" if g8 else "reviewer is the agent's operator"))

    return all(c["pass"] for c in checks), checks


def rate_failed(checks: list[dict]) -> bool:
    return any(c["rule"] == "G6_RATE" and not c["pass"] for c in checks)


def window_start(now: datetime, policy: dict) -> datetime:
    return now - timedelta(milliseconds=policy["rules"]["rate_window_ms"])
