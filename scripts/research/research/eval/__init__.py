"""Replay past researcher searches against web search providers and score them.

Run the steps in order: `collect` samples queries from OpenCode researcher sessions, `run`
replays them against each provider, `judge` grades the pooled top results blind with an LLM,
and `report` scores every provider on the same queries.
"""

from __future__ import annotations

from pathlib import Path

import click

from research._click import RecursiveHelpGroup
from research.eval._data import DEFAULT_DIR


@click.group(cls=RecursiveHelpGroup)
@click.option(
    "--dir",
    "data_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=DEFAULT_DIR,
    show_default=True,
    help="Evaluation data directory.",
)
@click.pass_context
def cli(ctx: click.Context, data_dir: Path) -> None:
    """Compare web search providers on replayed researcher queries; use a fresh --dir per study.

    Steps: collect (free), run (paid: provider API calls), judge (paid: NanoGPT LLM calls),
    report (free). Keys come from <NAME>_API_KEY or `rbw get <name>-api-key`; the judge uses
    NANO_GPT_API_KEY or rbw item "NanoGPT API Key".
    """
    ctx.obj = data_dir


from research.eval import collect, judge, report, run  # noqa: F401
