# platform, Fair Lending Lab backend

FastAPI service plus ingestion, statistical inference library, hypothesis registry, and CLI. Deployed to a Linux VPS behind nginx via the unit file in `deploy/`.

See the repository root `README.md` for the project narrative, and `deploy/README.md` for VPS install steps.

## Quick reference

```bash
flab db init                                  # apply schema
flab ingest hmda --year 2023 --state MA       # pull and load LAR
flab ingest build-curated                     # curate facts
flab analyze run-all                          # run hypotheses, cache
flab export-results                           # emit data/processed/results.json
uvicorn flab.api.main:app --port 8702         # serve the API
pytest                                        # run the test suite
```

## Module map

| Path | Purpose |
|---|---|
| `flab/config.py` | env-driven config, settings cache, seed helper |
| `flab/db/engine.py` | SQLAlchemy engine and psycopg3 raw connection |
| `flab/db/schema.sql` | idempotent `flab` schema, indices, results cache |
| `flab/ingest/hmda.py` | CFPB Data Browser CSV download, raw COPY, curated SQL |
| `flab/stats/effects.py` | Hedges g, rank-biserial, odds ratio CI, risk-difference CI |
| `flab/stats/multiple.py` | Bonferroni, Benjamini-Hochberg FDR |
| `flab/stats/power.py` | sample-size and MDE for means and proportions |
| `flab/stats/resampling.py` | percentile bootstrap CI, permutation mean-diff test |
| `flab/stats/tests.py` | Welch t, Mann-Whitney, two-proportion z, ANOVA, Kruskal-Wallis, Bayesian sensitivity |
| `flab/hypotheses/registry.py` | preregistered H0/H1 catalog, per-hypothesis runners |
| `flab/api/main.py` | read-only FastAPI service for the dashboard |
| `flab/cli.py` | `flab` Typer CLI |
