"""Reporting statistics. Counts with n, intervals, paired tests. No bare percentages."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.stats import binomtest

Z95 = 1.959963984540054


@dataclass(frozen=True)
class Rate:
    k: int
    n: int
    lo: float
    hi: float

    def __str__(self) -> str:
        if self.n == 0:
            return "n = 0"
        return f"{self.k}/{self.n} ({100 * self.k / self.n:.1f}%, 95% CI {100 * self.lo:.1f}-{100 * self.hi:.1f}%)"


def wilson(k: int, n: int, z: float = Z95) -> Rate:
    if n == 0:
        return Rate(0, 0, 0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return Rate(k, n, max(0.0, centre - half), min(1.0, centre + half))


def rule_of_three(n: int) -> float:
    """Approximate 95% upper bound on a rate when 0 events were seen in n trials."""
    return 3 / n if n else 1.0


def exact_zero_upper(n: int, alpha: float = 0.05) -> float:
    """Exact (Clopper-Pearson) one-sided upper bound for 0/n: 1 - alpha^(1/n)."""
    return 1 - alpha ** (1 / n) if n else 1.0


def mcnemar_exact(b: int, c: int) -> float:
    """Paired comparison on the same items. b = only baseline wrong, c = only Shiftline wrong."""
    if b + c == 0:
        return 1.0
    return binomtest(min(b, c), b + c, 0.5, alternative="two-sided").pvalue


def bootstrap_percentile(xs, q: float, n_boot: int = 1000, seed: int = 0) -> tuple[float, float, float]:
    """Point estimate and 95% bootstrap interval for the q-th percentile (e.g. q=95)."""
    a = np.asarray(xs, dtype=float)
    rng = np.random.default_rng(seed)
    est = float(np.percentile(a, q))
    boots = np.percentile(rng.choice(a, size=(n_boot, a.size), replace=True), q, axis=1)
    return est, float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def importance_estimate(log_weights, indicators) -> dict:
    """Unbiased IS estimate of P(event) with standard error and effective sample size."""
    w = np.exp(np.asarray(log_weights, float))
    y = np.asarray(indicators, float)
    n = w.size
    est = float((w * y).mean())
    se = float((w * y).std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
    ess = float(w.sum() ** 2 / (w ** 2).sum()) if w.sum() > 0 else 0.0
    return {"estimate": est, "se": se, "hi95": est + 1.96 * se, "n": n, "ess": ess}


def linear_fit(x, y) -> dict:
    """Least-squares slope/intercept and R^2: latency against guardrail count."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    slope, intercept = np.polyfit(x, y, 1)
    pred = slope * x + intercept
    ss_res, ss_tot = float(((y - pred) ** 2).sum()), float(((y - y.mean()) ** 2).sum())
    return {"slope": float(slope), "intercept": float(intercept), "r2": 1 - ss_res / ss_tot if ss_tot else 1.0}


def floor_cluster(dwells_ms: list[int], floor_ms: int, delta: float = 0.25, p0: float = 0.25, alpha: float = 0.001,
                  min_n: int = 8) -> dict:
    """Exact one-sided binomial test: do too many of a reviewer's approvals sit just above the policy floor?

    A reviewer who learned the floor and reviews at 31-37 s every time passes every per-case check and, being
    consistent from the very first case, defeats a self-baselined CUSUM. What gives them away is not speed but
    BUNCHING: an unconstrained reviewer's times spread over a wide range, so few land in the narrow band
    [floor, floor * (1 + delta)].

    H0: each approval lands in the band with probability <= p0. p0 = 0.25 is deliberately conservative: a reviewer
    whose median is only ~17% above the floor (log-sd 0.4) puts about 22% in a 25%-wide band, so an honest fast
    reviewer is not flagged, while a floor-gamer (almost every approval in the band) is flagged after min_n.
    Needs no honest-session data, only the policy floor and the model-free fact that bunching is improbable.
    The result is an EXAMINER FLAG, never a suspension: time alone cannot prove intent."""
    n = len(dwells_ms)
    hi = floor_ms * (1 + delta)
    k = sum(floor_ms <= d <= hi for d in dwells_ms)
    p = float(binomtest(k, n, p0, alternative="greater").pvalue) if n else 1.0
    return {"n": n, "n_near_floor": k, "band_ms": [int(floor_ms), int(hi)], "p0": p0, "p_value": p,
            "flagged": bool(n >= min_n and p <= alpha)}
