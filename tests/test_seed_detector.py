"""A freshly seeded tenant ships a CUSUM detector config, so the demo detector behaves as documented."""
from pg.detector import cusum_for


def test_seeded_policy_has_cusum(scratch):
    from pg.db import get_db
    pol = get_db().review_policies.find_one({"tenant_id": scratch, "status": "active"})
    c = cusum_for(pol)
    assert c is not None
    assert (c.sigma, c.h, c.warmup) == (0.4, 5.75, 5)
