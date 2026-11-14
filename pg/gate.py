"""The gate (PRD M6, M7, M10 suspension writes) inside ONE Atlas transaction.

Write-conflict design: every gate, approval and suspension transaction for a reviewer writes the
same `reviewer_state` document with a version guard. If another transaction committed a change to
it after this transaction's snapshot, MongoDB raises a write conflict (TransientTransactionError),
`with_transaction` re-runs the callback, and the retry re-reads `suspended`/the window and decides
again. EVERY operation inside the callback passes `session=s`.
"""
from __future__ import annotations

import secrets
import time
from datetime import timedelta

from pymongo.errors import PyMongoError
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

from pg import observability as obs
from pg.checks import evaluate, rate_failed, window_start
from pg.config import settings
from pg.db import client, get_db, now


class VersionMoved(PyMongoError):
    """Raised inside the callback when the reviewer_state guard matched 0 docs.

    It must be a PyMongoError carrying the TransientTransactionError label: with_transaction only
    retries those (belt and braces next to the server's own write-conflict detection)."""

    def __init__(self):
        super().__init__("reviewer_state version moved")
        self._add_error_label("TransientTransactionError")


def _id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(5)}"


def _audit(db, s, tenant, event, actor, case_id=None, reviewer_id=None, refs=None, policy_version=None):
    db.audit.insert_one({"tenant_id": tenant, "case_id": case_id, "reviewer_id": reviewer_id, "ts": now(), "actor": actor,
                         "event": event, "ref_ids": refs or {}, "policy_version": policy_version}, session=s)


def active_policy(db, tenant: str, action_type: str, s=None) -> dict:
    p = db.review_policies.find_one({"tenant_id": tenant, "action_type": action_type, "status": "active"}, session=s)
    if not p:
        raise LookupError(f"no active policy for {tenant}/{action_type}")
    return p


def suspend_in_txn(db, s, tenant: str, reviewer_id: str, source: str, rule: str, observed: dict, policy: dict) -> dict:
    """Shared suspension writes (gate inline G6, change-stream detector, supervisor halt). Runs inside the caller's txn."""
    t = now()
    rs_id = f"{tenant}|{reviewer_id}"
    existing = db.suspensions.find_one({"tenant_id": tenant, "reviewer_id": reviewer_id, "active": True}, session=s)
    sid = existing["suspension_id"] if existing else _id("SU")
    db.reviewer_state.update_one({"_id": rs_id}, {"$set": {"suspended": True, "suspension_id": sid}, "$inc": {"version": 1}},
                                 session=s)
    revoked = db.grants.update_many({"tenant_id": tenant, "reviewer_id": reviewer_id, "status": "issued"},
                                    {"$set": {"status": "revoked"}}, session=s).modified_count
    requeued = db.proposals.update_many({"tenant_id": tenant, "approved_by": reviewer_id, "status": {"$in": ["approved", "authorized"]}},
                                        {"$set": {"status": "needs_review"}, "$push": {"requeue_reasons": f"suspension {sid}"}},
                                        session=s).modified_count
    db.approvals.update_many({"tenant_id": tenant, "reviewer_id": reviewer_id, "status": "submitted"},
                             {"$set": {"status": "invalidated"}}, session=s)
    lookback = t - timedelta(milliseconds=policy["rules"]["compensation_lookback_ms"])
    created = 0
    for d in db.denials.find({"tenant_id": tenant, "reviewer_id": reviewer_id, "status": "CONFIRMED",
                              "confirmed_at": {"$gte": lookback}}, session=s):
        r = db.compensations.update_one(
            {"denial_id": d["denial_id"]},
            {"$setOnInsert": {"tenant_id": tenant, "denial_id": d["denial_id"], "record_id": d["record_id"],
                              "kind": policy["effect"]["kind"], "to_status": policy["effect"]["compensate_status"],
                              "status": "pending", "attempts": 0, "next_attempt_at": t, "suspension_id": sid}},
            upsert=True, session=s)
        created += int(r.upserted_id is not None)
    if not existing:
        db.suspensions.insert_one({"tenant_id": tenant, "suspension_id": sid, "reviewer_id": reviewer_id, "active": True,
                                   "source": source, "rule": rule, "observed": observed, "policy_id": policy["policy_id"],
                                   "policy_version": policy["version"], "ts": t, "grants_revoked": revoked,
                                   "proposals_requeued": requeued, "compensations_created": created}, session=s)
    _audit(db, s, tenant, "reviewer_suspended", source, reviewer_id=reviewer_id,
           refs={"suspension_id": sid}, policy_version=policy["version"])
    return {"suspension_id": sid, "grants_revoked": revoked, "proposals_requeued": requeued, "compensations_created": created}


