"""Live-DB tests run in a THROWAWAY tenant, never in the demo tenant `payer-acme`.

Any test module that declares `T = "payer-acme"` gets T rebound to a fresh seeded tenant for the duration of each test
(and `eval.test_conflict.T`, which the shared fixture helper reads). The tenant's data is deleted afterwards. A test
that mutates reviewers, suspensions, approvals or policies therefore cannot damage the seeded demo or other people's runs.
"""
import os
import secrets

import pytest


def _live() -> bool:
    return bool(os.getenv("MONGODB_URI"))


@pytest.fixture()
def scratch():
    """An explicitly requested throwaway tenant (for tests that are not module-level T based)."""
    if not _live():
        pytest.skip("needs MongoDB")
    from pg.db import get_db
    from seed.generate import reset, seed_tenant
    db = get_db()
    tenant = f"scratch-{secrets.token_hex(4)}"
    seed_tenant(db, tenant, 60, 7)
    try:
        yield tenant
    finally:
        reset(db, tenant)
        for coll in ("attestations", "reviewer_stats", "detector_state"):
            if coll != "detector_state":
                db[coll].delete_many({"tenant_id": tenant})


@pytest.fixture(autouse=True)
def _scratch_for_module_tenant(request, monkeypatch):
    mod = request.module
    if not _live() or getattr(mod, "T", None) != "payer-acme":
        yield
        return
    from pg.db import get_db
    from seed.generate import reset, seed_tenant
    db = get_db()
    tenant = f"scratch-{secrets.token_hex(4)}"
    seed_tenant(db, tenant, 60, 7)
    monkeypatch.setattr(mod, "T", tenant)
    import eval.test_conflict as tc
    monkeypatch.setattr(tc, "T", tenant)
    try:
        yield
    finally:
        reset(db, tenant)
        for coll in ("attestations", "reviewer_stats"):
            db[coll].delete_many({"tenant_id": tenant})
