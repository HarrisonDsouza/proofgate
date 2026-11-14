from pg.attest_score import boilerplate, pace, score, specificity

CASE = {"codes": {"icd10": ["M17.11"], "hcpcs": ["E0601"]},
        "evidence": [{"evidence_id": "E1", "label": "MRI right knee report", "content": "severe cartilage loss medial compartment"},
                     {"evidence_id": "E2", "label": "Physical therapy notes", "content": "twelve sessions completed no improvement"}]}


def test_specific_beats_generic():
    good = specificity("MRI of the right knee shows severe cartilage loss, M17.11, therapy twelve sessions", CASE)
    bad = specificity("I reviewed everything and it looks fine to deny", CASE)
    assert good["specificity"] > 0.5 > bad["specificity"] == 0.0
    assert "m17.11" in good["matched"]


def test_boilerplate_detected():
    t = "Reviewed knee MRI and therapy notes"
    assert boilerplate(t, [t]) == 1.0
    assert boilerplate(t, []) == 0.0


def test_pace_implausible_halves_score():
    assert pace("word " * 100, 2.0)["plausible"] is False
    t = "MRI knee cartilage loss M17.11 therapy sessions"
    fast = score(t, CASE, [], 0.5)["attestation_score"]
    ok = score(t, CASE, [], 6.0)["attestation_score"]
    assert fast < ok


def test_score_never_negative_and_bounded():
    s = score("", CASE, ["x"], None)
    assert 0.0 <= s["attestation_score"] <= 1.0


def test_unviewed_evidence_contradiction_detected():
    from pg.attest_score import unviewed_hits
    case = {"summary": "knee", "codes": {"icd10": ["M17.11"], "hcpcs": []},
            "evidence": [{"evidence_id": "E1", "label": "MRI", "content": "cartilage loss"},
                         {"evidence_id": "E2", "label": "PA letter", "content": "authorization PA-77213 expired"}]}
    assert unviewed_hits("mri cartilage loss and PA-77213 expired", case, {"E1"}) == ["expired", "pa-77213"]
    assert unviewed_hits("mri cartilage loss", case, {"E1"}) == []
    assert unviewed_hits("PA-77213", case, {"E1", "E2"}) == []