def suspend(tenant: str, reviewer_id: str, source: str, rule: str, observed: dict, action_type: str = "claim_denial") -> dict:
    db = get_db()
    with client().start_session() as s:
        return s.with_transaction(lambda ss: suspend_in_txn(db, ss, tenant, reviewer_id, source, rule, observed,
                                                            active_policy(db, tenant, action_type, ss)),
                                  read_concern=ReadConcern("snapshot"), write_concern=WriteConcern("majority"))


def execute(tenant: str, proposal_id: str, approval_id: str, agent_id: str, operator_id: str, debug_pause_ms: int = 0) -> dict:
    db = get_db()
    attempts = {"n": 0}

    def body(s):
        attempts["n"] += 1
        t = now()
        prop = db.proposals.find_one({"tenant_id": tenant, "proposal_id": proposal_id}, session=s)
        if not prop:
            raise LookupError("unknown proposal")
        approval = db.approvals.find_one({"tenant_id": tenant, "approval_id": approval_id}, session=s)
        case = db.cases.find_one({"tenant_id": tenant, "case_id": prop["case_id"]}, session=s)
        policy = active_policy(db, tenant, prop["action_type"], s)
        reviewer_id = (approval or {}).get("reviewer_id", "unknown")
        reviewer = db.reviewers.find_one({"tenant_id": tenant, "reviewer_id": reviewer_id}, session=s)
        rs_id = f"{tenant}|{reviewer_id}"
        rstate = db.reviewer_state.find_one({"_id": rs_id}, session=s)
        if rstate is None:  # seeded for every reviewer; a missing one fails closed below
            rstate = {"_id": rs_id, "version": -1, "suspended": True}
        susp = db.suspensions.find_one({"tenant_id": tenant, "reviewer_id": reviewer_id, "active": True}, session=s)
        paused = bool((db.agent_control.find_one({"_id": f"executor|{tenant}"}, session=s) or {}).get("paused"))
        window = db.approvals.count_documents({"tenant_id": tenant, "reviewer_id": reviewer_id,
                                               "created_at": {"$gte": window_start(t, policy), "$lte": t}}, session=s)
        allow, checks = evaluate(approval=approval, proposal=prop, case=case, policy=policy, reviewer=reviewer,
                                 reviewer_state=rstate, active_suspension=bool(susp), paused=paused,
                                 window_count=window, now=t, tenant_id=tenant)
        if debug_pause_ms and settings.debug_hooks and attempts["n"] == 1:
            time.sleep(debug_pause_ms / 1000)  # test-conflict hook: after reads, before the version write
        # the version-guarded write every competing transaction also makes
        if rstate["version"] >= 0:
            r = db.reviewer_state.update_one({"_id": rs_id, "version": rstate["version"]},
                                             {"$inc": {"version": 1}, "$set": {"last_gate_at": t}}, session=s)
            if r.matched_count == 0:
                raise VersionMoved()
        gd = {"tenant_id": tenant, "decision_id": _id("GD"), "case_id": prop["case_id"], "proposal_id": proposal_id,
              "approval_id": approval_id, "reviewer_id": reviewer_id, "agent_id": agent_id, "policy_id": policy["policy_id"],
              "policy_version": policy["version"], "decision": "ALLOW" if allow else "REFUSE", "checks": checks,
              "txn_attempts": attempts["n"], "ts": t}
        out = {"decision": gd["decision"], "gate_decision_id": gd["decision_id"],
               "policy": {"policy_id": policy["policy_id"], "version": policy["version"]}}
        if allow:
            denial_id, grant_id = _id("D"), f"g_{secrets.token_hex(16)}"
            eff = policy["effect"]
            db.denials.insert_one({"tenant_id": tenant, "denial_id": denial_id, "action_type": prop["action_type"],
                                   "case_id": prop["case_id"], "record_id": prop["case_id"], "proposal_id": proposal_id,
                                   "approval_id": approval_id, "reviewer_id": reviewer_id, "agent_id": agent_id,
                                   "operator_id": operator_id, "policy_id": policy["policy_id"], "policy_version": policy["version"],
                                   "grant_id": grant_id, "gate_decision_id": gd["decision_id"], "status": "AUTHORIZED",
                                   "created_at": t}, session=s)
            db.grants.insert_one({"_id": grant_id, "tenant_id": tenant, "audience": f"target:{eff['kind']}",
                                  "record_id": prop["case_id"], "case_id": prop["case_id"], "to_status": eff["apply_status"],
                                  "denial_id": denial_id, "approval_id": approval_id, "reviewer_id": reviewer_id,
                                  "agent_id": agent_id, "policy_version": policy["version"], "status": "issued",
                                  "expires_at": t + timedelta(seconds=60), "ttl_at": t + timedelta(days=7)}, session=s)
            db.approvals.update_one({"_id": approval["_id"]}, {"$set": {"status": "consumed"}}, session=s)
            db.proposals.update_one({"_id": prop["_id"]}, {"$set": {"status": "authorized"}}, session=s)
            out |= {"denial_id": denial_id, "grant_id": grant_id, "grant_expires_at": (t + timedelta(seconds=60)).isoformat(),
                    "target": {"kind": eff["kind"], "record_id": prop["case_id"], "to_status": eff["apply_status"]}}
        else:
            if approval and approval.get("status") == "submitted":
                db.approvals.update_one({"_id": approval["_id"]}, {"$set": {"status": "refused"}}, session=s)
            db.proposals.update_one({"_id": prop["_id"]}, {"$set": {"status": "needs_review"},
                                                           "$push": {"requeue_reasons": [c["rule"] for c in checks if not c["pass"]]}},
                                    session=s)
            out["reasons"] = [c for c in checks if not c["pass"]]
            if rate_failed(checks) and not rstate.get("suspended"):
                out["suspension"] = suspend_in_txn(db, s, tenant, reviewer_id, "gate_inline", "G6_RATE",
                                                   {"count": window, "window_ms": policy["rules"]["rate_window_ms"]}, policy)
        db.gate_decisions.insert_one(gd, session=s)
        _audit(db, s, tenant, f"gate_{gd['decision'].lower()}", agent_id, prop["case_id"], reviewer_id,
               {"gate_decision_id": gd["decision_id"]}, policy["version"])
        return out

    with obs.timed() as tm:
        with client().start_session() as s:
            out = s.with_transaction(body, read_concern=ReadConcern("snapshot"), write_concern=WriteConcern("majority"))
    out["txn_attempts"] = attempts["n"]
    db.gate_decisions.update_one({"decision_id": out["gate_decision_id"]}, {"$set": {"txn_attempts": attempts["n"]}})
    obs.DECISIONS.labels(out["decision"], "agent").inc()
    obs.OPERATE_LATENCY.observe(tm["ms"] / 1000)
    if attempts["n"] > 1:
        obs.TXN_RETRIES.inc(attempts["n"] - 1)
    obs.log_event("gate", decision=out["decision"], proposal=proposal_id, attempts=attempts["n"], ms=round(tm["ms"], 1),
                  gate_decision_id=out["gate_decision_id"])
    return out


