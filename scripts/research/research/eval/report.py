"""Score every provider on the queries all of them answered."""

from __future__ import annotations

import math
import random
import statistics
from pathlib import Path

import click

from research.eval import cli
from research.eval._data import (
    JUDGMENTS,
    QUERIES,
    RESULTS_DIR,
    domain_matches,
    read_jsonl,
    url_key,
)

_DEPTH = 5
# The researcher's production configuration (docs/decisions/0003-parallel-fast-search.md).
_BASELINE = "parallel-fast"
_RESAMPLES = 2000
# On 200 results Sonnet 5.5 had graded, Haiku 5.5 gave the same grade 80% of the time (kappa
# 0.63) and GLM 5.3 72% (kappa 0.53), at a small fraction of Sonnet's cost.
JUDGE_MODEL = "anthropic/claude-haiku-5.5"


def latest_results(data_dir: Path) -> dict[str, dict[str, dict]]:
    """Return each provider's latest successful result row per query ID."""
    providers: dict[str, dict[str, dict]] = {}
    for path in sorted((data_dir / RESULTS_DIR).glob("*.jsonl")):
        rows = providers.setdefault(path.stem, {})
        for row in read_jsonl(path):
            if not row["error"]:
                rows[row["id"]] = row
    return providers


def _errors(data_dir: Path, name: str) -> int:
    """Count queries whose every attempt failed."""
    rows = list(read_jsonl(data_dir / RESULTS_DIR / f"{name}.jsonl"))
    ok = {r["id"] for r in rows if not r["error"]}
    return len({r["id"] for r in rows if r["error"]} - ok)


def _dcg(grades: list[int]) -> float:
    return sum(g / math.log2(i + 2) for i, g in enumerate(grades))


def _ndcg(grades: list[int], ideal: list[int]) -> float:
    best = _dcg(sorted(ideal, reverse=True)[:_DEPTH])
    return _dcg(grades[:_DEPTH]) / best if best else 0.0


def _bootstrap(diffs: list[float], seed: int = 1) -> tuple[float, float]:
    """95% interval of the mean paired difference."""
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(_RESAMPLES))
    return means[int(0.025 * _RESAMPLES)], means[int(0.975 * _RESAMPLES) - 1]


def _percentile(values: list[int], share: float) -> int:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(share * len(ordered)))]


@cli.command()
@click.option(
    "--provider",
    "providers",
    multiple=True,
    help="Providers to compare. Default: all with results.",
)
@click.option(
    "--model",
    default=JUDGE_MODEL,
    show_default=True,
    help="Judge whose grades to score; grades from different judges are never mixed.",
)
@click.option(
    "--baseline",
    default=_BASELINE,
    show_default=True,
    help="Provider the paired confidence intervals compare against.",
)
@click.pass_obj
def report(data_dir: Path, providers: tuple[str, ...], model: str, baseline: str) -> None:
    """Free: report judged relevance, gold recall, filter compliance, and latency per provider.

    Only queries every compared provider answered are scored, so each provider faces the same
    questions. nDCG@5 uses grades 0-2 against the best five results any provider returned.
    """
    records = {r["id"]: r for r in read_jsonl(data_dir / QUERIES)}
    results = latest_results(data_dir)
    names = list(providers or results)
    unknown = [n for n in names if n not in results]
    if unknown or not names:
        available = ", ".join(sorted(results)) or "none; run `research eval run` first"
        raise click.UsageError(
            f"no results for {', '.join(unknown) or 'any provider'}; available: {available}"
        )
    common = sorted(set(records).intersection(*(results[n] for n in names)))
    grades: dict[tuple[str, str], int] = {
        (j["id"], j["url_key"]): j["grade"]
        for j in read_jsonl(data_dir / JUDGMENTS)
        if j["grade"] is not None and j["model"] == model
    }
    ideal: dict[str, list[int]] = {}
    for (qid, _), grade in grades.items():
        ideal.setdefault(qid, []).append(grade)

    filtered = [q for q in common if records[q]["domains"]]
    with_gold = [q for q in common if records[q]["gold"]]
    click.echo(
        f"{len(common)} of {len(records)} queries answered by all {len(names)} providers "
        f"({len(filtered)} domain-filtered, {len(with_gold)} with gold URLs)."
    )

    ndcg: dict[str, dict[str, float]] = {}
    for name in names:
        rows = results[name]
        per_query, unjudged = {}, 0
        useful = answers = top1 = empty = 0
        for qid in common:
            top = rows[qid]["results"][:_DEPTH]
            empty += not top
            query_grades = []
            for result in top:
                grade = grades.get((qid, url_key(result["url"])))
                unjudged += grade is None
                query_grades.append(grade or 0)
            per_query[qid] = _ndcg(query_grades, ideal.get(qid, []))
            useful += sum(g >= 1 for g in query_grades)
            answers += 2 in query_grades
            top1 += bool(query_grades) and query_grades[0] == 2
        ndcg[name] = per_query

        def mean(ids: list[str], scores: dict[str, float] = per_query) -> str:
            return f"{statistics.fmean(scores[q] for q in ids):.3f}" if ids else "n/a"

        open_ids = [q for q in common if not records[q]["domains"]]
        gold_hits = {5: 0, 10: 0}
        reciprocal = 0.0
        for qid in with_gold:
            gold = {url_key(u) for u in records[qid]["gold"]}
            ranks = [i for i, r in enumerate(rows[qid]["results"]) if url_key(r["url"]) in gold]
            if ranks:
                reciprocal += 1 / (ranks[0] + 1)
                gold_hits[5] += ranks[0] < 5
                gold_hits[10] += ranks[0] < 10
        in_domain = total = 0
        for qid in filtered:
            for result in rows[qid]["results"]:
                total += 1
                in_domain += domain_matches(result["url"], records[qid]["domains"])
        latencies = [rows[q]["latency_ms"] for q in common]
        n, g = len(common), max(len(with_gold), 1)
        click.echo(
            f"\n{name}: nDCG@5 {mean(common)} (open {mean(open_ids)}, filtered {mean(filtered)}); "
            f"useful/top5 {useful / n:.2f}; grade-2 in top5 {answers / n:.0%}; "
            f"grade-2 first {top1 / n:.0%}; empty {empty}; unjudged {unjudged}.\n"
            f"  gold recall@5 {gold_hits[5] / g:.0%}, @10 {gold_hits[10] / g:.0%}, "
            f"MRR {reciprocal / g:.3f}; in-domain {in_domain / max(total, 1):.0%} of "
            f"{total} filtered results; latency p50 {_percentile(latencies, 0.5)} ms, "
            f"p95 {_percentile(latencies, 0.95)} ms; failed queries {_errors(data_dir, name)}."
        )

    if baseline in ndcg:
        click.echo(f"\nnDCG@5 difference from {baseline}, 95% paired bootstrap interval:")
        for name in names:
            if name == baseline:
                continue
            diffs = [ndcg[name][q] - ndcg[baseline][q] for q in common]
            low, high = _bootstrap(diffs)
            click.echo(f"  {name}: {statistics.fmean(diffs):+.3f} [{low:+.3f}, {high:+.3f}]")
