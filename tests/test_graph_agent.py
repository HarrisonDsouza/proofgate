"""LangGraph triage agent: graph plumbing, code-side validation, fallback labelling and Atlas checkpoints.

Voyage is replaced by a fake (no network, no key needed); Atlas is real, in a throwaway tenant.
The fake judge is told what to answer, so these tests check what the agent does with a judgment, not model quality.
"""
import dataclasses
import random
from datetime import datetime, timezone
from types import SimpleNamespace as NS

import pytest

from pg import graph_agent as ga


class FakeVoyage:
    def __init__(self, unmet_wins=True, cite=None):
        self.unmet_wins, self.cite, self.calls = unmet_wins, cite, []

    def embed(self, texts, **kw):
        self.calls.append("embed")
        return NS(embeddings=[[0.1] * ga.DIMS for _ in texts])

    def rerank(self, query, documents, model, **kw):
        self.calls.append("rerank")
        if len(documents) == 2 and documents[0].startswith("The policy condition is satisfied"):
            met, unmet = (0.2, 0.8) if self.unmet_wins else (0.8, 0.2)
            return NS(results=[NS(index=1, relevance_score=unmet), NS(index=0, relevance_score=met)])
        idx = self.cite if self.cite is not None else list(range(len(documents)))
        return NS(results=[NS(index=i, relevance_score=1 - j / 10) for j, i in enumerate(idx)])


@pytest.fixture()
def voyage_on(monkeypatch, scratch):
    monkeypatch.setattr(ga, "settings", dataclasses.replace(ga.settings, voyage_api_key="test-not-a-key"))
    clauses = list(ga.get_db().policy_clauses.find({"tenant_id": scratch}, {"_id": 0, "clause_id": 1, "text": 1}))
    monkeypatch.setattr(ga, "vector_search", lambda db, t, v, k=8: [c | {"score": 0.9} for c in clauses[:k]])
    return scratch


def _case(tenant, i=1):
    from seed.generate import make_case
    c = make_case(random.Random(i), tenant, 900 + i, "orthopedics", datetime.now(timezone.utc))
    c["case_id"] = c["case_id"].replace("CLM-", "CLM-T")
    return c


def test_agent_denies_when_judge_says_unmet_and_writes_pending_proposal(voyage_on, monkeypatch):
    fake = FakeVoyage(unmet_wins=True)
    monkeypatch.setattr(ga, "_voyage", lambda: fake)
    c = _case(voyage_on)
    s = ga.run_case(voyage_on, c, ga.build_graph())
    assert s["proposer"].startswith("graph:voyage/") and s["fallback_reason"] is None
    assert s["proposal"]["recommendation"] == "deny"
    assert {"embed", "rerank"} <= set(fake.calls)
    p = ga.get_db().proposals.find_one({"tenant_id": voyage_on, "case_id": c["case_id"]})
    assert p["status"] == "pending_review" and p["proposer"].startswith("graph:")  # proposes only; humans + gate decide
    hashes = {e["evidence_id"]: e["hash"] for e in c["evidence"]}
    assert all(x["hash"] == hashes[x["evidence_id"]] for x in p["cited_evidence"])  # hashes from the case, not the model


def test_agent_pays_when_judge_is_not_clear(voyage_on, monkeypatch):
    monkeypatch.setattr(ga, "_voyage", lambda: FakeVoyage(unmet_wins=False))
    s = ga.run_case(voyage_on, _case(voyage_on, 2), ga.build_graph())
    assert s["proposal"]["recommendation"] == "pay" and s["proposer"].startswith("graph:")


def test_invalid_judgment_is_replaced_by_rule_and_labelled(voyage_on, monkeypatch):
    monkeypatch.setattr(ga, "_voyage", lambda: FakeVoyage())
    real_decide = ga.decide

    def bad_decide(state):
        out = real_decide(state)
        out["decision"]["cited_evidence_ids"] = ["E9"]  # evidence that does not exist
        return out
    monkeypatch.setattr(ga, "decide", bad_decide)
    s = ga.run_case(voyage_on, _case(voyage_on, 3), ga.build_graph())
    assert s["proposer"] == "rules-v1" and "not in case" in s["fallback_reason"]


def test_no_key_runs_rule_and_says_so(scratch, monkeypatch):
    monkeypatch.setattr(ga, "settings", dataclasses.replace(ga.settings, voyage_api_key=""))
    s = ga.run_case(scratch, _case(scratch, 4), ga.build_graph())
    assert s["proposer"] == "rules-v1" and s["fallback_reason"] == "no VOYAGE_API_KEY"


def test_model_error_does_not_lose_the_claim(voyage_on, monkeypatch):
    def boom():
        raise TimeoutError("voyage down")
    monkeypatch.setattr(ga, "_voyage", boom)
    c = _case(voyage_on, 5)
    s = ga.run_case(voyage_on, c, ga.build_graph())
    assert s["proposer"] == "rules-v1" and s["fallback_reason"].startswith("TimeoutError")
    assert ga.get_db().proposals.find_one({"tenant_id": voyage_on, "case_id": c["case_id"]})


def test_state_is_checkpointed_in_atlas(voyage_on, monkeypatch):
    monkeypatch.setattr(ga, "_voyage", lambda: FakeVoyage())
    c = _case(voyage_on, 6)
    thread = f"{voyage_on}|{c['case_id']}"
    try:
        ga.run_case(voyage_on, c, ga.build_graph(ga._checkpointer()))
        assert ga.get_db()[ga.CHECKPOINTS[0]].count_documents({"thread_id": thread}) >= 6  # one per node at least
    finally:
        for coll in ga.CHECKPOINTS:
            ga.get_db()[coll].delete_many({"thread_id": thread})
