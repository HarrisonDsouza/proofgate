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
from pg.checks import evaluate, rate_failed
from pg.config import settings
from pg.db import client, get_db, now
from pg.review import NotFound


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


def ensure_compensation(db, s, tenant: str, d: dict, policy: dict, suspension_id: str, t) -> int:
    """Idempotent: one compensation per denial (unique index on denial_id). Returns 1 when newly created."""
    r = db.compensations.update_one(
        {"denial_id": d["denial_id"]},
        {"$setOnInsert": {"tenant_id": tenant, "denial_id": d["denial_id"], "record_id": d["record_id"],
                          "kind": policy["effect"]["kind"], "to_status": policy["effect"]["compensate_status"],
                          "status": "pending", "attempts": 0, "next_attempt_at": t, "suspension_id": suspension_id}},
        upsert=True, session=s)
    return int(r.upserted_id is not None)


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
    # AUTHORIZED covers a denial the target already applied but confirm() has not yet read back: its grant is `used`
    # (revoked/issued grants changed nothing at the target, so they need no compensation).
    for d in db.denials.find({"tenant_id": tenant, "reviewer_id": reviewer_id, "status": {"$in": ["AUTHORIZED", "CONFIRMED"]},
                              "created_at": {"$gte": lookback}}, session=s):
        g = db.grants.find_one({"_id": d["grant_id"], "tenant_id": tenant}, session=s)
        if not g or g.get("status") != "used":
            continue
        created += ensure_compensation(db, s, tenant, d, policy, sid, t)
    if not existing:
        db.suspensions.insert_one({"tenant_id": tenant, "suspension_id": sid, "reviewer_id": reviewer_id, "active": True,
                                   "source": source, "rule": rule, "observed": observed, "policy_id": policy["policy_id"],
                                   "policy_version": policy["version"], "ts": t, "grants_revoked": revoked,
                                   "proposals_requeued": requeued, "compensations_created": created}, session=s)
    if not existing:
        _audit(db, s, tenant, "reviewer_suspended", source, reviewer_id=reviewer_id,
               refs={"suspension_id": sid}, policy_version=policy["version"])
    return {"suspension_id": sid, "grants_revoked": revoked, "proposals_requeued": requeued, "compensations_created": created}


def suspend(tenant: str, reviewer_id: str, source: str, rule: str, observed: dict, action_type: str = "claim_denial") -> dict:
    db = get_db()
    with client().start_session() as s:
        return s.with_transaction(lambda ss: suspend_in_txn(db, ss, tenant, reviewer_id, source, rule, observed,
                                                            active_policy(db, tenant, action_type, ss)),
                                  read_concern=ReadConcern("snapshot"), write_concern=WriteConcern("majority"))


