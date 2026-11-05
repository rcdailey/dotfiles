"""`project view` lists only open issues per milestone unless --all, and counts what it hides."""

from __future__ import annotations

import unittest
from unittest import mock

from click.testing import CliRunner
from linear_cli.project import cli

PROJECT = {
    "id": "11111111-2222-3333-4444-555555555555",
    "name": "LTI",
    "issues": {
        "pageInfo": {"hasNextPage": False},
        "nodes": [
            {
                "identifier": "ENG-1",
                "title": "Open work",
                "state": {"name": "Todo", "type": "unstarted"},
                "projectMilestone": {"id": "ms-1"},
            },
            {
                "identifier": "ENG-2",
                "title": "Finished work",
                "state": {"name": "Done", "type": "completed"},
                "projectMilestone": {"id": "ms-1"},
            },
        ],
    },
    "projectMilestones": {"nodes": [{"id": "ms-1", "name": "Deep Linking"}]},
}


def fake_execute(query: str, variables: dict | None = None) -> dict:
    return {"q0": {"nodes": [PROJECT]}}


class ProjectViewTest(unittest.TestCase):
    def setUp(self) -> None:
        for target in ("linear_cli.project.execute", "linear_cli._resolve.execute"):
            patcher = mock.patch(target, fake_execute)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.runner = CliRunner()

    def view(self, *args: str) -> str:
        result = self.runner.invoke(cli, ["view", "LTI", *args])
        self.assertEqual(result.exit_code, 0, result.output)
        return result.output

    def test_default_hides_closed_issues_but_counts_them(self) -> None:
        output = self.view()
        self.assertIn("ENG-1", output)
        self.assertNotIn("ENG-2", output)
        self.assertIn("+1 more (1 closed)", output)

    def test_all_lists_closed_issues(self) -> None:
        output = self.view("--all")
        self.assertIn("ENG-1", output)
        self.assertIn("ENG-2", output)
        self.assertNotIn("more", output)


if __name__ == "__main__":
    unittest.main()
