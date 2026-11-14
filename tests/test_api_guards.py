"""Security guards on the HTTP API that need no database: every refusal here happens before any Mongo call."""
from __future__ import annotations

import dataclasses

import pytest
from fastapi.testclient import TestClient

from pg import agent, config, main

GOOD = "k" * 32


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "settings", dataclasses.replace(main.settings, console_key=GOOD, agent_service_key=GOOD))
    return TestClient(main.app)  # no `with`: lifespan (and its DB threads) does not run


@pytest.mark.parametrize("method,path,body", [
    ("post", "/api/sessions", {"tenant_id": "payer-acme", "reviewer_id": "dr-demo"}),
    ("post", "/api/policies", {"rules": {"baseline_only_existence": True}}),
    ("post", "/api/suspensions", {"reviewer_id": "dr-demo"}),
    ("post", "/api/agent/pause", {"paused": True}),
    ("post", "/api/agent/run-once", None),
])
@pytest.mark.parametrize("key", [None, "", "wrong", GOOD[:-1]])
def test_control_routes_need_console_key(client, method, path, body, key):
    headers = {"X-Tenant-Id": "payer-acme"} | ({"X-Console-Key": key} if key is not None else {})
    r = getattr(client, method)(path, json=body, headers=headers)
    assert r.status_code == 401


@pytest.mark.parametrize("key", [None, "", "dev-agent-key-change-me", "wrong"])
def test_gate_needs_agent_key(client, key):
    headers = {"X-Tenant-Id": "payer-acme", "X-Service-Identity": "triage-agent-v1"} | ({"X-Service-Key": key} if key is not None else {})
    r = client.post("/api/gate/execute", json={"proposal_id": "p", "approval_id": "a"}, headers=headers)
    assert r.status_code == 401


def test_compensate_route_is_gone(client):
    r = client.post("/target/claim/CLM-A-0002/compensate", json={"to_status": "DENIED"},
                    headers={"X-Tenant-Id": "payer-acme", "X-Compensation-For": "x"})
    assert r.status_code in (404, 405)


@pytest.mark.parametrize("agent_key,console_key,ok", [
    ("", GOOD, False),
    ("dev-agent-key-change-me", GOOD, False),
    (GOOD, "short", False),
    (GOOD, "", False),
    (GOOD, GOOD, True),
])
def test_startup_refuses_weak_keys(agent_key, console_key, ok):
    s = dataclasses.replace(config.settings, agent_service_key=agent_key, console_key=console_key)
    assert (config.key_problems(s) == []) is ok


def test_run_once_returns_when_paused(monkeypatch):
    class Coll:
        def find_one(self, *_a, **_k):
            return {"paused": True}

    class DB:
        agent_control = Coll()

    monkeypatch.setattr(agent, "get_db", lambda: DB())
    assert agent.executor_loop("payer-acme", once=True) == []
