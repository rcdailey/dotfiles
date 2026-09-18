#!/usr/bin/env bash
set -euo pipefail

if ! command -v systemctl >/dev/null 2>&1; then
  exit 0
fi

systemctl --user disable --now cleanup-orphaned-procs.timer 2>/dev/null || true
systemctl --user stop cleanup-orphaned-procs.service 2>/dev/null || true
