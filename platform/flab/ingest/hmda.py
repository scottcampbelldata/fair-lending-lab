"""HMDA ingestion: pull CFPB LAR CSV per state and year, load to Postgres, curate facts.

Source: CFPB FFIEC Data Browser API. Public data, no key. One CSV per state per year.
"""
from __future__ import annotations

import io
from pathlib import Path

import httpx
import pandas as pd
from loguru import logger

from flab.config import get_data_dir, get_settings
from flab.db import get_conn

HMDA_CSV_URL = "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv"

# Columns we keep from the LAR. The wider HMDA dictionary has many more
# applicant_race_2..5 etc. that we collapse to the CFPB derived_race rollup.
RAW_COLS = [
    "activity_year",
    "lei",
    "derived_msa-md",
    "state_code",
    "county_code",
    "census_tract",
    "derived_loan_product_type",
    "derived_dwelling_category",
    "derived_ethnicity",
    "derived_race",
    "derived_sex",
    "action_taken",
    "preapproval",
    "loan_type",
    "loan_purpose",
    "lien_status",
    "open-end_line_of_credit",
    "business_or_commercial_purpose",
    "loan_amount",
    "loan_to_value_ratio",
    "interest_rate",
    "rate_spread",
    "hoepa_status",
    "property_value",
    "occupancy_type",
    "income",
    "debt_to_income_ratio",
    "applicant_age",
    "co-applicant_age",
    "denial_reason-1",
    "tract_population",
    "tract_minority_population_percent",
    "ffiec_msa_md_median_family_income",
    "tract_to_msa_income_percentage",
]

# Map LAR column names to schema column names.
RENAME = {
    "derived_msa-md": "derived_msa_md",
    "open-end_line_of_credit": "open_end_line_of_credit",
    "co-applicant_age": "co_applicant_age",
    "denial_reason-1": "denial_reason_1",
}

INT_COLS = [
    "activity_year",
    "action_taken",
    "preapproval",
    "loan_type",
    "loan_purpose",
    "lien_status",
    "open_end_line_of_credit",
    "business_or_commercial_purpose",
    "hoepa_status",
    "occupancy_type",
]
FLOAT_COLS = [
    "loan_amount",
    "loan_to_value_ratio",
    "interest_rate",
    "rate_spread",
    "property_value",
    "income",
    "tract_population",
    "tract_minority_population_percent",
    "ffiec_msa_md_median_family_income",
    "tract_to_msa_income_percentage",
]


def download_hmda_state(year: int, state: str) -> Path:
    """Pull the LAR CSV for one state and year from the CFPB Data Browser API."""
    state = state.upper()
    out = get_data_dir() / "raw" / f"hmda_{year}_{state}.csv"
    if out.exists() and out.stat().st_size > 1_000_000:
        logger.info("hmda csv already present", path=str(out))
        return out
    params = {"years": str(year), "states": state}
    logger.info("downloading HMDA LAR CSV", state=state, year=year)
    with httpx.stream(
        "GET", HMDA_CSV_URL, params=params, timeout=300.0, follow_redirects=True
    ) as r:
        r.raise_for_status()
        with out.open("wb") as f:
            for chunk in r.iter_bytes(chunk_size=1024 * 1024):
                f.write(chunk)
    logger.info("hmda downloaded", bytes=out.stat().st_size)
    return out


def load_hmda_csv(year: int, state: str) -> int:
    """Read the LAR CSV, project to RAW_COLS, COPY into flab.hmda_raw."""
    state = state.upper()
    path = download_hmda_state(year, state)
    logger.info("reading HMDA csv", path=str(path))

    # Read in chunks: HMDA columns are heavy (99 fields); we only keep the
    # 34 we care about. Header indices vary by year, so use names.
    df = pd.read_csv(
        path,
        usecols=lambda c: c in RAW_COLS,
        dtype=str,
        low_memory=False,
    )
    logger.info("rows read", n=len(df))

    df = df.rename(columns=RENAME)
    for c in INT_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    for c in FLOAT_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["ingest_year"] = year
    df["state_code"] = state

    schema_cols = [
        "ingest_year",
        "state_code",
        "activity_year",
        "lei",
        "derived_msa_md",
        "county_code",
        "census_tract",
        "derived_loan_product_type",
        "derived_dwelling_category",
        "derived_ethnicity",
        "derived_race",
        "derived_sex",
        "action_taken",
        "preapproval",
        "loan_type",
        "loan_purpose",
        "lien_status",
        "open_end_line_of_credit",
        "business_or_commercial_purpose",
        "loan_amount",
        "loan_to_value_ratio",
        "interest_rate",
        "rate_spread",
        "hoepa_status",
        "property_value",
        "occupancy_type",
        "income",
        "debt_to_income_ratio",
        "applicant_age",
        "co_applicant_age",
        "denial_reason_1",
        "tract_population",
        "tract_minority_population_percent",
        "ffiec_msa_md_median_family_income",
        "tract_to_msa_income_percentage",
    ]
    for c in schema_cols:
        if c not in df.columns:
            df[c] = None
    df = df[schema_cols]

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM flab.hmda_raw WHERE ingest_year=%s AND state_code=%s",
                (year, state),
            )
            buf = io.StringIO()
            df.to_csv(buf, index=False, header=False, na_rep="\\N")
            buf.seek(0)
            cols_sql = ", ".join(schema_cols)
            with cur.copy(
                f"COPY flab.hmda_raw ({cols_sql}) FROM STDIN "
                "WITH (FORMAT CSV, NULL '\\N')"
            ) as copy:
                copy.write(buf.read())
        conn.commit()
    logger.info("hmda_raw loaded", n=len(df))
    return len(df)


