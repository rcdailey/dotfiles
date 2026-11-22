"""`research web search` and `web fetch`: budget accounting, fallbacks, and one result per page."""

import os
import unittest
import uuid
from unittest import mock

from click.testing import CliRunner
from research._fetch import FetchError
from research._parallel import ParallelError
from research.cli import cli


def _result(url: str, content: str, title: str = "T") -> dict:
    return {"url": url, "title": title, "content": content, "published": None}


class _Session(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.dict(os.environ, {"OPENCODE_SESSION_ID": f"test-{uuid.uuid4()}"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def invoke(self, *args: str) -> object:
        return CliRunner().invoke(cli, list(args))


class SearchTest(_Session):
    def search(self, outcome: object) -> object:
        kwargs = (
            {"side_effect": outcome}
            if isinstance(outcome, Exception)
            else {"return_value": outcome}
        )
        with mock.patch("research._parallel.search", **kwargs):
            return self.invoke("web", "search", "--", f"query {uuid.uuid4()}")

    def test_failure_is_reported_and_refunds_the_budget_call(self) -> None:
        result = self.search(ParallelError("search failed: rate limited after one retry"))
        self.assertEqual(result.exit_code, 1)
        self.assertIn("error: search failed: rate limited", result.output)
        self.assertIn("budget restored to 0/", result.output)

    def test_success_spends_one_call_and_lists_each_page_once(self) -> None:
        page = " ".join(f"word{i}" for i in range(40))
        result = self.search(
            [
                _result("https://example.com/docs/setup?utm_source=x", page),
                _result("https://www.example.com/docs/setup/", "Same URL, different tracking."),
                _result("https://example.com/en/docs/setup", f"Breadcrumb\n{page}"),
                _result("https://example.net/docs/setup", page),
                # Same words, but a different page: another name, version, item, or site.
                _result("https://example.com/docs/install", page),
                _result("https://example.com/v2/docs/setup", page),
                _result("https://example.com/docs/setup?id=2", page),
                _result("https://wiki.example.com/docs/setup", page),
                _result("https://other.example.com/docs/setup", page),
            ]
        )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("budget call 1 of", result.output)
        self.assertEqual(result.output.count("Discovered:"), 6)
        self.assertIn("[3 duplicate or mirrored results hidden]", result.output)


class FetchFallbackTest(_Session):
    def fetch(self, local: object, remote: object) -> object:
        url = f"https://example.com/{uuid.uuid4()}"
        with (
            mock.patch("research.web.fetch_markdown", side_effect=local),
            mock.patch("research._parallel.extract", side_effect=remote) as extract,
        ):
            result = self.invoke("web", "fetch", "--", url)
        return result, extract

    def test_local_failure_falls_back_to_parallel_extract(self) -> None:
        result, _ = self.fetch(FetchError("timeout"), ["# Rendered page"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("# Rendered page", result.output)

    def test_both_failing_is_reported_and_refunds_the_budget_call(self) -> None:
        result, _ = self.fetch(FetchError("timeout"), ParallelError("fetch failed: blocked"))
        self.assertEqual(result.exit_code, 1)
        self.assertIn("via Parallel Extract", result.output)
        self.assertIn("record the page as unreachable", result.output)
        self.assertIn("budget restored to 0/", result.output)

    def test_remote_failure_gives_one_next_step(self) -> None:
        cases = {
            "page missing": (
                ParallelError("fetch failed: not found (HTTP 404)", page_missing=True),
                "the URL does not exist",
            ),
            "tool error": (
                ParallelError("fetch failed: HTTP 401", "report this as a tool error"),
                "report this as a tool error",
            ),
        }
        for name, (error, advice) in cases.items():
            with self.subTest(name):
                result, _ = self.fetch(FetchError("timeout"), error)
                self.assertIn(advice, result.output)
                self.assertNotIn("unreachable", result.output)

    def test_missing_page_skips_the_remote_fallback(self) -> None:
        result, extract = self.fetch(FetchError("HTTP 404", 404), ["unused"])
        self.assertEqual(result.exit_code, 1)
        extract.assert_not_called()


if __name__ == "__main__":
    unittest.main()
