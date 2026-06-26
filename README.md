# Fair Lending Lab

Hypothesis testing and statistical inference on CFPB HMDA mortgage application records. Multiple-method validation (parametric, non-parametric, permutation, bootstrap, Bayesian sensitivity), family-wise correction across the test family, effect sizes with confidence intervals, and explicit causal-framing caveats.

**Headline finding (Massachusetts 2023 LAR):** Black non-Hispanic applicants face a +10.7 percentage point (95% CI 8.9 to 12.4) higher denial rate than White non-Hispanic applicants for first-lien conventional owner-occupied home-purchase loans. The disparity persists inside the lowest income band (+18.5 pp). All five preregistered hypotheses reject the null at BH-FDR q = 0.05 and Bonferroni. **Screening signal, not a causal claim.** HMDA omits credit score and full underwriting.

## Live

- Frontend (Cloudflare Pages): https://fair-lending.scottcampbell.io
- API (VPS, FastAPI behind nginx): https://fair-lending-api.scottcampbell.io

## Repo layout

```
fair-lending-lab/
├── frontend/             # Next.js 14 + TypeScript + Tailwind + Recharts (Cloudflare Pages)
│   └── src/{app,components,lib}/
├── platform/             # Python backend (VPS via systemd + nginx)
│   ├── flab/
│   │   ├── api/          # FastAPI service (read-only JSON)
│   │   ├── db/           # SQLAlchemy engine + schema.sql
│   │   ├── ingest/       # CFPB HMDA download + curated build
│   │   ├── stats/        # tests, effects, power, resampling, multiple
│   │   ├── hypotheses/   # preregistered registry + per-hypothesis runners
│   │   └── cli.py        # `flab ...` entrypoint
│   ├── deploy/           # systemd unit, nginx config, deploy/README.md, bootstrap SQL
│   ├── notebooks/        # executed reproducible notebook
│   ├── tests/            # pytest + Hypothesis property tests
│   ├── data/             # raw + processed (gitignored)
│   └── pyproject.toml
├── docs/images/          # desktop and mobile dashboard screenshots
├── .github/workflows/    # CI: ruff, dash scan, pytest, frontend build
├── .gitignore
└── README.md
```

## Senior BI skills cross-reference

| Skill | Where it lives |
|---|---|
| Pre-registration of H0, H1, direction, effect of interest | `platform/flab/hypotheses/registry.py` REGISTRY entries |
| Power analysis (sample size, MDE) | `platform/flab/stats/power.py`, used in each runner |
| Parametric tests (Welch t, ANOVA with eta squared, omega squared) | `platform/flab/stats/tests.py` |
| Non-parametric tests (Mann-Whitney, Kruskal-Wallis) | `platform/flab/stats/tests.py` |
| Permutation tests (distribution-free) | `platform/flab/stats/resampling.py::permutation_test_means` |
| Bootstrap CIs for the difference | `platform/flab/stats/resampling.py::bootstrap_ci` |
| Bayesian sensitivity (conjugate posterior, BIC Bayes factor) | `platform/flab/stats/tests.py::bayesian_diff_in_means` |
| Effect sizes with CIs (Hedges g, OR, risk diff, rank-biserial) | `platform/flab/stats/effects.py` |
| Multiple comparison correction (BH-FDR, Bonferroni) | `platform/flab/stats/multiple.py`, applied in registry |
| Causal disclaimers (per-hypothesis, dashboard, README) | `platform/flab/hypotheses/registry.py::causal_caveat` |
| Stratified sensitivity (denial by income band, BH-FDR adjusted) | `_runner_h1` in `registry.py` |
| Reproducibility (fixed seed, deterministic notebook) | `platform/flab/config.py::get_random_seed` |
| Property-based testing (Hypothesis) | `platform/tests/test_stats.py` |
| CI (lint, pytest, dash scan, frontend build) | `.github/workflows/ci.yml` |
| Production deployment (systemd, nginx, certbot) | `platform/deploy/` |
| Visual design bar (Inter + IBM Plex Mono, near-black canvas) | `frontend/src/app/{layout,globals.css}` |

## Local development

### Backend

```bash
cd platform
python3.12 -m venv ../.venv
../.venv/bin/pip install -e .[dev]
cp .env.example .env  # fill in your local Postgres credentials
psql "$PG_URL" -f flab/db/schema.sql
../.venv/bin/python -m flab.cli ingest hmda --year 2023 --state MA
../.venv/bin/python -m flab.cli ingest build-curated
../.venv/bin/python -m flab.cli analyze run-all
../.venv/bin/python -m flab.cli export-results
../.venv/bin/python -m uvicorn flab.api.main:app --host 127.0.0.1 --port 8702
```

### Frontend

```bash
cd frontend
npm ci
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8702 npm run dev
# open http://127.0.0.1:3001
```

### Tests

```bash
cd platform
../.venv/bin/pytest -ra
```

### Re-screenshot

```bash
../.venv/bin/python platform/scripts/screenshot.py
# writes desktop and mobile PNGs to docs/images/
```

## Data

- Source: CFPB FFIEC HMDA Data Browser. Public, no API key needed.
- Pull: https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?years=2023&states=MA
- Year, state, and filter set are configurable via env vars (`FLAB_HMDA_YEAR`, `FLAB_HMDA_STATE`).
- 210,643 raw rows, curated to 41,287 first-lien conventional owner-occupied home-purchase applications. Filter set is documented in `flab/ingest/hmda.py::CURATED_SQL`.

## Caveats and limitations

- HMDA omits credit score, debt-to-income detail beyond a coarse band, full underwriting, property appraisal, and post-application history. The disparities reported here are statistical associations conditional on the observed covariates.
- Massachusetts 2023 only. The same pipeline can be re-run for any state and year by changing the env vars and re-running ingest.
- This project is BI methodology demonstration. Real fair-lending review uses supervisory HMDA data with matched credit-bureau records, plus loan-file audit pairs.

## License

MIT
