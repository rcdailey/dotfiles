#!/usr/bin/env bash
set -euo pipefail

if ! command -v systemctl >/dev/null 2>&1; then
  exit 0
fi

systemctl --user daemon-reload
