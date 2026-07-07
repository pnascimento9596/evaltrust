"""Tests for the additional statistical primitives behind the credibility rework:
McNemar's exact test (paired binary), Cohen's h (proportion effect size), and the
prospective minimum detectable effect (replacing post-hoc power).
"""

import math

import numpy as np
import pytest
from statsmodels.stats.contingency_tables import mcnemar as sm_mcnemar

from evaltrust.stats.effect import cohens_h
from evaltrust.stats.paired import mcnemar_exact
from evaltrust.stats.power import achieved_power, minimum_detectable_effect


# ---------------------------------------------------------------------------
# McNemar's exact test on discordant pair counts
# ---------------------------------------------------------------------------

def test_mcnemar_equal_discordant_pairs_is_not_significant():
    assert mcnemar_exact(10, 10) == pytest.approx(1.0)


def test_mcnemar_no_discordant_pairs_is_one():
    assert mcnemar_exact(0, 0) == 1.0


def test_mcnemar_strong_imbalance_is_significant():
    assert mcnemar_exact(20, 2) < 0.01


@pytest.mark.parametrize("b,c", [(3, 12), (15, 4), (8, 8), (1, 9)])
def test_mcnemar_matches_statsmodels_exact(b, c):
    table = [[0, b], [c, 0]]
    ref = sm_mcnemar(table, exact=True).pvalue
    assert mcnemar_exact(b, c) == pytest.approx(ref, abs=1e-9)


# ---------------------------------------------------------------------------
# Cohen's h effect size for two proportions
# ---------------------------------------------------------------------------

def test_cohens_h_is_zero_for_equal_proportions():
    assert cohens_h(0.5, 0.5) == pytest.approx(0.0)


def test_cohens_h_known_value():
    expected = 2 * math.asin(math.sqrt(0.6)) - 2 * math.asin(math.sqrt(0.4))
    assert cohens_h(0.6, 0.4) == pytest.approx(expected)


def test_cohens_h_sign_follows_argument_order():
    assert cohens_h(0.8, 0.2) > 0
    assert cohens_h(0.2, 0.8) < 0


# ---------------------------------------------------------------------------
# Minimum detectable effect (prospective) — NOT post-hoc power
# ---------------------------------------------------------------------------

def test_mde_reaches_target_power():
    mde = minimum_detectable_effect(n=100, power=0.8, alpha=0.05)
    # An effect exactly at the MDE should have ~the target power.
    assert achieved_power(mde, n=100, alpha=0.05) == pytest.approx(0.8, abs=0.02)


def test_mde_shrinks_as_sample_grows():
    assert minimum_detectable_effect(200) < minimum_detectable_effect(50)


def test_mde_is_positive():
    assert minimum_detectable_effect(30) > 0
