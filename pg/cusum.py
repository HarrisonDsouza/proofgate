"""Sequential rubber-stamp detection: one-sided CUSUM on log review time.

Why this, not only fixed thresholds: the gate's per-case floor (e.g. dwell >= 30 s) stops the
"approve 50" burst on its own. What a floor cannot catch is the SKIMMER who learns the floor and
reviews at 31-35 s every time: each approval passes, but the reviewer's behaviour has shifted far
below how real reviewers work. CUSUM (Page, 1954) is the classic quality-control test for a
sustained shift in a stream; it accumulates evidence across approvals and alarms with a known,
tunable false-alarm rate.

Model. For one reviewer, x_i = ln(active_dwell_seconds_i). Honest reviewers: x ~ N(mu0, sigma)
(log-normal review time, fitted from real honest sessions recorded today). Shifted behaviour:
mean mu1 < mu0. Lower CUSUM:
    S_0 = 0,  S_i = max(0, S_{i-1} + (mu0 - x_i)/sigma - k),  alarm when S_i > h
with k = (mu0 - mu1) / (2 sigma)  (the standard choice, optimal for detecting a shift to mu1).

h is NOT hand-picked: `calibrate_h` certifies, with Learn Then Test, that the probability an
HONEST reviewer is falsely suspended within a shift of N approvals is <= alpha (prob >= 1-delta).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from pg.riskcontrol import learn_then_test


@dataclass(frozen=True)
class HonestModel:
    mu0: float  # mean of ln(seconds)
    sigma: float  # sd of ln(seconds)

    @property
    def median_s(self) -> float:
        return math.exp(self.mu0)


def fit_honest(dwell_seconds: Iterable[float]) -> HonestModel:
    """MLE of the log-normal from real honest review sessions (drop non-positive values)."""
    x = np.log([d for d in dwell_seconds if d > 0])
    if x.size < 5:
        raise ValueError("need at least 5 honest reviews to fit")
    return HonestModel(float(x.mean()), float(x.std(ddof=1)))


@dataclass(frozen=True)
class Cusum:
    model: HonestModel
    shift_to_s: float  # the review time (seconds) we want to detect, e.g. just above the floor
    h: float

    @property
    def k(self) -> float:
        mu1 = math.log(self.shift_to_s)
        return (self.model.mu0 - mu1) / (2 * self.model.sigma)

    def step(self, s_prev: float, dwell_s: float) -> float:
        x = math.log(max(dwell_s, 1e-3))
        return max(0.0, s_prev + (self.model.mu0 - x) / self.model.sigma - self.k)

    def run(self, dwells: Sequence[float]) -> int | None:
        """Index (1-based) of the approval that triggers suspension, or None."""
        s = 0.0
        for i, d in enumerate(dwells, 1):
            s = self.step(s, d)
            if s > self.h:
                return i
        return None


@dataclass(frozen=True)
class SelfCusum:
    """Self-baselined CUSUM: each reviewer is compared with THEIR OWN first `warmup` approvals.

    Why: a population-baselined CUSUM calibrated on typical honest reviewers (median 75 s) suspends 100% of
    consistently fast honest reviewers (median 35 s) in simulation. Time alone cannot separate "fast and
    honest" from "gaming the floor". Self-baselining asks a question time CAN answer: did this reviewer's
    behaviour drop sharply partway through (fatigue, quota pressure, switching to stamping)?
    It does NOT catch someone who games the floor from their very first case; the gate's floor and the
    examiner's view data are the defence there, and we say so.
    """
    sigma: float  # within-reviewer sd of ln(seconds), from calibration
    drop: float = math.log(2)  # detect review time falling to about half of the reviewer's own baseline
    h: float = 4.0
    warmup: int = 5

    def run(self, dwells: Sequence[float]) -> int | None:
        if len(dwells) <= self.warmup:
            return None
        base = float(np.mean(np.log(np.maximum(dwells[: self.warmup], 1e-3))))
        k = self.drop / (2 * self.sigma)
        s = 0.0
        for i, d in enumerate(dwells[self.warmup:], self.warmup + 1):
            s = max(0.0, s + (base - math.log(max(d, 1e-3))) / self.sigma - k)
            if s > self.h:
                return i
        return None


def calibrate_self_h(sigma: float, honest_medians_s: Sequence[float], shift_len: int = 50, n_shifts: int = 600,
                     alpha: float = 0.05, delta: float = 0.05, seed: int = 0, drop: float = math.log(2)):
    """Certify h for SelfCusum on honest reviewers of ANY speed (each with their own median)."""
    rng = np.random.default_rng(seed)
    shifts = [rng.lognormal(math.log(rng.choice(honest_medians_s)), sigma, shift_len) for _ in range(n_shifts)]
    hs = [round(x, 2) for x in np.arange(12.0, 0.9, -0.25)]

    def evaluate(h: float, _m: float) -> tuple[int, int]:
        c = SelfCusum(sigma, drop, h)
        return sum(c.run(s) is not None for s in shifts), 0

    res = learn_then_test(hs, [0.0], evaluate, n_shifts, alpha, delta)
    return res, min((s[0] for s in res.safe), default=None)


# ---------------- simulation of reviewer behaviours ----------------
def simulate(kind: str, n: int, model: HonestModel, rng: np.random.Generator, floor_s: float = 30.0) -> np.ndarray:
    """Synthetic review times (seconds). Parameters for non-honest kinds are ASSUMPTIONS, stated in the README.

    honest   : log-normal fitted from today's real sessions
    stamper  : the reported PxDx pattern, ~1.2 s per case (ProPublica 2023, as reported)
    skimmer  : learned the floor; uniform just above it (floor+1 .. floor+8 s)
    drifter  : starts honest, halfway through slides to skimming (fatigue / quota pressure)
    """
    if kind == "honest":
        return rng.lognormal(model.mu0, model.sigma, n)
    if kind == "stamper":
        return rng.lognormal(math.log(1.2), 0.3, n)
    if kind == "skimmer":
        return rng.uniform(floor_s + 1, floor_s + 8, n)
    if kind == "drifter":
        half = n // 2
        return np.concatenate([rng.lognormal(model.mu0, model.sigma, half), rng.uniform(floor_s + 1, floor_s + 8, n - half)])
    raise ValueError(kind)


def calibrate_h(model: HonestModel, shift_to_s: float, shift_len: int = 50, n_shifts: int = 600,
                hs: Sequence[float] | None = None, alpha: float = 0.05, delta: float = 0.05, seed: int = 0):
    """Certify h so that P(honest reviewer falsely suspended within `shift_len` approvals) <= alpha.

    Monte Carlo over `n_shifts` simulated honest shifts, then Learn Then Test along h from
    strict (large h, few alarms) to lenient (small h). Among certified h, pick the smallest
    (fastest detection). Returns (LTTResult, chosen_h).
    """
    rng = np.random.default_rng(seed)
    shifts = [simulate("honest", shift_len, model, rng) for _ in range(n_shifts)]
    hs = list(hs) if hs is not None else [round(x, 2) for x in np.arange(12.0, 0.9, -0.25)]

    def evaluate(h: float, _m: float) -> tuple[int, int]:
        c = Cusum(model, shift_to_s, h)
        false_alarms = sum(c.run(s) is not None for s in shifts)
        return false_alarms, 0

    res = learn_then_test(hs, [0.0], evaluate, n_shifts, alpha, delta)
    chosen = min((s[0] for s in res.safe), default=None)
    return res, chosen


def detection_delay(c: Cusum, kind: str, model: HonestModel, n_runs: int = 300, shift_len: int = 50,
                    seed: int = 1) -> dict:
    """How many approvals of a misbehaving reviewer pass before suspension (median, p90, never-caught)."""
    rng = np.random.default_rng(seed)
    delays = []
    missed = 0
    for _ in range(n_runs):
        t = c.run(simulate(kind, shift_len, model, rng))
        if t is None:
            missed += 1
        else:
            delays.append(t)
    d = np.array(delays) if delays else np.array([np.nan])
    return {"kind": kind, "median": float(np.nanmedian(d)), "p90": float(np.nanpercentile(d, 90)),
            "missed": missed, "runs": n_runs}
