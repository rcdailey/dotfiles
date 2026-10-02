"""Reddit thread retrieval: the Arctic Shift archive API first, reddit.com endpoints as fallback.

Reddit's own routes are hostile to unauthenticated clients: old.reddit.com redirects to a login
wall, the .json API returns 403, and new-style thread pages are JavaScript shells. Arctic Shift
archives posts and comments within minutes of creation and serves them as JSON.
"""

from __future__ import annotations

import json
import re
import time
from urllib.parse import urlparse

import click
from lxml import etree
from lxml import html as lxml_html

from research._fetch import FetchError, fetch_response

_REDDIT_HOSTS = (
    "www.reddit.com",
    "reddit.com",
    "old.reddit.com",
    "new.reddit.com",
    "np.reddit.com",
)
_THREAD_PATH_RE = re.compile(r"^/r/([^/]+)/comments/([a-z0-9]+)", re.IGNORECASE)
_ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
_ARCTIC_SHIFT_API = "https://arctic-shift.photon-reddit.com/api"


def reddit_thread(url: str) -> tuple[str, str] | None:
    """Return (subreddit, post id) when the URL points at a Reddit thread."""
    parsed = urlparse(url)
    if parsed.hostname not in _REDDIT_HOSTS:
        return None
    match = _THREAD_PATH_RE.match(parsed.path)
    return (match.group(1), match.group(2).lower()) if match else None


def fetch_thread(subreddit: str, post_id: str) -> str:
    """Render a thread as markdown; raises FetchError when no source returns it."""
    try:
        return _fetch_arctic_shift_thread(subreddit, post_id)
    except FetchError as e:
        click.echo(f"[Arctic Shift failed: {e}; falling back to reddit.com]", err=True)
    try:
        return _fetch_reddit_thread(subreddit, post_id)
    except etree.XMLSyntaxError as e:
        raise FetchError(f"no content extracted: {e}") from e


def _render_comment(author: str, score: object, date: str, body: str, depth: int) -> str:
    """Render one comment as markdown, nesting replies as one blockquote level per depth."""
    prefix = "> " * depth
    text = f"**u/{author}** (score {score}, {date})\n\n{body.strip()}"
    return "\n".join(f"{prefix}{line}".rstrip() for line in text.splitlines())


def _comments_section(rendered: list[str]) -> str:
    if not rendered:
        return "## Comments\n\nNo comments loaded."
    return "## Comments\n\n" + "\n\n".join(rendered)


def _utc_date(timestamp: object) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(float(timestamp or 0)))


def _arctic_shift_json(path: str) -> list:
    response = fetch_response(f"{_ARCTIC_SHIFT_API}{path}")
    try:
        data = json.loads(response.text).get("data")
    except (json.JSONDecodeError, AttributeError) as e:
        raise FetchError(f"Arctic Shift returned invalid JSON: {e}") from e
    return data if isinstance(data, list) else []


def _arctic_shift_comments(children: list, depth: int, rendered: list[str]) -> None:
    """Flatten a Reddit-style comment listing depth-first; collapsed "more" stubs are skipped."""
    for child in children:
        if child.get("kind") != "t1":
            continue
        comment = child.get("data", {})
        rendered.append(
            _render_comment(
                comment.get("author", "[deleted]"),
                comment.get("score", "?"),
                _utc_date(comment.get("created_utc")),
                comment.get("body", ""),
                depth,
            )
        )
        replies = comment.get("replies")
        if isinstance(replies, dict):
            _arctic_shift_comments(replies.get("data", {}).get("children", []), depth + 1, rendered)


