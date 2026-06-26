"""Property-based and numerical tests for the stats helpers."""
from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from flab.stats import (
    bh_fdr,
    bonferroni,
    bootstrap_ci,
    cohens_d,
    cohens_d_ci,
    minimum_detectable_effect_two_means,
    odds_ratio_ci,
    permutation_test_means,
    risk_difference_ci,
    sample_size_two_means,
    sample_size_two_props,
    two_proportion_z,
    welch_t,
)
from flab.stats.tests import two_proportion_or


# --- cohens d --------------------------------------------------------------

def test_cohens_d_zero_when_identical():
    a = np.array([1.0, 2.0, 3.0, 4.0])
    b = np.array([1.0, 2.0, 3.0, 4.0])
    assert cohens_d(a, b) == pytest.approx(0.0, abs=1e-9)


def test_cohens_d_sign_matches_mean_diff():
    rng = np.random.default_rng(0)
    a = rng.normal(2.0, 1.0, 200)
    b = rng.normal(0.0, 1.0, 200)
    assert cohens_d(a, b) > 0
    assert cohens_d(b, a) < 0


@given(
    n=st.integers(min_value=10, max_value=200),
    delta=st.floats(min_value=-2.0, max_value=2.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_cohens_d_recovers_known_delta(n: int, delta: float):
    rng = np.random.default_rng(42)
    a = rng.normal(delta, 1.0, n)
    b = rng.normal(0.0, 1.0, n)
    d = cohens_d(a, b)
    # noisy estimate, but mean should fall within a wide band of the true delta
    assert abs(d - delta) < 1.5


# --- effect-size CIs ---------------------------------------------------------

def test_cohens_d_ci_contains_estimate():
    rng = np.random.default_rng(1)
    a = rng.normal(0.5, 1.0, 200)
    b = rng.normal(0.0, 1.0, 200)
    eff = cohens_d_ci(a, b)
    assert eff.ci_low < eff.estimate < eff.ci_high


def test_risk_difference_ci_centers_on_estimate():
    eff = risk_difference_ci(40, 100, 25, 100)
    assert eff.estimate == pytest.approx(0.15)
    assert eff.ci_low < 0.15 < eff.ci_high


def test_odds_ratio_ci_haldane_correction_when_zero_cell():
    # zero cell would otherwise produce inf; correction prevents that
    eff = odds_ratio_ci(0, 100, 10, 100)
    assert math.isfinite(eff.estimate)
    assert math.isfinite(eff.ci_low)
    assert math.isfinite(eff.ci_high)


# --- two-proportion tests --------------------------------------------------

def test_two_proportion_z_no_difference_yields_high_pvalue():
    res = two_proportion_z(50, 100, 50, 100)
    assert res.p_value > 0.5


def test_two_proportion_z_big_difference_yields_tiny_pvalue():
    res = two_proportion_z(80, 100, 20, 100)
    assert res.p_value < 1e-10
    assert res.effect_size == pytest.approx(0.60)


def test_two_proportion_or_or_above_one_for_higher_a():
    res = two_proportion_or(40, 100, 20, 100)
    assert res.effect_size > 1


# --- welch t -----------------------------------------------------------------

def test_welch_t_no_difference():
    rng = np.random.default_rng(2)
    a = rng.normal(0.0, 1.0, 500)
    b = rng.normal(0.0, 1.0, 500)
    res = welch_t(a, b)
    assert 0.0 <= res.p_value <= 1.0


def test_welch_t_clear_difference():
    rng = np.random.default_rng(3)
    a = rng.normal(2.0, 1.0, 200)
    b = rng.normal(0.0, 1.0, 200)
    res = welch_t(a, b)
    assert res.p_value < 1e-20
    assert res.effect_size > 1.5  # huge effect


# --- permutation -------------------------------------------------------------

def test_permutation_no_difference_pvalue_large():
    rng = np.random.default_rng(4)
    a = rng.normal(0.0, 1.0, 100)
    b = rng.normal(0.0, 1.0, 100)
    res = permutation_test_means(a, b, n_permutations=500, seed=10)
    assert res["p_value"] > 0.05


def test_permutation_clear_difference_pvalue_tiny():
    rng = np.random.default_rng(5)
    a = rng.normal(3.0, 1.0, 100)
    b = rng.normal(0.0, 1.0, 100)
    res = permutation_test_means(a, b, n_permutations=500, seed=10)
    assert res["p_value"] < 0.05


# --- bootstrap ---------------------------------------------------------------

def test_bootstrap_mean_ci_covers_truth_on_average():
    rng = np.random.default_rng(6)
    coverages = 0
    runs = 30
    for _ in range(runs):
        a = rng.normal(5.0, 1.0, 80)
        b = rng.normal(0.0, 1.0, 80)
        res = bootstrap_ci(a, b, n_resamples=800, seed=int(rng.integers(0, 10_000)))
        if res.ci_low <= 5.0 <= res.ci_high:
            coverages += 1
    # 95% nominal, accept 22/30 or more (binomial slack)
    assert coverages >= 22


# --- multiple comparison correction ----------------------------------------

def test_bonferroni_threshold():
    res = bonferroni([0.01, 0.02, 0.03], alpha=0.05)
    assert res["threshold"] == pytest.approx(0.05 / 3)
    assert res["reject"] == [True, False, False]


def test_bh_fdr_rejects_all_small_pvalues():
    res = bh_fdr([1e-6, 1e-5, 1e-4, 1e-3, 0.5], q=0.05)
    # first four should reject; the 0.5 should not
    assert sum(res["reject"]) >= 4
    assert res["reject"][-1] is False


def test_bh_fdr_handles_all_large_pvalues():
    res = bh_fdr([0.5, 0.6, 0.7], q=0.05)
    assert sum(res["reject"]) == 0


# --- power ------------------------------------------------------------------

def test_sample_size_two_means_increases_as_effect_shrinks():
    n_small = sample_size_two_means(0.1)
    n_med = sample_size_two_means(0.5)
    n_large = sample_size_two_means(1.0)
    assert n_small > n_med > n_large


def test_minimum_detectable_effect_decreases_with_n():
    mde_small = minimum_detectable_effect_two_means(50)
    mde_large = minimum_detectable_effect_two_means(500)
    assert mde_small > mde_large


def test_sample_size_two_props_known_value():
    # textbook example: p1=0.5, p2=0.4, alpha=0.05, power=0.8 -> ~388 per group
    n = sample_size_two_props(0.5, 0.4)
    assert 350 < n < 500
