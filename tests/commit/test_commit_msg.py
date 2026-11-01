"""Exercise the global commit-msg hook through real git commit runs.

Run with python -m unittest discover -s tests/commit.
"""

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "home/dot_config/git/hooks/executable_commit-msg"
RULES = {"rules": {"type-enum": [2, "always", ["project"]], "type-empty": [2, "never"]}}
LONG = (
    "This paragraph is long enough that it has to wrap at seventy-two columns, and it"
    " keeps going so the second line is also needed for the test."
)


class CommitMsgHookTests(unittest.TestCase):
    def setUp(self):
        for tool in ("git", "rumdl", "commitlint", "yq"):
            self.assertIsNotNone(shutil.which(tool), f"required tool missing: {tool}")
        self.temp = tempfile.TemporaryDirectory(prefix="commit-msg-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repository with spaces"
        self.repo.mkdir()
        global_config = self.root / "gitconfig"
        command = f"{shlex.quote(sys.executable)} {shlex.quote(str(HOOK))}"
        global_config.write_text(
            f'[hook "commit-message"]\n\tevent = commit-msg\n\tcommand = {command}\n'
        )
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(
            {
                "HOME": str(self.root),
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": str(global_config),
                "MISE_TRUSTED_CONFIG_PATHS": str(self.root),
            }
        )
        self.git("init", "--quiet")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgSign", "false")
        self.counter = 0

    def git(self, *args, check=True):
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            env=self.env,
            text=True,
            capture_output=True,
            check=check,
        )

    def commit(self, *args):
        self.counter += 1
        (self.repo / "change.txt").write_text(f"content {self.counter}\n")
        self.git("add", "change.txt")
        return self.git("commit", "--quiet", *args, check=False)

    def commit_messages(self, *paragraphs):
        return self.commit(*[arg for paragraph in paragraphs for arg in ("-m", paragraph)])

    def message(self):
        return self.git("log", "-1", "--format=%B").stdout

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def config(self, name=".commitlintrc.json", content=None, tracked=True):
        path = self.repo / name
        path.write_text(json.dumps(RULES) if content is None else content)
        if tracked:
            self.git("add", "--", name)
        return path

    def test_body_paragraphs_and_lists_reflow_and_subject_stays(self):
        subject = "Subject line that stays as written"
        self.assert_ok(
            self.commit_messages(subject, f"{LONG}\nshort tail", f"- {LONG}\n- second item")
        )
        message = self.message()
        lines = message.splitlines()
        self.assertEqual(lines[0], subject)
        self.assertTrue(all(len(line) <= 72 for line in lines), message)
        self.assertTrue(lines[6].startswith("- ") and lines[7].startswith("  "), message)
        self.assertEqual(" ".join(message.split("\n\n")[1].split()), f"{LONG} short tail")

    def test_list_items_passed_as_separate_paragraphs_become_one_tight_list(self):
        self.assert_ok(
            self.commit_messages("Subject", "Intro.", f"- {LONG}", "- second", "1. third")
        )
        body = self.git("log", "-1", "--format=%b").stdout.rstrip("\n")
        intro, _, items = body.partition("\n\n")
        self.assertEqual(intro, "Intro.")
        self.assertNotIn("\n\n", items)
        self.assertTrue(items.endswith("\n- second\n1. third"), body)

    def test_amend_without_edit_keeps_formatted_message(self):
        self.assert_ok(self.commit_messages("Subject", LONG, f"- {LONG}"))
        before = self.message()
        self.assert_ok(self.commit("--amend", "--no-edit"))
        self.assertEqual(self.message(), before)

    def test_unedited_amend_of_older_message_reflows_without_rejecting(self):
        subject = "x" * 80
        self.git("config", "hook.commit-message.enabled", "false")
        self.assert_ok(self.commit("-m", subject, "-m", LONG))
        self.git("config", "--unset", "hook.commit-message.enabled")
        self.assert_ok(self.commit("--amend", "--no-edit"))
        lines = self.message().splitlines()
        self.assertEqual(lines[0], subject)
        self.assertTrue(all(len(line) <= 72 for line in lines[1:]), lines)

    def test_final_footer_block_stays_verbatim(self):
        cases = (
            "Refs: #12\nCo-authored-by: Someone <someone@example.invalid>",
            "Fixes #12\nRefs #3",
        )
        for footer in cases:
            with self.subTest(footer=footer):
                self.assert_ok(self.commit_messages("Subject", LONG, footer))
                message = self.message().rstrip("\n")
                self.assertTrue(message.endswith(f"\n\n{footer}"), message)

    def test_wrapped_lines_do_not_start_with_footer_tokens(self):
        paragraph = (
            "CodeRabbit now posts findings that fall outside the diff inside a caution callout,"
            " one collapsed block per finding. The sanitizer dropped them: the summary regex"
            " did not allow the blockquote marker."
        )
        self.assert_ok(self.commit_messages("Subject", paragraph))
        body = self.git("log", "-1", "--format=%b").stdout
        self.assertEqual(" ".join(body.split()), paragraph)
        self.assertNotIn("\nthem: ", body)

    def test_code_blocks_stay_verbatim(self):
        code = "```sh\n" + "echo " + "x" * 90 + "\n```"
        self.assert_ok(self.commit_messages("Subject", code))
        self.assertIn(code, self.message())

    def test_editor_comments_and_scissors_section_are_left_for_git(self):
        edited = self.root / "edited.txt"
        edited.write_text(
            f"Subject\n\n{LONG}\n\n# a comment line\n"
            "# ------------------------ >8 ------------------------\n"
            f"{LONG}\n"
        )
        self.env["GIT_EDITOR"] = f"cp {shlex.quote(str(edited))}"
        self.assert_ok(self.commit("--verbose"))
        message = self.message()
        self.assertNotIn("# a comment", message)
        self.assertEqual(message.count("seventy-two"), 1)
        self.assertTrue(all(len(line) <= 72 for line in message.splitlines()), message)

    def test_long_subject_is_rejected_unless_derived(self):
        head = self.commit_messages("Short subject")
        self.assert_ok(head)
        rejected = self.commit_messages("x" * 80)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("exceeds 72-char limit", rejected.stderr)
        for prefix in ("fixup! ", 'Reapply "'):
            with self.subTest(prefix=prefix):
                self.assert_ok(self.commit_messages(prefix + "x" * 70))

    def test_literal_line_break_escapes_are_rejected_outside_code(self):
        rejected = self.commit_messages("Subject", "First line\\nsecond line")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("literal", rejected.stderr)
        list_texts = (
            f"- Top item\n  - Nested item. {LONG} Then an escape a\\nb follows.",
            "- Top item\n\n  - Second level\n\n    - Third level with escape a\\nb here",
            "- Top item\n  - Nested item\n\n    Second paragraph with escape a\\nb here",
        )
        for text in list_texts:
            with self.subTest(text=text):
                self.assertNotEqual(self.commit_messages("Subject", text).returncode, 0)
        self.assert_ok(self.commit_messages("Subject", "Use `printf '\\n'` here."))
        self.assert_ok(self.commit_messages("Subject", "Example:", "    printf 'a\\nb'"))

    def test_rejected_message_can_be_rerun_from_its_file(self):
        rejected = self.commit_messages("x" * 80, LONG)
        self.assertNotEqual(rejected.returncode, 0)
        message_file = Path(self.git("rev-parse", "--git-path", "COMMIT_EDITMSG").stdout.strip())
        message_file = self.repo / message_file
        self.assertIn(str(message_file.resolve()), rejected.stderr)
        message_file.write_text(message_file.read_text().replace("x" * 80, "Fixed subject", 1))
        self.assert_ok(self.git("commit", "--quiet", "-F", str(message_file), check=False))
        self.assertTrue(self.message().startswith("Fixed subject\n\nThis paragraph"))

    def test_tracked_commitlint_config_is_enforced(self):
        self.config()
        rejected = self.commit_messages("feat: wrong type")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("type-enum", rejected.stdout + rejected.stderr)
        self.assert_ok(self.commit_messages("project: permitted type"))

    def test_package_commitlint_config_is_enforced(self):
        self.config("package.json", json.dumps({"commitlint": RULES}))
        self.assertNotEqual(self.commit_messages("feat: wrong type").returncode, 0)
        self.assert_ok(self.commit_messages("project: permitted type"))

    def test_untracked_or_absent_commitlint_config_does_not_opt_in(self):
        self.config(tracked=False)
        self.config("package.yaml", "name: example\n")
        self.assert_ok(self.commit_messages("An upstream subject"))

    def test_indexed_config_missing_from_worktree_fails(self):
        config = self.config()
        self.assert_ok(self.commit_messages("project: initial"))
        config.unlink()
        rejected = self.commit_messages("project: next")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("missing from the working tree", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
