# Zinit plugin manager initialization
# Depends on XDG_DATA_HOME being set in .zshenv

ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"
if [[ ! -f "$ZINIT_HOME/zinit.zsh" ]]; then
  command mkdir -p "$(dirname "$ZINIT_HOME")" >/dev/null 2>&1
  command git clone https://github.com/zdharma-continuum/zinit.git "$ZINIT_HOME" >/dev/null 2>&1
fi
source "$ZINIT_HOME/zinit.zsh"
