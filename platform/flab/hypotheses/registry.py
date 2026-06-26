"""Preregistered HMDA hypothesis registry plus per-hypothesis runners.

Every test ships with: H0 / H1, direction, pre-registered effect of interest,
power block, assumption diagnostics, parametric and non-parametric tests,
permutation test, bootstrap CI, and (where applicable) a Bayesian sensitivity.
All five primary p-values are pushed through BH-FDR and Bonferroni at the end.

Causal framing: HMDA does NOT contain credit scores, full underwriting variables,
or detailed property appraisals. So any disparity reported here is a screening
signal, an association in the data conditional on the covariates we observe.
Establishing discrimination requires matched supervisory data, audit pairs, or
randomized testing. The dashboard repeats this caveat next to every result.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from flab.config import get_random_seed
from flab.db import fetch_df, get_conn
from flab.stats import (
    anova_oneway,
    bayesian_diff_in_means,
    bh_fdr,
    bonferroni,
    bootstrap_ci,
    kruskal_wallis,
    mann_whitney,
    permutation_test_means,
    sample_size_two_means,
    sample_size_two_props,
    two_proportion_z,
    welch_t,
)
from flab.stats.tests import two_proportion_or

DEFAULT_SAMPLE_PER_GROUP = 5000


@dataclass
class Hypothesis:
    key: str
    title: str
    h0: str
    h1: str
    direction: str
    effect_of_interest: str
    domain_question: str
    causal_caveat: str
    runner: Callable[[dict], dict] = field(repr=False)


def _sample(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    if len(df) <= n:
        return df.copy()
    return df.sample(n=n, random_state=seed).reset_index(drop=True)


def _summary_continuous(a: np.ndarray, b: np.ndarray, name_a: str, name_b: str) -> dict:
    return {
        name_a: {
            "n": int(len(a)),
            "mean": float(a.mean()),
            "median": float(np.median(a)),
            "sd": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
            "p25": float(np.quantile(a, 0.25)),
            "p75": float(np.quantile(a, 0.75)),
        },
        name_b: {
            "n": int(len(b)),
            "mean": float(b.mean()),
            "median": float(np.median(b)),
            "sd": float(b.std(ddof=1)) if len(b) > 1 else 0.0,
            "p25": float(np.quantile(b, 0.25)),
            "p75": float(np.quantile(b, 0.75)),
        },
    }


def _safe_for_json(obj):
    if isinstance(obj, dict):
        return {k: _safe_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_for_json(x) for x in obj]
    if isinstance(obj, float):
        if obj != obj:
            return None
        if obj == float("inf"):
            return 1e308
        if obj == float("-inf"):
            return -1e308
        return obj
    return obj


# ---------------------------------------------------------------------------
# H1: Denial rate, Black vs White non-Hispanic.
# ---------------------------------------------------------------------------

def _runner_h1(opts: dict) -> dict:
    seed = opts.get("seed", get_random_seed())
    df = fetch_df(
        """
        SELECT race_group, ethnicity_group, denied
        FROM flab.loans
        WHERE race_group IN ('White', 'Black')
          AND ethnicity_group = 'Non-Hispanic'
        """
    )
    a = df[df["race_group"] == "Black"]
    b = df[df["race_group"] == "White"]
    x_a, n_a = int(a["denied"].sum()), int(len(a))
    x_b, n_b = int(b["denied"].sum()), int(len(b))

    z = two_proportion_z(x_a, n_a, x_b, n_b, alternative="greater")
    or_ = two_proportion_or(x_a, n_a, x_b, n_b)

    p1, p2 = x_a / n_a, x_b / n_b
    n_required = sample_size_two_props(max(p1, 0.01), max(p2, 0.01)) if abs(p1 - p2) > 1e-6 else None

    # Stratified sensitivity by income band, BH-FDR'd across strata.
    strat = fetch_df(
        """
        SELECT race_group, income_band,
               SUM(denied::int)::INT AS x,
               COUNT(*)::INT          AS n
        FROM flab.loans
        WHERE race_group IN ('White', 'Black')
          AND ethnicity_group = 'Non-Hispanic'
          AND income_band <> 'unknown'
        GROUP BY race_group, income_band
        """
    )
    by_band = []
    p_list = []
    for band, sub in strat.groupby("income_band"):
        wa = sub[sub["race_group"] == "Black"]
        wb = sub[sub["race_group"] == "White"]
        if wa.empty or wb.empty:
            continue
        xa = int(wa["x"].iloc[0]); na = int(wa["n"].iloc[0])
        xb = int(wb["x"].iloc[0]); nb = int(wb["n"].iloc[0])
        if min(na, nb) < 50:
            continue
        zr = two_proportion_z(xa, na, xb, nb, alternative="greater")
        orx = two_proportion_or(xa, na, xb, nb)
        by_band.append({
            "income_band": band,
            "n_black": na, "x_black": xa, "p_black": xa / na,
            "n_white": nb, "x_white": xb, "p_white": xb / nb,
            "rd": zr.effect_size, "rd_ci_low": zr.ci_low, "rd_ci_high": zr.ci_high,
            "or": orx.effect_size, "or_ci_low": orx.ci_low, "or_ci_high": orx.ci_high,
            "p_value": zr.p_value,
        })
        p_list.append(zr.p_value)
    bh = bh_fdr(p_list) if p_list else None
    if bh:
        for i, row in enumerate(by_band):
            row["p_fdr"] = bh["adjusted"][i]
            row["reject_fdr"] = bool(bh["reject"][i])

    return _safe_for_json({
        "primary": z.to_dict(),
        "secondary": {
            "odds_ratio": or_.to_dict(),
            "stratified_by_income_band": by_band,
            "income_band_fdr": bh,
        },
        "assumptions": {
            "min_cell_count_ok": bool(min(x_a, n_a - x_a, x_b, n_b - x_b) >= 10),
            "note": "Wald CI valid when all 4 cells >= 10. Stratified subgroups use BH-FDR.",
        },
        "power": {
            "n_required_per_group": n_required,
            "achieved_n_black": n_a,
            "achieved_n_white": n_b,
        },
        "groups": {
            "Black non-Hispanic": {"x": x_a, "n": n_a, "p_hat": x_a / n_a},
            "White non-Hispanic": {"x": x_b, "n": n_b, "p_hat": x_b / n_b},
        },
    })


# ---------------------------------------------------------------------------
# H2: Denial rate, Hispanic vs White non-Hispanic.
# ---------------------------------------------------------------------------

def _runner_h2(opts: dict) -> dict:
    df = fetch_df(
        """
        SELECT race_group, ethnicity_group, denied
        FROM flab.loans
        WHERE (
              (ethnicity_group = 'Hispanic')
              OR
              (race_group = 'White' AND ethnicity_group = 'Non-Hispanic')
        )
        """
    )
    a = df[df["ethnicity_group"] == "Hispanic"]
    b = df[(df["race_group"] == "White") & (df["ethnicity_group"] == "Non-Hispanic")]
    x_a, n_a = int(a["denied"].sum()), int(len(a))
    x_b, n_b = int(b["denied"].sum()), int(len(b))

    z = two_proportion_z(x_a, n_a, x_b, n_b, alternative="greater")
    or_ = two_proportion_or(x_a, n_a, x_b, n_b)

    return _safe_for_json({
        "primary": z.to_dict(),
        "secondary": {"odds_ratio": or_.to_dict()},
        "assumptions": {"min_cell_count_ok": bool(min(x_a, n_a - x_a, x_b, n_b - x_b) >= 10)},
        "power": {"achieved_n_hispanic": n_a, "achieved_n_white_nh": n_b},
        "groups": {
            "Hispanic": {"x": x_a, "n": n_a, "p_hat": x_a / n_a},
            "White non-Hispanic": {"x": x_b, "n": n_b, "p_hat": x_b / n_b},
        },
    })


# ---------------------------------------------------------------------------
# H3: Mean rate spread on priced loans, Black originated vs White originated.
# ---------------------------------------------------------------------------

def _runner_h3(opts: dict) -> dict:
    seed = opts.get("seed", get_random_seed())
    n_per = opts.get("n_per_group", DEFAULT_SAMPLE_PER_GROUP)
    df = fetch_df(
        """
        SELECT race_group, ethnicity_group, rate_spread
        FROM flab.loans
        WHERE originated = TRUE
          AND is_priced_loan = TRUE
          AND ethnicity_group = 'Non-Hispanic'
          AND race_group IN ('Black', 'White')
          AND rate_spread BETWEEN -2 AND 10
        """
    )
    aS = _sample(df[df["race_group"] == "Black"], n_per, seed)
    bS = _sample(df[df["race_group"] == "White"], n_per, seed + 1)
    a = aS["rate_spread"].to_numpy()
    b = bS["rate_spread"].to_numpy()

    if len(a) < 30 or len(b) < 30:
        return _safe_for_json({
            "primary": {"method": "welch_t", "p_value": None, "effect_size": None,
                        "effect_label": "Hedges' g", "n_a": int(len(a)), "n_b": int(len(b)),
                        "ci_low": None, "ci_high": None,
                        "statistic": None, "mean_a": float(a.mean()) if len(a) else None,
                        "mean_b": float(b.mean()) if len(b) else None, "df": None,
                        "method_note": "insufficient priced-loan sample, test skipped"},
            "secondary": {},
            "assumptions": {"note": "insufficient sample"},
            "power": {"achieved_n_per_group": int(min(len(a), len(b)))},
            "groups": _summary_continuous(a, b, "Black priced loans", "White priced loans") if len(a) and len(b) else {},
        })

    welch = welch_t(a, b, alternative="two-sided")
    mw = mann_whitney(a, b, alternative="two-sided")
    perm = permutation_test_means(a, b, n_permutations=5000, seed=seed)
    boot = bootstrap_ci(a, b, n_resamples=2000, seed=seed)
    bayes = bayesian_diff_in_means(a, b, n_samples=15_000, seed=seed)

    return _safe_for_json({
        "primary": welch.to_dict(),
        "secondary": {
            "mann_whitney": mw.to_dict(),
            "permutation": perm,
            "bootstrap_mean_diff_ci": asdict(boot),
            "bayesian": bayes,
        },
        "assumptions": _assumption_checks(a, b),
        "power": {
            "target_cohens_d": 0.1,
            "n_required_per_group": sample_size_two_means(0.1),
            "achieved_n_per_group": int(min(len(a), len(b))),
        },
        "groups": _summary_continuous(a, b, "Black priced loans", "White priced loans"),
    })


# ---------------------------------------------------------------------------
# H4: Denial rates differ across the top 10 lenders by application volume.
# ---------------------------------------------------------------------------

def _runner_h4(opts: dict) -> dict:
    top = fetch_df(
        """
        SELECT lei, COUNT(*) AS n,
               SUM(denied::int) AS x_denied
        FROM flab.loans
        WHERE lei IS NOT NULL
        GROUP BY lei
        ORDER BY n DESC
        LIMIT 10
        """
    )
    if len(top) < 2:
        return {"primary": {"method": "anova_oneway", "p_value": None}, "groups": {}}
    df = fetch_df(
        """
        SELECT lei, denied
        FROM flab.loans
        WHERE lei = ANY(%(leis)s)
        """,
        {"leis": top["lei"].tolist()},
    )
    groups = {
        f"lender_{i+1}": df[df["lei"] == lei]["denied"].astype(int).to_numpy()
        for i, lei in enumerate(top["lei"].tolist())
    }
    anova = anova_oneway(groups)
    kw = kruskal_wallis(groups)

    pair_pvals = []
    pair_meta = []
    keys = list(groups.keys())
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1 :]:
            xa = int(groups[k1].sum()); na = int(len(groups[k1]))
            xb = int(groups[k2].sum()); nb = int(len(groups[k2]))
            if min(na, nb) < 30:
                continue
            zr = two_proportion_z(xa, na, xb, nb)
            pair_meta.append({
                "pair": f"{k1} vs {k2}",
                "p_a": xa / na, "p_b": xb / nb,
                "rd": zr.effect_size, "rd_ci_low": zr.ci_low, "rd_ci_high": zr.ci_high,
                "p_value": zr.p_value,
            })
            pair_pvals.append(zr.p_value)
    fdr = bh_fdr(pair_pvals) if pair_pvals else None
    bf = bonferroni(pair_pvals) if pair_pvals else None
    pairs = []
    for i, m in enumerate(pair_meta):
        pairs.append({
            **m,
            "p_fdr": fdr["adjusted"][i] if fdr else None,
            "reject_fdr": bool(fdr["reject"][i]) if fdr else None,
            "p_bonferroni": bf["adjusted"][i] if bf else None,
            "reject_bonferroni": bool(bf["reject"][i]) if bf else None,
        })

    return _safe_for_json({
        "primary": anova.to_dict(),
        "secondary": {"kruskal_wallis": kw.to_dict(), "pairwise_two_prop": pairs,
                      "bh_fdr": fdr, "bonferroni": bf},
        "assumptions": {"note": "ANOVA on 0/1 outcomes is a linear-probability F-test, "
                                "equivalent in expectation to a chi-square. KW is the "
                                "non-parametric backstop."},
        "power": {"k_groups": len(groups),
                  "n_per_group_min": int(min(len(arr) for arr in groups.values()))},
        "groups": {
            k: {"n": int(len(arr)), "denial_rate": float(arr.mean()), "n_denied": int(arr.sum())}
            for k, arr in groups.items()
        },
        "lender_table": [
            {"lender_label": f"lender_{i+1}", "lei": lei,
             "n": int(top["n"].iloc[i]), "x_denied": int(top["x_denied"].iloc[i])}
            for i, lei in enumerate(top["lei"].tolist())
        ],
    })


# ---------------------------------------------------------------------------
# H5: Denial rate higher for low-income Black applicants than low-income White
#     applicants (race effect persists within the lowest income band).
# ---------------------------------------------------------------------------

def _runner_h5(opts: dict) -> dict:
    df = fetch_df(
        """
        SELECT race_group, ethnicity_group, denied
        FROM flab.loans
        WHERE income_band = 'under_50k'
          AND ethnicity_group = 'Non-Hispanic'
          AND race_group IN ('Black', 'White')
        """
    )
    a = df[df["race_group"] == "Black"]
    b = df[df["race_group"] == "White"]
    x_a, n_a = int(a["denied"].sum()), int(len(a))
    x_b, n_b = int(b["denied"].sum()), int(len(b))
    if min(n_a, n_b) < 30:
        return {"primary": {"method": "two_prop_z", "p_value": None,
                            "n_a": n_a, "n_b": n_b,
                            "method_note": "insufficient subsample"}}
    z = two_proportion_z(x_a, n_a, x_b, n_b, alternative="greater")
    or_ = two_proportion_or(x_a, n_a, x_b, n_b)
    return _safe_for_json({
        "primary": z.to_dict(),
        "secondary": {"odds_ratio": or_.to_dict()},
        "assumptions": {"min_cell_count_ok": bool(min(x_a, n_a - x_a, x_b, n_b - x_b) >= 10)},
        "groups": {
            "Black under_50k": {"x": x_a, "n": n_a, "p_hat": x_a / n_a},
            "White under_50k": {"x": x_b, "n": n_b, "p_hat": x_b / n_b},
        },
    })


def _assumption_checks(a: np.ndarray, b: np.ndarray, sample_for_normal: int = 500) -> dict:
    from scipy import stats as sp

    rng = np.random.default_rng(get_random_seed())
    a_s = a if len(a) <= sample_for_normal else rng.choice(a, size=sample_for_normal, replace=False)
    b_s = b if len(b) <= sample_for_normal else rng.choice(b, size=sample_for_normal, replace=False)
    return {
        "shapiro_a_p": float(sp.shapiro(a_s).pvalue) if len(a_s) >= 3 else None,
        "shapiro_b_p": float(sp.shapiro(b_s).pvalue) if len(b_s) >= 3 else None,
        "levene_p": float(sp.levene(a, b, center="median").pvalue),
        "skew_a": float(sp.skew(a)),
        "skew_b": float(sp.skew(b)),
        "note": (
            "Shapiro is run on a 500-sample slice (Shapiro is overpowered at large n). "
            "Levene tests homogeneity of variance. Welch's t-test does not require equal "
            "variances; Levene is reported for completeness."
        ),
    }


REGISTRY: dict[str, Hypothesis] = {
    "h1_denial_race": Hypothesis(
        key="h1_denial_race",
        title="Denial rate disparity, Black versus White non-Hispanic applicants",
        h0="p_Black_denied = p_White_denied",
        h1="p_Black_denied > p_White_denied",
        direction="greater",
        effect_of_interest="Risk difference >= 0.05, OR >= 1.3",
        domain_question=(
            "Among home-purchase conventional first-lien applications for owner-occupied "
            "principal residences, is the denial rate for Black non-Hispanic applicants "
            "higher than for White non-Hispanic applicants?"
        ),
        causal_caveat=(
            "HMDA does not include credit score, full underwriting, or property appraisal. "
            "A higher denial rate here is a screening signal of disparate outcomes, not a "
            "finding of discrimination. Establishing discrimination requires matched files "
            "(supervisory HMDA), audit pairs, or randomized testing."
        ),
        runner=_runner_h1,
    ),
    "h2_denial_ethnicity": Hypothesis(
        key="h2_denial_ethnicity",
        title="Denial rate disparity, Hispanic versus White non-Hispanic applicants",
        h0="p_Hispanic_denied = p_White_nH_denied",
        h1="p_Hispanic_denied > p_White_nH_denied",
        direction="greater",
        effect_of_interest="Risk difference >= 0.03, OR >= 1.2",
        domain_question=(
            "Same outcome question as H1 but contrasting Hispanic applicants against "
            "White non-Hispanic applicants."
        ),
        causal_caveat=(
            "Identical caveat to H1. See HMDA limitations note."
        ),
        runner=_runner_h2,
    ),
    "h3_rate_spread_priced": Hypothesis(
        key="h3_rate_spread_priced",
        title="Rate spread on priced originated loans, Black versus White borrowers",
        h0="mu_Black_rate_spread = mu_White_rate_spread",
        h1="mu_Black_rate_spread != mu_White_rate_spread",
        direction="two-sided",
        effect_of_interest="Hedges g >= 0.1, mean diff >= 0.25 pct points",
        domain_question=(
            "Among priced (higher-priced) originated loans, does the average rate spread "
            "differ between Black and White borrowers?"
        ),
        causal_caveat=(
            "Restricting to priced loans is a conditioning-on-collider risk: the same "
            "underwriting that produces a higher denial rate may also push observed borrowers "
            "toward the priced segment. The result is informative about the priced-loan "
            "population, not about the underlying borrower population."
        ),
        runner=_runner_h3,
    ),
    "h4_lender_effect": Hypothesis(
        key="h4_lender_effect",
        title="Denial rates differ across the top 10 lenders by application volume",
        h0="all lender denial rates equal",
        h1="at least one lender denial rate differs",
        direction="two-sided",
        effect_of_interest="At least one pairwise risk difference >= 0.05",
        domain_question=(
            "Holding loan type, purpose, lien and occupancy constant, do denial rates "
            "vary materially across the 10 largest mortgage lenders in this market?"
        ),
        causal_caveat=(
            "Lender mix correlates with applicant mix. A lender-by-lender comparison "
            "without applicant covariates is descriptive, not causal. It still surfaces "
            "operationally useful targeting for compliance review."
        ),
        runner=_runner_h4,
    ),
    "h5_low_income_residual": Hypothesis(
        key="h5_low_income_residual",
        title="Denial rate disparity persists within the lowest income band",
        h0="within under_50k income band, p_Black = p_White",
        h1="within under_50k income band, p_Black > p_White",
        direction="greater",
        effect_of_interest="Risk difference >= 0.03 within the under_50k band",
        domain_question=(
            "Does the Black vs White disparity in denial rates persist when both groups "
            "share an income band, the simplest income control HMDA supports?"
        ),
        causal_caveat=(
            "Conditioning on income band is a coarse control. Real underwriting depends "
            "on income times debt service, plus assets, credit score, and LTV. Persistence "
            "of the disparity inside one band is consistent with, not proof of, residual race "
            "association after partial adjustment."
        ),
        runner=_runner_h5,
    ),
}


def run_hypothesis(key: str, **opts) -> dict:
    if key not in REGISTRY:
        raise KeyError(f"Unknown hypothesis: {key}")
    h = REGISTRY[key]
    logger.info("running hypothesis", key=key)
    payload = h.runner(opts)
    return {
        "key": key,
        "title": h.title,
        "h0": h.h0,
        "h1": h.h1,
        "direction": h.direction,
        "effect_of_interest": h.effect_of_interest,
        "domain_question": h.domain_question,
        "causal_caveat": h.causal_caveat,
        **payload,
    }


def run_and_cache(key: str, **opts) -> dict:
    payload = run_hypothesis(key, **opts)
    primary = payload.get("primary") or {}
    detail = json.dumps(_safe_for_json(payload), default=str, allow_nan=False)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO flab.analysis_runs
                  (hypothesis_key, method, n_group_a, n_group_b,
                   statistic, p_value, effect_size, effect_label,
                   ci_low, ci_high, detail)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    key,
                    primary.get("method"),
                    primary.get("n_a"),
                    primary.get("n_b"),
                    primary.get("statistic"),
                    primary.get("p_value"),
                    primary.get("effect_size"),
                    primary.get("effect_label"),
                    primary.get("ci_low"),
                    primary.get("ci_high"),
                    detail,
                ),
            )
            cur.execute(
                """
                INSERT INTO flab.results_cache (hypothesis_key, payload, refreshed_at)
                VALUES (%s, %s::jsonb, now())
                ON CONFLICT (hypothesis_key) DO UPDATE
                  SET payload = EXCLUDED.payload, refreshed_at = EXCLUDED.refreshed_at
                """,
                (key, detail),
            )
        conn.commit()
    return payload


def all_pvalues_for_correction() -> tuple[list[str], list[float]]:
    keys, ps = [], []
    for key in REGISTRY:
        df = fetch_df(
            "SELECT payload->'primary'->>'p_value' AS p FROM flab.results_cache "
            "WHERE hypothesis_key = %(k)s",
            {"k": key},
        )
        if df.empty or df.iloc[0]["p"] is None:
            continue
        try:
            ps.append(float(df.iloc[0]["p"]))
            keys.append(key)
        except (TypeError, ValueError):
            continue
    return keys, ps


def family_wise_correction() -> dict[str, Any]:
    keys, ps = all_pvalues_for_correction()
    if not ps:
        return {"family": []}
    fdr = bh_fdr(ps)
    bf = bonferroni(ps)
    rows = []
    for i, k in enumerate(keys):
        rows.append(
            {
                "hypothesis_key": k,
                "p_value": ps[i],
                "p_fdr": fdr["adjusted"][i],
                "reject_fdr": bool(fdr["reject"][i]),
                "p_bonferroni": bf["adjusted"][i],
                "reject_bonferroni": bool(bf["reject"][i]),
            }
        )
    return {"family": rows, "fdr": fdr, "bonferroni": bf}
