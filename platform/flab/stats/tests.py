"""Frequentist tests + Bayesian sensitivity for difference in means."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy import stats

from flab.config import get_random_seed
from flab.stats.effects import cohens_d_ci, odds_ratio_ci, rank_biserial, risk_difference_ci


@dataclass(frozen=True)
class ContResult:
    method: str
    n_a: int
    n_b: int
    mean_a: float
    mean_b: float
    statistic: float
    p_value: float
    df: float | None
    effect_label: str
    effect_size: float
    ci_low: float
    ci_high: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BinaryResult:
    method: str
    n_a: int
    n_b: int
    x_a: int
    x_b: int
    p_hat_a: float
    p_hat_b: float
    statistic: float
    p_value: float
    effect_label: str
    effect_size: float
    ci_low: float
    ci_high: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AnovaResult:
    method: str
    k: int
    n_total: int
    statistic: float
    p_value: float
    df_between: int
    df_within: int
    eta_squared: float
    omega_squared: float
    group_means: dict[str, float]
    group_ns: dict[str, int]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class BootstrapResult:
    estimate: float
    ci_low: float
    ci_high: float
    n_resamples: int
    method: str

    def to_dict(self) -> dict:
        return asdict(self)


def welch_t(a: np.ndarray, b: np.ndarray, alternative: str = "two-sided") -> ContResult:
    """Welch's two-sample t-test (unequal variances) + Hedges' g effect size."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    t = stats.ttest_ind(a, b, equal_var=False, alternative=alternative)
    eff = cohens_d_ci(a, b)
    return ContResult(
        method="welch_t",
        n_a=len(a),
        n_b=len(b),
        mean_a=float(a.mean()),
        mean_b=float(b.mean()),
        statistic=float(t.statistic),
        p_value=float(t.pvalue),
        df=float(getattr(t, "df", np.nan)),
        effect_label=eff.label,
        effect_size=eff.estimate,
        ci_low=eff.ci_low,
        ci_high=eff.ci_high,
    )


