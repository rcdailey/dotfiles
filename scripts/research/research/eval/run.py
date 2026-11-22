"""Replay the sampled queries against each provider."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import click

from research.eval import cli
from research.eval._data import QUERIES, RESULTS_DIR, append_jsonl, read_jsonl
from research.eval._providers import PROVIDERS, Query

# Seconds between calls for providers whose plan allows one request per second (Brave's).
_SERIAL = {"brave": 1.1}


def _replay(name: str, record: dict) -> dict:
    time.sleep(_SERIAL.get(name, 0))
    query = Query(
        query=record["query"],
        domains=record["domains"],
        exclude_domains=record["exclude_domains"],
        time_range=record["time_range"],
    )
    start = time.perf_counter()
    try:
        results = PROVIDERS[name](query)
        error = None
    except Exception as e:  # noqa: BLE001 - every failure is recorded, not fatal
        results, error = [], f"{type(e).__name__}: {e}"
    return {
        "id": record["id"],
        "latency_ms": round((time.perf_counter() - start) * 1000),
        "error": error,
        "results": results,
    }


def _run_provider(data_dir: Path, name: str, records: list[dict], workers: int) -> str:
    path = data_dir / RESULTS_DIR / f"{name}.jsonl"
    if name in _SERIAL:
        workers = 1
    # Failed calls are retried on the next run; finished ones are kept.
    done = {r["id"] for r in read_jsonl(path) if not r["error"]}
    todo = [r for r in records if r["id"] not in done]
    errors = 0
    with ThreadPoolExecutor(workers) as pool:
        for row in pool.map(lambda r: _replay(name, r), todo):
            append_jsonl(path, row)
            errors += bool(row["error"])
    return f"{name}: {len(todo)} replayed, {errors} failed, {len(done)} already done"


@cli.command()
@click.option(
    "--provider",
    "providers",
    multiple=True,
    type=click.Choice(sorted(PROVIDERS)),
    help="Default: all.",
)
@click.option("--limit", type=int, help="Replay only the first N queries.")
@click.option("--workers", default=3, show_default=True, help="Concurrent calls per provider.")
@click.pass_obj
def run(data_dir: Path, providers: tuple[str, ...], limit: int | None, workers: int) -> None:
    """Paid: send every sampled query to each provider; resumes, retrying only failed calls."""
    records = list(read_jsonl(data_dir / QUERIES))[:limit]
    if not records:
        raise click.ClickException("no queries; run `research eval collect` first")
    names = providers or tuple(PROVIDERS)
    with ThreadPoolExecutor(len(names)) as pool:
        for line in pool.map(lambda n: _run_provider(data_dir, n, records, workers), names):
            click.echo(line)
