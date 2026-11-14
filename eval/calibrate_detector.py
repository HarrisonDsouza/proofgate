"""Fit honest review behaviour from REAL sessions, then certify the self-baselined CUSUM threshold.

1. Volunteers outside the team review cases honestly in tenant payer-live (13:00-14:30).
2. This script reads their server-timed approvals: per-reviewer medians (how fast people honestly are)
   and the pooled within-reviewer sd of ln(seconds) (how much one person varies case to case).
3. Learn Then Test over Monte Carlo honest shifts drawn at THOSE speeds certifies h:
   P(honest reviewer of any observed speed falsely suspended within 50 approvals) <= alpha, w.p. >= 1-delta.

    python -m eval.calibrate_detector --tenant payer-live
    python -m eval.calibrate_detector --prd-model     # fallback: PRD honest + fast-honest models (SYNTHETIC, label it)
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from pg.cusum import SelfCusum, calibrate_self_h
from pg.db import get_db


def within_sd(by_reviewer: dict[str, list[float]]) -> float:
    resid = []
    for xs in by_reviewer.values():
        if len(xs) >= 2:
            lx = np.log(xs)
            resid += list(lx - lx.mean())
    return float(np.sqrt(np.sum(np.square(resid)) / max(1, len(resid) - len(by_reviewer)))) if resid else 0.4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tenant", default="payer-live")
    ap.add_argument("--reviewers", default="")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--prd-model", action="store_true")
    a = ap.parse_args()
    db = get_db()
    if a.prd_model:
        medians, sigma, n, source = [75.0, 35.0], 0.4, 0, "PRD synthetic honest (75 s) and fast-honest (35 s) models"
    else:
        q = {"tenant_id": a.tenant}
        if a.reviewers:
            q["reviewer_id"] = {"$in": a.reviewers.split(",")}
        by = defaultdict(list)
        for x in db.approvals.find(q, {"reviewer_id": 1, "active_dwell_ms": 1}):
            if x["active_dwell_ms"] > 0:
                by[x["reviewer_id"]].append(x["active_dwell_ms"] / 1000)
        if sum(map(len, by.values())) < 10:
            print("fewer than 10 real honest approvals: collect more, or run --prd-model and label it synthetic")
            return
        medians = [float(np.median(v)) for v in by.values()]
        sigma, n, source = within_sd(by), sum(map(len, by.values())), f"{sum(map(len, by.values()))} real approvals by {len(by)} volunteers"
    res, h = calibrate_self_h(sigma, medians, alpha=a.alpha, delta=a.delta)
    if h is None:
        print("nothing certified: collect more honest sessions or relax alpha")
        return
    c = SelfCusum(sigma, math.log(2), h)
    rng = np.random.default_rng(11)

    def rate(gen, k=400):
        return float(np.mean([c.run(gen()) is not None for _ in range(k)]))

    checks = {f"honest@{m:.0f}s_false_suspension": rate(lambda m=m: rng.lognormal(math.log(m), sigma, 50)) for m in medians}
    checks["drifter_caught"] = rate(lambda: np.concatenate([rng.lognormal(math.log(np.median(medians)), sigma, 16), rng.uniform(31, 38, 34)]))
    checks["floor_gamer_from_start_caught"] = rate(lambda: rng.uniform(31, 38, 50))
    doc = {"kind": "detector_calibration", "source": source, "n_honest": n, "alpha": a.alpha, "delta": a.delta,
           "cusum": {"mode": "self", "sigma": sigma, "h": h, "drop": math.log(2), "warmup": 5},
           "honest_medians_s": medians, "checks": checks, "createdAt": datetime.now(timezone.utc)}
    db.eval_runs.insert_one(dict(doc))
    print(json.dumps({k: v for k, v in doc.items() if k != "createdAt"}, indent=1, default=str))


if __name__ == "__main__":
    main()
