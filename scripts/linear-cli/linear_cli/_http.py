"""Keep-alive HTTP POST client on the standard library.

httpx cost about 45ms of import time per invocation versus about 12ms for http.client and ssl.
The CLI only POSTs JSON or form bodies to two Linear endpoints, so it does not need more.
"""

from __future__ import annotations

import http.client
import json
import zlib
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from linear_cli import __version__

TRANSPORT_ERRORS = (OSError, http.client.HTTPException)
_TIMEOUT = 15.0
_GZIP_WBITS = 16 + zlib.MAX_WBITS
_connections: dict[str, http.client.HTTPConnection] = {}


@dataclass(frozen=True)
class Response:
    """Fully read HTTP response with a decoded body."""

    status: int
    headers: http.client.HTTPMessage
    body: bytes

    def json(self) -> Any:
        """Decode the body as JSON; raises ValueError when it is not JSON."""
        return json.loads(self.body)


def post(url: str, body: bytes, headers: dict[str, str]) -> Response:
    """POST over a per-host connection reused for the life of the process.

    Raises one of TRANSPORT_ERRORS when the request cannot complete; the broken connection is
    dropped so the next call reconnects.
    """
    parts = urlsplit(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    conn = _connections.get(origin)
    if conn is None:
        conn_cls = (
            http.client.HTTPSConnection if parts.scheme == "https" else http.client.HTTPConnection
        )
        conn = _connections[origin] = conn_cls(parts.netloc, timeout=_TIMEOUT)
    target = parts.path or "/"
    if parts.query:
        target += f"?{parts.query}"
    request_headers = {
        "Accept-Encoding": "gzip",
        "User-Agent": f"linear-cli/{__version__}",
        **headers,
    }
    try:
        conn.request("POST", target, body, request_headers)
        response = conn.getresponse()
        data = response.read()
    except TRANSPORT_ERRORS:
        conn.close()
        del _connections[origin]
        raise
    if response.getheader("Content-Encoding") == "gzip":
        data = zlib.decompress(data, _GZIP_WBITS)
    return Response(response.status, response.headers, data)
