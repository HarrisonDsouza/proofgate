"""Gate invariant, property-tested: ALLOW iff every one of G1-G8 holds. If this fails, nothing else matters."""
from datetime import datetime, timedelta, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from pg.checks import credit_heartbeat, evaluate

NOW = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)
RULES = {"min_active_dwell_ms": 30000, "min_item_active_ms": 5000, "rate_max_approvals": 10, "rate_window_ms": 60000,
         "median_n": 5, "require_specialty_match": True, "max_proposal_age_ms": 86400000, "compensation_lookback_ms": 3600000}
H = {"E1": "a" * 64, "E3": "b" * 64}


def world(*, status="submitted", suspended=False, paused=False, expired=False, specialty="orthopedics",
          viewed=("E1", "E3"), dwell=40000, item_ms=20000, window=1, age_h=1, reviewer_id="dr-demo", changed_hash=False):
    case = {"case_id": "C1", "specialty": "orthopedics",
            "evidence": [{"evidence_id": e, "hash": ("c" * 64 if (changed_hash and e == "E1") else h)} for e, h in H.items()]}
    proposal = {"proposal_id": "P1", "case_id": "C1", "status": "approved", "approval_id": "AP1", "operator_id": "op-ops-1", "agent_id": "triage-agent-v1",
                "cited_evidence": [{"evidence_id": e, "hash": h} for e, h in H.items()], "created_at": NOW - timedelta(hours=age_h)}
    reviewer = {"reviewer_id": reviewer_id, "license_no": "L1", "specialty": specialty,
                "license_expires_at": NOW - timedelta(days=1) if expired else NOW + timedelta(days=300)}
    approval = {"tenant_id": "t", "approval_id": "AP1", "case_id": "C1", "proposal_id": "P1", "status": status, "reviewer_id": reviewer_id,
                "credential_snapshot": {"license_no": "L1", "specialty": specialty},
                "views": [{"evidence_id": e, "active_ms": item_ms} for e in viewed],
                "evidence_hashes_viewed": [H[e] for e in viewed], "active_dwell_ms": dwell}
    return dict(approval=approval, proposal=proposal, case=case, policy={"rules": RULES}, reviewer=reviewer,
                reviewer_state={"suspended": suspended}, active_suspension=False, paused=paused, window_count=window,
                now=NOW, tenant_id="t")


@settings(max_examples=400)
@given(status=st.sampled_from(["submitted", "consumed", "refused"]), suspended=st.booleans(), paused=st.booleans(),
       expired=st.booleans(), specialty=st.sampled_from(["orthopedics", "cardiology"]),
       viewed=st.sampled_from([("E1", "E3"), ("E1",), ()]), dwell=st.integers(0, 90000), item_ms=st.integers(0, 40000),
       window=st.integers(0, 30), age_h=st.integers(0, 48), reviewer_id=st.sampled_from(["dr-demo", "op-ops-1"]),
       changed_hash=st.booleans())
def test_allow_iff_all_rules_hold(status, suspended, paused, expired, specialty, viewed, dwell, item_ms, window, age_h,
                                  reviewer_id, changed_hash):
    allow, checks = evaluate(**world(status=status, suspended=suspended, paused=paused, expired=expired, specialty=specialty,
                                     viewed=viewed, dwell=dwell, item_ms=item_ms, window=window, age_h=age_h,
                                     reviewer_id=reviewer_id, changed_hash=changed_hash))
    expected = (status == "submitted" and not suspended and not paused and not expired and specialty == "orthopedics"
                and viewed == ("E1", "E3") and not changed_hash and dwell >= 30000 and item_ms >= 5000 and window < 10
                and age_h <= 24 and reviewer_id != "op-ops-1")
    assert allow == expected
    assert allow == all(c["pass"] for c in checks)


def test_missing_approval_fails_closed():
    w = world()
    w["approval"] = None
    assert evaluate(**w)[0] is False


def test_baseline_policy_only_checks_existence():
    w = world(dwell=0, viewed=())
    w["policy"] = {"rules": RULES | {"baseline_only_existence": True}}
    allow, checks = evaluate(**w)
    assert allow and [c["rule"] for c in checks] == ["G1_APPROVAL_FOR_CASE"]


def test_refusal_reasons_name_the_floor():
    allow, checks = evaluate(**world(dwell=400, item_ms=200))
    g5 = next(c for c in checks if c["rule"] == "G5_DWELL")
    assert not allow and "0.4 s < 30 s floor" in g5["detail"]


# ---------- server-side dwell crediting ----------
T0 = datetime(2026, 11, 14, tzinfo=timezone.utc)


def test_credit_normal_heartbeat():
    assert credit_heartbeat(T0, T0 + timedelta(seconds=5), True, 1000) == 5000


def test_no_credit_when_hidden_idle_or_gap_too_long():
    assert credit_heartbeat(T0, T0 + timedelta(seconds=5), False, 1000) == 0
    assert credit_heartbeat(T0, T0 + timedelta(seconds=5), True, 20000) == 0
    assert credit_heartbeat(T0, T0 + timedelta(seconds=9), True, 1000) == 0


@given(st.lists(st.tuples(st.floats(0, 20), st.booleans(), st.integers(0, 30000)), max_size=60))
def test_credited_time_never_exceeds_wall_clock(beats):
    t, total, credited = T0, 0.0, 0
    for gap, vis, inter in beats:
        nxt = t + timedelta(seconds=gap)
        credited += credit_heartbeat(t, nxt, vis, inter)
        total += gap
        t = nxt
    assert credited <= total * 1000 + 1


def test_policy_validator_allows_only_tightening_of_known_int_keys():
    import pytest

    from pg.gate import PolicyRejected, validate_policy_change
    cur = {"min_active_dwell_ms": 30000, "rate_max_approvals": 10, "max_proposal_age_ms": 86400000}
    assert validate_policy_change(cur, {"min_active_dwell_ms": 60000, "rate_max_approvals": 5}) == {"min_active_dwell_ms": 60000, "rate_max_approvals": 5}
    for bad in ({"min_active_dwell_ms": 1000},                 # loosens a floor
                {"rate_max_approvals": 500},                    # loosens a cap
                {"max_proposal_age_ms": 10 ** 12},              # loosens an age and exceeds the range
                {"baseline_only_existence": True},              # switches the gate off
                {"require_specialty_match": False},
                {"median_n": 1},
                {"min_active_dwell_ms": "60000"},               # wrong type
                {"min_active_dwell_ms": 60000.5},
                {"min_active_dwell_ms": True},                  # bool is not an int here
                {"min_active_dwell_ms": 0},
                {}, [], None):
        with pytest.raises(PolicyRejected):
            validate_policy_change(cur, bad)
