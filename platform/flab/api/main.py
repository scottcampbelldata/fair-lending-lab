"""FastAPI: read-only JSON for the Next.js frontend."""
from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from flab import __version__
from flab.config import get_data_dir, get_settings
from flab.db import fetch_df
from flab.hypotheses import REGISTRY
from flab.hypotheses.registry import family_wise_correction

app = FastAPI(
    title="Fair Lending Lab API",
    version=__version__,
    description=(
        "Read-only JSON for the Fair Lending Lab dashboard: HMDA hypothesis "
        "registry, cached test results, family-wise corrections, and "
        "aggregated summary slices for chart-building."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, Any]:
    s = get_settings()
    return {
        "ok": True,
        "version": __version__,
        "database": s.pgdatabase,
        "hypotheses": len(REGISTRY),
        "hmda_year": s.hmda_year,
        "hmda_state": s.hmda_state,
    }


@app.get("/api/overview")
def overview() -> dict[str, Any]:
    counts = fetch_df(
        "SELECT 'loans' AS k, COUNT(*)::BIGINT AS v FROM flab.loans "
        "UNION ALL SELECT 'hmda_raw', COUNT(*) FROM flab.hmda_raw "
        "UNION ALL SELECT 'analysis_runs', COUNT(*) FROM flab.analysis_runs "
        "UNION ALL SELECT 'results_cache', COUNT(*) FROM flab.results_cache"
    )
    by_action = fetch_df(
        "SELECT action_taken, COUNT(*)::BIGINT AS n FROM flab.loans GROUP BY action_taken ORDER BY action_taken"
    )
    by_race = fetch_df(
        "SELECT race_group, COUNT(*)::BIGINT AS n, "
        "  SUM(denied::int)::BIGINT AS n_denied "
        "FROM flab.loans GROUP BY race_group ORDER BY n DESC"
    )
    by_eth = fetch_df(
        "SELECT ethnicity_group, COUNT(*)::BIGINT AS n, "
        "  SUM(denied::int)::BIGINT AS n_denied "
        "FROM flab.loans GROUP BY ethnicity_group ORDER BY n DESC"
    )
    by_msa = fetch_df(
        "SELECT msa_md, COUNT(*)::BIGINT AS n, "
        "  SUM(denied::int)::BIGINT AS n_denied "
        "FROM flab.loans WHERE msa_md IS NOT NULL "
        "GROUP BY msa_md ORDER BY n DESC LIMIT 8"
    )
    return {
        "counts": {row["k"]: int(row["v"]) for _, row in counts.iterrows()},
        "by_action": [{"action_taken": int(r["action_taken"]), "n": int(r["n"])} for _, r in by_action.iterrows()],
        "by_race": [
            {"race_group": r["race_group"], "n": int(r["n"]),
             "n_denied": int(r["n_denied"]), "denial_rate": float(r["n_denied"]) / max(int(r["n"]), 1)}
            for _, r in by_race.iterrows()
        ],
        "by_ethnicity": [
            {"ethnicity_group": r["ethnicity_group"], "n": int(r["n"]),
             "n_denied": int(r["n_denied"]), "denial_rate": float(r["n_denied"]) / max(int(r["n"]), 1)}
            for _, r in by_eth.iterrows()
        ],
        "by_msa": [
            {"msa_md": r["msa_md"], "n": int(r["n"]),
             "n_denied": int(r["n_denied"]), "denial_rate": float(r["n_denied"]) / max(int(r["n"]), 1)}
            for _, r in by_msa.iterrows()
        ],
    }


@app.get("/api/hypotheses")
def list_hypotheses() -> list[dict[str, Any]]:
    cache = fetch_df(
        "SELECT hypothesis_key, payload, refreshed_at FROM flab.results_cache"
    )
    cached = {
        row["hypothesis_key"]: (row["payload"], row["refreshed_at"])
        for _, row in cache.iterrows()
    }
    out = []
    for key, h in REGISTRY.items():
        payload, refreshed = cached.get(key, (None, None))
        primary = (payload or {}).get("primary", {}) if payload else {}
        out.append({
            "key": key,
            "title": h.title,
            "h0": h.h0,
            "h1": h.h1,
            "direction": h.direction,
            "effect_of_interest": h.effect_of_interest,
            "domain_question": h.domain_question,
            "causal_caveat": h.causal_caveat,
            "primary_method": primary.get("method"),
            "p_value": primary.get("p_value"),
            "effect_size": primary.get("effect_size") or primary.get("eta_squared"),
            "effect_label": primary.get("effect_label"),
            "n_a": primary.get("n_a"),
            "n_b": primary.get("n_b"),
            "ci_low": primary.get("ci_low"),
            "ci_high": primary.get("ci_high"),
            "refreshed_at": str(refreshed) if refreshed else None,
        })
    return out


@app.get("/api/hypothesis/{key}")
def get_hypothesis(key: str) -> dict[str, Any]:
    if key not in REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown hypothesis: {key}")
    df = fetch_df(
        "SELECT payload, refreshed_at FROM flab.results_cache WHERE hypothesis_key = %(k)s",
        {"k": key},
    )
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No cached result for {key}. Run `flab analyze run-all`.",
        )
    payload = df.iloc[0]["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    payload["_refreshed_at"] = str(df.iloc[0]["refreshed_at"])
    return payload


@app.get("/api/family_correction")
def family_correction() -> dict[str, Any]:
    return family_wise_correction()


@app.get("/api/results.json")
def results_json() -> FileResponse:
    """Full exported results with exact (unrounded) p-values and effect sizes.

    The dashboard collapses tiny p-values to "< 0.001" for readability; this is
    the downloadable artifact for anyone who wants the exact figures. Produced by
    `flab export-results`.
    """
    path = get_data_dir() / "processed" / "results.json"
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="results.json not generated yet. Run `flab export-results`.",
        )
    return FileResponse(
        path,
        media_type="application/json",
        filename="fair-lending-results.json",
    )


@app.get("/api/denial_rates_by_race")
def denial_rates_by_race() -> list[dict[str, Any]]:
    df = fetch_df(
        """
        SELECT race_group, ethnicity_group,
               COUNT(*) AS n,
               SUM(denied::int) AS n_denied,
               AVG(denied::int)::FLOAT AS denial_rate
        FROM flab.loans
        GROUP BY race_group, ethnicity_group
        ORDER BY n DESC
        """
    )
    return [
        {
            "race_group": r["race_group"],
            "ethnicity_group": r["ethnicity_group"],
            "n": int(r["n"]),
            "n_denied": int(r["n_denied"]),
            "denial_rate": float(r["denial_rate"]),
        }
        for _, r in df.iterrows()
    ]


@app.get("/api/denial_by_income_band")
def denial_by_income_band() -> list[dict[str, Any]]:
    df = fetch_df(
        """
        SELECT income_band, race_group,
               COUNT(*) AS n,
               SUM(denied::int) AS n_denied,
               AVG(denied::int)::FLOAT AS denial_rate
        FROM flab.loans
        WHERE race_group IN ('White','Black','Asian','Hispanic','Joint')
          AND ethnicity_group <> 'Joint'
        GROUP BY income_band, race_group
        ORDER BY income_band, race_group
        """
    )
    return [
        {
            "income_band": r["income_band"],
            "race_group": r["race_group"],
            "n": int(r["n"]),
            "n_denied": int(r["n_denied"]),
            "denial_rate": float(r["denial_rate"]),
        }
        for _, r in df.iterrows()
    ]
