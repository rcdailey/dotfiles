#!/usr/bin/env zsh

# Install packages when Brewfile changes
# Brewfile hash: {{ include "Brewfile" | sha256sum }}
# This script runs whenever the Brewfile content changes

# Check if brew is available
if ! command -v brew &>/dev/null; then
  echo "Error: Homebrew is not installed or not in PATH" >&2
  exit 1
fi

# Install all packages from Brewfile in home directory
echo "Brewfile changed, installing packages..."
brew bundle --file="$HOME/Brewfile"

echo "Package installation complete!"
