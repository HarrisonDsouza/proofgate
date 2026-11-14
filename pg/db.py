"""Atlas connection, validators (presence/type only), tenant-led indexes, TTLs, and the smoke test.

    python -m pg.db --setup     # idempotent: collections, validators, indexes
    python -m pg.db --smoke     # one transaction + one change-stream event on THIS tier (12:40 checkpoint)
"""
from __future__ import annotations

import argparse
import threading
import time
from datetime import datetime, timezone
from functools import lru_cache

from pymongo import ASCENDING as A
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid

from pg.config import settings

HEX64 = "^[a-f0-9]{64}$"
T = {"bsonType": "string", "minLength": 1}

VALIDATORS = {
    "approvals": {"bsonType": "object",
                  "required": ["tenant_id", "approval_id", "case_id", "proposal_id", "reviewer_id", "session_id",
                               "credential_snapshot", "views", "evidence_hashes_viewed", "active_dwell_ms",
                               "policy_version_at_approval", "attestation_text", "status", "created_at"],
                  "properties": {"tenant_id": T,
                                 "credential_snapshot": {"bsonType": "object", "required": ["license_no", "specialty", "license_expires_at"]},
                                 "views": {"bsonType": "array", "items": {"bsonType": "object", "required": ["evidence_id", "hash", "active_ms", "open_ms"]}},
                                 "evidence_hashes_viewed": {"bsonType": "array", "items": {"bsonType": "string", "pattern": HEX64}},
                                 "active_dwell_ms": {"bsonType": ["int", "long"], "minimum": 0},
                                 "policy_version_at_approval": {"bsonType": ["int", "long"]},
                                 "attestation_text": {"bsonType": "string", "minLength": 10},
                                 "status": {"enum": ["submitted", "consumed", "refused", "invalidated"]},
                                 "created_at": {"bsonType": "date"}}},
    "denials": {"bsonType": "object",
                "required": ["tenant_id", "denial_id", "action_type", "case_id", "record_id", "approval_id", "reviewer_id",
                             "agent_id", "operator_id", "policy_id", "policy_version", "grant_id", "gate_decision_id",
                             "status", "created_at"],
                "properties": {"tenant_id": T, "policy_version": {"bsonType": ["int", "long"]},
                               "status": {"enum": ["AUTHORIZED", "CONFIRMED", "NOT_EXECUTED", "REVERSED"]},
                               "created_at": {"bsonType": "date"}}},
    "review_policies": {"bsonType": "object",
                        "required": ["tenant_id", "policy_id", "action_type", "version", "status", "rules", "effect", "rationale", "created_at"],
                        "properties": {"status": {"enum": ["active", "superseded"]},
                                       "rules": {"bsonType": "object", "required": ["min_active_dwell_ms", "min_item_active_ms", "rate_max_approvals",
                                                                                    "rate_window_ms", "median_n", "max_proposal_age_ms", "compensation_lookback_ms"]},
                                       "effect": {"bsonType": "object", "required": ["kind", "apply_status", "compensate_status"]}}},
    "suspensions": {"bsonType": "object", "required": ["tenant_id", "suspension_id", "reviewer_id", "active", "source", "rule",
                                                       "policy_id", "policy_version", "ts"]},
    "review_events": {"bsonType": "object", "required": ["tenant_id", "session_id", "seq", "reviewer_id", "case_id", "type", "ts", "credited_ms"],
                      "properties": {"type": {"enum": ["open", "heartbeat", "close", "approve"]}}},
    "reviewers": {"bsonType": "object", "required": ["tenant_id", "reviewer_id", "license_no", "specialty", "license_expires_at"]},
    "gate_decisions": {"bsonType": "object", "required": ["tenant_id", "decision_id", "case_id", "decision", "checks", "txn_attempts", "ts"],
                       "properties": {"decision": {"enum": ["ALLOW", "REFUSE"]}}},
    "grants": {"bsonType": "object", "required": ["tenant_id", "audience", "record_id", "denial_id", "status", "expires_at"],
               "properties": {"status": {"enum": ["issued", "used", "revoked", "expired"]}}},
    "compensations": {"bsonType": "object", "required": ["tenant_id", "denial_id", "record_id", "status"],
                      "properties": {"status": {"enum": ["pending", "confirmed"]}}},
    "proposals": {"bsonType": "object", "required": ["tenant_id", "proposal_id", "case_id", "status"],
                  "properties": {"status": {"enum": ["pending_review", "approved", "authorized", "executed", "needs_review", "reversed"]}}},
    "audit": {"bsonType": "object", "required": ["tenant_id", "ts", "actor", "event"]},
    "attestations": {"bsonType": "object",
                     "required": ["tenant_id", "attestation_id", "session_id", "reviewer_id", "case_id", "transcript", "source", "score", "created_at"],
                     "properties": {"tenant_id": T, "source": {"enum": ["elevenlabs_stt", "typed_fallback"]},
                                    "audio_sha256": {"bsonType": ["string", "null"]},
                                    "score": {"bsonType": "object", "required": ["attestation_score", "specificity", "boilerplate"]},
                                    "created_at": {"bsonType": "date"}}},
}
PLAIN = ["cases", "target_records", "target_log", "policy_clauses", "reviewer_sessions", "view_tokens",
         "reviewer_state", "chain_heads", "detector_state", "agent_control", "eval_runs", "telemetry_points"]

