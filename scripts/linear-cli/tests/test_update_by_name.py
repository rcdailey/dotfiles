"""Updates resolve users and milestones by name, and `none` clears a field.

Each test runs a command through Click against a fake Linear API and asserts the mutation input
the CLI sends, or that no mutation is sent when a lookup fails.
"""

from __future__ import annotations

import re
import unittest
from unittest import mock

from click.testing import CliRunner
from linear_cli import issue, milestone, project

PROJECT_ID = "11111111-2222-3333-4444-555555555555"
USERS = [
    {"id": "user-robert", "name": "Robert Dailey", "email": "robert@example.com"},
    {"id": "user-sam-a", "name": "Sam", "email": "sam.a@example.com"},
    {"id": "user-sam-b", "name": "Sam", "email": "sam.b@example.com"},
]
MILESTONE = {
    "id": "ms-hardening",
    "name": "Hardening",
    "issues": {"pageInfo": {"hasNextPage": False}, "nodes": [{"identifier": "ENG-1"}]},
}
_ALIAS_RE = re.compile(r"(q\d+): (\w+)")


class FakeLinear:
    """Answers name lookups from fixed data and records every mutation input."""

    def __init__(self) -> None:
        self.mutations: list[tuple[str, dict]] = []

    def execute(self, query: str, variables: dict | None = None) -> dict:
        variables = variables or {}
        if query.lstrip().startswith("mutation"):
            return self._mutate(query, variables)
        data: dict = {}
        for alias, field in _ALIAS_RE.findall(query):
            data[alias] = self._lookup(field, variables.get(f"{alias}_filter") or {})
        return data

    def _lookup(self, field: str, filt: dict) -> dict:
        if field == "projects":
            return {"nodes": [{"id": PROJECT_ID}]}
        if field == "projectMilestones":
            name = filt["name"]["eqIgnoreCase"].lower()
            return {"nodes": [MILESTONE] if name == MILESTONE["name"].lower() else []}
        if field == "users":
            ref = filt["or"][0]["name"]["eqIgnoreCase"].lower()
            matches = [u for u in USERS if ref in (u["name"].lower(), u["email"].lower())]
            return {"nodes": matches}
        return {}

    def _mutate(self, query: str, variables: dict) -> dict:
        if "projectMilestoneDelete(" in query:
            self.mutations.append(("milestoneDelete", {"id": variables["id"]}))
            return {"projectMilestoneDelete": {"success": True}}
        if "projectMilestoneUpdate(" in query:
            self.mutations.append(
                ("milestoneUpdate", {"id": variables["id"], **variables["input"]})
            )
            return {"projectMilestoneUpdate": {"success": True, "projectMilestone": {}}}
        if "projectUpdate(" in query:
            self.mutations.append(("projectUpdate", {"id": variables["id"], **variables["input"]}))
            return {"projectUpdate": {"success": True, "project": {}}}
        if "u0: issueUpdate" in query:
            data = {}
            for key, ref in variables.items():
                if re.fullmatch(r"i\d+", key):
                    self.mutations.append(("issueUpdate", {"id": ref, **variables["input"]}))
                    data[f"u{key[1:]}"] = {"success": True, "issue": {"identifier": ref}}
            return data
        self.mutations.append(("issueUpdate", {"id": variables["id"], **variables["input"]}))
        return {"issueUpdate": {"success": True, "issue": {"identifier": variables["id"]}}}


