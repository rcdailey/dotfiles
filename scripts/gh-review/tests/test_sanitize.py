import textwrap
import unittest

from gh_review._sanitize import sanitize_bot_body

# Shape of a CodeRabbit quiet-mode review body: findings that were not posted inline live in
# collapsed groups next to boilerplate blocks.
QUIET_REVIEW = textwrap.dedent("""\
    > [!NOTE]
    > Quiet mode is enabled, so only the most important comments were posted inline.

    <details>
    <summary>🟡 Other comments: 1</summary><blockquote>

    <details>
    <summary>db/V1.420__views.sql: 1</summary><blockquote>

    `21-24`: **🟡 Minor**

    **Preserve legacy partner domains in the reporting view.**

    <details>
    <summary>Suggested fix</summary>

    ```diff
    +SELECT domain FROM public.partner_email_domains;
    ```

    </details>

    <details>
    <summary>🤖 Prompt for AI Agents</summary>

    Review comment at db/V1.420__views.sql
    </details>

    </blockquote></details>

    </blockquote></details>

    <details>
    <summary>🤖 Prompt to fix review comments</summary>

    Other comments: duplicated agent prompt
    </details>

    <details>
    <summary>ℹ️ Review info</summary>

    <details>
    <summary>📒 Files selected for processing: 4</summary>

    * `libs/shared/database/db.config.ts`
    </details>
    </details>
    """)

# Shape of a CodeRabbit outside-diff finding: one collapsed block per finding inside a caution
# callout, its summary ending with the file location.
OUTSIDE_DIFF_REVIEW = textwrap.dedent("""\
    > [!CAUTION]
    > Some comments are outside the diff and can't be posted inline due to GitHub limitations.
    >
    > **⚠️ Outside diff range comments (1)**
    >
    > <details>
    > <summary><strong>🟠 Major</strong> · Fix guard. · <code>guard.sh:4-9</code></summary><blockquote>
    >
    > **Match flagged and admin commands in Cursor.**
    >
    > <details>
    > <summary>🤖 Prompt for AI Agents</summary>
    >
    > Review comment at guard.sh
    > </details>
    >
    > </blockquote></details>

    <details>
    <summary>🤖 Prompt to fix review comments</summary>

    Outside diff comments: duplicated agent prompt
    </details>
    """)


class SanitizeBotBodyTest(unittest.TestCase):
    def test_keeps_coderabbit_outside_diff_findings(self) -> None:
        text = sanitize_bot_body(OUTSIDE_DIFF_REVIEW, "coderabbitai")

        self.assertIn("guard.sh:4-9", text)
        self.assertIn("Match flagged and admin commands in Cursor.", text)
        self.assertNotIn("Prompt for AI Agents", text)
        self.assertNotIn("duplicated agent prompt", text)

    def test_keeps_coderabbit_findings_grouped_in_collapsed_comment_blocks(self) -> None:
        for login in ("coderabbitai", "coderabbitai[bot]"):
            text = sanitize_bot_body(QUIET_REVIEW, login)

            self.assertIn("Other comments: 1", text)
            self.assertIn("db/V1.420__views.sql: 1", text)
            self.assertIn("`21-24`", text)
            self.assertIn("Preserve legacy partner domains in the reporting view.", text)

    def test_drops_every_collapsed_block_for_bots_without_a_policy(self) -> None:
        text = sanitize_bot_body(QUIET_REVIEW, "other-bot[bot]")

        self.assertIn("Quiet mode is enabled", text)
        self.assertNotIn("Other comments", text)
        self.assertNotIn("Preserve legacy partner domains", text)

    def test_drops_coderabbit_boilerplate_collapsed_blocks(self) -> None:
        text = sanitize_bot_body(QUIET_REVIEW, "coderabbitai")

        for noise in (
            "Suggested fix",
            "Prompt for AI Agents",
            "Prompt to fix review comments",
            "duplicated agent prompt",
            "Review info",
            "Files selected for processing",
            "db.config.ts",
        ):
            self.assertNotIn(noise, text)


if __name__ == "__main__":
    unittest.main()
