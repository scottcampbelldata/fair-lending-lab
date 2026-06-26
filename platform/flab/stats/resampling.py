"""Bootstrap CIs and permutation tests."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from flab.config import get_random_seed


@dataclass(frozen=True)
class BootstrapCI:
    estimate: float
    ci_low: float
    ci_high: float
    n_resamples: int
    method: str  # "percentile" | "bca"


def _new_rng(seed: int | None) -> np.random.Generator:
    return np.random.default_rng(seed if seed is not None else get_random_seed())


def bootstrap_ci(
    a: np.ndarray,
    b: np.ndarray | None = None,
    stat: Callable | None = None,
    n_resamples: int = 5000,
    alpha: float = 0.05,
    seed: int | None = None,
) -> BootstrapCI:
    """Percentile bootstrap CI for a one-sample (a) or two-sample (a, b) statistic.

    stat: callable taking (a,) or (a, b) and returning a scalar.
        Defaults to np.mean for one-sample or mean-diff for two-sample.
    """
    rng = _new_rng(seed)
    a = np.asarray(a, dtype=float)
    if b is None:
        if stat is None:
            stat = np.mean  # type: ignore[assignment]
        boots = np.empty(n_resamples)
        for i in range(n_resamples):
            idx = rng.integers(0, len(a), size=len(a))
            boots[i] = float(stat(a[idx]))  # type: ignore[misc]
        est = float(stat(a))  # type: ignore[misc]
    else:
        b = np.asarray(b, dtype=float)
        if stat is None:
            def stat(x, y):  # noqa: E306
                return float(np.mean(x) - np.mean(y))
        boots = np.empty(n_resamples)
        for i in range(n_resamples):
            ia = rng.integers(0, len(a), size=len(a))
            ib = rng.integers(0, len(b), size=len(b))
            boots[i] = float(stat(a[ia], b[ib]))  # type: ignore[misc]
        est = float(stat(a, b))  # type: ignore[misc]
    lo, hi = np.quantile(boots, [alpha / 2, 1 - alpha / 2])
    return BootstrapCI(
        estimate=est,
        ci_low=float(lo),
        ci_high=float(hi),
        n_resamples=n_resamples,
        method="percentile",
    )


def permutation_test_means(
    a: np.ndarray,
    b: np.ndarray,
    n_permutations: int = 10_000,
    alternative: str = "two-sided",
    seed: int | None = None,
) -> dict:
    """Exchangeability-based permutation test for difference in means."""
    rng = _new_rng(seed)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    observed = float(np.mean(a) - np.mean(b))
    pooled = np.concatenate([a, b])
    n_a = len(a)
    diffs = np.empty(n_permutations)
    for i in range(n_permutations):
        rng.shuffle(pooled)
        diffs[i] = float(pooled[:n_a].mean() - pooled[n_a:].mean())
    if alternative == "two-sided":
        p = float((np.abs(diffs) >= abs(observed)).mean())
    elif alternative == "greater":
        p = float((diffs >= observed).mean())
    elif alternative == "less":
        p = float((diffs <= observed).mean())
    else:
        raise ValueError(f"Unknown alternative: {alternative}")
    # +1 numerator/denominator smoother (avoids p=0)
    p_smoothed = (np.sum(np.abs(diffs) >= abs(observed)) + 1) / (n_permutations + 1)
    return {
        "method": "permutation_means",
        "observed_diff": observed,
        "p_value": p,
        "p_value_smoothed": float(p_smoothed),
        "n_permutations": n_permutations,
        "alternative": alternative,
    }