def load_gate_inputs(db, s, tenant: str, proposal_id: str, approval_id: str, t) -> dict:
    """Everything the gate must read, in a single aggregation inside the transaction's snapshot.

    Why: over the network each round trip costs ~85 ms; nine separate reads made every gate call ~1.5 s, so the
    50-case burst took over a minute. The aggregation starts at the proposal and $lookups the approval, case, active
    policy, reviewer, reviewer_state, active suspension, executor flag and the rate-window count. It returns exactly
    what the nine reads returned (tests/test_gate_inputs.py compares them on every kind of case), the version guard
    and every write below are unchanged, and it runs on the transaction's session, so it sees the same snapshot."""
    def by_id(coll: str, key: str, expr) -> dict:
        return {"$lookup": {"from": coll, "let": {"v": expr}, "as": coll_alias[coll],
                            "pipeline": [{"$match": {"tenant_id": tenant, "$expr": {"$eq": ["$" + key, "$$v"]}}}, {"$limit": 1}]}}
    coll_alias = {"cases": "case", "reviewers": "reviewer", "review_policies": "policy"}
    pipeline = [
        {"$match": {"tenant_id": tenant, "proposal_id": proposal_id}},
        {"$limit": 1},
        {"$lookup": {"from": "approvals", "as": "approval",
                     "pipeline": [{"$match": {"tenant_id": tenant, "approval_id": approval_id}}, {"$limit": 1}]}},
        {"$addFields": {"_rid": {"$ifNull": [{"$arrayElemAt": ["$approval.reviewer_id", 0]}, "unknown"]}}},
        by_id("cases", "case_id", "$case_id"),
        {"$lookup": {"from": "review_policies", "let": {"a": "$action_type"}, "as": "policy",
                     "pipeline": [{"$match": {"tenant_id": tenant, "status": "active", "$expr": {"$eq": ["$action_type", "$$a"]}}},
                                  {"$limit": 1}]}},
        by_id("reviewers", "reviewer_id", "$_rid"),
        {"$lookup": {"from": "reviewer_state", "let": {"r": "$_rid"}, "as": "rstate",
                     "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", {"$concat": [tenant, "|", "$$r"]}]}}}, {"$limit": 1}]}},
        {"$lookup": {"from": "suspensions", "let": {"r": "$_rid"}, "as": "susp",
                     "pipeline": [{"$match": {"tenant_id": tenant, "active": True, "$expr": {"$eq": ["$reviewer_id", "$$r"]}}},
                                  {"$limit": 1}]}},
        {"$lookup": {"from": "agent_control", "as": "ctl",
                     "pipeline": [{"$match": {"_id": f"executor|{tenant}"}}, {"$limit": 1}]}},
        {"$lookup": {"from": "approvals", "as": "winc",
                     "let": {"r": "$_rid", "ms": {"$ifNull": [{"$arrayElemAt": ["$policy.rules.rate_window_ms", 0]}, 0]}},
                     "pipeline": [{"$match": {"tenant_id": tenant, "$expr": {"$and": [
                         {"$eq": ["$reviewer_id", "$$r"]},
                         {"$gte": ["$created_at", {"$subtract": [t, "$$ms"]}]}, {"$lte": ["$created_at", t]}]}}},
                         {"$count": "n"}]}},
    ]
    row = next(iter(db.proposals.aggregate(pipeline, session=s)), None)
    if row is None:
        raise NotFound("unknown proposal")
    if not row["policy"]:
        raise LookupError(f"no active policy for {tenant}/{row['action_type']}")
    rid = row["_rid"]
    rstate = row["rstate"][0] if row["rstate"] else {"_id": f"{tenant}|{rid}", "version": -1, "suspended": True}  # fail closed
    prop = {k: v for k, v in row.items() if k not in ("approval", "case", "policy", "reviewer", "rstate", "susp", "ctl", "winc", "_rid")}
    return {"prop": prop, "approval": row["approval"][0] if row["approval"] else None,
            "case": row["case"][0] if row["case"] else None, "policy": row["policy"][0],
            "reviewer": row["reviewer"][0] if row["reviewer"] else None, "rstate": rstate,
            "susp": row["susp"][0] if row["susp"] else None,
            "paused": bool((row["ctl"][0] if row["ctl"] else {}).get("paused")),
            "window": row["winc"][0]["n"] if row["winc"] else 0}


def execute(tenant: str, proposal_id: str, approval_id: str, agent_id: str, operator_id: str, debug_pause_ms: int = 0) -> dict:
    db = get_db()
    attempts = {"n": 0}

    def body(s):
        attempts["n"] += 1
        t = now()
        ctx = load_gate_inputs(db, s, tenant, proposal_id, approval_id, t)  # ONE round trip, not nine
        prop, approval, case, policy = ctx["prop"], ctx["approval"], ctx["case"], ctx["policy"]
        reviewer, rstate, susp, paused, window = ctx["reviewer"], ctx["rstate"], ctx["susp"], ctx["paused"], ctx["window"]
        reviewer_id = (approval or {}).get("reviewer_id", "unknown")
        rs_id = f"{tenant}|{reviewer_id}"
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
    obs.DECISIONS.labels(out["decision"], "agent").inc()
    obs.OPERATE_LATENCY.observe(tm["ms"] / 1000)
    if attempts["n"] > 1:
        obs.TXN_RETRIES.inc(attempts["n"] - 1)
    obs.record_telemetry(db, "gate_latency_ms", tm["ms"], tenant_id=tenant, decision=out["decision"], attempts=attempts["n"],
                         gate_decision_id=out["gate_decision_id"])
    obs.log_event("gate", decision=out["decision"], proposal=proposal_id, attempts=attempts["n"], ms=round(tm["ms"], 1),
                  gate_decision_id=out["gate_decision_id"])
    return out