# Action codes (CFPB):
#  1 originated, 2 approved-not-accepted, 3 denied, 4 withdrawn,
#  5 file closed for incompleteness, 6 purchased loan, 7 preapproval denied,
#  8 preapproval approved-not-accepted
ACTION_DENIED = 3
ACTION_ORIGINATED = 1


CURATED_SQL = """
TRUNCATE TABLE flab.loans RESTART IDENTITY;

INSERT INTO flab.loans (
    activity_year, state_code, msa_md, lei,
    action_taken, denied, originated,
    race_group, ethnicity_group, sex_group, age_group,
    loan_amount, loan_to_value, rate_spread, interest_rate,
    debt_to_income, debt_to_income_band,
    income_thousands, income_band, loan_amount_band,
    property_value, tract_minority_share, tract_to_msa_income_pct,
    is_priced_loan, denial_reason_1
)
SELECT
    activity_year,
    state_code,
    derived_msa_md AS msa_md,
    lei,
    action_taken,
    (action_taken = 3)              AS denied,
    (action_taken = 1)              AS originated,
    CASE derived_race
        WHEN 'White'                                                              THEN 'White'
        WHEN 'Black or African American'                                          THEN 'Black'
        WHEN 'Asian'                                                              THEN 'Asian'
        WHEN 'American Indian or Alaska Native'                                   THEN 'Native'
        WHEN 'Native Hawaiian or Other Pacific Islander'                          THEN 'Pacific'
        WHEN 'Joint'                                                              THEN 'Joint'
        WHEN '2 or more minority races'                                           THEN 'Multi'
        WHEN 'Race Not Available'                                                 THEN 'Not Available'
        WHEN 'Free Form Text Only'                                                THEN 'Not Available'
        ELSE COALESCE(derived_race, 'Not Available')
    END AS race_group,
    CASE derived_ethnicity
        WHEN 'Hispanic or Latino'                  THEN 'Hispanic'
        WHEN 'Not Hispanic or Latino'              THEN 'Non-Hispanic'
        WHEN 'Joint'                               THEN 'Joint'
        WHEN 'Ethnicity Not Available'             THEN 'Not Available'
        WHEN 'Free Form Text Only'                 THEN 'Not Available'
        ELSE COALESCE(derived_ethnicity, 'Not Available')
    END AS ethnicity_group,
    CASE derived_sex
        WHEN 'Male'                          THEN 'Male'
        WHEN 'Female'                        THEN 'Female'
        WHEN 'Joint'                         THEN 'Joint'
        ELSE 'Not Available'
    END AS sex_group,
    COALESCE(applicant_age, 'Not Available') AS age_group,
    loan_amount,
    loan_to_value_ratio,
    rate_spread,
    interest_rate,
    debt_to_income_ratio,
    CASE
        WHEN debt_to_income_ratio IN ('<20%','20%-<30%')                THEN 'under_30'
        WHEN debt_to_income_ratio IN ('30%-<36%','36','37','38','39')   THEN '30_to_39'
        WHEN debt_to_income_ratio IN ('40','41','42','43','44','45','46','47','48','49') THEN '40_to_49'
        WHEN debt_to_income_ratio = '50%-60%'                          THEN '50_to_60'
        WHEN debt_to_income_ratio = '>60%'                              THEN 'over_60'
        ELSE 'unknown'
    END                                              AS debt_to_income_band,
    income                                           AS income_thousands,
    CASE
        WHEN income IS NULL                                              THEN 'unknown'
        WHEN income < 50                                                 THEN 'under_50k'
        WHEN income < 100                                                THEN '50k_to_100k'
        WHEN income < 150                                                THEN '100k_to_150k'
        WHEN income < 250                                                THEN '150k_to_250k'
        ELSE 'over_250k'
    END                                              AS income_band,
    CASE
        WHEN loan_amount < 125000                                        THEN 'under_125k'
        WHEN loan_amount < 250000                                        THEN '125k_to_250k'
        WHEN loan_amount < 500000                                        THEN '250k_to_500k'
        WHEN loan_amount < 750000                                        THEN '500k_to_750k'
        ELSE 'over_750k'
    END                                              AS loan_amount_band,
    property_value,
    tract_minority_population_percent                AS tract_minority_share,
    tract_to_msa_income_percentage                   AS tract_to_msa_income_pct,
    (rate_spread IS NOT NULL AND rate_spread > 0)    AS is_priced_loan,
    denial_reason_1
FROM flab.hmda_raw
WHERE action_taken IN (1, 3)
  AND loan_purpose = 1              -- home purchase
  AND loan_type    = 1              -- conventional
  AND lien_status  = 1              -- first lien
  AND occupancy_type = 1            -- principal residence
  AND business_or_commercial_purpose = 2     -- non-business
  AND loan_amount IS NOT NULL
  AND loan_amount BETWEEN 50000 AND 2000000;
"""


def build_curated() -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(CURATED_SQL)
            cur.execute("SELECT COUNT(*) FROM flab.loans")
            n = cur.fetchone()[0]
        conn.commit()
    logger.info("loans curated", n=n)
    return n


def default_year_state() -> tuple[int, str]:
    s = get_settings()
    return s.hmda_year, s.hmda_state
