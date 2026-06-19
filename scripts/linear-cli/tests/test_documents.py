"""Tests for the documents commands."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from linear_cli.cli import cli


def _doc_node(
    doc_id: str = "doc-uuid-1",
    title: str = "Design Doc",
    project_name: str | None = "Alpha",
    updated_at: str = "2026-06-01T00:00:00Z",
) -> dict:
    return {
        "id": doc_id,
        "title": title,
        "updatedAt": updated_at,
        "project": {"name": project_name} if project_name else None,
    }


def _doc_detail_node(
    doc_id: str = "doc-uuid-1",
    title: str = "Design Doc",
    content: str = "# Overview\n\nDetails here.",
    project_name: str | None = "Alpha",
) -> dict:
    return {
        "id": doc_id,
        "title": title,
        "content": content,
        "updatedAt": "2026-06-01T00:00:00Z",
        "project": {"name": project_name} if project_name else None,
        "creator": {"name": "Alice"},
    }


def test_documents_list_shows_titles():
    with patch(
        "linear_cli.documents.execute",
        return_value={"documents": {"nodes": [_doc_node()]}},
    ):
        result = CliRunner().invoke(cli, ["documents", "list"])

    assert result.exit_code == 0
    assert "Design Doc" in result.output
    assert "Alpha" in result.output


def test_documents_list_empty():
    with patch(
        "linear_cli.documents.execute",
        return_value={"documents": {"nodes": []}},
    ):
        result = CliRunner().invoke(cli, ["documents", "list"])

    assert result.exit_code == 0
    assert "no documents found" in result.output


def test_documents_list_filter_by_project():
    nodes = [
        _doc_node(doc_id="d1", title="Doc A", project_name="Alpha"),
        _doc_node(doc_id="d2", title="Doc B", project_name="Beta"),
    ]
    with patch(
        "linear_cli.documents.execute",
        return_value={"documents": {"nodes": nodes}},
    ):
        result = CliRunner().invoke(cli, ["documents", "list", "--project", "Alpha"])

    assert result.exit_code == 0
    assert "Doc A" in result.output
    assert "Doc B" not in result.output


def test_documents_view_shows_content():
    with patch(
        "linear_cli.documents.execute",
        return_value={"document": _doc_detail_node()},
    ):
        result = CliRunner().invoke(cli, ["documents", "view", "doc-uuid-1"])

    assert result.exit_code == 0
    assert "Design Doc" in result.output
    assert "Alice" in result.output
    assert "# Overview" in result.output


def test_documents_view_not_found():
    with patch(
        "linear_cli.documents.execute",
        return_value={"document": None},
    ):
        result = CliRunner().invoke(cli, ["documents", "view", "doc-uuid-999"])

    assert result.exit_code != 0