def confirm(tenant: str, denial_id: str) -> dict:
    """The gate reads the target back itself; CONFIRMED only if the effect and the grant match.

    If the reviewer was suspended after the target applied the grant but before this read-back, the denial is
    CONFIRMED (it did happen) but a compensation is queued here and the proposal stays `needs_review`: a suspended
    reviewer's denial must not stand. The other order (suspension commits after this) is covered in suspend_in_txn."""
    db = get_db()
    d = db.denials.find_one({"tenant_id": tenant, "denial_id": denial_id})
    if d is None:
        raise NotFound("unknown denial")
    if d["status"] != "AUTHORIZED":  # idempotent: a confirmed, reversed or failed denial is never flipped by a repeat call
        return {"denial_id": denial_id, "status": d["status"],
                "readback": {"status": (d.get("readback") or {}).get("status"), "grant_id": d["grant_id"]}}
    pol = db.review_policies.find_one({"tenant_id": tenant, "policy_id": d["policy_id"], "version": d["policy_version"]})
    rec = db.target_records.find_one({"tenant_id": tenant, "kind": pol["effect"]["kind"], "record_id": d["record_id"]})
    ok = rec and rec.get("status") == pol["effect"]["apply_status"] and rec.get("last_apply", {}).get("grant_id") == d["grant_id"]
    status = "CONFIRMED" if ok else "NOT_EXECUTED"
    t = now()
    db.denials.update_one({"_id": d["_id"]}, {"$set": {"status": status, "readback": {"status": (rec or {}).get("status"), "at": t},
                                                       **({"confirmed_at": t} if ok else {})}})
    if ok:
        susp = db.suspensions.find_one({"tenant_id": tenant, "reviewer_id": d["reviewer_id"], "active": True})
        if susp:
            with client().start_session() as s:
                s.with_transaction(lambda ss: ensure_compensation(db, ss, tenant, d, pol, susp["suspension_id"], t))
        else:
            db.proposals.update_one({"tenant_id": tenant, "proposal_id": d["proposal_id"]}, {"$set": {"status": "executed"}})
    return {"denial_id": denial_id, "status": status, "readback": {"status": (rec or {}).get("status"), "grant_id": d["grant_id"]}}


class PolicyRejected(ValueError):
    """The requested policy change is not allowed (unknown key, wrong type, or it would loosen a protection)."""


# The only keys a supervisor may change through the API, and which direction is TIGHTER. Anything else (including
# `baseline_only_existence`, which turns every check but G1 off, and `require_specialty_match`) is rejected.
TUNABLE = {"min_active_dwell_ms": "up", "min_item_active_ms": "up", "rate_window_ms": "up", "compensation_lookback_ms": "up",
           "rate_max_approvals": "down", "max_proposal_age_ms": "down"}
MAX_MS = 7 * 24 * 3600 * 1000


def validate_policy_change(current: dict, changes: dict) -> dict:
    """Return the validated subset to merge, or raise PolicyRejected. Tightening only: floors and windows may rise,
    caps and ages may fall. A policy API that can loosen is a way to switch the gate off with one request."""
    if not isinstance(changes, dict) or not changes:
        raise PolicyRejected("rules must be a non-empty object")
    out = {}
    for k, v in changes.items():
        if k not in TUNABLE:
            raise PolicyRejected(f"{k!r} is not a tunable policy key")
        if type(v) is not int:  # bool, float, str and None are all refused
            raise PolicyRejected(f"{k} must be an integer")
        if not (1 <= v <= MAX_MS):
            raise PolicyRejected(f"{k} out of range")
        cur = current.get(k)
        if cur is not None and ((TUNABLE[k] == "up" and v < cur) or (TUNABLE[k] == "down" and v > cur)):
            raise PolicyRejected(f"{k}={v} would loosen the policy (current {cur}); only tightening is allowed")
        out[k] = v
    return out


def new_policy_version(tenant: str, action_type: str, rules: dict, rationale: str, created_by: str) -> dict:
    """Supersede the active version and insert v+1 in one transaction (validated rules merged over the current ones)."""
    db = get_db()
    rationale = str(rationale)[:500]
    created_by = str(created_by)[:64]

    def body(s):
        cur = active_policy(db, tenant, action_type, s)
        rules_ok = validate_policy_change(cur["rules"], rules)  # raises PolicyRejected: nothing is written
        db.review_policies.update_one({"_id": cur["_id"]}, {"$set": {"status": "superseded"}}, session=s)
        nv = {k: v for k, v in cur.items() if k != "_id"} | {"version": cur["version"] + 1, "status": "active",
                                                              "rules": cur["rules"] | rules_ok, "rationale": rationale,
                                                              "created_by": created_by, "created_at": now()}
        db.review_policies.insert_one(nv, session=s)
        return {"policy_id": cur["policy_id"], "version": nv["version"], "status": "active", "superseded_version": cur["version"]}

    with client().start_session() as s:
        return s.with_transaction(body)


def set_paused(tenant: str, paused: bool) -> dict:
    get_db().agent_control.update_one({"_id": f"executor|{tenant}"}, {"$set": {"paused": paused}}, upsert=True)
    return {"paused": paused}
