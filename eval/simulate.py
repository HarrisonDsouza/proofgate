"""Pre-registered evaluation (PRD Section 12) + two extra groups. Drives the REAL gate, detector and target.

    python -m eval.simulate --seed 1            # dev run
    python -m eval.simulate --seed 20261114     # held-out run: ONCE, after PREREGISTRATION.md is committed
    python -m eval.simulate --seed 20261114 --baseline   # policy v0 ("approval exists"), same workload

Time-scaled /10 (floor 3 s, item floor 0.5 s, window 6 s). Behaviour models are stated below and in
PREREGISTRATION.md; honest/fast-honest parameters are the PRD's (synthetic) until today's real sessions
are fitted with eval/calibrate_detector.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import threading
import time
from collections import Counter
from datetime import datetime, timezone

import numpy as np

from pg import agent, review
from pg.db import get_db
from pg.rules import run_rules
from pg.stats import wilson

TENANT = "payer-eval"
SCALE = 10
HB = 0.5  # heartbeat period in scaled time (5 s real / 10)

GROUPS = {  # name: (n reviewers, cases each)
    "honest": (12, 8), "fast-honest": (4, 8), "stamper": (4, 50), "tab-idler": (4, 8),
    "skimmer": (4, 8), "hb-forger": (2, 8), "floor-gamer": (4, 8), "drifter": (4, 16),
}


def _read_for(tenant, sess, case_id, eid, seconds, interact=True):
    tok = review.fetch_evidence(tenant, sess, case_id, eid)["view_token"]
    t_end = time.time() + seconds
    while time.time() < t_end:
        time.sleep(min(HB, max(0.0, t_end - time.time())))
        review.heartbeat(tenant, tok, True, 1000 if interact else 20000)
    review.close_view(tenant, tok)


def per_case_seconds(group: str, rng: np.random.Generator, k: int, n: int) -> float:
    """Total active review seconds per case, already divided by SCALE."""
    if group in ("honest",) or (group == "drifter" and k < n // 2):
        return float(rng.lognormal(np.log(75), 0.5)) / SCALE
    if group == "fast-honest":
        return float(rng.lognormal(np.log(35), 0.3)) / SCALE
    if group in ("floor-gamer", "drifter"):
        return float(rng.uniform(31, 38)) / SCALE
    if group == "hb-forger":
        return 31 / SCALE
    if group == "skimmer":
        return 2 * 2 / SCALE  # 2 s on each of 2 cited items
    return 0.0


def run_reviewer(tenant, group, idx, cases, seed, log):
    db = get_db()
    rid = f"ev-{group}-{idx}"
    rng = np.random.default_rng(int(hashlib.sha256(f'{seed}|{group}|{idx}'.encode()).hexdigest(), 16) % (2 ** 32))
    sess = review.open_session(tenant, rid)["session_id"]
    props = list(db.proposals.find({"tenant_id": tenant, "recommendation": "deny", "status": "pending_review",
                                    "case_id": {"$in": cases}}))
    if group == "stamper":
        ids = review.approve_bulk(tenant, sess, [p["proposal_id"] for p in props], "Reviewed in batch.")["approval_ids"]
        for p, aid in zip(props, ids, strict=True):
            res = agent.execute_one(tenant, p | {"approval_id": aid})
            log.append({"group": group, "reviewer": rid, "case": p["case_id"], "decision": res["decision"],
                        "reasons": [c["rule"] for c in res.get("reasons", [])]})
        return
    for k, p in enumerate(props):
        total = per_case_seconds(group, rng, k, len(props))
        cited = [c["evidence_id"] for c in p["cited_evidence"]]
        if group == "tab-idler":
            _read_for(tenant, sess, p["case_id"], cited[0], 4.0, interact=False)
        else:
            for eid in cited:
                _read_for(tenant, sess, p["case_id"], eid, total / len(cited))
        ap = review.approve(tenant, sess, p["proposal_id"], "I reviewed the cited evidence for this case.")
        res = agent.execute_one(tenant, p | {"approval_id": ap["approval_id"]})
        log.append({"group": group, "reviewer": rid, "case": p["case_id"], "decision": res["decision"],
                    "dwell_ms": ap["active_dwell_ms"], "reasons": [c["rule"] for c in res.get("reasons", [])]})


def setup_eval(seed: int, baseline: bool):
    from seed.generate import reset, seed_tenant
    db = get_db()
    reset(db, TENANT)
    revs = [(f"ev-{g}-{i}", "orthopedics", "2027-06-30", g) for g, (n, _) in GROUPS.items() for i in range(n)]
    n_cases = sum(n * c for n, c in GROUPS.values()) * 3  # ~1/3 are ortho denials after triage
    seed_tenant(db, TENANT, n_cases, seed, SCALE, reviewers=revs)
    db.cases.update_many({"tenant_id": TENANT}, {"$set": {"specialty": "orthopedics"}})
    pol = db.review_policies.find_one({"tenant_id": TENANT, "status": "active"})
    cal = db.eval_runs.find_one({"kind": "detector_calibration"}, sort=[("createdAt", -1)])
    upd = {"detector": {"cusum": cal["cusum"], "time_scale": SCALE}} if cal else {}
    if baseline:
        upd["rules"] = pol["rules"] | {"baseline_only_existence": True}
    if upd:
        db.review_policies.update_one({"_id": pol["_id"]}, {"$set": upd})
    deny = [p["case_id"] for p in db.proposals.find({"tenant_id": TENANT, "recommendation": "deny"})]
    plan, i = {}, 0
    for g, (n, c) in GROUPS.items():
        for j in range(n):
            plan[(g, j)] = deny[i:i + c]
            i += c
    return plan, bool(cal)


def summarise(log, db):
    susp = {s["reviewer_id"]: s for s in db.suspensions.find({"tenant_id": TENANT})}
    denials = {d["case_id"]: d for d in db.denials.find({"tenant_id": TENANT})}
    rows = {}
    for g, (n, _) in GROUPS.items():
        L = [x for x in log if x["group"] == g]
        executed = sum(1 for x in L if (d := denials.get(x["case"])) and d["status"] in ("CONFIRMED", "REVERSED"))
        reversed_ = sum(1 for x in L if (d := denials.get(x["case"])) and d["status"] == "REVERSED")
        sus = [r for r in {x["reviewer"] for x in L} if r in susp]
        rows[g] = {"n": n, "attempted": len(L), "executed": executed, "reversed_after": reversed_,
                   "refused": len(L) - executed, "suspended": len(sus),
                   "suspension_rules": dict(Counter(susp[r]["rule"] for r in sus)),
                   "refusal_reasons": dict(Counter(r for x in L for r in x["reasons"])),
                   "exec_rate": str(wilson(executed, len(L))), "suspension_rate": str(wilson(len(sus), n))}
    honest = [g for g in ("honest", "fast-honest")]
    hon_att = sum(rows[g]["attempted"] for g in honest)
    out = {"groups": rows,
           "false_refusal": str(wilson(sum(rows[g]["refused"] for g in honest), hon_att)),
           "false_suspension": str(wilson(sum(rows[g]["suspended"] for g in honest), sum(rows[g]["n"] for g in honest))),
           "median_verified_active_s_per_executed": (statistics.median(
               [x["dwell_ms"] for x in log if x.get("dwell_ms") and (d := denials.get(x["case"])) and d["status"] in ("CONFIRMED", "REVERSED")])
               * SCALE / 1000) if denials else None,
           "txn_attempts": {str(k): v for k, v in Counter(g["txn_attempts"] for g in db.gate_decisions.find({"tenant_id": TENANT})).items()},  # BSON keys must be strings
           "rules": {k: v["pass"] for k, v in run_rules(TENANT).items()}}
    return out


def bson_safe(x):
    """BSON documents only allow string keys: stringify dict keys recursively (the results hold int keys)."""
    if isinstance(x, dict):
        return {str(k): bson_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [bson_safe(v) for v in x]
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--baseline", action="store_true")
    a = ap.parse_args()
    from pg import detector
    db = get_db()
    plan, has_cusum = setup_eval(a.seed, a.baseline)
    stop = detector.start_background()
    log: list = []
    threads = [threading.Thread(target=run_reviewer, args=(TENANT, g, j, cases, a.seed, log)) for (g, j), cases in plan.items()]
    t0 = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    time.sleep(3)  # let the detector and compensation worker drain
    stop.set()
    res = summarise(log, db)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    doc = {"kind": "eval", "seed": a.seed, "baseline": a.baseline, "cusum": has_cusum, "prereg_commit": commit,
           "seconds": round(time.time() - t0, 1), "results": res, "createdAt": datetime.now(timezone.utc)}
    db.eval_runs.insert_one(bson_safe(doc))
    print(f"commit {commit} seed {a.seed} baseline={a.baseline} cusum={has_cusum}")
    print(f"{'group':<12}{'n':>3}{'att':>6}{'exec':>6}{'refused':>8}{'susp':>6}  reasons")
    for g, r in res["groups"].items():
        print(f"{g:<12}{r['n']:>3}{r['attempted']:>6}{r['executed']:>6}{r['refused']:>8}{r['suspended']:>6}  {r['refusal_reasons']} {r['suspension_rules']}")
    print(json.dumps({k: v for k, v in res.items() if k != "groups"}, indent=1, default=str))


if __name__ == "__main__":
    main()