def confirm(tenant: str, denial_id: str) -> dict:
    """The gate reads the target back itself; CONFIRMED only if the effect and the grant match."""
    db = get_db()
    d = db.denials.find_one({"tenant_id": tenant, "denial_id": denial_id})
    pol = db.review_policies.find_one({"tenant_id": tenant, "policy_id": d["policy_id"], "version": d["policy_version"]})
    rec = db.target_records.find_one({"tenant_id": tenant, "record_id": d["record_id"]})
    ok = rec and rec.get("status") == pol["effect"]["apply_status"] and rec.get("last_apply", {}).get("grant_id") == d["grant_id"]
    status = "CONFIRMED" if ok else "NOT_EXECUTED"
    t = now()
    db.denials.update_one({"_id": d["_id"]}, {"$set": {"status": status, "readback": {"status": (rec or {}).get("status"), "at": t},
                                                       **({"confirmed_at": t} if ok else {})}})
    if ok:
        db.proposals.update_one({"tenant_id": tenant, "proposal_id": d["proposal_id"]}, {"$set": {"status": "executed"}})
    return {"denial_id": denial_id, "status": status, "readback": {"status": (rec or {}).get("status"), "grant_id": d["grant_id"]}}


def new_policy_version(tenant: str, action_type: str, rules: dict, rationale: str, created_by: str) -> dict:
    """Supersede the active version and insert v+1 in one transaction (rules merged over the current ones)."""
    db = get_db()

    def body(s):
        cur = active_policy(db, tenant, action_type, s)
        db.review_policies.update_one({"_id": cur["_id"]}, {"$set": {"status": "superseded"}}, session=s)
        nv = {k: v for k, v in cur.items() if k != "_id"} | {"version": cur["version"] + 1, "status": "active",
                                                              "rules": cur["rules"] | rules, "rationale": rationale,
                                                              "created_by": created_by, "created_at": now()}
        db.review_policies.insert_one(nv, session=s)
        return {"policy_id": cur["policy_id"], "version": nv["version"], "status": "active", "superseded_version": cur["version"]}

    with client().start_session() as s:
        return s.with_transaction(body)


def set_paused(tenant: str, paused: bool) -> dict:
    get_db().agent_control.update_one({"_id": f"executor|{tenant}"}, {"$set": {"paused": paused}}, upsert=True)
    return {"paused": paused}
