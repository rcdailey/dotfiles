# Environment variables and exports (console-output safe for instant prompt)

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

[[ "$TERM_PROGRAM" == "vscode" ]] && . "$(code --locate-shell-integration-path zsh)"

# Enable extended globbing for zsh (globstar is enabled by default in zsh)
# Extended globbing provides advanced pattern matching features
setopt EXTENDED_GLOB

# History settings (zsh-specific, removed bash cruft)
export HISTSIZE=10000
export SAVEHIST=10000
export HISTFILE=~/.zsh_history

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

# Homebrew - disable new casks/formula messages and analytics
export HOMEBREW_NO_ANALYTICS=1
export HOMEBREW_BOOTSNAP=1
export HOMEBREW_NO_ENV_HINTS=1
export HOMEBREW_NO_UPDATE_REPORT_FORMULAE=1
export HOMEBREW_NO_UPDATE_REPORT_CASKS=1

# In some cases TMPDIR is not defined, such as VS Code integrated terminal on Windows
if [[ -z "$TMPDIR" ]]; then
    export TMPDIR=/tmp
fi
