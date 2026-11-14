"""Live-DB concurrency tests (skipped without MONGODB_URI): the gate is a serialisation point, not just a check."""
import os
import threading
import time

import pytest

pytestmark = pytest.mark.skipif(not os.getenv("MONGODB_URI"), reason="needs MongoDB")
T = "payer-acme"


def _reset(db, reviewer):
    db.suspensions.delete_many({"tenant_id": T, "reviewer_id": reviewer})
    db.reviewer_state.update_one({"_id": f"{T}|{reviewer}"}, {"$set": {"suspended": False}, "$unset": {"suspension_id": ""}})
    db.approvals.delete_many({"tenant_id": T, "reviewer_id": reviewer, "session_id": "S-test"})


def test_one_approval_cannot_be_spent_twice():
    from eval.test_conflict import seeded_honest_approval
    from pg import gate
    from pg.config import AGENT_ID, OPERATOR_ID
    from pg.db import get_db
    db = get_db()
    _reset(db, "dr-prep")
    p, ap = seeded_honest_approval(db, "dr-prep")
    out, ths = [], []
    for _ in range(8):
        ths.append(threading.Thread(target=lambda: out.append(gate.execute(T, p["proposal_id"], ap["approval_id"], AGENT_ID, OPERATOR_ID))))
    [t.start() for t in ths]
    [t.join() for t in ths]
    assert sum(o["decision"] == "ALLOW" for o in out) == 1
    assert db.denials.count_documents({"tenant_id": T, "approval_id": ap["approval_id"]}) == 1
    assert db.grants.count_documents({"tenant_id": T, "approval_id": ap["approval_id"]}) == 1


def test_no_allow_commits_after_a_suspension():
    from eval.test_conflict import seeded_honest_approval
    from pg import gate
    from pg.config import AGENT_ID, OPERATOR_ID
    from pg.db import get_db
    db = get_db()
    _reset(db, "dr-late")
    fx = [seeded_honest_approval(db, "dr-late") for _ in range(8)]  # 8 < rate_max 10, so G6 does not interfere
    out = []

    def run(p, ap):
        out.append(gate.execute(T, p["proposal_id"], ap["approval_id"], AGENT_ID, OPERATOR_ID))

    ths = [threading.Thread(target=run, args=f) for f in fx]
    def suspender():  # suspend only after at least one denial was authorised, so the test is not vacuous
        end = time.time() + 5
        while time.time() < end and not any(o["decision"] == "ALLOW" for o in list(out)):
            time.sleep(0.001)
        gate.suspend(T, "dr-late", "supervisor", "STRESS", {})

    ths.append(threading.Thread(target=suspender))
    [t.start() for t in ths]
    [t.join() for t in ths]
    susp = db.suspensions.find_one({"tenant_id": T, "reviewer_id": "dr-late", "active": True})
    assert susp is not None
    assert any(o["decision"] == "ALLOW" for o in out) and any(o["decision"] == "REFUSE" for o in out), "race did not occur"
    late_allow = db.gate_decisions.count_documents({"tenant_id": T, "reviewer_id": "dr-late", "decision": "ALLOW", "ts": {"$gt": susp["ts"]}})
    assert late_allow == 0, "an ALLOW decision was committed after the suspension"
    for o in out:  # every ALLOW before the suspension must have been reopened by the compensation record
        if o["decision"] == "ALLOW":
            assert db.compensations.count_documents({"denial_id": o["denial_id"]}) <= 1
