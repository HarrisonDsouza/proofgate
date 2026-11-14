"""Reviewer sessions, server-timed evidence views, heartbeats, approvals (PRD M4, M5).

Dwell is computed ONLY here, from view tokens and heartbeats. A client-sent dwell_ms is stored
under client_supplied_ignored and never used.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from datetime import timedelta, timezone

from pymongo import UpdateOne
from pymongo.errors import DuplicateKeyError

from pg.checks import credit_heartbeat
from pg.db import client, get_db, now


class NotFound(LookupError):
    pass


class BadRequest(Exception):
    pass


def _rid(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(4)}"


def chain_body(ev: dict) -> str:
    """Canonical text that is hashed. Includes ts (ms), so event times cannot be edited without detection."""
    ts = ev["ts"].astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    return json.dumps({**{k: ev.get(k) for k in ("session_id", "seq", "case_id", "evidence_id", "type", "credited_ms", "audio_sha256")}, "ts": ts},
                      sort_keys=True)


def _event(db, tenant: str, session_id: str, reviewer_id: str, case_id: str, typ: str, credited_ms: int = 0,
           evidence_id: str | None = None, s=None, audio_sha256: str | None = None) -> None:
    """Append one review_event to the session's hash chain (S3)."""
    _events(db, tenant, session_id, reviewer_id, [{"case_id": case_id, "type": typ, "credited_ms": credited_ms,
                                                  "evidence_id": evidence_id, "audio_sha256": audio_sha256}], s)


