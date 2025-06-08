#!/usr/bin/env bash

# Check if brew is available
if ! command -v brew &> /dev/null; then
  echo "Error: Homebrew is not installed or not in PATH" >&2
  exit 1
fi

brew install git-delta
