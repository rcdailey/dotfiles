"""The `mdwrap` command as callers invoke it: file safety, check mode, and stdin."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

LONG = "one two three four five six seven eight nine ten\n"
WRAPPED = "one two three four five six\nseven eight nine ten\n"


def run(cwd: Path, *args: str, stdin: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "mdwrap", *args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        check=False,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".editorconfig").write_text("root = true\n[*]\nmax_line_length = 30\n")
    return tmp_path


def test_rewrites_in_place(repo: Path) -> None:
    target = repo / "a.md"
    target.write_text(LONG)
    result = run(repo, str(target))
    assert result.returncode == 0, result.stderr
    assert target.read_text() == WRAPPED


def test_unchanged_file_is_not_rewritten(repo: Path) -> None:
    target = repo / "a.md"
    target.write_text(WRAPPED)
    os.utime(target, ns=(1_000_000_000, 1_000_000_000))
    assert run(repo, str(target)).returncode == 0
    assert target.stat().st_mtime_ns == 1_000_000_000


def test_no_width_leaves_file_unchanged(tmp_path: Path) -> None:
    (tmp_path / ".editorconfig").write_text("root = true\n")
    target = tmp_path / "a.md"
    target.write_text(LONG)
    result = run(tmp_path, str(target))
    assert result.returncode == 0
    assert target.read_text() == LONG
    assert f"no wrap width for {target}; unchanged" in result.stderr.decode()


def test_check_reports_without_writing(repo: Path) -> None:
    target = repo / "a.md"
    target.write_text(LONG)
    result = run(repo, "--check", str(target))
    assert result.returncode == 1
    assert result.stdout.decode() == f"would rewrap: {target}\n"
    assert target.read_text() == LONG


def test_check_clean(repo: Path) -> None:
    target = repo / "a.md"
    target.write_text(WRAPPED)
    result = run(repo, "--check", str(target))
    assert (result.returncode, result.stdout) == (0, b"")


def test_width_override(repo: Path) -> None:
    target = repo / "a.md"
    target.write_text(LONG)
    assert run(repo, "--width", "100", str(target)).returncode == 0
    assert target.read_text() == LONG


def test_stdin_to_stdout(repo: Path) -> None:
    result = run(repo, "-", stdin=LONG.encode())
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode() == WRAPPED


def test_stdin_filename_selects_dialect_and_config(repo: Path) -> None:
    sub = repo / "docs"
    sub.mkdir()
    (sub / ".markdownlint.yaml").write_text("line-length:\n  line_length: 20\n")
    text = "import Thing from 'library';\n\nShort words that wrap here.\n"
    result = run(repo, "--stdin-filename", "docs/page.mdx", "-", stdin=text.encode())
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode() == (
        "import Thing from 'library';\n\nShort words that\nwrap here.\n"
    )
    result = run(repo, "--stdin-filename", "docs/page.md", "-", stdin=text.encode())
    assert result.stdout.decode().startswith("import Thing from\n'library';\n")


def test_stdin_without_filename_matches_markdown_sections(tmp_path: Path) -> None:
    (tmp_path / ".editorconfig").write_text("root = true\n[*.md]\nmax_line_length = 30\n")
    result = run(tmp_path, "-", stdin=LONG.encode())
    assert result.stdout.decode() == WRAPPED


def test_write_failure_is_reported_and_other_paths_continue(repo: Path) -> None:
    locked = repo / "locked"
    locked.mkdir()
    blocked = locked / "a.md"
    blocked.write_text(LONG)
    good = repo / "b.md"
    good.write_text(LONG)
    locked.chmod(0o555)
    try:
        result = run(repo, str(blocked), str(good))
    finally:
        locked.chmod(0o755)
    assert result.returncode == 1
    assert f"error: {blocked}:" in result.stderr.decode()
    assert blocked.read_text() == LONG
    assert good.read_text() == WRAPPED


def test_preserves_crlf_bom_and_missing_final_newline(repo: Path) -> None:
    target = repo / "a.md"
    target.write_bytes(b"\xef\xbb\xbf" + LONG.rstrip("\n").encode().replace(b"\n", b"\r\n"))
    target.write_bytes(target.read_bytes() + b"\r\n\r\nshort\r\ntext")
    assert run(repo, str(target)).returncode == 0
    expected = b"\xef\xbb\xbfone two three four five six\r\nseven eight nine ten\r\n\r\nshort text"
    assert target.read_bytes() == expected


def test_invalid_utf8_is_an_error(repo: Path) -> None:
    target = repo / "a.md"
    data = b"\xff\xfe " + LONG.encode()
    target.write_bytes(data)
    result = run(repo, str(target))
    assert result.returncode == 1
    assert str(target) in result.stderr.decode()
    assert target.read_bytes() == data


def test_malformed_config_is_an_error(repo: Path) -> None:
    (repo / ".markdownlint.json").write_text("{")
    target = repo / "a.md"
    target.write_text(LONG)
    result = run(repo, str(target))
    assert result.returncode == 1
    assert str(repo / ".markdownlint.json") in result.stderr.decode()
    assert target.read_text() == LONG


def test_symlink_target_is_rewritten(repo: Path) -> None:
    real = repo / "real.md"
    real.write_text(LONG)
    real.chmod(0o640)
    link = repo / "link.md"
    link.symlink_to(real)
    assert run(repo, str(link)).returncode == 0
    assert link.is_symlink()
    assert real.read_text() == WRAPPED
    assert real.stat().st_mode & 0o777 == 0o640


def test_multiple_paths_continue_after_error(repo: Path) -> None:
    good = repo / "a.md"
    good.write_text(LONG)
    missing = repo / "missing.md"
    result = run(repo, str(missing), str(good))
    assert result.returncode == 1
    assert str(missing) in result.stderr.decode()
    assert good.read_text() == WRAPPED


def test_directory_is_an_error(repo: Path) -> None:
    result = run(repo, str(repo))
    assert result.returncode == 1
    assert str(repo) in result.stderr.decode()


def test_stdin_must_be_the_only_path(repo: Path) -> None:
    (repo / "a.md").write_text(LONG)
    result = run(repo, "-", "a.md", stdin=b"")
    assert result.returncode == 2
