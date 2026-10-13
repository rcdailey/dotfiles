"""CodeRabbit review-body conventions."""

from __future__ import annotations

import re

LOGIN = "coderabbitai"

# Findings not posted inline (quiet mode, outside-diff range, nitpicks) are collapsed into counted
# groups such as "Other comments: 1" or "Nitpick comments (3)".
_FINDINGS_GROUP = re.compile(r"\bcomments?\s*(?::\s*|\()\d+", re.IGNORECASE)
# Inside a findings group, per-file subgroups are counted too: "src/app.py: 2", "src/app.py (2)".
_COUNTED_SUMMARY = re.compile(r"(?::\s*\d+|\(\d+\))\s*$")


def keeps_details(summary: str, in_kept: bool) -> bool:
    """Keep finding groups and their per-file subgroups; drop prompts, fix diffs, review info."""
    if _FINDINGS_GROUP.search(summary):
        return True
    return in_kept and bool(_COUNTED_SUMMARY.search(summary))
