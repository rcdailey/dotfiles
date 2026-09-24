"""Behavioral tests for the acceptance-snapshot CLI."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).parents[1]


def _git(repository: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


class SnapshotCliTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.repository = root / "repository"
        self.repository.mkdir()
        (root / "state").mkdir()
        self.environment = os.environ | {
            "OPENCODE_SESSION_ID": "test-session",
            "TMPDIR": str(root / "state"),
            "PYTHONPATH": str(PROJECT),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
        }
        _git(self.repository, "init", "--quiet", "--initial-branch=main")
        (self.repository / ".gitignore").write_text("ignored.txt\n")
        (self.repository / "ignored.txt").write_text("ignored\n")
        (self.repository / "staged.txt").write_text("staged\n")
        (self.repository / "untracked.txt").write_text("untracked\n")
        _git(self.repository, "add", "staged.txt")

    def _snapshot(self, *args: str) -> str:
        result = subprocess.run(
            [sys.executable, "-m", "acceptance_snapshot", *args],
            cwd=self.repository,
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def _commit(self) -> None:
        _git(
            self.repository,
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "--quiet",
            "--message=Initial",
        )

    def test_repository_without_commits_compares_against_empty_tree(self) -> None:
        empty_tree = _git(self.repository, "hash-object", "-t", "tree", os.devnull)

        output = self._snapshot("begin")

        self.assertIn(f"Previous tree: {empty_tree}\n", output)
        self.assertIn(
            "Changes:\nA\t.gitignore\nA\tstaged.txt\nA\tuntracked.txt\n",
            output,
        )
        self.assertIn("+staged\n", self._snapshot("diff", "--", "staged.txt"))
        self.assertIn("Result: stable\n", self._snapshot("finish"))

    def test_repository_with_commits_compares_against_head(self) -> None:
        self._commit()
        (self.repository / "staged.txt").write_text("changed\n")

        head_tree = _git(self.repository, "rev-parse", "HEAD^{tree}")

        output = self._snapshot("begin")

        self.assertIn(f"Previous tree: {head_tree}\n", output)
        self.assertIn("Changes:\nA\t.gitignore\nM\tstaged.txt\nA\tuntracked.txt\n", output)
        self.assertIn("Result: stable\n", self._snapshot("finish"))

    def test_first_commit_after_audit_keeps_audited_tree(self) -> None:
        self._snapshot("begin")
        self._snapshot("finish")
        self._commit()

        output = self._snapshot("begin")

        self.assertIn("Iteration: 2\n", output)
        self.assertIn("Changes:\n(none)\n", output)


if __name__ == "__main__":
    unittest.main()
