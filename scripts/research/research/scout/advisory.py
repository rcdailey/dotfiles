"""Security advisories from the global GitHub Advisory Database."""

from __future__ import annotations

import re

import click

from research._ghapi import APIError, advisories
from research._render import DEFAULT_MAX_CHARS, kv_line, section_heading, truncate_output
from research._source_ledger import record_visible_sources
from research.scout import cli
from research.scout._common import die

_ADVISORY_ID = re.compile(r"(GHSA(-[23456789cfghjmpqrvwx]{4}){3}|CVE-\d{4}-\d{4,})", re.IGNORECASE)


def _affected(vulnerability: dict) -> str:
    package = vulnerability.get("package") or {}
    line = (
        f"{package.get('ecosystem', '?')} {package.get('name', '?')}: vulnerable "
        f"{vulnerability.get('vulnerable_version_range') or 'unknown range'}; first patched "
        f"{vulnerability.get('first_patched_version') or 'none'}"
    )
    functions = vulnerability.get("vulnerable_functions") or []
    if functions:
        line += f"; vulnerable functions {', '.join(functions)}"
    return f"- {line}"


def _render(entry: dict) -> str:
    cve = entry.get("cve_id")
    title = entry["ghsa_id"] + (f" ({cve})" if cve else "")
    lines = [section_heading(title), entry.get("summary", "")]
    lines.append(kv_line("Severity", entry.get("severity", "unknown")))
    for version in ("cvss_v4", "cvss_v3"):
        cvss = (entry.get("cvss_severities") or {}).get(version) or {}
        if cvss.get("score"):
            lines.append(kv_line(version.upper(), f"{cvss['score']} {cvss.get('vector_string')}"))
            break
    epss = entry.get("epss") or {}
    if epss.get("percentage") is not None:
        lines.append(kv_line("EPSS", f"{epss['percentage']} (percentile {epss['percentile']})"))
    cwes = [c["cwe_id"] for c in entry.get("cwes") or []]
    if cwes:
        lines.append(kv_line("CWEs", ", ".join(cwes)))
    lines.append(kv_line("Type", entry.get("type", "unknown")))
    lines.append(kv_line("Published", (entry.get("published_at") or "unknown")[:10]))
    if entry.get("withdrawn_at"):
        lines.append(kv_line("Withdrawn", entry["withdrawn_at"][:10]))
    if entry.get("source_code_location"):
        lines.append(kv_line("Source code", entry["source_code_location"]))
    lines.append(kv_line("Source", entry["html_url"]))
    lines.append(section_heading("Affected packages"))
    lines.extend(_affected(v) for v in entry.get("vulnerabilities") or [])
    lines.append(section_heading("Description"))
    lines.append(entry.get("description") or "none")
    references = entry.get("references") or []
    if references:
        lines.append(section_heading("References"))
        lines.extend(f"- {url}" for url in references)
    return "\n".join(lines)


@cli.command()
@click.argument("advisory_id")
@click.option("--max-chars", type=click.IntRange(min=0), default=DEFAULT_MAX_CHARS)
def advisory(advisory_id: str, max_chars: int) -> None:
    """View a GitHub security advisory by GHSA or CVE ID."""
    if not _ADVISORY_ID.fullmatch(advisory_id):
        raise click.UsageError(f"not a GHSA or CVE ID: {advisory_id}")
    try:
        entries = advisories(advisory_id)
    except APIError as e:
        die(str(e))
    if not entries:
        click.echo(f"No GitHub advisory found for {advisory_id}")
        return
    rendered = truncate_output(
        "\n".join(_render(entry) for entry in entries),
        max_chars,
        "fetch a listed reference for narrower evidence",
    )
    record_visible_sources(rendered, [entry["html_url"] for entry in entries])
    click.echo(rendered)