def mann_whitney(a: np.ndarray, b: np.ndarray, alternative: str = "two-sided") -> ContResult:
    """Mann-Whitney U + rank-biserial correlation as effect size."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    u = stats.mannwhitneyu(a, b, alternative=alternative)
    r = rank_biserial(a, b)
    # bootstrap CI for the effect (1000 resamples is plenty for the dashboard)
    rng = np.random.default_rng(get_random_seed())
    boots = np.empty(1000)
    for i in range(1000):
        boots[i] = rank_biserial(
            a[rng.integers(0, len(a), size=len(a))],
            b[rng.integers(0, len(b), size=len(b))],
        )
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return ContResult(
        method="mann_whitney",
        n_a=len(a),
        n_b=len(b),
        mean_a=float(np.median(a)),
        mean_b=float(np.median(b)),
        statistic=float(u.statistic),
        p_value=float(u.pvalue),
        df=None,
        effect_label="rank-biserial r",
        effect_size=float(r),
        ci_low=float(lo),
        ci_high=float(hi),
    )


def two_proportion_z(
    x_a: int, n_a: int, x_b: int, n_b: int, alternative: str = "two-sided"
) -> BinaryResult:
    """Two-proportion z-test (pooled) with risk-difference Wald CI."""
    if min(n_a, n_b) == 0:
        raise ValueError("n_a and n_b must be > 0")
    p_a, p_b = x_a / n_a, x_b / n_b
    p_pool = (x_a + x_b) / (n_a + n_b)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
    if se == 0:
        z = 0.0
    else:
        z = (p_a - p_b) / se
    if alternative == "two-sided":
        p = 2 * (1 - stats.norm.cdf(abs(z)))
    elif alternative == "greater":
        p = 1 - stats.norm.cdf(z)
    else:
        p = stats.norm.cdf(z)
    rd = risk_difference_ci(x_a, n_a, x_b, n_b)
    return BinaryResult(
        method="two_prop_z",
        n_a=n_a,
        n_b=n_b,
        x_a=x_a,
        x_b=x_b,
        p_hat_a=float(p_a),
        p_hat_b=float(p_b),
        statistic=float(z),
        p_value=float(p),
        effect_label=rd.label,
        effect_size=rd.estimate,
        ci_low=rd.ci_low,
        ci_high=rd.ci_high,
    )


def two_proportion_or(x_a: int, n_a: int, x_b: int, n_b: int) -> BinaryResult:
    """Same data as `two_proportion_z`, but reports the odds ratio + Wald log-OR CI."""
    if min(n_a, n_b) == 0:
        raise ValueError("n_a and n_b must be > 0")
    p_a, p_b = x_a / n_a, x_b / n_b
    p_pool = (x_a + x_b) / (n_a + n_b)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
    z = (p_a - p_b) / se if se > 0 else 0.0
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    or_ = odds_ratio_ci(x_a, n_a, x_b, n_b)
    return BinaryResult(
        method="odds_ratio",
        n_a=n_a,
        n_b=n_b,
        x_a=x_a,
        x_b=x_b,
        p_hat_a=float(p_a),
        p_hat_b=float(p_b),
        statistic=float(z),
        p_value=float(p),
        effect_label=or_.label,
        effect_size=or_.estimate,
        ci_low=or_.ci_low,
        ci_high=or_.ci_high,
    )


def anova_oneway(groups: dict[str, np.ndarray]) -> AnovaResult:
    """One-way ANOVA + eta-squared and omega-squared effect sizes."""
    labels = list(groups.keys())
    arrays = [np.asarray(groups[k], dtype=float) for k in labels]
    if len(arrays) < 2:
        raise ValueError("Need at least 2 groups")
    f = stats.f_oneway(*arrays)
    n_total = sum(len(x) for x in arrays)
    k = len(arrays)
    df_between = k - 1
    df_within = n_total - k
    grand = np.concatenate(arrays).mean()
    ss_between = sum(len(x) * (x.mean() - grand) ** 2 for x in arrays)
    ss_total = sum(((np.concatenate(arrays) - grand) ** 2).sum() for _ in [None])
    ms_within = (ss_total - ss_between) / df_within if df_within > 0 else np.nan
    eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
    omega_sq = (
        (ss_between - df_between * ms_within) / (ss_total + ms_within)
        if ms_within is not None and ss_total + ms_within != 0
        else 0.0
    )
    return AnovaResult(
        method="anova_oneway",
        k=k,
        n_total=n_total,
        statistic=float(f.statistic),
        p_value=float(f.pvalue),
        df_between=df_between,
        df_within=df_within,
        eta_squared=float(max(0.0, eta_sq)),
        omega_squared=float(max(0.0, omega_sq)),
        group_means={lab: float(arr.mean()) for lab, arr in zip(labels, arrays)},
        group_ns={lab: int(len(arr)) for lab, arr in zip(labels, arrays)},
    )


def kruskal_wallis(groups: dict[str, np.ndarray]) -> AnovaResult:
    """Kruskal-Wallis H + epsilon-squared effect size."""
    labels = list(groups.keys())
    arrays = [np.asarray(groups[k], dtype=float) for k in labels]
    h = stats.kruskal(*arrays)
    n_total = sum(len(x) for x in arrays)
    k = len(arrays)
    # Epsilon-squared = (H - k + 1) / (n - k)
    eps_sq = max(0.0, (h.statistic - k + 1) / (n_total - k)) if n_total > k else 0.0
    return AnovaResult(
        method="kruskal_wallis",
        k=k,
        n_total=n_total,
        statistic=float(h.statistic),
        p_value=float(h.pvalue),
        df_between=k - 1,
        df_within=n_total - k,
        eta_squared=float(eps_sq),
        omega_squared=float(eps_sq),
        group_means={lab: float(np.median(arr)) for lab, arr in zip(labels, arrays)},
        group_ns={lab: int(len(arr)) for lab, arr in zip(labels, arrays)},
    )


def bayesian_diff_in_means(
    a: np.ndarray,
    b: np.ndarray,
    n_samples: int = 20_000,
    seed: int | None = None,
) -> dict:
    """Conjugate Normal-Inverse-Gamma posterior for two-sample mean difference.

    Uses uninformative Jeffreys-style priors:
        mu_i | sigma_i^2 ~ Normal(mean_i, sigma_i^2 / n_i)   (data-driven prior shift)
        sigma_i^2        ~ scaled-inverse-chi-square(n_i - 1, sample_var_i)

    Posterior samples of (mu_a - mu_b) come directly from these conjugate forms.
    Reports posterior mean diff, 95% credible interval, P(mu_a > mu_b), and
    Bayes factor (BIC approximation) for sensitivity vs the frequentist test.

    This is a deliberate Bayesian sensitivity layer: it is NOT meant to replace
    the headline test, but to show convergence (or divergence) of conclusions
    under a generative model. Avoids PyMC to keep CI runtime small.
    """
    rng = np.random.default_rng(seed if seed is not None else get_random_seed())
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 2 or len(b) < 2:
        raise ValueError("Need at least 2 observations per group")

    def posterior_samples(x: np.ndarray) -> np.ndarray:
        n = len(x)
        mean = x.mean()
        var = x.var(ddof=1)
        # sigma^2 from scaled inv-chi-square(n-1, var) == (n-1)*var / chi2(n-1)
        chi2 = rng.chisquare(df=n - 1, size=n_samples)
        sigma2 = (n - 1) * var / chi2
        mu = rng.normal(loc=mean, scale=np.sqrt(sigma2 / n), size=n_samples)
        return mu

    mu_a = posterior_samples(a)
    mu_b = posterior_samples(b)
    diff = mu_a - mu_b
    lo, hi = np.quantile(diff, [0.025, 0.975])
    prob_a_gt_b = float((diff > 0).mean())

    # BIC-based BF approximation (Wagenmakers 2007) for H1: means differ vs H0: equal.
    # Compute in log space to avoid float overflow on huge t-stats.
    t_stat = stats.ttest_ind(a, b, equal_var=False)
    n_total = len(a) + len(b)
    log_bf10 = 0.5 * np.log(n_total) + 0.5 * t_stat.statistic**2 - 0.5 * np.log(n_total)
    log_bf10 = float(log_bf10)
    # cap at 1e300 (well within float64) by clipping log
    bf10 = float(np.exp(min(log_bf10, 700)))

    return {
        "method": "bayesian_diff_in_means",
        "posterior_mean_diff": float(diff.mean()),
        "posterior_median_diff": float(np.median(diff)),
        "credible_low": float(lo),
        "credible_high": float(hi),
        "prob_a_gt_b": prob_a_gt_b,
        "bf10_bic": bf10,
        "log_bf10_bic": log_bf10,
        "n_a": len(a),
        "n_b": len(b),
        "n_samples": n_samples,
    }
