"""Edit-file round trip: `issue view` writes it, `issue update --from-file` applies it."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from click.testing import CliRunner
from linear_cli.issue import cli

UPDATED_AT = "2026-10-29T14:00:00.000Z"


class FakeLinear:
    """Stands in for the Linear API so tests observe the mutations the CLI sends."""

    def __init__(self) -> None:
        self.updated_at = UPDATED_AT
        self.mutations: list[dict] = []

    def execute(self, query: str, variables: dict | None = None) -> dict:
        variables = variables or {}
        if "issueUpdate" in query:
            self.mutations.append(variables["input"])
            issue = {"identifier": "ENG-1", "title": variables["input"].get("title", "Old")}
            return {"issueUpdate": {"success": True, "issue": issue}}
        if query.lstrip().startswith("query IssueView") or "withComments" in variables:
            return {"issue": self._issue()}
        # Batched lookups alias the issue as q0.
        return {"q0": {"id": "uuid-1", "identifier": "ENG-1", "updatedAt": self.updated_at}}

    def _issue(self) -> dict:
        return {
            "id": "uuid-1",
            "identifier": "ENG-1",
            "title": "Old title",
            "description": "## Goal\n\nOld body.",
            "updatedAt": self.updated_at,
        }


class EditFileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tempdir = mock.patch.object(tempfile, "tempdir", self.tmp.name)
        tempdir.start()
        self.addCleanup(tempdir.stop)
        self.linear = FakeLinear()
        for target in ("linear_cli.issue.execute", "linear_cli._resolve.execute"):
            patcher = mock.patch(target, self.linear.execute)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.runner = CliRunner()

    def view(self) -> tuple[str, Path]:
        result = self.runner.invoke(cli, ["view", "ENG-1"])
        self.assertEqual(result.exit_code, 0, result.output)
        last = result.output.rstrip("\n").splitlines()[-1]
        self.assertTrue(last.startswith("edit file: "), result.output)
        return result.output, Path(last.removeprefix("edit file: "))

    def update(self, path: Path, *extra: str):
        return self.runner.invoke(cli, ["update", "ENG-1", "--from-file", str(path), *extra])

    def test_view_prints_title_heading_and_writes_edit_file(self) -> None:
        output, path = self.view()
        self.assertTrue(output.startswith("# Old title\n"))
        self.assertEqual(
            path.read_text(),
            f"---\nidentifier: ENG-1\nupdatedAt: {UPDATED_AT}\n---\n"
            "# Old title\n\n## Goal\n\nOld body.\n",
        )

    def test_update_from_file_sets_title_and_description_then_deletes_file(self) -> None:
        _, path = self.view()
        path.write_text(path.read_text().replace("Old title", "New title").replace("Old", "New"))
        result = self.update(path)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            self.linear.mutations, [{"title": "New title", "description": "## Goal\n\nNew body."}]
        )
        self.assertFalse(path.exists())

    def test_update_from_file_accepts_blank_lines_before_title(self) -> None:
        _, path = self.view()
        path.write_text(path.read_text().replace("---\n# Old title", "---\n\n# New title"))
        result = self.update(path)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(self.linear.mutations[0]["title"], "New title")

    def test_view_excludes_edit_files_from_markdown_formatting(self) -> None:
        _, path = self.view()
        self.assertIn('exclude = ["*"]', (path.parent / ".rumdl.toml").read_text())

    def test_rejects_file_without_title_heading(self) -> None:
        _, path = self.view()
        path.write_text(path.read_text().replace("# Old title\n", ""))
        result = self.update(path)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("'# <title>'", result.output)
        self.assertEqual(self.linear.mutations, [])
        self.assertTrue(path.exists())

    def test_rejects_file_without_frontmatter(self) -> None:
        _, path = self.view()
        path.write_text("# Old title\n\nBody.\n")
        result = self.update(path)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("frontmatter", result.output)
        self.assertEqual(self.linear.mutations, [])

    def test_rejects_file_when_issue_changed_after_view(self) -> None:
        _, path = self.view()
        self.linear.updated_at = "2026-10-29T15:00:00.000Z"
        result = self.update(path)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("changed after the edit file was written", result.output)
        self.assertEqual(self.linear.mutations, [])
        self.assertTrue(path.exists())

    def test_rejects_file_for_another_issue(self) -> None:
        _, path = self.view()
        path.write_text(path.read_text().replace("identifier: ENG-1", "identifier: ENG-2"))
        result = self.update(path)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("edit file is for ENG-2", result.output)
        self.assertEqual(self.linear.mutations, [])

    def test_rejects_from_file_with_title_flag(self) -> None:
        _, path = self.view()
        result = self.update(path, "--title", "Other")
        self.assertEqual(result.exit_code, 2)
        self.assertEqual(self.linear.mutations, [])

    def test_update_without_from_file_ignores_edit_file(self) -> None:
        _, path = self.view()
        path.write_text(path.read_text().replace("Old title", "New title"))
        result = self.runner.invoke(cli, ["update", "ENG-1", "--priority", "2"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(self.linear.mutations, [{"priority": 2}])
        self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
