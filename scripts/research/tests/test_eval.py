"""`research eval`: reruns never repeat paid work, and judges' grades never mix."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from click.testing import CliRunner
from research.cli import cli
from research.eval._providers import ProviderError


def _write(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


def _read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _query(qid: str) -> dict:
    return {
        "id": qid,
        "session": "s",
        "date": "2026-11-01",
        "query": f"query {qid}",
        "domains": [],
        "exclude_domains": [],
        "time_range": None,
        "gold": [],
        "task": "task",
    }


class EvalTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        _write(self.dir / "queries.jsonl", [_query("q1"), _query("q2")])

    def eval(self, *args: str) -> object:
        result = CliRunner().invoke(cli, ["eval", "--dir", str(self.dir), *args])
        self.assertEqual(result.exit_code, 0, result.output)
        return result

    def test_collect_refuses_to_replace_a_query_set(self) -> None:
        result = CliRunner().invoke(cli, ["eval", "--dir", str(self.dir), "collect"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(len(_read(self.dir / "queries.jsonl")), 2)

    def test_run_replays_only_failed_or_missing_queries(self) -> None:
        calls: list[str] = []

        def provider(q: object) -> list[dict]:
            calls.append(q.query)
            if q.query == "query q2" and len(calls) == 2:
                raise RuntimeError("flaky")
            return [{"url": f"https://example.com/{len(calls)}", "title": "", "snippet": ""}]

        with mock.patch.dict("research.eval._providers.PROVIDERS", {"fake": provider}, clear=True):
            self.eval("run", "--workers", "1")
            self.eval("run", "--workers", "1")
            self.eval("run", "--workers", "1")
        self.assertEqual(calls, ["query q1", "query q2", "query q2"])

    def test_judge_regrades_only_failures_and_report_uses_one_judge(self) -> None:
        _write(
            self.dir / "results" / "fake.jsonl",
            [
                {
                    "id": qid,
                    "latency_ms": 1,
                    "error": None,
                    "results": [{"url": f"https://example.com/{qid}", "title": "", "snippet": ""}],
                }
                for qid in ("q1", "q2")
            ],
        )
        graded: list[str] = []

        def judge_api(url: str, body: dict, headers: dict) -> dict:
            graded.append(body["model"])
            if body["model"] == "a" and len(graded) == 1:
                raise ProviderError("transient")
            grade = 2 if body["model"] == "a" else 0
            return {"choices": [{"message": {"content": json.dumps({"grade": grade})}}]}

        with (
            mock.patch("research.eval.judge.post_json", side_effect=judge_api),
            mock.patch("research.eval.judge.fetch_markdown", return_value="page"),
            mock.patch("research.eval.judge.read_secret", return_value="key"),
        ):
            self.eval("judge", "--model", "a", "--workers", "1")
            self.eval("judge", "--model", "a", "--workers", "1")
            self.eval("judge", "--model", "b", "--workers", "1")
        self.assertEqual(graded, ["a", "a", "a", "b", "b"])

        self.assertIn("grade-2 in top5 100%", self.eval("report", "--model", "a").output)
        self.assertIn("grade-2 in top5 0%", self.eval("report", "--model", "b").output)


if __name__ == "__main__":
    unittest.main()
