import math

import numpy as np

from pg.cusum import Cusum, HonestModel, calibrate_h, detection_delay, fit_honest, simulate

MODEL = HonestModel(mu0=math.log(90), sigma=0.5)  # placeholder until today's honest sessions are fitted


def test_fit_recovers_parameters():
    rng = np.random.default_rng(0)
    m = fit_honest(rng.lognormal(math.log(90), 0.5, 5000))
    assert abs(m.median_s - 90) < 3 and abs(m.sigma - 0.5) < 0.02


def test_cusum_never_alarms_on_slow_reviews():
    c = Cusum(MODEL, shift_to_s=34, h=4.0)
    assert c.run([300.0] * 100) is None


def test_cusum_catches_stamper_immediately():
    c = Cusum(MODEL, shift_to_s=34, h=4.0)
    assert c.run([1.2] * 10) <= 2


def test_calibration_certifies_false_suspension_rate():
    res, h = calibrate_h(MODEL, shift_to_s=34, shift_len=50, n_shifts=400, alpha=0.05, delta=0.05, seed=3)
    assert h is not None
    # out-of-sample check on fresh honest shifts: false-suspension rate should sit under alpha
    rng = np.random.default_rng(99)
    c = Cusum(MODEL, 34, h)
    fa = np.mean([c.run(simulate("honest", 50, MODEL, rng)) is not None for _ in range(1500)])
    assert fa <= 0.06, fa


def test_skimmer_is_caught_where_a_floor_is_not():
    _, h = calibrate_h(MODEL, shift_to_s=34, n_shifts=400, seed=3)
    c = Cusum(MODEL, 34, h)
    d = detection_delay(c, "skimmer", MODEL, n_runs=200)
    assert d["missed"] == 0 and d["median"] <= 15  # every skimming approval passes a 30 s floor


# ---------- self-baselined CUSUM (the deployed default) ----------
from pg.cusum import SelfCusum, calibrate_self_h  # noqa: E402


def test_population_cusum_would_suspend_fast_honest():
    """Documents WHY the default is self-baselined: population mode flags consistently fast honest reviewers."""
    _, h = calibrate_h(MODEL, 34, n_shifts=400, seed=3)
    c = Cusum(MODEL, 34, h)
    rng = np.random.default_rng(5)
    assert np.mean([c.run(rng.lognormal(math.log(35), 0.3, 50)) is not None for _ in range(200)]) > 0.5


def test_self_cusum_spares_fast_honest_and_catches_drift():
    _, h = calibrate_self_h(0.4, [75, 35], n_shifts=500, seed=3)
    c = SelfCusum(0.4, h=h)
    rng = np.random.default_rng(11)
    fast = np.mean([c.run(rng.lognormal(math.log(35), 0.4, 50)) is not None for _ in range(300)])
    drift = np.mean([c.run(np.concatenate([rng.lognormal(math.log(75), 0.4, 16), rng.uniform(31, 38, 34)])) is not None
                     for _ in range(300)])
    assert fast <= 0.08 and drift >= 0.9


def test_self_cusum_limit_floor_gamer_from_start_is_not_caught():
    """The stated limit: someone who games the floor from case 1 has no 'drop' to detect."""
    _, h = calibrate_self_h(0.4, [75, 35], n_shifts=500, seed=3)
    c = SelfCusum(0.4, h=h)
    rng = np.random.default_rng(2)
    assert np.mean([c.run(rng.uniform(31, 38, 50)) is not None for _ in range(200)]) < 0.1
