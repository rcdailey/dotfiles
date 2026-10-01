"""Spec examples: vendored Rewrap Markdown specs plus mdwrap's own extensions."""

from __future__ import annotations

from pathlib import Path

import pytest
from mdwrap._format import Dialect, rewrap

from tests._spec_format import Example, read_examples

SPECS = Path(__file__).parent / "specs"
DIALECTS = {"markdown": Dialect.MARKDOWN, "mdx": Dialect.MDX}
EXAMPLES = [ex for path in sorted(SPECS.rglob("*.txt")) for ex in read_examples(path)]

# Rewrap joins CJK lines without a space, so a space before a character that may not start a
# line (or after one that may not end it) is lost when the output is wrapped again.
NOT_IDEMPOTENT = {"feature-special-characters.txt:51", "feature-special-characters.txt:61"}


def _skip_reason(ex: Example) -> str | None:
    language = ex.settings.get("language", "plaintext")
    if language not in DIALECTS:
        return f"language {language} is out of scope"
    if ex.settings.get("reformat") == "true":
        return "reformat is not supported"
    if ex.settings.get("doubleSentenceSpacing") == "true":
        return "doubleSentenceSpacing is not supported"
    if ex.has_selection:
        return "selections are not supported"
    return None


def _run(ex: Example, lines: list[str]) -> list[str]:
    text = rewrap(
        "\n".join(lines),
        width=ex.width,
        tab_width=int(ex.settings.get("tabWidth", 4)),
        dialect=DIALECTS[ex.settings.get("language", "markdown")],
    )
    return text.split("\n")


@pytest.mark.parametrize("ex", EXAMPLES, ids=[ex.id for ex in EXAMPLES])
def test_example(ex: Example) -> None:
    assert ex.error is None, ex.error
    reason = _skip_reason(ex)
    if reason:
        pytest.skip(reason)
    assert _run(ex, ex.input) == ex.expected
    if ex.id not in NOT_IDEMPOTENT:
        assert _run(ex, ex.expected) == ex.expected, "not idempotent"
