"""Multiple-comparison corrections."""
from __future__ import annotations

import numpy as np


def bonferroni(pvalues: list[float] | np.ndarray, alpha: float = 0.05) -> dict:
    """Bonferroni correction: per-test threshold = alpha / m."""
    p = np.asarray(pvalues, dtype=float)
    m = len(p)
    adjusted = np.minimum(p * m, 1.0)
    threshold = alpha / m
    return {
        "method": "Bonferroni",
        "m": int(m),
        "alpha": float(alpha),
        "threshold": float(threshold),
        "adjusted": adjusted.tolist(),
        "reject": (p < threshold).tolist(),
    }


def bh_fdr(pvalues: list[float] | np.ndarray, q: float = 0.05) -> dict:
    """Benjamini-Hochberg FDR-controlling procedure.

    Returns adjusted q-values and reject decisions at false-discovery rate q.
    """
    p = np.asarray(pvalues, dtype=float)
    m = len(p)
    order = np.argsort(p)
    ranked = p[order]
    bh = ranked * m / (np.arange(1, m + 1))
    # enforce monotonicity from the largest down
    bh_mono = np.minimum.accumulate(bh[::-1])[::-1]
    bh_mono = np.minimum(bh_mono, 1.0)
    # restore original order
    adjusted = np.empty_like(bh_mono)
    adjusted[order] = bh_mono
    # find largest k such that p_(k) <= k/m * q
    thresholds = np.arange(1, m + 1) / m * q
    below = ranked <= thresholds
    if below.any():
        k_max = int(np.where(below)[0].max())
        cutoff = ranked[k_max]
    else:
        cutoff = 0.0
    reject = (p <= cutoff) if cutoff > 0 else np.zeros_like(p, dtype=bool)
    return {
        "method": "Benjamini-Hochberg",
        "m": int(m),
        "q": float(q),
        "cutoff_pvalue": float(cutoff),
        "adjusted": adjusted.tolist(),
        "reject": reject.tolist(),
    }