def _fetch_arctic_shift_thread(subreddit: str, post_id: str) -> str:
    """Render a thread from the Arctic Shift archive; raises FetchError when it is not archived."""
    posts = _arctic_shift_json(f"/posts/ids?ids={post_id}")
    if not posts:
        raise FetchError("thread not in Arctic Shift archive")
    post = posts[0]
    parts = [
        f"# {post.get('title', '').strip()}",
        (
            f"r/{post.get('subreddit', subreddit)} | u/{post.get('author', '[deleted]')} | "
            f"{_utc_date(post.get('created_utc'))} | score {post.get('score', '?')} | "
            f"{post.get('num_comments', '?')} comments | source: Arctic Shift archive"
        ),
    ]
    if not post.get("is_self", True) and post.get("url"):
        parts.append(f"Link: {post['url']}")
    if post.get("selftext", "").strip():
        parts.append(post["selftext"].strip())
    rendered: list[str] = []
    _arctic_shift_comments(
        _arctic_shift_json(f"/comments/tree?link_id={post_id}&limit=9999"), 0, rendered
    )
    return "\n\n".join(parts) + f"\n\n---\n\n{_comments_section(rendered)}"


def _fetch_reddit_thread(subreddit: str, post_id: str) -> str:
    """Fetch a thread from the reddit.com endpoints that still serve it without a login.

    The post comes from the thread's Atom feed, which allows about one request per minute, and
    the comments from the web client's comment partial.
    """
    try:
        post = _reddit_post(subreddit, post_id)
    except FetchError as e:
        post = f"[post body unavailable: {e}]"
    return f"{post}\n\n---\n\n{_reddit_comments(subreddit, post_id)}"


def _block_text(element: lxml_html.HtmlElement) -> str:
    """Join an element's top-level blocks (paragraphs, lists, quotes) with blank lines."""
    for embedded in element.xpath(".//script | .//style"):
        embedded.drop_tree()
    blocks = [child.text_content() for child in element if isinstance(child.tag, str)]
    text = "\n\n".join(_strip_lines(block) for block in blocks if block.strip())
    return text or _strip_lines(element.text_content())


def _strip_lines(text: str) -> str:
    """Drop source-formatting indentation, which markdown would render as code blocks."""
    return "\n".join(line.strip() for line in text.strip().splitlines())


def _reddit_post(subreddit: str, post_id: str) -> str:
    """Render a thread's title and body from its Atom feed, whose first entry is the post."""
    feed = fetch_response(f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/.rss")
    root = etree.fromstring(feed.content)
    post = root.find("atom:entry", _ATOM_NS)
    if post is None:
        raise FetchError("no content extracted: thread feed has no entries")
    title = post.findtext("atom:title", "", _ATOM_NS).strip()
    author = post.findtext("atom:author/atom:name", "", _ATOM_NS).strip()
    published = post.findtext("atom:published", "", _ATOM_NS).strip()
    parts = [f"# {title}", f"r/{subreddit} | {author} | {published}"]
    content = post.findtext("atom:content", "", _ATOM_NS)
    if content.strip():
        wrapper = lxml_html.fragment_fromstring(content, create_parent="div")
        # The feed appends a "submitted by ... [link] [comments]" trailer after the post body.
        body = wrapper.find(".//div[@class='md']")
        parts.append(_block_text(body if body is not None else wrapper))
    return "\n\n".join(parts)


def _reddit_comments(subreddit: str, post_id: str) -> str:
    """Render the comment tree that Reddit's web client loads, nesting replies as quotes.

    Reddit serves only the first batch of comments here; deeper "more replies" stay unloaded.
    """
    response = fetch_response(
        f"https://www.reddit.com/svc/shreddit/comments/r/{subreddit}/t3_{post_id}"
    )
    tree = lxml_html.fromstring(response.text)
    rendered: list[str] = []
    for comment in tree.xpath("//shreddit-comment"):
        thing_id = comment.get("thingid", "")
        bodies = comment.xpath(f'.//div[@id="{thing_id}-comment-rtjson-content"]')
        if not bodies:
            continue
        rendered.append(
            _render_comment(
                comment.get("author", "[deleted]"),
                comment.get("score", "?"),
                comment.get("created", "")[:10],
                _block_text(bodies[0]),
                int(comment.get("depth", "0")),
            )
        )
    return _comments_section(rendered)
