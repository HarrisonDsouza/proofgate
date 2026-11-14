"""PRD M10 demo, automated: kill the detector mid-burst, restart it, exactly ONE suspension results.

    python -m eval.test_detector_restart            (needs MONGODB_URI; run `make seed` first)
The detector runs as its own OS process (RUN_BACKGROUND=0 make detector). We SIGKILL it with the burst half
written, finish the burst while no detector is alive, restart it, and check it resumes from the stored token,
suspends once, and that a second kill/restart does not create a second suspension.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

from pg import review
from pg.db import get_db

T, REVIEWER = "payer-acme", "dr-prep"


def report(name: str, ok: bool) -> bool:
    print(("PASS " if ok else "FAIL ") + name)
    return ok


def start() -> subprocess.Popen:
    env = {**os.environ, "RUN_BACKGROUND": "0"}
    return subprocess.Popen([sys.executable, "-m", "pg.detector"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_for(pred, secs: float = 15.0) -> bool:
    end = time.time() + secs
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.2)
    return False


def main() -> int:
    db = get_db()
    db.suspensions.delete_many({"tenant_id": T, "reviewer_id": REVIEWER})
    db.reviewer_state.update_one({"_id": f"{T}|{REVIEWER}"}, {"$set": {"suspended": False}, "$unset": {"suspension_id": ""}})
    db.reviewer_stats.delete_one({"_id": f"{T}|{REVIEWER}"})
    for r in (REVIEWER, "dr-skim"):  # a clean slate: earlier runs' approvals would count toward the median/CUSUM
        db.approvals.delete_many({"tenant_id": T, "reviewer_id": r})
    ids = [p["proposal_id"] for p in db.proposals.find({"tenant_id": T, "status": "pending_review", "recommendation": "deny"}).limit(9)]
    sess = review.open_session(T, REVIEWER)["session_id"]
    active = lambda: db.suspensions.count_documents({"tenant_id": T, "reviewer_id": REVIEWER, "active": True})  # noqa: E731

    det = start()
    time.sleep(3)
    before = (db.detector_state.find_one({"_id": "rubber_stamp_detector"}) or {}).get("events_processed", 0)
    for pid in ids[:3]:  # 3 zero-dwell approvals: below the median window, so no alarm yet
        review.approve(T, sess, pid, "Reviewed in batch.")
    seen = wait_for(lambda: (db.detector_state.find_one({"_id": "rubber_stamp_detector"}) or {}).get("events_processed", 0) >= before + 3)
    report("detector processed the first 3 events before the kill", seen)
    os.kill(det.pid, signal.SIGKILL)
    det.wait()
    print("killed detector (SIGKILL) mid-burst")
    for pid in ids[3:9]:  # burst continues with NO detector alive
        review.approve(T, sess, pid, "Reviewed in batch.")
    report("no suspension while the detector is dead", active() == 0)

    det = start()
    ok = wait_for(lambda: active() == 1, 20)
    s = db.suspensions.find_one({"tenant_id": T, "reviewer_id": REVIEWER, "active": True}) or {}
    report("restart resumes from the stored token and suspends exactly once", ok and active() == 1 and s.get("source") == "change_stream")
    print(f"   suspension {s.get('suspension_id')} rule={s.get('rule')} source={s.get('source')}")
    os.kill(det.pid, signal.SIGKILL)
    det.wait()
    det = start()
    time.sleep(4)
    report("a second kill/restart creates no second suspension", db.suspensions.count_documents({"tenant_id": T, "reviewer_id": REVIEWER}) == 1)
    det.terminate()
    det.wait()

    # scenario 2: FIRST start ever (no resume token) after approvals were written with no detector watching
    r2 = "dr-skim"
    db.suspensions.delete_many({"tenant_id": T, "reviewer_id": r2})
    db.reviewer_state.update_one({"_id": f"{T}|{r2}"}, {"$set": {"suspended": False}, "$unset": {"suspension_id": ""}})
    db.reviewer_stats.delete_one({"_id": f"{T}|{r2}"})
    db.detector_state.delete_many({})
    sess2 = review.open_session(T, r2)["session_id"]
    more = [p["proposal_id"] for p in db.proposals.find({"tenant_id": T, "status": "pending_review", "recommendation": "deny"}).limit(6)]
    for pid in more:
        review.approve(T, sess2, pid, "Reviewed in batch.")
    det = start()
    ok2 = wait_for(lambda: db.suspensions.count_documents({"tenant_id": T, "reviewer_id": r2, "active": True}) == 1, 20)
    s2 = db.suspensions.find_one({"tenant_id": T, "reviewer_id": r2, "active": True}) or {}
    report("first start with no token catches up on approvals written while no detector ran", ok2 and s2.get("source") == "detector_catchup")
    det.terminate()
    det.wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
