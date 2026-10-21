#!/usr/bin/env bash
# Publish the local OpenCode service on the tailnet at https://<host>.<tailnet>.ts.net so `ocr`
# can reach it from other machines. The service keeps listening on localhost only.
# Linux needs a one-time `sudo tailscale set --operator=$USER` for non-root `tailscale serve`.
# Runs on every apply (idempotent) so a skipped machine publishes once its prerequisites are fixed.
set -uo pipefail

skip() {
  echo "tailscale-serve-opencode: skipped, $1" >&2
  exit 0
}

command -v tailscale >/dev/null || skip "tailscale not installed"
command -v opencode >/dev/null || skip "opencode not installed"
tailscale status >/dev/null 2>&1 || skip "tailscale not running"

service_url=$(opencode service status 2>/dev/null) || skip "opencode service unavailable"
[[ $service_url == http://127.0.0.1:* ]] || skip "unexpected service address: $service_url"

# Bounded so a pending HTTPS-certificate consent prompt cannot hang chezmoi apply; stock macOS
# lacks timeout, so it runs unbounded there
bounded=()
command -v timeout >/dev/null && bounded=(timeout 30)
${bounded[@]+"${bounded[@]}"} tailscale serve --bg --yes "$service_url" >/dev/null 2>&1 ||
  skip "tailscale serve failed; on Linux run: sudo tailscale set --operator=\$USER"
