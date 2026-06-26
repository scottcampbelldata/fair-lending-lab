"""Power analysis: sample size and minimum detectable effect (MDE)."""
from __future__ import annotations

import math

from scipy import stats


def sample_size_two_means(
    effect_size: float, alpha: float = 0.05, power: float = 0.8, ratio: float = 1.0
) -> int:
    """Sample size per group for a two-sample test of means at given Cohen's d.

    ratio = n_b / n_a. Returns the larger group's size (rounded up).
    Formula: n = (z_{1-a/2} + z_{1-b})^2 * (1 + 1/ratio) / d^2
    """
    if effect_size <= 0:
        raise ValueError("effect_size must be positive")
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    n_per_group = (z_a + z_b) ** 2 * (1 + 1 / ratio) / (effect_size**2)
    return int(math.ceil(n_per_group))


def sample_size_two_props(
    p1: float, p2: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Sample size per group for a two-proportion z-test, two-sided."""
    if not (0 < p1 < 1 and 0 < p2 < 1):
        raise ValueError("p1 and p2 must be in (0, 1)")
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    p_bar = (p1 + p2) / 2
    num = (
        z_a * math.sqrt(2 * p_bar * (1 - p_bar))
        + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    ) ** 2
    n = num / (p1 - p2) ** 2
    return int(math.ceil(n))


def minimum_detectable_effect_two_means(
    n_per_group: int, alpha: float = 0.05, power: float = 0.8
) -> float:
    """Cohen's d MDE for a two-sample mean comparison with n per group."""
    if n_per_group < 2:
        raise ValueError("n_per_group must be >= 2")
    z_a = stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    return float((z_a + z_b) * math.sqrt(2 / n_per_group))
