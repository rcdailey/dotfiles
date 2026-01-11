#!/bin/bash
# Build NODE_PATH from all mise npm package installations
# This allows npm packages installed via mise to resolve each other
for dir in ~/.local/share/mise/installs/npm-*/*/lib/node_modules; do
  [ -d "$dir" ] && NODE_PATH="${NODE_PATH:+$NODE_PATH:}$dir"
done
export NODE_PATH
