"""Goal accountability: goals before retrieval, and a closing report checked against reads."""

import json
import os
import unittest
import uuid
from typing import ClassVar
from unittest import mock

from click.testing import CliRunner
from research.cli import cli


def _search_result(url: str) -> dict:
    return {"url": url, "title": "T", "content": f"About {url}", "published": None}


class _Session(unittest.TestCase):
    env: ClassVar[dict[str, str]] = {}

    def setUp(self) -> None:
        env = {"OPENCODE_SESSION_ID": f"test-{uuid.uuid4()}", **self.env}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)

    def invoke(self, *args: str) -> object:
        return CliRunner().invoke(cli, list(args))

    def search(self, *urls: str) -> object:
        results = [_search_result(u) for u in urls]
        with mock.patch("research._parallel.search", return_value=results):
            return self.invoke("web", "search", "--", f"query {uuid.uuid4()}")

    def read(self, url: str) -> None:
        with mock.patch("research.web.fetch_markdown", return_value="# Page\n\nBody text."):
            result = self.invoke("web", "fetch", "--", url)
        self.assertEqual(result.exit_code, 0, result.output)

    def close(self, *entries: dict) -> object:
        return self.invoke("ledger", "--report", json.dumps(list(entries)))


class WithoutGoalProtocolTest(_Session):
    """Agents other than the researcher use the same tools without recording goals."""

    def test_retrieval_and_ledger_work_without_goals(self) -> None:
        url = f"https://example.com/{uuid.uuid4()}"
        searched = self.search(url)
        self.assertEqual(searched.exit_code, 0, searched.output)
        self.read(url)
        ledger = self.invoke("ledger")
        self.assertEqual(ledger.exit_code, 0, ledger.output)
        self.assertIn(f"1. {url}", ledger.output)
        self.assertNotIn("## Goals", ledger.output)


class GoalsTest(_Session):
    env: ClassVar[dict[str, str]] = {"RESEARCH_REQUIRE_GOALS": "1"}

    def test_closing_without_a_report_is_refused(self) -> None:
        self.invoke("plan", "--", "goal one")
        result = self.invoke("ledger")
        self.assertEqual(result.exit_code, 2)
        self.assertIn("--report is required", result.output)

    def test_retrieval_requires_recorded_goals(self) -> None:
        blocked = self.search("https://example.com/a")
        self.assertEqual(blocked.exit_code, 2)
        self.assertIn("research_plan", blocked.output)
        self.assertNotIn("budget call", blocked.output)

        self.invoke("plan", "--", "goal one")
        allowed = self.search("https://example.com/a")
        self.assertEqual(allowed.exit_code, 0, allowed.output)
        self.assertIn("budget call 1 of", allowed.output)

    def start_session(self) -> tuple[str, str]:
        """Begin a fresh session with two goals, one read URL, and one unread search result."""
        patcher = mock.patch.dict(os.environ, {"OPENCODE_SESSION_ID": f"test-{uuid.uuid4()}"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.invoke("plan", "--", "goal one", "goal two")
        read_url = f"https://example.com/{uuid.uuid4()}"
        unread_url = f"https://example.com/{uuid.uuid4()}"
        self.search(read_url, unread_url)
        self.read(read_url)
        return read_url, unread_url

    def test_report_is_checked_against_what_the_session_read(self) -> None:
        def supported(url: str) -> dict:
            return {"goal": 1, "status": "supported", "sources": [url]}

        def gap(kind: str) -> dict:
            return {"goal": 2, "status": "gap", "kind": kind, "reason": "searched docs"}

        cases = {
            "missing goal": (
                lambda read, _: [supported(read)],
                "goal 2: missing from the report",
            ),
            "search result cited as evidence": (
                lambda _, unread: [supported(unread), gap("not_found")],
                "goal 1: cites no URL read in this session",
            ),
            "out of budget while budget remains": (
                lambda read, _: [supported(read), gap("out_of_budget")],
                "ordinary budget calls remain",
            ),
        }
        for name, (report, problem) in cases.items():
            with self.subTest(name):
                read_url, unread_url = self.start_session()
                result = self.close(*report(read_url, unread_url))
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn("Report rejected", result.output)
                self.assertIn(problem, result.output)
                self.assertIn(unread_url, result.output)
                self.assertNotIn("## Sources", result.output)

        read_url, _ = self.start_session()
        accepted = self.close(
            {"goal": 1, "status": "supported", "sources": [read_url]},
            {"goal": 2, "status": "gap", "kind": "not_found", "reason": "no source states it"},
        )
        self.assertIn("## Goals", accepted.output)
        self.assertIn(f"supported: {read_url}", accepted.output)
        self.assertIn("gap (not_found): no source states it", accepted.output)
        self.assertIn(f"1. {read_url}", accepted.output)
        self.assertNotIn("Kind: coverage", accepted.output)

    def test_out_of_budget_is_allowed_once_ordinary_calls_are_spent(self) -> None:
        self.invoke("plan", "--", "goal one")
        for _ in range(17):
            self.assertEqual(self.search("https://example.com/a").exit_code, 0)
        result = self.close(
            {"goal": 1, "status": "gap", "kind": "out_of_budget", "reason": "budget spent"}
        )
        self.assertIn("## Goals", result.output)

    def test_rejection_is_bounded_and_unresolved_problems_reach_errors(self) -> None:
        self.invoke("plan", "--", "goal one")
        for attempt in (1, 2):
            rejected = self.close()
            self.assertIn(f"Report rejected ({attempt} of 2)", rejected.output)
        accepted = self.close()
        self.assertIn("## Goals", accepted.output)
        self.assertIn("1. goal one\n   not reported", accepted.output)
        self.assertIn("Kind: coverage", accepted.output)
        self.assertIn("goal 1: missing from the report", accepted.output)
