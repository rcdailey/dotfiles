"""Tests for bot detection and body sanitization."""

from gh_review.sanitize import is_bot, sanitize_bot_body, truncate_body


class TestIsBot:
    def test_github_app_bot(self):
        assert is_bot("coderabbitai[bot]") is True

    def test_another_bot(self):
        assert is_bot("renovate[bot]") is True

    def test_human(self):
        assert is_bot("rcdailey") is False

    def test_bot_substring_without_brackets(self):
        assert is_bot("botperson") is False

    def test_empty(self):
        assert is_bot("") is False

    def test_graphql_typename_bot(self):
        assert is_bot("linear", "Bot") is True

    def test_graphql_typename_user(self):
        assert is_bot("linear", "User") is False

    def test_graphql_typename_empty(self):
        assert is_bot("coderabbitai", "") is False

    def test_graphql_typename_bot_without_bracket_suffix(self):
        assert is_bot("coderabbitai", "Bot") is True


class TestSanitizeBotBody:
    def test_strips_details_blocks(self):
        body = (
            "Main finding.\n"
            "<details>\n<summary>Suggestion</summary>\n"
            "Some long suggestion content\n"
            "</details>\n"
            "After details."
        )
        result = sanitize_bot_body(body)
        assert "Suggestion" not in result
        assert "Some long suggestion" not in result
        assert "Main finding." in result
        assert "After details." in result

    def test_strips_html_comments(self):
        body = (
            "Real content.\n"
            "<!-- fingerprinting:phantom:poseidon:puma -->\n"
            "<!-- This is an auto-generated comment -->\n"
            "More content."
        )
        result = sanitize_bot_body(body)
        assert "fingerprinting" not in result
        assert "auto-generated" not in result
        assert "Real content." in result
        assert "More content." in result

    def test_strips_decorative_separators(self):
        body = "Content above\n---\nContent below"
        result = sanitize_bot_body(body)
        assert "---" not in result
        assert "Content above" in result
        assert "Content below" in result

    def test_collapses_blank_lines(self):
        body = "Line one.\n\n\n\n\nLine two."
        result = sanitize_bot_body(body)
        assert "\n\n\n" not in result
        assert "Line one." in result
        assert "Line two." in result

    def test_strips_nested_details(self):
        body = (
            "Finding.\n"
            "<details>\n<summary>Outer</summary>\n"
            "<details><summary>Inner</summary>Nested</details>\n"
            "</details>"
        )
        result = sanitize_bot_body(body)
        assert "Outer" not in result
        assert "Inner" not in result
        assert "Finding." in result

    def test_preserves_plain_content(self):
        body = "This is a normal review comment with no HTML."
        result = sanitize_bot_body(body)
        assert result == body

    def test_multiline_html_comment(self):
        body = "Before.\n<!--\n  multi-line\n  comment block\n-->\nAfter."
        result = sanitize_bot_body(body)
        assert "multi-line" not in result
        assert "Before." in result
        assert "After." in result

    def test_strips_html_tables(self):
        body = (
            "Deploy successful!\n"
            "<table><tr><td><strong>Status:</strong></td>"
            "<td>OK</td></tr></table>\n"
            "Done."
        )
        result = sanitize_bot_body(body)
        assert "<table" not in result
        assert "<td" not in result
        assert "Deploy successful!" in result
        assert "Done." in result

    def test_strips_mermaid_blocks(self):
        body = "## Summary\n\n```mermaid\nflowchart LR\n  A --> B\n```\n\nDetails here."
        result = sanitize_bot_body(body)
        assert "mermaid" not in result
        assert "flowchart" not in result
        assert "## Summary" in result
        assert "Details here." in result

    def test_strips_markdown_tables(self):
        body = (
            "Changes:\n\n"
            "| File | Change |\n"
            "| --- | --- |\n"
            "| foo.py | Added |\n"
            "| bar.py | Removed |\n\n"
            "Summary."
        )
        result = sanitize_bot_body(body)
        assert "| File" not in result
        assert "| foo.py" not in result
        assert "Changes:" in result
        assert "Summary." in result

    def test_strips_inline_html_keeps_text(self):
        body = "Found <strong>3 issues</strong> in <code>main.py</code>."
        result = sanitize_bot_body(body)
        assert "<strong>" not in result
        assert "<code>" not in result
        assert "3 issues" in result
        assert "main.py" in result

    def test_strips_br_tags(self):
        body = "Line one<br>Line two<br/>Line three"
        result = sanitize_bot_body(body)
        assert "<br" not in result
        assert "Line one" in result
        assert "Line two" in result

    def test_strips_badge_links(self):
        body = (
            "Status: [![Build](https://img.shields.io/badge.svg)]"
            "(https://example.com)\nReal content."
        )
        result = sanitize_bot_body(body)
        assert "img.shields.io" not in result
        assert "Real content." in result

    def test_strips_image_markdown(self):
        body = "See: ![screenshot](https://example.com/img.png)\nText."
        result = sanitize_bot_body(body)
        assert "![screenshot]" not in result
        assert "Text." in result

    def test_cloudflare_deploy_comment(self):
        """Real-world github-actions deploy comment."""
        body = (
            "Deploying with Cloudflare Pages<br>"
            "<table><tr><td><strong>Latest commit:</strong></td>"
            "<td><code>abc123</code></td></tr>"
            "<tr><td><strong>Status:</strong></td>"
            "<td>Deploy successful!</td></tr>"
            "<tr><td><strong>Preview URL:</strong></td>"
            "<td><a href='https://example.pages.dev'>"
            "https://example.pages.dev</a></td></tr></table>"
        )
        result = sanitize_bot_body(body)
        assert "<table" not in result
        assert "<strong>" not in result
        assert "Deploying with Cloudflare Pages" in result

    def test_sourcery_reviewer_guide(self):
        """Real-world sourcery-ai comment structure."""
        body = (
            "## Reviewer's Guide\n\n"
            "Summary of changes.\n\n"
            "#### Flow diagram\n\n"
            "```mermaid\nflowchart LR\n  A --> B\n```\n\n"
            "### File-Level Changes\n\n"
            "| Change | Details | Files |\n"
            "| ------ | ------- | ----- |\n"
            "| Harden workflow | Added perms | `deploy.yml` |\n\n"
            "<details>\n<summary>Tips</summary>\n"
            "Bot tips here.\n</details>"
        )
        result = sanitize_bot_body(body)
        assert "## Reviewer's Guide" in result
        assert "Summary of changes." in result
        assert "mermaid" not in result
        assert "flowchart" not in result
        assert "| Change" not in result
        assert "Tips" not in result

    def test_markdown_table_with_html_in_cells(self):
        """Table cells containing <br/> and <ul><li> tags."""
        body = (
            "### File-Level Changes\n\n"
            "| Change | Details | Files |\n"
            "| ------ | ------- | ----- |\n"
            "| Tighten perms | <ul><li>Add read-only</li>"
            "<li>Set persist-credentials</li></ul>"
            " | `a.yml`<br/>`b.yml`<br/>`c.yml` |\n\n"
            "Summary."
        )
        result = sanitize_bot_body(body)
        assert "| Tighten" not in result
        assert "| Change" not in result
        assert "<ul>" not in result
        assert "Summary." in result


class TestTruncateBody:
    def test_short_body_unchanged(self):
        assert truncate_body("hello", 500) == "hello"

    def test_exact_length_unchanged(self):
        body = "x" * 500
        assert truncate_body(body, 500) == body

    def test_long_body_truncated(self):
        body = "a" * 1000
        result = truncate_body(body, 500)
        assert result.startswith("a" * 500)
        assert "[truncated, 1000 chars]" in result

    def test_zero_max_returns_original(self):
        assert truncate_body("hello", 0) == "hello"

    def test_negative_max_returns_original(self):
        assert truncate_body("hello", -1) == "hello"