INDEXES = {
    "cases": [([("tenant_id", A), ("case_id", A)], {"unique": True})],
    "target_records": [([("tenant_id", A), ("kind", A), ("record_id", A)], {"unique": True}), ([("tenant_id", A), ("status", A)], {})],
    "target_log": [([("tenant_id", A), ("record_id", A), ("ts", A)], {})],
    "proposals": [([("tenant_id", A), ("proposal_id", A)], {"unique": True}), ([("tenant_id", A), ("status", A), ("created_at", A)], {}),
                  ([("tenant_id", A), ("approved_by", A), ("status", A)], {}), ([("tenant_id", A), ("case_id", A)], {})],
    "reviewers": [([("tenant_id", A), ("reviewer_id", A)], {"unique": True})],
    "reviewer_sessions": [([("tenant_id", A), ("session_id", A)], {"unique": True})],
    "view_tokens": [([("tenant_id", A), ("session_id", A), ("case_id", A)], {}), ([("tenant_id", A), ("session_id", A), ("closed_at", A)], {}),
                    ([("expire_at", A)], {"expireAfterSeconds": 0})],
    "review_events": [([("tenant_id", A), ("session_id", A), ("seq", A)], {"unique": True}), ([("tenant_id", A), ("case_id", A), ("ts", A)], {}),
                      ([("tenant_id", A), ("reviewer_id", A), ("ts", A)], {})],
    "approvals": [([("tenant_id", A), ("approval_id", A)], {"unique": True}), ([("tenant_id", A), ("reviewer_id", A), ("created_at", A)], {}),
                  ([("tenant_id", A), ("case_id", A)], {})],
    "review_policies": [([("tenant_id", A), ("action_type", A), ("version", A)], {"unique": True}),
                        ([("tenant_id", A), ("action_type", A)], {"unique": True, "partialFilterExpression": {"status": "active"},
                                                                    "name": "one_active_policy"})],
    "gate_decisions": [([("tenant_id", A), ("case_id", A), ("ts", A)], {}), ([("tenant_id", A), ("reviewer_id", A), ("ts", A)], {})],
    "denials": [([("tenant_id", A), ("denial_id", A)], {"unique": True}), ([("approval_id", A)], {"unique": True}),
                ([("tenant_id", A), ("case_id", A)], {}), ([("tenant_id", A), ("reviewer_id", A), ("status", A), ("confirmed_at", A)], {})],
    "grants": [([("tenant_id", A), ("reviewer_id", A), ("status", A)], {}), ([("ttl_at", A)], {"expireAfterSeconds": 0})],
    "suspensions": [([("tenant_id", A), ("reviewer_id", A), ("ts", A)], {}),
                    ([("tenant_id", A), ("reviewer_id", A)], {"unique": True, "partialFilterExpression": {"active": True},
                                                            "name": "one_active_suspension"})],
    "compensations": [([("denial_id", A)], {"unique": True}), ([("status", A), ("next_attempt_at", A)], {})],
    "attestations": [([("tenant_id", A), ("attestation_id", A)], {"unique": True}),
                     ([("tenant_id", A), ("reviewer_id", A), ("created_at", A)], {}), ([("tenant_id", A), ("case_id", A)], {})],
    "audit": [([("tenant_id", A), ("case_id", A), ("ts", A)], {}), ([("tenant_id", A), ("reviewer_id", A), ("ts", A)], {})],
}


@lru_cache(maxsize=1)
def client() -> MongoClient:
    if not settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI not set: use the event's Atlas SANDBOX cluster")
    return MongoClient(settings.mongodb_uri, appname="proofgate", retryWrites=True, tz_aware=True)


def get_db():
    return client()[settings.db_name]


def now() -> datetime:
    return datetime.now(timezone.utc)


def setup(db=None) -> None:
    db = db if db is not None else get_db()
    have = set(db.list_collection_names())
    for name, schema in VALIDATORS.items():
        opts = {"validator": {"$jsonSchema": schema}, "validationLevel": "strict", "validationAction": "error"}
        if name in have:
            db.command("collMod", name, **opts)
        else:
            db.create_collection(name, **opts)
    for name in PLAIN:
        if name not in have:
            try:
                db.create_collection(name)
            except CollectionInvalid:
                pass
    for coll, specs in INDEXES.items():
        for keys, opts in specs:
            db[coll].create_index(keys, **opts)


def smoke() -> None:
    """The 12:40 go/no-go: a multi-document transaction and a change-stream event on this tier."""
    db = get_db()
    db.smoke.drop()
    with client().start_session() as s:
        s.with_transaction(lambda ss: (db.smoke.insert_one({"_id": "a"}, session=ss), db.smoke.insert_one({"_id": "b"}, session=ss)))
    assert db.smoke.count_documents({}) == 2
    print("PASS transaction (2 docs committed atomically)")
    got = {}

    def watch():
        with db.smoke.watch(max_await_time_ms=5000) as cs:
            for ch in cs:
                got["ev"] = ch["operationType"]
                return

    th = threading.Thread(target=watch)
    th.start()
    time.sleep(1.0)
    db.smoke.insert_one({"_id": "c"})
    th.join(timeout=10)
    print("PASS change stream" if got.get("ev") == "insert" else "FAIL change stream: ask MongoDB staff for another tier NOW")
    db.smoke.drop()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.setup:
        setup()
        print("collections, validators, indexes ready")
    if a.smoke:
        smoke()
