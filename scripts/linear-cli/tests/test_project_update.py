"""`project update --state` resolves a project status display name to its ID."""

from __future__ import annotations

import unittest
from unittest import mock

from click.testing import CliRunner
from linear_cli.project import cli

PROJECT_ID = "11111111-2222-3333-4444-555555555555"
STATUSES = [{"id": "status-started", "name": "In Progress"}, {"id": "status-done", "name": "Done"}]


class FakeLinear:
    """Stands in for the Linear API so tests observe the mutations the CLI sends."""

    def __init__(self) -> None:
        self.mutations: list[dict] = []

    def execute(self, query: str, variables: dict | None = None) -> dict:
        variables = variables or {}
        if "projectUpdate(" in query:
            self.mutations.append({"id": variables["id"], **variables["input"]})
            return {"projectUpdate": {"success": True, "project": {"name": "Roadmap"}}}
        data: dict = {}
        for alias in ("q0", "q1"):
            if f"{alias}: projectStatuses" in query:
                data[alias] = {"nodes": STATUSES}
            elif f"{alias}: projects" in query:
                data[alias] = {"nodes": [{"id": PROJECT_ID}]}
        return data


class ProjectUpdateStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.linear = FakeLinear()
        for target in ("linear_cli.project.execute", "linear_cli._resolve.execute"):
            patcher = mock.patch(target, self.linear.execute)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.runner = CliRunner()

    def test_state_name_sets_status_id_case_insensitively(self) -> None:
        result = self.runner.invoke(cli, ["update", "Roadmap", "--state", "done"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(self.linear.mutations, [{"id": PROJECT_ID, "statusId": "status-done"}])

    def test_state_combines_with_other_fields_for_uuid_reference(self) -> None:
        result = self.runner.invoke(
            cli, ["update", PROJECT_ID, "--name", "Renamed", "--state", "In Progress"]
        )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            self.linear.mutations,
            [{"id": PROJECT_ID, "name": "Renamed", "statusId": "status-started"}],
        )

    def test_unknown_state_fails_without_mutation(self) -> None:
        result = self.runner.invoke(cli, ["update", "Roadmap", "--state", "Shipped"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("project status 'Shipped' not found", result.output)
        self.assertEqual(self.linear.mutations, [])


if __name__ == "__main__":
    unittest.main()
