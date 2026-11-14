"""Tracing must redact grant ids on every span and change nothing when LangSmith is off."""
import json
from unittest import mock

import langsmith
from langsmith import tracing_context

from pg import agent
from pg import observability as obs

GRANT = "g_" + "ab12cd34" * 4


def test_redact_cuts_grant_ids_to_six_chars():
    out = obs.redact_grants({"grant_id": GRANT, "target": {"applied_by_grant": GRANT},
                             "hdr": f"Grant {GRANT}", "list": [GRANT], "n": 3})
    assert out["grant_id"] == "g_ab12…"
    assert out["target"]["applied_by_grant"] == "g_ab12…"
    assert out["hdr"] == "Grant g_ab12…"
    assert out["list"] == ["g_ab12…"]
    assert out["n"] == 3
    assert GRANT not in json.dumps(out)


def test_redact_does_not_mutate_input():
    src = {"grant_id": GRANT}
    obs.redact_grants(src)
    assert src["grant_id"] == GRANT


def _fake_gate_target():
    res = {"decision": "ALLOW", "grant_id": GRANT, "denial_id": "D1",
           "target": {"kind": "claim", "record_id": "R1", "to_status": "denied"}}
    return (mock.patch.object(agent.gate, "execute", return_value=res),
            mock.patch.object(agent.target, "apply", return_value={"applied_by_grant": GRANT}),
            mock.patch.object(agent.gate, "confirm", return_value={"readback": {"grant_id": GRANT, "ok": True}}))


def test_execute_one_result_is_identical_with_tracing_off():
    g, t, c = _fake_gate_target()
    with tracing_context(enabled=False), g, t as apply, c:
        out = agent.execute_one("payer-acme", {"proposal_id": "P1", "approval_id": "A1", "case_id": "C1"})
    assert out["grant_id"] == GRANT                     # the real value still flows to the caller
    assert out["confirm"]["readback"]["ok"] is True
    assert apply.call_args.args[4] == f"Grant {GRANT}"  # the claims system still gets the full grant


def test_uploaded_runs_never_contain_a_full_grant_id():
    client = mock.MagicMock(spec=langsmith.Client)
    sent = []
    client.create_run.side_effect = lambda **kw: sent.append(kw)
    client.update_run.side_effect = lambda *a, **kw: sent.append(kw)
    g, t, c = _fake_gate_target()
    with tracing_context(enabled=True, client=client), g, t, c:
        agent.execute_one("payer-acme", {"proposal_id": "P1", "approval_id": "A1", "case_id": "C1"})
    blob = json.dumps(sent, default=str)
    assert "gate_execute" in blob and "target_apply" in blob and "gate_confirm" in blob and "execute_one" in blob
    assert GRANT not in blob
    assert "g_ab12" in blob
