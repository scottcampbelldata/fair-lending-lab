"""CLI for ingest, build, analyze, export."""
from __future__ import annotations

import json
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Fair Lending Lab CLI", no_args_is_help=True)
ingest = typer.Typer(help="HMDA ingestion")
analyze = typer.Typer(help="Run hypothesis tests")
db = typer.Typer(help="Database utilities")
app.add_typer(ingest, name="ingest")
app.add_typer(analyze, name="analyze")
app.add_typer(db, name="db")
console = Console()


@db.command("init")
def db_init() -> None:
    from pathlib import Path

    from flab.db import get_conn

    sql = (Path(__file__).resolve().parent / "db" / "schema.sql").read_text(encoding="utf-8")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    console.print("[green]schema applied[/green]")


@db.command("stats")
def db_stats() -> None:
    from flab.db import fetch_df

    df = fetch_df(
        "SELECT 'loans' AS table, COUNT(*)::BIGINT AS rows FROM flab.loans "
        "UNION ALL SELECT 'hmda_raw', COUNT(*) FROM flab.hmda_raw "
        "UNION ALL SELECT 'analysis_runs', COUNT(*) FROM flab.analysis_runs "
        "UNION ALL SELECT 'results_cache', COUNT(*) FROM flab.results_cache"
    )
    console.print(df.to_string(index=False))


@ingest.command("hmda")
def ingest_hmda(
    year: int = typer.Option(None, "--year"),
    state: str = typer.Option(None, "--state"),
) -> None:
    from flab.ingest import load_hmda_csv
    from flab.ingest.hmda import default_year_state

    y, s = default_year_state()
    if year is not None:
        y = year
    if state is not None:
        s = state
    n = load_hmda_csv(y, s)
    console.print(f"[green]hmda_raw loaded for {y}-{s}:[/green] {n}")


@ingest.command("build-curated")
def ingest_build_curated() -> None:
    from flab.ingest import build_curated

    n = build_curated()
    console.print(f"[green]loans curated:[/green] {n}")


@analyze.command("run-all")
def analyze_run_all() -> None:
    from flab.hypotheses import REGISTRY, run_and_cache

    summary = []
    for key in REGISTRY:
        payload = run_and_cache(key)
        primary = payload.get("primary") or {}
        summary.append({
            "key": key,
            "method": primary.get("method", ""),
            "p_value": primary.get("p_value"),
            "effect_label": primary.get("effect_label"),
            "effect_size": primary.get("effect_size") or primary.get("eta_squared"),
        })
    tbl = Table(title="Hypothesis results")
    for c in ("key", "method", "p_value", "effect_label", "effect_size"):
        tbl.add_column(c)
    for row in summary:
        tbl.add_row(
            row["key"],
            str(row["method"]),
            f"{row['p_value']:.3g}" if row["p_value"] is not None else "-",
            str(row["effect_label"]),
            f"{row['effect_size']:.3f}" if row["effect_size"] is not None else "-",
        )
    console.print(tbl)


@app.command("export-results")
def export_results(out: str = "data/processed/results.json") -> None:
    from pathlib import Path

    from flab.db import fetch_df
    from flab.hypotheses.registry import family_wise_correction

    df = fetch_df("SELECT hypothesis_key, payload, refreshed_at FROM flab.results_cache")
    payloads = {
        row["hypothesis_key"]: {**row["payload"], "_refreshed_at": str(row["refreshed_at"])}
        for _, row in df.iterrows()
    }
    counts = fetch_df(
        "SELECT 'loans' AS k, COUNT(*)::BIGINT AS v FROM flab.loans "
        "UNION ALL SELECT 'hmda_raw', COUNT(*) FROM flab.hmda_raw"
    )
    out_payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "row_counts": {row["k"]: int(row["v"]) for _, row in counts.iterrows()},
        "results": payloads,
        "family_correction": family_wise_correction(),
    }
    p = Path(out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out_payload, indent=2, default=str), encoding="utf-8")
    console.print(f"[green]wrote[/green] {p} ({len(payloads)} hypotheses)")


if __name__ == "__main__":
    app()
