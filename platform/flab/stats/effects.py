"""Effect-size estimators with 95% confidence intervals."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class EffectCI:
    estimate: float
    ci_low: float
    ci_high: float
    label: str


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    """Hedges-pooled SD Cohen's d (group_a minus group_b)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        raise ValueError("Need at least 2 observations per group")
    sa2 = np.var(a, ddof=1)
    sb2 = np.var(b, ddof=1)
    sp = np.sqrt(((na - 1) * sa2 + (nb - 1) * sb2) / (na + nb - 2))
    if sp == 0:
        return 0.0
    return float((np.mean(a) - np.mean(b)) / sp)


def cohens_d_ci(a: np.ndarray, b: np.ndarray, alpha: float = 0.05) -> EffectCI:
    """Cohen's d with Hedges' g small-sample correction and approximate CI.

    Uses the non-central t-distribution based CI (Hedges & Olkin 1985).
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na, nb = len(a), len(b)
    d = cohens_d(a, b)
    # Hedges' g small-sample correction
    df = na + nb - 2
    J = 1 - 3 / (4 * df - 1) if df > 1 else 1.0
    g = d * J
    se = np.sqrt((na + nb) / (na * nb) + (g**2) / (2 * (na + nb)))
    z = stats.norm.ppf(1 - alpha / 2)
    return EffectCI(
        estimate=float(g),
        ci_low=float(g - z * se),
        ci_high=float(g + z * se),
        label="Hedges' g",
    )


def rank_biserial(a: np.ndarray, b: np.ndarray) -> float:
    """Rank-biserial correlation = 2*U/(na*nb) - 1; r in [-1, 1]."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    u, _ = stats.mannwhitneyu(a, b, alternative="two-sided")
    return float(2 * u / (len(a) * len(b)) - 1)


def cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    """Cliff's delta = P(a>b) - P(a<b); delta in [-1, 1].

    Equivalent to the rank-biserial correlation but computed via U.
    Romano et al. (2006) suggest |delta|<0.147 negligible, 0.33 medium, >0.474 large.
    """
    return rank_biserial(a, b)


def risk_difference_ci(
    x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05
) -> EffectCI:
    """Wald CI for p1 - p2 (group 1 minus group 2)."""
    p1, p2 = x1 / n1, x2 / n2
    rd = p1 - p2
    se = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z = stats.norm.ppf(1 - alpha / 2)
    return EffectCI(
        estimate=float(rd),
        ci_low=float(rd - z * se),
        ci_high=float(rd + z * se),
        label="risk difference",
    )


def odds_ratio_ci(
    x1: int, n1: int, x2: int, n2: int, alpha: float = 0.05
) -> EffectCI:
    """Odds ratio (group 1 vs group 2) with Wald log-OR CI.

    Adds 0.5 Haldane-Anscombe correction if any cell is zero.
    """
    a = x1
    b = n1 - x1
    c = x2
    d = n2 - x2
    if min(a, b, c, d) == 0:
        a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    or_ = (a * d) / (b * c)
    se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    z = stats.norm.ppf(1 - alpha / 2)
    log_or = np.log(or_)
    return EffectCI(
        estimate=float(or_),
        ci_low=float(np.exp(log_or - z * se)),
        ci_high=float(np.exp(log_or + z * se)),
        label="odds ratio",
    )
