#!/usr/bin/env bash
set -euo pipefail

# Test the install script in a container
# Usage: ./test.sh [os]
#   os: fedora (default), ubuntu (future)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OS="${1:-fedora}"

cd "$SCRIPT_DIR"
docker compose run --rm "$OS"
