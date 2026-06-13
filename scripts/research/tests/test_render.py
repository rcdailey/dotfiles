"""Tests for _render.py."""

from __future__ import annotations

from research._render import (
    apply_find,
    is_github_url,
    is_pdf_url,
    strip_github_host,
    truncate_output,
)


# --- apply_find ---


def test_apply_find_substring_match() -> None:
    text = "hello world\n\nfoo bar\n\nbaz qux"
    result = apply_find(text, "foo", 0)
    assert "foo bar" in result
    assert "hello world" not in result


def test_apply_find_regex_match() -> None:
    text = "Error: something failed\n\nunrelated paragraph\n\nAnother error here"
    result = apply_find(text, r"error", 0)
    assert "Error: something failed" in result
    assert "Another error here" in result
    assert "unrelated paragraph" not in result


def test_apply_find_regex_case_insensitive() -> None:
    text = "UPPER CASE\n\nlower case\n\nMixed Case"
    result = apply_find(text, r"upper", 0)
    assert "UPPER CASE" in result
    assert "lower case" not in result


def test_apply_find_regex_pattern() -> None:
    text = "v1.2.3 released\n\nsome other text\n\nv2.0.0 released"
    result = apply_find(text, r"v\d+\.\d+\.\d+", 0)
    assert "v1.2.3 released" in result
    assert "v2.0.0 released" in result
    assert "some other text" not in result


def test_apply_find_invalid_regex_falls_back_to_substring() -> None:
    text = "foo [bar\n\nbaz"
    # "[bar" is invalid regex (unmatched bracket); should fall back to substring
    result = apply_find(text, "[bar", 0)
    assert "foo [bar" in result


def test_apply_find_no_match() -> None:
    text = "hello\n\nworld"
    result = apply_find(text, "notfound", 0)
    assert "no paragraphs matched" in result
    assert "notfound" in result


def test_apply_find_context_paragraphs() -> None:
    text = "para0\n\npara1\n\nTARGET\n\npara3\n\npara4"
    result = apply_find(text, "TARGET", 1)
    assert "para1" in result
    assert "TARGET" in result
    assert "para3" in result
    assert "para0" not in result
    assert "para4" not in result


def test_apply_find_context_clamps_at_edges() -> None:
    text = "TARGET\n\npara1\n\npara2"
    result = apply_find(text, "TARGET", 2)
    assert "TARGET" in result
    assert "para1" in result
    assert "para2" in result


# --- truncate_output ---


def test_truncate_output_no_truncation_needed() -> None:
    text = "short"
    assert truncate_output(text, 100) == text


def test_truncate_output_truncates() -> None:
    text = "a" * 200
    result = truncate_output(text, 100)
    assert len(result) > 100  # includes the truncation message
    assert "truncated at 100 chars" in result
    assert result.startswith("a" * 100)


def test_truncate_output_disabled_with_zero() -> None:
    text = "a" * 200
    result = truncate_output(text, 0)
    assert result == text


def test_truncate_output_disabled_with_negative() -> None:
    text = "a" * 200
    result = truncate_output(text, -1)
    assert result == text


# --- is_github_url ---


def test_is_github_url_true() -> None:
    assert is_github_url("https://github.com/owner/repo")
    assert is_github_url("https://www.github.com/owner/repo")
    assert is_github_url("http://github.com/owner/repo")


def test_is_github_url_false() -> None:
    assert not is_github_url("https://gitlab.com/owner/repo")
    assert not is_github_url("https://example.com")
    assert not is_github_url("not-a-url")


# --- is_pdf_url ---


def test_is_pdf_url_true() -> None:
    assert is_pdf_url("https://example.com/doc.pdf")
    assert is_pdf_url("https://example.com/doc.pdf?foo=1")
    assert is_pdf_url("https://example.com/doc.PDF")


def test_is_pdf_url_false() -> None:
    assert not is_pdf_url("https://example.com/page.html")
    assert not is_pdf_url("https://example.com/pdf-guide")


# --- strip_github_host ---


def test_strip_github_host_basic() -> None:
    assert strip_github_host("https://github.com/owner/repo") == "owner/repo"


def test_strip_github_host_with_path() -> None:
    assert strip_github_host("https://github.com/owner/repo/issues/1") == "owner/repo/issues/1"


def test_strip_github_host_strips_query() -> None:
    result = strip_github_host("https://github.com/owner/repo?tab=readme")
    assert "?" not in result
    assert result == "owner/repo"


def test_strip_github_host_non_github() -> None:
    assert strip_github_host("https://gitlab.com/owner/repo") == ""