def _events(db, tenant: str, session_id: str, reviewer_id: str, items: list[dict], s=None) -> None:
    """Append N review_events to the session's hash chain in ONE read, ONE insert_many and ONE head update.

    Atomic: the read of chain_head, the inserts and the head update commit together, so two concurrent writers on one
    session conflict on the session document and one retries; the chain cannot fork. Seq numbers are reserved by
    incrementing the session's counter by N, then the hashes are chained in order in memory."""
    n = len(items)
    if not n:
        return

    def body(ss):
        sess = db.reviewer_sessions.find_one_and_update({"tenant_id": tenant, "session_id": session_id},
                                                        {"$inc": {"seq": n}}, return_document=True, session=ss)
        prev = sess.get("chain_head", "0" * 64)
        first = sess["seq"] - n + 1
        evs = []
        for i, it in enumerate(items):
            t = now()
            ev = {"tenant_id": tenant, "session_id": session_id, "seq": first + i, "reviewer_id": reviewer_id,
                  "case_id": it["case_id"], "evidence_id": it.get("evidence_id"), "type": it["type"],
                  "credited_ms": int(it.get("credited_ms", 0)), "audio_sha256": it.get("audio_sha256"),
                  "ts": t.replace(microsecond=t.microsecond // 1000 * 1000)}  # BSON dates are ms: hash what is stored
            ev["prev_hash"] = prev
            ev["hash"] = hashlib.sha256((prev + chain_body(ev)).encode()).hexdigest()
            prev = ev["hash"]
            evs.append(ev)
        db.review_events.insert_many(evs, ordered=True, session=ss)
        db.reviewer_sessions.update_one({"_id": sess["_id"]}, {"$set": {"chain_head": prev}}, session=ss)

    if s is not None:  # already inside the caller's transaction
        body(s)
    else:
        with client().start_session() as ss:
            ss.with_transaction(body)


def open_session(tenant: str, reviewer_id: str) -> dict:
    db = get_db()
    rv = db.reviewers.find_one({"tenant_id": tenant, "reviewer_id": reviewer_id})
    if not rv:
        raise NotFound("unknown reviewer")
    sid = _rid("S")
    db.reviewer_sessions.insert_one({"tenant_id": tenant, "session_id": sid, "reviewer_id": reviewer_id,
                                     "started_at": now(), "chain_head": "0" * 64, "seq": 0})
    return {"session_id": sid, "reviewer": {k: rv[k] for k in ("reviewer_id", "specialty", "license_expires_at")}}


def _session(db, tenant: str, session_id: str) -> dict:
    s = db.reviewer_sessions.find_one({"tenant_id": tenant, "session_id": session_id})
    if not s:
        raise NotFound("unknown session")
    return s


def _close_open_tokens(db, tenant: str, session_id: str) -> None:
    for t in db.view_tokens.find({"tenant_id": tenant, "session_id": session_id, "closed_at": None}):
        if db.view_tokens.find_one_and_update({"_id": t["_id"], "closed_at": None}, {"$set": {"closed_at": now()}}):
            _event(db, tenant, session_id, t["reviewer_id"], t["case_id"], "close", 0, t["evidence_id"])  # once, not per racer


def fetch_evidence(tenant: str, session_id: str, case_id: str, evidence_id: str) -> dict:
    """Serving evidence opens a server view token and closes any other open token (exclusive focus)."""
    db = get_db()
    sess = _session(db, tenant, session_id)
    case = db.cases.find_one({"tenant_id": tenant, "case_id": case_id})
    ev = next((e for e in (case or {}).get("evidence", []) if e["evidence_id"] == evidence_id), None)
    if not ev:
        raise NotFound("unknown evidence")
    for attempt in range(15):  # unique partial index `one_open_view_per_session` makes parallel opens collide, not stack
        _close_open_tokens(db, tenant, session_id)
        tok, t0 = f"VT-{secrets.token_hex(8)}", now()
        try:
            db.view_tokens.insert_one({"tenant_id": tenant, "token": tok, "session_id": session_id, "reviewer_id": sess["reviewer_id"],
                                       "case_id": case_id, "evidence_id": evidence_id, "evidence_hash": ev["hash"],
                                       "opened_at": t0, "last_hb_at": t0, "active_ms": 0, "idle_ms": 0, "closed_at": None,
                                       "expire_at": t0 + timedelta(hours=2)})
            break
        except DuplicateKeyError:
            if attempt == 14:
                raise
            time.sleep(0.005 * (attempt + 1))  # another open raced us: back off, close its token, retry
    _event(db, tenant, session_id, sess["reviewer_id"], case_id, "open", 0, evidence_id)
    return {"evidence_id": evidence_id, "label": ev["label"], "content": ev["content"], "hash": ev["hash"],
            "view_token": tok, "opened_at": t0.isoformat()}


def heartbeat(tenant: str, token: str, visible: bool, interacted_within_ms: int) -> dict:
    db = get_db()
    t = db.view_tokens.find_one({"tenant_id": tenant, "token": token})
    if not t or t.get("closed_at"):
        return {"active_ms": (t or {}).get("active_ms", 0), "idle_ms": (t or {}).get("idle_ms", 0), "credited_ms": 0}
    n = now()
    credited = credit_heartbeat(t["last_hb_at"], n, visible, interacted_within_ms)
    gap = int((n - t["last_hb_at"]).total_seconds() * 1000)
    # Compare-and-set on last_hb_at: ten parallel heartbeats cannot each be credited the same gap (that would turn
    # 7 s of wall time into 70 s of dwell). Only the one that advances last_hb_at is credited; the rest get 0.
    t2 = db.view_tokens.find_one_and_update(
        {"_id": t["_id"], "last_hb_at": t["last_hb_at"], "closed_at": None},
        {"$set": {"last_hb_at": n}, "$inc": {"active_ms": credited, "idle_ms": max(0, gap - credited)}},
        return_document=True)
    if t2 is None:
        cur = db.view_tokens.find_one({"_id": t["_id"]}) or t
        return {"active_ms": cur["active_ms"], "idle_ms": cur["idle_ms"], "credited_ms": 0}
    _event(db, tenant, t["session_id"], t["reviewer_id"], t["case_id"], "heartbeat", credited, t["evidence_id"])
    return {"active_ms": t2["active_ms"], "idle_ms": t2["idle_ms"], "credited_ms": credited}


def close_view(tenant: str, token: str) -> dict:
    db = get_db()
    t = db.view_tokens.find_one_and_update({"tenant_id": tenant, "token": token, "closed_at": None},
                                           {"$set": {"closed_at": now()}}, return_document=True)
    if t:
        _event(db, tenant, t["session_id"], t["reviewer_id"], t["case_id"], "close", 0, t["evidence_id"])
    return {"active_ms": (t or {}).get("active_ms", 0)}


def _views_from_tokens(tokens) -> list[dict]:
    per: dict[str, dict] = {}
    for t in tokens:
        end = t.get("closed_at") or t["last_hb_at"]
        v = per.setdefault(t["evidence_id"], {"evidence_id": t["evidence_id"], "hash": t["evidence_hash"], "active_ms": 0, "open_ms": 0})
        v["active_ms"] += int(t["active_ms"])
        v["open_ms"] += int((end - t["opened_at"]).total_seconds() * 1000)
    return list(per.values())


def _views_for(db, tenant: str, session_id: str, case_id: str) -> list[dict]:
    return _views_from_tokens(db.view_tokens.find({"tenant_id": tenant, "session_id": session_id, "case_id": case_id}))


def _build_approval(tenant: str, sess: dict, prop: dict, rv: dict, pol: dict, views: list[dict], text: str,
                    client_extra: dict | None, created_at) -> dict:
    return {"tenant_id": tenant, "approval_id": _rid("AP"), "case_id": prop["case_id"], "proposal_id": prop["proposal_id"],
            "reviewer_id": sess["reviewer_id"], "session_id": sess["session_id"],
            "credential_snapshot": {k: rv[k] for k in ("license_no", "specialty", "license_expires_at")},
            "views": views, "evidence_hashes_viewed": sorted({v["hash"] for v in views}),
            "active_dwell_ms": int(sum(v["active_ms"] for v in views)), "policy_version_at_approval": int(pol["version"]),
            "attestation_text": text if len(text or "") >= 10 else (text or "").ljust(10, "."),
            "client_supplied_ignored": {k: v for k, v in (client_extra or {}).items()
                                        if k not in ("proposal_id", "attestation_text", "attestation_id")},
            "status": "submitted", "created_at": created_at}


def approve(tenant: str, session_id: str, proposal_id: str, attestation_text: str, client_extra: dict | None = None,
            attestation_id: str | None = None) -> dict:
    """Server computes views and dwell. Always stores the approval (it is evidence); the gate judges it."""
    db = get_db()
    sess = _session(db, tenant, session_id)
    prop = db.proposals.find_one({"tenant_id": tenant, "proposal_id": proposal_id})
    if not prop:
        raise NotFound("unknown proposal")
    if prop.get("status") not in ("pending_review", "needs_review"):
        raise BadRequest(f"proposal is {prop.get('status')}; it cannot be approved again")
    rv = db.reviewers.find_one({"tenant_id": tenant, "reviewer_id": sess["reviewer_id"]})
    pol = db.review_policies.find_one({"tenant_id": tenant, "action_type": prop["action_type"], "status": "active"})
    _close_open_tokens(db, tenant, session_id)
    views = _views_for(db, tenant, session_id, prop["case_id"])
    att = None
    if attestation_id:  # voice is evidence: copy the transcript, never change the gate's inputs
        att = db.attestations.find_one({"tenant_id": tenant, "attestation_id": attestation_id, "session_id": session_id,
                                        "case_id": prop["case_id"]})
        if not att:  # wrong case/session/tenant: one good recording cannot be reused across cases
            raise BadRequest("attestation does not belong to this session and case")
        attestation_text = att["transcript"]
    ap = _build_approval(tenant, sess, prop, rv, pol, views, attestation_text, client_extra, now())
    if att:
        ap["attestation_id"] = att["attestation_id"]
        ap["attestation_score"] = att["score"]["attestation_score"]
    rs_id = f"{tenant}|{sess['reviewer_id']}"

    def body(s):
        db.approvals.insert_one(ap, session=s)
        # Conditional: only a proposal still awaiting review can be approved. A concurrent gate call may have moved
        # it to authorized/executed; resetting that to `approved` would allow a second grant for the same case.
        r = db.proposals.update_one({"_id": prop["_id"], "status": {"$in": ["pending_review", "needs_review"]}},
                                    {"$set": {"status": "approved", "approved_by": sess["reviewer_id"],
                                              "approval_id": ap["approval_id"]}}, session=s)
        if r.matched_count == 0:
            raise BadRequest("proposal is no longer awaiting review")
        db.reviewer_state.update_one({"_id": rs_id}, {"$push": {"approval_ts": {"$each": [ap["created_at"]], "$slice": -100}},
                                                      "$inc": {"version": 1}}, session=s)
        _event(db, tenant, session_id, sess["reviewer_id"], prop["case_id"], "approve", 0, None, s)

    with client().start_session() as s:
        s.with_transaction(body)
    ap.pop("_id", None)
    return ap


def approve_bulk(tenant: str, session_id: str, proposal_ids: list[str], attestation_text: str) -> dict:
    """The deliberate 'Select all, approve 50' as ONE transaction.

    Same approvals as calling approve() in a loop (tests/test_bulk_approve.py compares them field by field), but the
    reads are batched and the writes are insert_many + bulk_write + one reviewer_state update + one chained event
    batch, so the cost is about a dozen round trips whether the batch is 5 or 100 (a loop was ~15 round trips per
    proposal: about a minute for 50 over the network). All-or-nothing: if any proposal moved on, nothing is stored."""
    db = get_db()
    pids = list(dict.fromkeys(proposal_ids))  # de-duplicate, keep order
    sess = _session(db, tenant, session_id)
    props = {p["proposal_id"]: p for p in db.proposals.find({"tenant_id": tenant, "proposal_id": {"$in": pids},
                                                             "status": {"$in": ["pending_review", "needs_review"]}})}
    missing = [p for p in pids if p not in props]
    if missing:  # validate everything first: a bad id must not leave half a batch approved
        raise BadRequest(f"{len(missing)} proposal id(s) unknown or not awaiting review, e.g. {missing[0]!r}; nothing was approved")
    rv = db.reviewers.find_one({"tenant_id": tenant, "reviewer_id": sess["reviewer_id"]})
    pols = {p["action_type"]: p for p in db.review_policies.find({"tenant_id": tenant, "status": "active",
                                                                  "action_type": {"$in": list({p["action_type"] for p in props.values()})}})}
    _close_open_tokens(db, tenant, session_id)
    by_case: dict[str, list] = {}
    for t in db.view_tokens.find({"tenant_id": tenant, "session_id": session_id,
                                  "case_id": {"$in": list({p["case_id"] for p in props.values()})}}):
        by_case.setdefault(t["case_id"], []).append(t)
    base = now()
    aps = []
    for i, pid in enumerate(pids):
        prop = props[pid]
        t = base + timedelta(milliseconds=i)  # distinct, ordered timestamps, as a sequential loop would produce
        aps.append(_build_approval(tenant, sess, prop, rv, pols[prop["action_type"]], _views_from_tokens(by_case.get(prop["case_id"], [])),
                                   attestation_text, None, t))
    rs_id = f"{tenant}|{sess['reviewer_id']}"

    def body(s):
        db.approvals.insert_many([dict(a) for a in aps], ordered=True, session=s)
        # conditional per proposal, exactly as approve(): a concurrent gate call may have moved one on
        r = db.proposals.bulk_write([UpdateOne({"_id": props[a["proposal_id"]]["_id"], "status": {"$in": ["pending_review", "needs_review"]}},
                                               {"$set": {"status": "approved", "approved_by": sess["reviewer_id"], "approval_id": a["approval_id"]}})
                                     for a in aps], ordered=True, session=s)
        if r.matched_count != len(aps):
            raise BadRequest("a proposal is no longer awaiting review; nothing was approved")
        db.reviewer_state.update_one({"_id": rs_id}, {"$push": {"approval_ts": {"$each": [a["created_at"] for a in aps], "$slice": -100}},
                                                      "$inc": {"version": 1}}, session=s)
        _events(db, tenant, session_id, sess["reviewer_id"], [{"case_id": a["case_id"], "type": "approve"} for a in aps], s)

    with client().start_session() as s:
        s.with_transaction(body)
    return {"submitted": len(aps), "approval_ids": [a["approval_id"] for a in aps]}
