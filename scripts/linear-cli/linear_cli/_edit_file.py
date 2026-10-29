"""Issue edit files: an issue's title and description as one Markdown document.

`issue view` writes the file; `issue update --from-file` reads it back. Frontmatter records which
issue the file came from and the issue's `updatedAt` at write time, so an update can refuse a file
written for another issue or one that predates a newer change in Linear.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EditFile:
    """Parsed edit-file contents."""

    identifier: str
    updated_at: str
    title: str
    description: str


def edit_dir() -> Path:
    """Return the edit-file directory, preferring OpenCode's pre-approved temp directory."""
    tmp = Path(tempfile.gettempdir())
    opencode_tmp = tmp / "opencode"
    return (opencode_tmp if opencode_tmp.is_dir() else tmp) / "linear"


def write_edit_file(identifier: str, updated_at: str, title: str, description: str) -> Path:
    """Write the issue's edit file, replacing any earlier one, and return its path."""
    path = edit_dir() / f"{identifier}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    # Editors format Markdown on save (OpenCode runs rumdl through md-format). Rumdl honors a
    # nearer config's exclude even for named files, so formatting cannot rewrite issue content.
    (path.parent / ".rumdl.toml").write_text('[global]\nexclude = ["*"]\n', encoding="utf-8")
    text = f"---\nidentifier: {identifier}\nupdatedAt: {updated_at}\n---\n# {title}\n"
    if description := description.strip("\n"):
        text += f"\n{description}\n"
    path.write_text(text, encoding="utf-8")
    return path


def read_edit_file(path: Path) -> EditFile:
    """Parse an edit file. Raises ValueError naming the first problem found."""
    lines = path.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise ValueError("missing frontmatter")
    end = lines.index("---", 1)
    meta = dict(line.split(": ", 1) for line in lines[1:end] if ": " in line)
    identifier, updated_at = meta.get("identifier"), meta.get("updatedAt")
    if not identifier or not updated_at:
        raise ValueError("frontmatter needs identifier and updatedAt")
    body = lines[end + 1 :]
    while body and not body[0].strip():
        body = body[1:]
    if not body or not body[0].startswith("# ") or not body[0][2:].strip():
        raise ValueError("first line after frontmatter must be '# <title>'")
    description = "\n".join(body[1:]).strip("\n")
    return EditFile(identifier, updated_at, body[0][2:].strip(), description)
