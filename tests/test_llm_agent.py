"""The LLM proposes, code decides: validation of Claude's tool call and the fallback to rules (offline, no API calls)."""
import dataclasses

import pytest

from pg import llm_agent

CASE = {"case_id": "CLM-T-0001", "specialty": "orthopedics", "billed_amount": 480,
        "evidence": [{"evidence_id": "E1", "label": "Claim line", "content": "HCPCS L1832", "hash": "h1"},
                     {"evidence_id": "E3", "label": "Prior-auth record", "content": "Prior-auth record: none on file", "hash": "h3"}]}
CLAUSES = [{"clause_id": "MP-001", "text": "Orthotics need prior auth."}, {"clause_id": "MP-002", "text": "DME rules."}]


def test_valid_call_uses_case_hashes_not_model_text():
    out = llm_agent._validate(CASE, CLAUSES, {"recommendation": "deny", "cited_evidence_ids": ["E1", "E3"],
                                              "clause_id": "MP-001", "rationale": "No prior auth on file."})
    assert out["cited_evidence"] == [{"evidence_id": "E1", "hash": "h1"}, {"evidence_id": "E3", "hash": "h3"}]
    assert out["cited_clauses"] == ["MP-001"]


@pytest.mark.parametrize("bad", [
    {"recommendation": "deny", "cited_evidence_ids": ["E1", "E9"], "clause_id": "MP-001", "rationale": "x"},  # invented evidence
    {"recommendation": "deny", "cited_evidence_ids": [], "clause_id": "MP-001", "rationale": "x"},  # cites nothing
    {"recommendation": "deny", "cited_evidence_ids": ["E1"], "clause_id": "MP-999", "rationale": "x"},  # invented clause
    {"recommendation": "approve", "cited_evidence_ids": ["E1"], "clause_id": "MP-001", "rationale": "x"},
    {"recommendation": "deny", "cited_evidence_ids": ["E1"], "clause_id": "MP-001", "rationale": "  "},
])
def test_invalid_calls_are_rejected(bad):
    with pytest.raises(ValueError):
        llm_agent._validate(CASE, CLAUSES, bad)


def test_bad_model_output_falls_back_to_rules(monkeypatch):
    monkeypatch.setattr(llm_agent, "settings", dataclasses.replace(llm_agent.settings, anthropic_api_key="test-not-a-key"))
    monkeypatch.setattr(llm_agent, "_ask_claude", lambda c, cl: {"recommendation": "deny", "cited_evidence_ids": ["E7"],
                                                                 "clause_id": "MP-001", "rationale": "x"})
    fields, proposer, why = llm_agent.triage(CASE, CLAUSES)
    assert proposer == "rules-v1" and "not in case" in why
    assert fields["recommendation"] == "deny"


def test_good_model_output_is_recorded_as_llm(monkeypatch):
    monkeypatch.setattr(llm_agent, "settings", dataclasses.replace(llm_agent.settings, anthropic_api_key="test-not-a-key"))
    monkeypatch.setattr(llm_agent, "_ask_claude", lambda c, cl: {"recommendation": "deny", "cited_evidence_ids": ["E3"],
                                                                 "clause_id": "MP-002", "rationale": "No PA."})
    fields, proposer, why = llm_agent.triage(CASE, CLAUSES)
    assert proposer.startswith("llm:") and why is None and fields["cited_clauses"] == ["MP-002"]


def test_timeout_falls_back(monkeypatch):
    monkeypatch.setattr(llm_agent, "settings", dataclasses.replace(llm_agent.settings, anthropic_api_key="test-not-a-key"))

    def slow(c, cl):
        raise TimeoutError("8 s")
    monkeypatch.setattr(llm_agent, "_ask_claude", slow)
    _, proposer, why = llm_agent.triage(CASE, CLAUSES)
    assert proposer == "rules-v1" and why.startswith("TimeoutError")