class UpdateByNameTest(unittest.TestCase):
    def setUp(self) -> None:
        self.linear = FakeLinear()
        for module in ("issue", "milestone", "project", "_resolve"):
            patcher = mock.patch(f"linear_cli.{module}.execute", self.linear.execute)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.runner = CliRunner()

    def run_ok(self, cli, args: list[str]) -> str:
        result = self.runner.invoke(cli, args)
        self.assertEqual(result.exit_code, 0, result.output)
        return result.output

    def run_fails(self, cli, args: list[str], message: str) -> None:
        result = self.runner.invoke(cli, args)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn(message, result.output)
        self.assertEqual(self.linear.mutations, [])

    def test_issue_update_none_clears_fields(self) -> None:
        self.run_ok(
            issue.cli,
            ["update", "ENG-1", "--assignee", "none", "--estimate", "none", "--parent", "none"]
            + ["--project", "none", "--milestone", "none"],
        )
        cleared = {
            "assigneeId": None,
            "estimate": None,
            "parentId": None,
            "projectId": None,
            "projectMilestoneId": None,
        }
        self.assertEqual(self.linear.mutations, [("issueUpdate", {"id": "ENG-1", **cleared})])

    def test_multi_issue_update_clears_milestone(self) -> None:
        self.run_ok(issue.cli, ["update", "ENG-1", "ENG-2", "--milestone", "none"])
        self.assertEqual(
            self.linear.mutations,
            [
                ("issueUpdate", {"id": "ENG-1", "projectMilestoneId": None}),
                ("issueUpdate", {"id": "ENG-2", "projectMilestoneId": None}),
            ],
        )

    def test_milestone_name_cannot_combine_with_project_none(self) -> None:
        self.run_fails(
            issue.cli,
            ["update", "ENG-1", "--project", "none", "--milestone", "Hardening"],
            "--milestone needs a project",
        )

    def test_issue_update_assigns_user_by_name(self) -> None:
        self.run_ok(issue.cli, ["update", "ENG-1", "--assignee", "robert dailey"])
        self.assertEqual(
            self.linear.mutations, [("issueUpdate", {"id": "ENG-1", "assigneeId": "user-robert"})]
        )

    def test_ambiguous_user_name_fails_without_mutation(self) -> None:
        self.run_fails(issue.cli, ["update", "ENG-1", "--assignee", "Sam"], "matches several users")

    def test_unknown_user_fails_without_mutation(self) -> None:
        self.run_fails(issue.cli, ["update", "ENG-1", "--assignee", "Nobody"], "not found")

    def test_milestone_update_by_name(self) -> None:
        self.run_ok(
            milestone.cli,
            ["update", "hardening", "--project", "LTI", "--target-date", "2026-12-01"]
            + ["--description", "none"],
        )
        self.assertEqual(
            self.linear.mutations,
            [
                (
                    "milestoneUpdate",
                    {"id": "ms-hardening", "targetDate": "2026-12-01", "description": None},
                )
            ],
        )

    def test_milestone_delete_by_name_lists_affected_issues(self) -> None:
        output = self.run_ok(milestone.cli, ["delete", "Hardening", "--project", "LTI"])
        self.assertEqual(self.linear.mutations, [("milestoneDelete", {"id": "ms-hardening"})])
        self.assertIn("ENG-1", output)

    def test_unknown_milestone_fails_without_mutation(self) -> None:
        self.run_fails(
            milestone.cli, ["delete", "Nope", "--project", "LTI"], "milestone 'Nope' not found"
        )

    def test_project_update_sets_and_clears_dates_and_lead(self) -> None:
        self.run_ok(
            project.cli,
            ["update", PROJECT_ID, "--start-date", "2026-01-05", "--target-date", "none"]
            + ["--lead", "robert@example.com"],
        )
        self.assertEqual(
            self.linear.mutations,
            [
                (
                    "projectUpdate",
                    {
                        "id": PROJECT_ID,
                        "startDate": "2026-01-05",
                        "targetDate": None,
                        "leadId": "user-robert",
                    },
                )
            ],
        )

    def test_project_update_clears_lead(self) -> None:
        self.run_ok(project.cli, ["update", PROJECT_ID, "--lead", "none"])
        self.assertEqual(
            self.linear.mutations, [("projectUpdate", {"id": PROJECT_ID, "leadId": None})]
        )


if __name__ == "__main__":
    unittest.main()
