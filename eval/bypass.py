"""`make bypass`: the agent calls the claims system directly, with no grant and with a stale grant. Both 403."""
from __future__ import annotations

from fastapi import HTTPException

from pg import target
from pg.db import get_db

T = "payer-acme"


def main():
    db = get_db()
    rec = db.target_records.find_one({"tenant_id": T, "status": "PENDING"})
    for label, header in [("no grant", None), ("made-up grant", "Grant g_" + "0" * 32)]:
        try:
            target.apply(T, "claim", rec["record_id"], "DENIED", header, "triage-agent-v1")
            print(f"FAIL {label}: target changed")
        except HTTPException as e:
            print(f"PASS {label}: {e.status_code} {e.detail}")
    after = db.target_records.find_one({"_id": rec["_id"]})
    print("PASS record unchanged" if after["status"] == "PENDING" else "FAIL record changed")
    print("target_log:", [x["outcome"] for x in db.target_log.find({"tenant_id": T, "record_id": rec["record_id"]})])


if __name__ == "__main__":
    main()
