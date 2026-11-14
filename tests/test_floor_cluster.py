import numpy as np

from pg.stats import floor_cluster

FLOOR = 30000


def test_needs_enough_approvals_and_flags_a_floor_gamer_at_the_eighth():
    gamer = [31000, 33500, 32000, 35000, 31500, 36000, 34000, 32500]
    assert not floor_cluster(gamer[:7], FLOOR)["flagged"]       # 7 in the band is not yet enough evidence
    r = floor_cluster(gamer, FLOOR)
    assert r["flagged"] and r["n_near_floor"] == 8 and r["p_value"] < 1e-4


def test_honest_spread_is_not_flagged():
    honest = [75000, 52000, 140000, 61000, 98000, 44000, 83000, 120000, 67000, 39000]
    assert not floor_cluster(honest, FLOOR)["flagged"]


def test_stamper_far_below_the_floor_is_not_a_floor_cluster():
    assert not floor_cluster([1200] * 20, FLOOR)["flagged"]     # the gate and the median rule handle this, not this test


def test_false_flag_rate_on_the_worst_honest_case_stays_under_alpha():
    """Fast but honest: median only ~17% above the floor, log-sd 0.4 (about 22% of times land in the band). With p0=0.25
    the exact test is conservative, so flags should be (far) rarer than alpha=0.001."""
    rng = np.random.default_rng(7)
    flagged = sum(floor_cluster(list((rng.lognormal(np.log(35000), 0.4, 30)).astype(int)), FLOOR)["flagged"] for _ in range(20000))
    assert flagged / 20000 <= 0.002, flagged


def test_power_against_a_noisy_floor_gamer():
    """A gamer who adds jitter but stays within the band 80% of the time is still caught within a 30-approval window."""
    rng = np.random.default_rng(11)
    caught = 0
    for _ in range(2000):
        xs = np.where(rng.random(30) < 0.8, rng.uniform(30000, 37500, 30), rng.uniform(40000, 90000, 30)).astype(int)
        caught += floor_cluster(list(xs), FLOOR)["flagged"]
    assert caught / 2000 > 0.99
