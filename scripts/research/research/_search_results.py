"""Render web search results as compact, discovery-only prose."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit

_DISCOVERY_NOTICE = "[discovery only; fetch a URL before citing it]"

# Query parameters that identify a visit or campaign, not a page.
_TRACKING_PREFIXES = ("utm_", "probe", "fbclid", "gclid", "mc_")
_TRACKING_VALUES = {"source": "post_page"}  # Medium appends ?source=post_page-----...

# Mirrors of one page (bun.sh/guides/x and bun.com/guides/x, helm.sh/fr/docs/x and
# helm.sh/docs/x) share nearly all the smaller excerpt's words even when the excerpts cover
# different slices or render code differently. Distinct pages overlap just as much (other threads,
# videos, doc versions, sibling wikis), so the identifying query and the path must also match
# (see _same_page_path); short excerpts carry too few words to judge.
_MIRROR_CONTAINMENT = 0.8
_MIRROR_MIN_WORDS = 30
_CROSS_DOMAIN_MIN_TAIL = 3
_WORD = re.compile(r"\w+")

_HTML_TAG = re.compile(r"</?[A-Za-z][^>\n]*>")
_IMAGE = re.compile(r"!\[([^\]\n]*)\]\([^)\n]*\)")
_LINK = re.compile(r"\[([^\]\n]+)\]\([^)\n]*\)")
_EMPTY_LINK = re.compile(r"\[\]\([^)\n]*\)")
_SPACES = re.compile(r"[ \t]{2,}")
# Documentation-site controls that extractors keep as text.
_CHROME = re.compile(
    r"^(?:\s*(?:copy page|copy|edit this page(?: on github)?|view as markdown|ask ai|"
    r"was this page helpful\??|skip to (?:main )?content|toggle navigation|on this page|"
    r"table of contents|share)\s*)+$",
    re.IGNORECASE,
)


def url_key(url: str) -> str:
    """Return one identity for URLs that differ only by scheme, www, case, slash, or tracking."""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    prefix = "" if scheme in ("http", "https") else f"{scheme}:"
    host = (parts.hostname or parts.netloc).lower().removeprefix("www.")
    if parts.port and (scheme, parts.port) not in (("http", 80), ("https", 443)):
        host = f"{host}:{parts.port}"
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith(_TRACKING_PREFIXES)
        and not v.startswith(_TRACKING_VALUES.get(k.lower(), "\0"))
    ]
    suffix = f"?{urlencode(sorted(query))}" if query else ""
    return f"{prefix}{host}{parts.path.rstrip('/')}{suffix}"


def clean_excerpt(text: str) -> str:
    """Strip markup noise while keeping link text, line structure, and code blocks intact."""
    lines: list[str] = []
    in_code = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            lines.append(line.rstrip())
            continue
        if in_code:
            lines.append(line.rstrip())
            continue
        indent = line[: len(line) - len(line.lstrip())]
        line = _EMPTY_LINK.sub("", line)
        line = _IMAGE.sub(r"\1", line)
        line = _LINK.sub(r"\1", line)
        line = _HTML_TAG.sub("", line)
        line = _SPACES.sub(" ", line).strip()
        if _CHROME.match(line):
            continue
        line = f"{indent}{line}" if line else ""
        if line or (lines and lines[-1]):
            lines.append(line)
    return "\n".join(lines).strip()


# A path segment that names a release or channel marks a different version of a page.
_VERSION = re.compile(
    r"^(?:v?\d+(?:[.\-_]\d+)*(?:\.x)?|latest|stable|current|main|master|dev|next|nightly|preview)$"
)

_Page = tuple[str, tuple[str, ...], str, set[str]]


def _page(url: str, words: set[str]) -> _Page:
    """Return a result's host, path segments, identifying query, and excerpt words."""
    host, _, rest = url_key(url).partition("/")
    path, _, query = rest.partition("?")
    segments = tuple(s for s in path.lower().split("/") if s)
    return host, segments, query, words


def _same_page_path(a: _Page, b: _Page) -> bool:
    """Return whether two results' hosts and paths can name one page.

    One path may end with the other after extra leading segments (a locale or docs prefix) that
    name no version. Across domains that needs a shared tail of at least three segments
    (bun.sh/guides/test/x and bun.com/docs/guides/test/x), since short tails such as
    owner/repo recur on unrelated platforms; otherwise the paths must match exactly. Sibling
    subdomains of one domain (fandom wikis, versioned docs hosts) are always different sites.
    """
    host_a, host_b = (p[0].rsplit(":", 1)[0] for p in (a, b))
    shorter, longer = sorted((a[1], b[1]), key=len)
    if not shorter:
        return False
    if host_a != host_b:
        if host_a.split(".")[-2:] == host_b.split(".")[-2:]:
            return False
        if shorter != longer and len(shorter) < _CROSS_DOMAIN_MIN_TAIL:
            return False
    extra = longer[: len(longer) - len(shorter)]
    return longer[len(extra) :] == shorter and not any(_VERSION.match(s) for s in extra)


def _is_mirror(page: _Page, earlier: list[_Page]) -> bool:
    words = page[3]
    if len(words) < _MIRROR_MIN_WORDS:
        return False
    return any(
        other[2] == page[2]
        and _same_page_path(page, other)
        and len(other[3]) >= _MIRROR_MIN_WORDS
        and len(words & other[3]) / min(len(words), len(other[3])) >= _MIRROR_CONTAINMENT
        for other in earlier
    )


def _fit(content: str, limit: int) -> str:
    """Cut to `limit` characters and close any code block left open.

    Provider excerpts are themselves slices of pages, so a fence can be open before any cut.
    """
    truncated = len(content) > limit
    text = content[:limit].rstrip() if truncated else content
    if sum(1 for line in text.splitlines() if line.lstrip().startswith("```")) % 2:
        text += "\n```"
    return f"{text}\n[...]" if truncated else text


def format_search_results(results: list[dict], char_budget: int) -> str:
    """Format `title`/`url`/`content`/`published` results as numbered prose.

    Keeps one result per page: repeated URLs and mirrors (same path tail and query, nearly the
    same words) are hidden. Excerpts share `char_budget` evenly, so every search route returns a similar amount
    of text.
    """
    kept: list[tuple[dict, str]] = []
    seen_urls: set[str] = set()
    seen_pages: list[_Page] = []
    hidden = 0
    for r in results:
        content = clean_excerpt(r.get("content") or "")
        page = _page(r["url"], set(_WORD.findall(content.lower())))
        key = url_key(r["url"])
        if key in seen_urls or _is_mirror(page, seen_pages):
            hidden += 1
            continue
        seen_urls.add(key)
        seen_pages.append(page)
        kept.append((r, content))

    share = char_budget // max(len(kept), 1)
    blocks: list[str] = []
    for i, (r, content) in enumerate(kept, 1):
        content = _fit(content, share)
        published = f" ({r['published']})" if r.get("published") else ""
        body = "\n".join(f"   {line}" if line else "" for line in content.splitlines())
        blocks.append(
            f"{i}. {r.get('title') or 'Untitled'}{published}\n   Discovered: {r['url']}\n{body}"
        )
    output = "\n\n".join(blocks) if blocks else "[no results]"
    if hidden:
        output += f"\n\n[{hidden} duplicate or mirrored results hidden]"
    return f"{_DISCOVERY_NOTICE}\n\n{output}"
