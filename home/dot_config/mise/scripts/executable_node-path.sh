#!/usr/bin/env bash
# Print a NODE_PATH covering every mise npm package installation, so npm packages installed via
# mise resolve each other. mise config reads the output through exec(), not _.source: _.source
# keeps PATH prepends from the script's bash, and BASH_ENV (~/.config/bash/env.bash) prepends the
# shims directory there, which leaked shims into interactive PATH.
node_path=
for dir in ~/.local/share/mise/installs/npm-*/*/lib/node_modules; do
  [ -d "$dir" ] && node_path="${node_path:+$node_path:}$dir"
done
printf '%s' "$node_path"
