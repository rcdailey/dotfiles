#!/usr/bin/env bash

set -euo pipefail

readonly package_id="io.github.akitaonrails.ai-usagebar"

if command -v busctl >/dev/null 2>&1; then
  plasma_script="$(cat <<EOF
var ps = panels();
for (var i = 0; i < ps.length; i++) {
    var widgets = ps[i].widgets("$package_id");
    for (var j = 0; j < widgets.length; j++) widgets[j].remove();
}
EOF
)"
  busctl --user call org.kde.plasmashell /PlasmaShell \
    org.kde.PlasmaShell evaluateScript s "$plasma_script" >/dev/null || true
fi

if command -v kpackagetool6 >/dev/null 2>&1 && \
  kpackagetool6 --type Plasma/Applet --list | rg -Fxq "$package_id"; then
  kpackagetool6 --type Plasma/Applet --remove "$package_id"
fi

rm -rf "${XDG_STATE_HOME:-$HOME/.local/state}/ai-usagebar"

if command -v mise >/dev/null 2>&1; then
  mise uninstall --all --yes github:akitaonrails/ai-usagebar || true
fi
