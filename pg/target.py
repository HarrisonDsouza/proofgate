"""Mock target systems (claims, accounts): PRD M8. A record changes only by atomically consuming a valid grant."""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from pg.db import client, get_db, now

router = APIRouter(prefix="/target")


def _log(db, s, tenant, kind, record_id, caller, op, outcome, grant_id=None, denial_id=None):
    db.target_log.insert_one({"tenant_id": tenant, "kind": kind, "record_id": record_id, "ts": now(), "caller": caller,
                              "op": op, "outcome": outcome, "grant_id": grant_id, "denial_id": denial_id}, session=s)


def apply(tenant: str, kind: str, record_id: str, to_status: str, grant_header: str | None, caller: str) -> dict:
    db = get_db()
    gid = (grant_header or "").removeprefix("Grant ").strip()

    def body(s):
        g = db.grants.find_one_and_update(
            {"_id": gid, "status": "issued", "expires_at": {"$gt": now()}, "tenant_id": tenant, "record_id": record_id,
             "audience": f"target:{kind}", "to_status": to_status},
            {"$set": {"status": "used"}}, session=s)
        if not g:
            _log(db, s, tenant, kind, record_id, caller, "apply", "REFUSED_NO_GRANT" if not gid else "REFUSED_GRANT_INVALID", gid or None)
            return None
        t = now()
        db.target_records.update_one({"tenant_id": tenant, "kind": kind, "record_id": record_id},
                                     {"$set": {"status": to_status, "last_apply": {"grant_id": gid, "denial_id": g["denial_id"],
                                                                                   "reviewer_id": g["reviewer_id"], "at": t}},
                                      "$push": {"history": {"op": "apply", "to": to_status, "grant_id": gid, "at": t}}}, session=s)
        _log(db, s, tenant, kind, record_id, caller, "apply", "APPLIED", gid, g["denial_id"])
        return {"record_id": record_id, "status": to_status, "applied_by_grant": gid}

    with client().start_session() as s:
        out = s.with_transaction(body)
    if out is None:
        raise HTTPException(403, {"error": "NO_VALID_GRANT", "logged": True})
    return out


def compensate(tenant: str, kind: str, record_id: str, to_status: str, denial_id: str, caller: str) -> dict:
    """Idempotent per denial_id: a repeat call is a no-op."""
    db = get_db()
    rec = db.target_records.find_one({"tenant_id": tenant, "kind": kind, "record_id": record_id})
    if rec is None:
        raise HTTPException(404, "unknown record")
    if denial_id in rec.get("reopened_for", []):
        with client().start_session() as s:
            _log(db, s, tenant, kind, record_id, caller, "compensate", "NOOP_IDEMPOTENT", denial_id=denial_id)
        return {"status": rec["status"], "noop": True}
    db.target_records.update_one({"_id": rec["_id"]}, {"$set": {"status": to_status}, "$addToSet": {"reopened_for": denial_id},
                                                       "$push": {"history": {"op": "compensate", "to": to_status, "denial_id": denial_id, "at": now()}}})
    with client().start_session() as s:
        _log(db, s, tenant, kind, record_id, caller, "compensate", "COMPENSATED", denial_id=denial_id)
    return {"status": to_status, "noop": False}


@router.post("/{kind}/{record_id}/apply")
def apply_route(kind: str, record_id: str, body: dict, x_tenant_id: str = Header(...),
                authorization: str | None = Header(None), x_service_identity: str = Header("unknown")):
    return apply(x_tenant_id, kind, record_id, body.get("to_status", ""), authorization, x_service_identity)


# No HTTP compensate route: only the compensation worker (pg/detector.py) reopens records, by calling compensate()
# in-process from a stored compensation document. An open route let any caller set any status without a grant.


@router.get("/{kind}/{record_id}")
def read_route(kind: str, record_id: str, x_tenant_id: str = Header(...)):
    rec = get_db().target_records.find_one({"tenant_id": x_tenant_id, "kind": kind, "record_id": record_id}, {"_id": 0})
    if not rec:
        raise HTTPException(404)
    return {"status": rec["status"], "last_apply": rec.get("last_apply"), "reopened_for": rec.get("reopened_for", [])}
