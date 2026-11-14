import json

from fastapi.testclient import TestClient

from pg import main


def test_langsmith_info_never_exposes_the_key(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "lsv2_secret_value")
    monkeypatch.setenv("LANGSMITH_PROJECT_URL", "https://smith.langchain.com/o/x/projects/p/y")
    r = TestClient(main.app).get("/api/observability/langsmith")
    assert r.status_code == 200
    assert r.json() == {"enabled": True, "project": "proofgate", "project_url": "https://smith.langchain.com/o/x/projects/p/y"}
    assert "lsv2_secret_value" not in json.dumps(r.json())


def test_langsmith_info_off_and_rejects_non_https_url(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGSMITH_API_KEY", "k")
    monkeypatch.setenv("LANGSMITH_PROJECT_URL", "javascript:alert(1)")
    j = TestClient(main.app).get("/api/observability/langsmith").json()
    assert j["enabled"] is False and j["project_url"] is None
