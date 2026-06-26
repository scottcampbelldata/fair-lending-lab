-- flab schema: HMDA raw load + curated loan application facts + analysis run log.
-- Idempotent: re-run safely.

CREATE SCHEMA IF NOT EXISTS flab;

-- Raw monthly load: one row per HMDA LAR record, ingest_year + state_code keyed.
CREATE TABLE IF NOT EXISTS flab.hmda_raw (
    ingest_year                      INTEGER NOT NULL,
    state_code                       TEXT    NOT NULL,
    activity_year                    INTEGER,
    lei                              TEXT,
    derived_msa_md                   TEXT,
    county_code                      TEXT,
    census_tract                     TEXT,
    derived_loan_product_type        TEXT,
    derived_dwelling_category        TEXT,
    derived_ethnicity                TEXT,
    derived_race                     TEXT,
    derived_sex                      TEXT,
    action_taken                     SMALLINT,
    preapproval                      SMALLINT,
    loan_type                        SMALLINT,
    loan_purpose                     SMALLINT,
    lien_status                      SMALLINT,
    open_end_line_of_credit          SMALLINT,
    business_or_commercial_purpose   SMALLINT,
    loan_amount                      DOUBLE PRECISION,
    loan_to_value_ratio              DOUBLE PRECISION,
    interest_rate                    DOUBLE PRECISION,
    rate_spread                      DOUBLE PRECISION,
    hoepa_status                     SMALLINT,
    property_value                   DOUBLE PRECISION,
    occupancy_type                   SMALLINT,
    income                           DOUBLE PRECISION,
    debt_to_income_ratio             TEXT,
    applicant_age                    TEXT,
    co_applicant_age                 TEXT,
    denial_reason_1                  TEXT,
    tract_population                 DOUBLE PRECISION,
    tract_minority_population_percent DOUBLE PRECISION,
    ffiec_msa_md_median_family_income DOUBLE PRECISION,
    tract_to_msa_income_percentage   DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS hmda_raw_action_idx  ON flab.hmda_raw (action_taken);
CREATE INDEX IF NOT EXISTS hmda_raw_race_idx    ON flab.hmda_raw (derived_race);
CREATE INDEX IF NOT EXISTS hmda_raw_lei_idx     ON flab.hmda_raw (lei);
CREATE INDEX IF NOT EXISTS hmda_raw_msa_idx     ON flab.hmda_raw (derived_msa_md);
CREATE INDEX IF NOT EXISTS hmda_raw_state_idx   ON flab.hmda_raw (state_code);

-- Curated loan application facts: filtered to comparable home purchase, conventional,
-- first-lien, 1-4 family, owner-occupied, originated or denied applications.
CREATE TABLE IF NOT EXISTS flab.loans (
    loan_uid                    BIGSERIAL PRIMARY KEY,
    activity_year               INTEGER NOT NULL,
    state_code                  TEXT    NOT NULL,
    msa_md                      TEXT,
    lei                         TEXT,
    action_taken                SMALLINT NOT NULL,
    denied                      BOOLEAN  NOT NULL,
    originated                  BOOLEAN  NOT NULL,
    race_group                  TEXT    NOT NULL,   -- White, Black, Asian, Native, Pacific, Hispanic, Joint, Race Not Available
    ethnicity_group             TEXT    NOT NULL,   -- Hispanic, Non-Hispanic, Not Available, Joint
    sex_group                   TEXT    NOT NULL,
    age_group                   TEXT    NOT NULL,
    loan_amount                 DOUBLE PRECISION NOT NULL,
    loan_to_value               DOUBLE PRECISION,
    rate_spread                 DOUBLE PRECISION,
    interest_rate               DOUBLE PRECISION,
    debt_to_income              TEXT,
    debt_to_income_band         TEXT,
    income_thousands            DOUBLE PRECISION,
    income_band                 TEXT,
    loan_amount_band            TEXT,
    property_value              DOUBLE PRECISION,
    tract_minority_share        DOUBLE PRECISION,
    tract_to_msa_income_pct     DOUBLE PRECISION,
    is_priced_loan              BOOLEAN  NOT NULL,
    denial_reason_1             TEXT
);
CREATE INDEX IF NOT EXISTS loans_action_idx ON flab.loans (action_taken);
CREATE INDEX IF NOT EXISTS loans_race_idx   ON flab.loans (race_group);
CREATE INDEX IF NOT EXISTS loans_eth_idx    ON flab.loans (ethnicity_group);
CREATE INDEX IF NOT EXISTS loans_msa_idx    ON flab.loans (msa_md);
CREATE INDEX IF NOT EXISTS loans_lei_idx    ON flab.loans (lei);
CREATE INDEX IF NOT EXISTS loans_priced_idx ON flab.loans (is_priced_loan);

-- Analysis run log: each hypothesis test execution.
CREATE TABLE IF NOT EXISTS flab.analysis_runs (
    run_id         BIGSERIAL PRIMARY KEY,
    run_at         TIMESTAMP NOT NULL DEFAULT now(),
    hypothesis_key TEXT      NOT NULL,
    method         TEXT      NOT NULL,
    n_group_a      INTEGER,
    n_group_b      INTEGER,
    statistic      DOUBLE PRECISION,
    p_value        DOUBLE PRECISION,
    effect_size    DOUBLE PRECISION,
    effect_label   TEXT,
    ci_low         DOUBLE PRECISION,
    ci_high        DOUBLE PRECISION,
    detail         JSONB
);
CREATE INDEX IF NOT EXISTS runs_hyp_idx ON flab.analysis_runs (hypothesis_key, run_at DESC);

CREATE TABLE IF NOT EXISTS flab.results_cache (
    hypothesis_key TEXT PRIMARY KEY,
    payload        JSONB NOT NULL,
    refreshed_at   TIMESTAMP NOT NULL DEFAULT now()
);
