"""Learn Then Test (Angelopoulos, Bates, Candès, Jordan, Lei 2021): pick resolution thresholds
with a distribution-free guarantee on the wrong-asset rate.

Loss for one spoken reference = 1 if the resolver picked a WRONG asset, else 0 (a refusal is
not a loss here: refusing fails closed and only costs a false block, which we report separately).

For each candidate threshold lambda, test H0: risk(lambda) > alpha with the exact binomial
p-value P(Bin(n, alpha) <= k). Reject along a path ordered from strictest to most lenient
(fixed-sequence testing, valid FWER control with no correction), and Bonferroni across the few
margin paths. Every lambda in the returned safe set satisfies, with probability >= 1 - delta
over the calibration draw:  P(wrong asset) <= alpha  -- for references exchangeable with the
calibration set. That condition is the honest caveat: the guarantee covers the calibration
distribution (team gold pairs + simulated STT noise + Set B), not any plant floor.

Minimum calibration size to certify anything: n >= ln(delta) / ln(1 - alpha)
(alpha=0.05, delta=0.05 -> n >= 59; alpha=0.02 -> n >= 149).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

from scipy.stats import binom


def binom_pvalue(k: int, n: int, alpha: float) -> float:
    """Exact p-value for H0: risk >= alpha after seeing k losses in n trials."""
    return float(binom.cdf(k, n, alpha))


def min_n(alpha: float, delta: float) -> int:
    return math.ceil(math.log(delta) / math.log(1 - alpha))


@dataclass(frozen=True)
class LTTResult:
    safe: list[tuple[float, float]]  # (tau, margin) pairs certified safe
    chosen: tuple[float, float] | None  # the safe pair with the fewest refusals
    table: list[dict]  # every tested pair with k, refusals, p-value, rejected


def learn_then_test(
    taus_strict_to_lenient: Sequence[float],
    margins: Sequence[float],
    evaluate: Callable[[float, float], tuple[int, int]],
    n: int,
    alpha: float = 0.05,
    delta: float = 0.05,
) -> LTTResult:
    """`evaluate(tau, margin)` returns (wrong_resolutions, refusals) over the n calibration refs."""
    per_path_delta = delta / max(1, len(margins))  # Bonferroni across margin paths
    safe, table = [], []
    for m in margins:
        for tau in taus_strict_to_lenient:  # fixed sequence: stop at the first failure
            k, refused = evaluate(tau, m)
            p = binom_pvalue(k, n, alpha)
            ok = p <= per_path_delta
            table.append({"tau": tau, "margin": m, "wrong": k, "refused": refused, "p": p, "rejected": ok})
            if not ok:
                break
            safe.append((tau, m))
    refusals = {(r["tau"], r["margin"]): r["refused"] for r in table}
    chosen = min(safe, key=lambda s: (refusals[s], -s[1], -s[0])) if safe else None
    return LTTResult(safe, chosen, table)
