"""Exercise commit save with real Git and commitlint.

Run with python -m unittest discover -s tests/commit.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

COMMIT = Path(__file__).resolve().parents[2] / "home/dot_local/bin/executable_commit"
RULES = {
    "rules": {
        "type-enum": [2, "always", ["project"]],
        "type-empty": [2, "never"],
    }
}


class CommitSaveTests(unittest.TestCase):
    def setUp(self):
        for tool in ("git", "commitlint", "yq"):
            self.assertIsNotNone(shutil.which(tool), f"required tool missing: {tool}")
        self.temp = tempfile.TemporaryDirectory(prefix="commit-save-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repository with spaces"
        self.repo.mkdir()
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(
            {
                "HOME": str(self.root),
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "MISE_TRUSTED_CONFIG_PATHS": str(self.root),
            }
        )
        self.git("init", "--quiet")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgSign", "false")
        self.change = self.repo / "change.txt"

    def git(self, *args, check=True):
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            env=self.env,
            text=True,
            capture_output=True,
            check=check,
        )

    def config(self, name=".commitlintrc.json", content=None, tracked=True):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(RULES) if content is None else content)
        if tracked:
            self.git("add", "--", name)
        return path

    def save(self, subject, *files):
        return subprocess.run(
            [sys.executable, str(COMMIT), "save", *files, "-s", subject],
            cwd=self.repo,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_change(self):
        self.change.write_text("content\n")

    def assert_committed(self, subject):
        self.assertEqual(
            self.git("log", "-1", "--format=%s").stdout.strip(),
            subject,
        )

    def test_no_config_allows_repository_documented_subject(self):
        (self.root / ".commitlintrc.json").write_text(json.dumps(RULES))
        global_config = self.root / ".config/commitlint/config.json"
        global_config.parent.mkdir(parents=True)
        global_config.write_text(json.dumps(RULES))
        self.write_change()
        result = self.save("An upstream subject", "change.txt")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_committed("An upstream subject")

    def test_newly_staged_config_enforces_its_policy(self):
        self.write_change()
        self.config()
        result = self.save("feat: wrong project type", "change.txt", ".commitlintrc.json")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("type-enum", result.stdout + result.stderr)
        self.assertEqual(
            self.git("diff", "--cached", "--name-only").stdout.splitlines(),
            [".commitlintrc.json", "change.txt"],
        )
        result = self.save("project: permitted type", "change.txt", ".commitlintrc.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_committed("project: permitted type")

    def test_untracked_nested_and_backup_configs_do_not_opt_in(self):
        self.write_change()
        self.config(tracked=False)
        self.config("nested/commitlint.config.mjs", "throw Error('must not load');")
        self.config(".commitlintrc.json.backup")
        result = self.save(
            "An upstream subject",
            "change.txt",
            "nested/commitlint.config.mjs",
            ".commitlintrc.json.backup",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_package_configs_are_enforced(self):
        formats = (
            ("package.json", json.dumps({"commitlint": RULES})),
            ("package.yaml", "commitlint:\n  rules:\n    type-enum: [2, always, [project]]\n"),
        )
        for index, (name, content) in enumerate(formats):
            with self.subTest(name=name):
                self.change.write_text(f"content {index}\n")
                package = self.config(name, content)
                result = self.save("feat: wrong project type", "change.txt", package.name)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                result = self.save("project: permitted type", "change.txt", package.name)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                package.unlink()
                self.change.write_text(f"removed {index}\n")
                result = self.save("Remove package config", "change.txt", package.name)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_all_standalone_config_formats_are_enforced(self):
        formats = {
            ".commitlintrc": json.dumps(RULES),
            ".commitlintrc.json": json.dumps(RULES),
            ".commitlintrc.yaml": "rules:\n  type-empty: [2, never]\n",
            ".commitlintrc.yml": "rules:\n  type-empty: [2, never]\n",
        }
        for prefix in (".commitlintrc", "commitlint.config"):
            for extension in ("js", "cjs", "mjs", "ts", "cts", "mts"):
                export = "module.exports = " if extension in ("js", "cjs") else "export default "
                formats[f"{prefix}.{extension}"] = export + json.dumps(RULES) + ";\n"

        for index, (name, content) in enumerate(formats.items()):
            with self.subTest(name=name):
                self.change.write_text(f"content {index}\n")
                config = self.config(name, content)
                result = self.save("An upstream subject", "change.txt", config.name)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                result = self.save("project: permitted type", "change.txt", config.name)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                config.unlink()
                self.change.write_text(f"removed {index}\n")
                result = self.save("Remove test config", "change.txt", config.name)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_package_without_commitlint_does_not_opt_in(self):
        self.write_change()
        package = self.config("package.yaml", "name: example\n")
        result = self.save("An upstream subject", "change.txt", package.name)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_invalid_config_fails_without_fallback(self):
        self.write_change()
        self.config(content="{}")
        result = self.save("project: permitted type", "change.txt", ".commitlintrc.json")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.git("rev-list", "--count", "HEAD", check=False).returncode, 128)

    def test_indexed_config_missing_from_worktree_fails(self):
        self.write_change()
        config = self.config()
        result = self.save("project: initial", "change.txt", config.name)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        config.unlink()
        self.change.write_text("updated\n")
        result = self.save("An upstream subject", "change.txt")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("missing from the working tree", result.stderr)
        self.assertEqual(self.git("rev-list", "--count", "HEAD").stdout.strip(), "1")

    def test_all_git_hooks_are_bypassed(self):
        hooks = self.repo / "project-hooks"
        hooks.mkdir()
        marker = self.repo / "hook-ran"
        for hook_name in (
            "pre-commit",
            "prepare-commit-msg",
            "commit-msg",
            "post-commit",
        ):
            hook = hooks / hook_name
            hook.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 99\n')
            hook.chmod(0o755)
        self.git("config", "core.hooksPath", str(hooks))
        self.write_change()
        result = self.save("An upstream subject", "change.txt")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(marker.exists())
        self.assert_committed("An upstream subject")


if __name__ == "__main__":
    unittest.main()
