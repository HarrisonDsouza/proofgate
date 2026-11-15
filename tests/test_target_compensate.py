"""compensate() is idempotent per denial_id even under concurrency (one atomic conditional update)."""
import secrets
from concurrent.futures import ThreadPoolExecutor

import pytest

from pg.target import compensate


def test_concurrent_compensate_applies_once(scratch):
    from pg.db import get_db
    db = get_db()
    rec = db.target_records.find_one({"tenant_id": scratch})
    if rec is None:
        pytest.skip("scratch tenant has no target record")
    did = "den-" + secrets.token_hex(3)
    with ThreadPoolExecutor(8) as ex:
        outs = list(ex.map(lambda _: compensate(scratch, rec["kind"], rec["record_id"], "OPEN", did, "test"), range(8)))
    assert sum(1 for o in outs if not o["noop"]) == 1
    after = db.target_records.find_one({"_id": rec["_id"]})
    assert after["reopened_for"].count(did) == 1
    assert sum(1 for h in after["history"] if h.get("op") == "compensate" and h.get("denial_id") == did) == 1
