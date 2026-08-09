"""Covariate-adjusted denial model for H1 (Black non-Hispanic vs White non-Hispanic).

Why this file exists
--------------------
The preregistered H1 test in ``flab.hypotheses.registry`` estimates a RAW,
MARGINAL denial-rate difference and then validates it five ways: two-proportion
z, odds ratio, permutation, bootstrap, and a stratified/FDR sensitivity. All
five layers answer the same question, "is this marginal difference real given
the sampling noise", and at n = 41,287 sampling noise was never the binding
constraint. The binding constraint is omitted-variable bias, and every one of
those five layers inherits it.

HMDA carries underwriting-relevant fields the marginal estimate ignores:
debt-to-income, combined loan-to-value, loan amount, property value, income,
and which automated underwriting system saw the file. This module refits the
same contrast with those covariates in a logistic regression and reports the
adjusted odds ratio and the adjusted average marginal risk difference next to
the raw number, so the headline can state how much of the gap survives
adjustment rather than implying the raw gap is the effect.

What this is NOT
----------------
This is still not a causal estimate.

  * HMDA has no credit score, no reserves, no full appraisal, no compensating
    factors. What survives adjustment is an upper bound on any lender effect
    plus whatever those unobserved variables carry.
  * Several controls are downstream of things a lender does. The automated
    underwriting system is a lender/channel choice, and loan amount and CLTV
    are negotiated. Conditioning on them can be conditioning on a collider or
    on a mediator, which can bias the race coefficient in either direction.
    That is why AUS enters as a separate layer, not as part of the primary
    adjusted spec, and why ``denial_reason`` is never a control: it is defined
    by the outcome.
  * Denominator note: the curated cohort keeps action_taken in (1, 3),
    originated or denied. Withdrawn and closed-for-incompleteness files are
    excluded, which is itself a selection decision inherited from the
    preregistered pipeline.

Claiming discrimination still requires matched supervisory data with credit
scores, audit pairs, or randomized testing. This module narrows the screen. It
does not close it.

Reproducing
-----------
    python -m flab.analysis.adjusted_model --csv data/raw/hmda_2023_MA.csv

If the CSV is absent it is downloaded from the same CFPB FFIEC Data Browser
endpoint ``flab.ingest.hmda`` already uses. Everything is seeded.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

# Mirror flab.ingest.hmda so this script can run without a Postgres instance.
HMDA_CSV_URL = "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv"
DEFAULT_YEAR = 2023
DEFAULT_STATE = "MA"

try:  # keep the repo's seed if the package config is importable
    from flab.config import get_random_seed

    DEFAULT_SEED = get_random_seed()
except Exception:  # pragma: no cover - standalone execution
    DEFAULT_SEED = 20260625

USECOLS = [
    "action_taken",
    "loan_purpose",
    "loan_type",
    "lien_status",
    "occupancy_type",
    "business_or_commercial_purpose",
    "loan_amount",
    "loan_to_value_ratio",
    "property_value",
    "income",
    "debt_to_income_ratio",
    "derived_race",
    "derived_ethnicity",
    "derived_sex",
    "applicant_age",
    "derived_msa-md",
    "lei",
    "aus-1",
]
NUMERIC = [
    "action_taken",
    "loan_purpose",
    "loan_type",
    "lien_status",
    "occupancy_type",
    "business_or_commercial_purpose",
    "loan_amount",
    "loan_to_value_ratio",
    "property_value",
    "income",
]

# CLTV bin edges. Right-closed, so the large mass at exactly 80 sits at the top
# of the (75, 80] bin rather than being smeared across a wide interval.
CLTV_EDGES = [0, 50, 60, 70, 75, 80, 85, 90, 95, 97, 100, np.inf]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def download_csv(path: Path, year: int, state: str) -> Path:
    import httpx

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 1_000_000:
        return path
    with httpx.stream(
        "GET",
        HMDA_CSV_URL,
        params={"years": str(year), "states": state.upper()},
        timeout=900.0,
        follow_redirects=True,
    ) as r:
        r.raise_for_status()
        with path.open("wb") as f:
            for chunk in r.iter_bytes(chunk_size=1024 * 1024):
                f.write(chunk)
    return path


def load_curated(csv_path: Path) -> pd.DataFrame:
    """Reproduce flab.ingest.hmda.CURATED_SQL in pandas.

    first lien + conventional + home purchase + principal residence +
    non-business + originated-or-denied + loan amount in [50k, 2M].
    """
    df = pd.read_csv(csv_path, usecols=USECOLS, dtype=str, low_memory=False)
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    keep = (
        df["action_taken"].isin([1, 3])
        & (df["loan_purpose"] == 1)
        & (df["loan_type"] == 1)
        & (df["lien_status"] == 1)
        & (df["occupancy_type"] == 1)
        & (df["business_or_commercial_purpose"] == 2)
        & df["loan_amount"].notna()
        & df["loan_amount"].between(50_000, 2_000_000)
    )
    cur = df.loc[keep].copy()
    cur["denied"] = (cur["action_taken"] == 3).astype(int)
    cur["race_group"] = cur["derived_race"].map(
        {"White": "White", "Black or African American": "Black"}
    )
    cur["ethnicity_group"] = cur["derived_ethnicity"].map(
        {"Hispanic or Latino": "Hispanic", "Not Hispanic or Latino": "Non-Hispanic"}
    )
    return cur.reset_index(drop=True)


def h1_cohort(curated: pd.DataFrame) -> pd.DataFrame:
    m = curated["race_group"].isin(["Black", "White"]) & (
        curated["ethnicity_group"] == "Non-Hispanic"
    )
    return curated.loc[m].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Feature construction
# ---------------------------------------------------------------------------

def _dti_band(v: object) -> str:  # noqa: PLR0911
    """HMDA reports DTI as bands below 36 and above 49, integers in between.

    Keep every reported integer as its own level so the control is as flexible
    as the field allows.
    """
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "unknown"
    s = str(v).strip()
    if s in {"", "nan", "NA", "Exempt"}:
        return "unknown"
    if s == "<20%":
        return "a_lt20"
    if s == "20%-<30%":
        return "b_20_30"
    if s == "30%-<36%":
        return "c_30_36"
    if s == "50%-60%":
        return "y_50_60"
    if s == ">60%":
        return "z_gt60"
    try:
        return f"d_{int(float(s)):02d}"
    except ValueError:
        return "unknown"


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=df.index)
    f["denied"] = df["denied"].to_numpy()
    f["black"] = (df["race_group"] == "Black").astype(int)

    f["dti"] = df["debt_to_income_ratio"].map(_dti_band)

    cltv = df["loan_to_value_ratio"]
    band = pd.cut(cltv, bins=CLTV_EDGES, right=True).astype(str)
    f["cltv"] = np.where(cltv.isna(), "unknown", band)

    # log-scale money variables, median imputation plus an explicit missingness
    # flag so N stays identical across specs and missingness is never silently
    # differenced away.
    for src, name in (
        ("loan_amount", "log_loan_amount"),
        ("property_value", "log_property_value"),
        ("income", "log_income"),
    ):
        v = df[src].astype(float).copy()
        bad = v.isna() | (v <= 0)
        f[f"{name}_missing"] = bad.astype(int)
        med = float(v[~bad].median())
        v = v.where(~bad, med)
        f[name] = np.log(v)

    f["aus"] = df["aus-1"].fillna("unknown").astype(str)
    f["msa"] = df["derived_msa-md"].fillna("unknown").astype(str)
    f["sex"] = df["derived_sex"].fillna("unknown").astype(str)
    f["age"] = df["applicant_age"].fillna("unknown").astype(str)

    lei = df["lei"].fillna("unknown").astype(str)
    counts = lei.value_counts()
    small = counts[counts < 50].index
    f["lender"] = lei.where(~lei.isin(small), "other_small_lender")
    return f


CORE_CONT = [
    "log_loan_amount",
    "log_property_value",
    "log_income",
    "log_loan_amount_missing",
    "log_property_value_missing",
    "log_income_missing",
]

SPECS: dict[str, dict[str, list[str]]] = {
    # raw / marginal: the current published headline
    "raw_marginal": {"cat": [], "cont": []},
    # primary adjusted spec: applicant and loan financials only
    "adjusted_financials": {"cat": ["dti", "cltv"], "cont": CORE_CONT},
    # + which automated underwriting system saw the file (channel proxy)
    "adjusted_plus_aus": {"cat": ["dti", "cltv", "aus"], "cont": CORE_CONT},
    # + geography
    "adjusted_plus_geo": {"cat": ["dti", "cltv", "aus", "msa"], "cont": CORE_CONT},
    # + demographics HMDA reports but that are not underwriting inputs
    "adjusted_plus_demo": {
        "cat": ["dti", "cltv", "aus", "msa", "sex", "age"],
        "cont": CORE_CONT,
    },
    # within-lender: changes the estimand to "same lender, different applicant"
    "adjusted_within_lender": {
        "cat": ["dti", "cltv", "aus", "msa", "sex", "age", "lender"],
        "cont": CORE_CONT,
    },
}


def design(f: pd.DataFrame, spec: dict[str, list[str]]) -> pd.DataFrame:
    parts = [f[["black"]].astype(float)]
    for c in spec["cont"]:
        parts.append(f[[c]].astype(float))
    for c in spec["cat"]:
        d = pd.get_dummies(f[c], prefix=c, drop_first=True, dtype=float)
        parts.append(d)
    X = pd.concat(parts, axis=1)
    X.insert(0, "const", 1.0)
    # drop any all-constant dummy columns produced by empty categories
    keep = [c for c in X.columns if c == "const" or X[c].nunique() > 1]
    return X[keep]


# ---------------------------------------------------------------------------
# Estimation
# ---------------------------------------------------------------------------

@dataclass
class SpecResult:
    spec: str
    n: int
    n_black: int
    n_white: int
    n_params: int
    log_or: float | None
    odds_ratio: float | None
    or_ci_low: float | None
    or_ci_high: float | None
    p_value: float | None
    rd_pp: float
    rd_ci_low_pp: float
    rd_ci_high_pp: float
    share_of_raw_gap: float | None
    se_method: str


def _fit(X: pd.DataFrame, y: np.ndarray, clusters: np.ndarray | None):
    model = sm.GLM(y, X.to_numpy(), family=sm.families.Binomial())
    if clusters is not None:
        return model.fit(cov_type="cluster", cov_kwds={"groups": clusters})
    return model.fit(cov_type="HC1")


def _ame(res, X: pd.DataFrame) -> tuple[float, float]:
    """Average marginal effect of `black` on P(denied), with delta-method SE.

    g-computation: set black=1 for everyone, then black=0 for everyone, average
    the predicted-probability difference. This is the adjusted risk difference
    on the same scale as the raw percentage-point gap.
    """
    j = list(X.columns).index("black")
    A = X.to_numpy(dtype=float)
    X1 = A.copy()
    X1[:, j] = 1.0
    X0 = A.copy()
    X0[:, j] = 0.0
    b = res.params
    p1 = 1.0 / (1.0 + np.exp(-(X1 @ b)))
    p0 = 1.0 / (1.0 + np.exp(-(X0 @ b)))
    ame = float(np.mean(p1 - p0))
    grad = ((p1 * (1 - p1))[:, None] * X1 - (p0 * (1 - p0))[:, None] * X0).mean(axis=0)
    var = float(grad @ res.cov_params() @ grad)
    return ame, float(np.sqrt(max(var, 0.0)))


def raw_gap(f: pd.DataFrame) -> tuple[float, float, float]:
    b = f.loc[f["black"] == 1, "denied"]
    w = f.loc[f["black"] == 0, "denied"]
    pb, pw = float(b.mean()), float(w.mean())
    rd = pb - pw
    se = float(np.sqrt(pb * (1 - pb) / len(b) + pw * (1 - pw) / len(w)))
    return rd, se, rd / se


def run_spec(name: str, f: pd.DataFrame, cluster: bool) -> SpecResult:
    y = f["denied"].to_numpy(dtype=float)
    X = design(f, SPECS[name])
    clusters = f["lender"].to_numpy() if cluster else None
    se_method = "cluster-robust by lender (LEI)" if cluster else "HC1"

    # For the raw_marginal spec the design is just an intercept plus `black`,
    # so the AME below reproduces the two-proportion risk difference exactly.
    res = _fit(X, y, clusters)
    ame, ame_se = _ame(res, X)
    z = stats.norm.ppf(0.975)

    j = list(X.columns).index("black")
    log_or = float(res.params[j])
    log_or_se = float(res.bse[j])
    return SpecResult(
        spec=name,
        n=len(f),
        n_black=int(f["black"].sum()),
        n_white=int((1 - f["black"]).sum()),
        n_params=int(X.shape[1]),
        log_or=log_or,
        odds_ratio=float(np.exp(log_or)),
        or_ci_low=float(np.exp(log_or - z * log_or_se)),
        or_ci_high=float(np.exp(log_or + z * log_or_se)),
        p_value=float(2 * stats.norm.sf(abs(log_or / log_or_se))),
        rd_pp=100 * ame,
        rd_ci_low_pp=100 * (ame - z * ame_se),
        rd_ci_high_pp=100 * (ame + z * ame_se),
        share_of_raw_gap=None,
        se_method=se_method,
    )


def bootstrap_share(
    f: pd.DataFrame, spec: str, n_boot: int, seed: int
) -> dict[str, Any]:
    """Bootstrap the adjusted RD, the raw RD, and the ratio of the two.

    The ratio is the headline "how much of the raw gap survives adjustment", so
    it gets its own interval rather than being read off two separate ones.
    """
    rng = np.random.default_rng(seed)
    n = len(f)
    idx_all = np.arange(n)
    raw_s, adj_s, share_s = [], [], []
    for _ in range(n_boot):
        idx = rng.choice(idx_all, size=n, replace=True)
        fb = f.iloc[idx].reset_index(drop=True)
        if fb["black"].sum() < 30 or (1 - fb["black"]).sum() < 30:
            continue
        try:
            Xb = design(fb, SPECS[spec])
            if "black" not in Xb.columns:
                continue
            resb = sm.GLM(
                fb["denied"].to_numpy(dtype=float),
                Xb.to_numpy(),
                family=sm.families.Binomial(),
            ).fit()
            ame, _ = _ame(resb, Xb)
        except Exception:
            continue
        r, _, _ = raw_gap(fb)
        raw_s.append(r)
        adj_s.append(ame)
        if abs(r) > 1e-9:
            share_s.append(ame / r)
    q = lambda a, p: float(np.quantile(a, p))  # noqa: E731
    return {
        "n_boot_effective": len(adj_s),
        "raw_rd_pp": [100 * q(raw_s, 0.025), 100 * q(raw_s, 0.975)],
        "adjusted_rd_pp": [100 * q(adj_s, 0.025), 100 * q(adj_s, 0.975)],
        "share_of_raw_gap": [q(share_s, 0.025), q(share_s, 0.975)],
        "share_point_from_bootstrap_median": q(share_s, 0.5),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default="data/raw/hmda_2023_MA.csv")
    ap.add_argument("--year", type=int, default=DEFAULT_YEAR)
    ap.add_argument("--state", default=DEFAULT_STATE)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--n-boot", type=int, default=500)
    ap.add_argument("--primary", default="adjusted_financials")
    ap.add_argument("--out", default="data/processed/adjusted_model.json")
    ap.add_argument(
        "--no-cluster",
        action="store_true",
        help="use HC1 instead of cluster-robust-by-lender standard errors",
    )
    args = ap.parse_args(argv)

    np.random.seed(args.seed)
    csv_path = Path(args.csv)
    if not csv_path.exists():
        csv_path = download_csv(csv_path, args.year, args.state)

    curated = load_curated(csv_path)
    cohort = h1_cohort(curated)
    f = build_features(cohort)

    rd, se, _ = raw_gap(f)
    z = stats.norm.ppf(0.975)
    print(f"curated applications (all races): {len(curated):,}")
    print(f"H1 cohort (Black NH vs White NH): {len(f):,}")
    print(
        f"raw denial rates: Black {f.loc[f.black == 1, 'denied'].mean():.4f}  "
        f"White {f.loc[f.black == 0, 'denied'].mean():.4f}"
    )
    print(
        f"raw risk difference: {100 * rd:.2f} pp "
        f"(95% CI {100 * (rd - z * se):.2f} to {100 * (rd + z * se):.2f})\n"
    )

    cluster = not args.no_cluster
    results: list[SpecResult] = []
    for name in SPECS:
        r = run_spec(name, f, cluster)
        r.share_of_raw_gap = r.rd_pp / (100 * rd) if abs(rd) > 1e-9 else None
        results.append(r)
        print(
            f"{name:<26} k={r.n_params:<4} "
            f"OR={r.odds_ratio:.3f} [{r.or_ci_low:.3f}, {r.or_ci_high:.3f}]  "
            f"RD={r.rd_pp:+.2f} pp [{r.rd_ci_low_pp:+.2f}, {r.rd_ci_high_pp:+.2f}]  "
            f"share_of_raw={r.share_of_raw_gap:.3f}  p={r.p_value:.3g}"
        )

    print(f"\nbootstrapping share of raw gap, spec={args.primary}, B={args.n_boot} ...")
    boot = bootstrap_share(f, args.primary, args.n_boot, args.seed)
    print(json.dumps(boot, indent=2))

    payload = {
        "seed": args.seed,
        "source_csv": str(csv_path),
        "year": args.year,
        "state": args.state,
        "n_curated": len(curated),
        "cohort": {
            "n": len(f),
            "n_black": int(f["black"].sum()),
            "n_white": int((1 - f["black"]).sum()),
            "denial_rate_black": float(f.loc[f.black == 1, "denied"].mean()),
            "denial_rate_white": float(f.loc[f.black == 0, "denied"].mean()),
        },
        "raw_rd_pp": 100 * rd,
        "raw_rd_ci_pp": [100 * (rd - z * se), 100 * (rd + z * se)],
        "primary_spec": args.primary,
        "specs": [asdict(r) for r in results],
        "bootstrap": boot,
        "caveat": (
            "Adjusted estimates are not causal. HMDA has no credit score, no "
            "reserves, no appraisal detail. Controls such as AUS, loan amount "
            "and CLTV are partly downstream of lender behaviour, so "
            "conditioning on them can induce collider or mediator bias. "
            "Denial reason is never a control because it is defined by the "
            "outcome."
        ),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
