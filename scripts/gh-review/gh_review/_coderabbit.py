"""CodeRabbit review-body conventions."""

from __future__ import annotations

import re

LOGIN = "coderabbitai"

# Findings not posted inline (quiet mode, outside-diff range, nitpicks) are collapsed into counted
# groups such as "Other comments: 1" or "Nitpick comments (3)".
_FINDINGS_GROUP = re.compile(r"\bcomments?\s*(?::\s*|\()\d+", re.IGNORECASE)
# Inside a findings group, per-file subgroups are counted too: "src/app.py: 2", "src/app.py (2)".
_COUNTED_SUMMARY = re.compile(r"(?::\s*\d+|\(\d+\))\s*$")
# Outside-diff findings sit in a callout, one block per finding, each summary ending with its
# location: "Major · Title · <code>path/file.sh:4-9</code>".
_FINDING_LOCATION = re.compile(r"<code>[^<]+:\d+(?:-\d+)?</code>\s*$")


def keeps_details(summary: str, in_kept: bool) -> bool:
    """Keep findings and their groups; drop prompts, fix diffs, review info."""
    if _FINDINGS_GROUP.search(summary) or _FINDING_LOCATION.search(summary):
        return True
    return in_kept and bool(_COUNTED_SUMMARY.search(summary))
