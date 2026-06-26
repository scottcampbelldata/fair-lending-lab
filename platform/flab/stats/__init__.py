"""Statistical-inference helpers used across the case study.

Modules are pure (no DB) so they are trivially testable. Every function returns
a dataclass with statistic, p_value, effect_size, confidence interval, and any
auxiliary diagnostic fields. Seeds default to flab.config.get_random_seed().
"""
from flab.stats.effects import (
    cohens_d,
    cohens_d_ci,
    cliffs_delta,
    odds_ratio_ci,
    rank_biserial,
    risk_difference_ci,
)
from flab.stats.multiple import bh_fdr, bonferroni
from flab.stats.power import (
    minimum_detectable_effect_two_means,
    sample_size_two_means,
    sample_size_two_props,
)
from flab.stats.resampling import bootstrap_ci, permutation_test_means
from flab.stats.tests import (
    AnovaResult,
    BinaryResult,
    BootstrapResult,
    ContResult,
    anova_oneway,
    bayesian_diff_in_means,
    kruskal_wallis,
    mann_whitney,
    two_proportion_z,
    welch_t,
)

__all__ = [
    "AnovaResult",
    "BinaryResult",
    "BootstrapResult",
    "ContResult",
    "anova_oneway",
    "bayesian_diff_in_means",
    "bh_fdr",
    "bonferroni",
    "bootstrap_ci",
    "cliffs_delta",
    "cohens_d",
    "cohens_d_ci",
    "kruskal_wallis",
    "mann_whitney",
    "minimum_detectable_effect_two_means",
    "odds_ratio_ci",
    "permutation_test_means",
    "rank_biserial",
    "risk_difference_ci",
    "sample_size_two_means",
    "sample_size_two_props",
    "two_proportion_z",
    "welch_t",
]
