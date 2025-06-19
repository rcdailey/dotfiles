# Environment variables and exports

# Editor and paging
export EDITOR="code"
export LESS="-RSic~ -x2"
export DELTA_PAGER="less"
export PSQL_PAGER="pspg"
export LESSHISTSIZE=0
export LESSCHARSET=UTF-8

# Unset GIT_PAGER if running inside VS Code integrated terminal
# This addresses a bug where GIT_PAGER is set to `cat` by the Copilot extension.
if [ "$TERM_PROGRAM" = "vscode" ]; then
  unset GIT_PAGER
fi

[[ "$TERM_PROGRAM" == "vscode" ]] && . "$(code --locate-shell-integration-path bash)"

# Enable globstar for ** pattern matching (recursively match directories)
# Only enable if bash version 4.0 or higher (globstar was added in bash 4.0)
if [[ ${BASH_VERSINFO[0]} -ge 4 ]]; then
    shopt -s globstar
fi

# XDG Base Directory Specification - consistent across all platforms
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_DATA_HOME="$HOME/.local/share"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_STATE_HOME="$HOME/.local/state"

# History control
export HISTCONTROL=ignoreboth
export HISTSIZE=1000
export HISTFILESIZE=2000

# Development
export COLUMNS
export DOCKER_UID="$(id -u)"
export DOCKER_GID="$(id -g)"

# Terminal color support - enable 256-color and true color support across all platforms
export TERM=xterm-256color
export COLORTERM=truecolor

# Disable husky pre-commit hooks (slows down git)
export HUSKY_SKIP_HOOKS=1 # For legacy purposes
export HUSKY=0 # This replaces HUSKY_SKIP_HOOKS

# In some cases TMPDIR is not defined, such as VS Code integrated terminal on Windows
if [[ -z "$TMPDIR" ]]; then
    export TMPDIR=/tmp
fi
