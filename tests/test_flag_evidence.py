"""/api/reviewers/{id}/flag-evidence shows the suspension and the reviewer's own dwell series, tenant-scoped."""
from fastapi.testclient import TestClient

from pg.main import app


def test_flag_evidence_shape_and_tenant_scope(scratch):
    from pg.db import get_db
    db = get_db()
    rid = db.reviewer_state.find_one({"tenant_id": scratch})["reviewer_id"]
    c = TestClient(app)
    r = c.get(f"/api/reviewers/{rid}/flag-evidence", headers={"x-tenant-id": scratch})
    assert r.status_code == 200
    body = r.json()
    assert body["reviewer_id"] == rid and body["floor_ms"] == 30000
    assert isinstance(body["dwell"], list) and body["suspension"] is None
    other = c.get(f"/api/reviewers/{rid}/flag-evidence", headers={"x-tenant-id": scratch + "-nope"}).json()
    assert other["dwell"] == [] and other["suspension"] is None


def test_limit_is_bounded(scratch):
    c = TestClient(app)
    r = c.get("/api/reviewers/x/flag-evidence?limit=100000", headers={"x-tenant-id": scratch})
    assert r.status_code == 422
