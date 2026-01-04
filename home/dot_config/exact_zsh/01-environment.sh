# Performance monitoring: Uncomment to profile startup time
# zmodload zsh/zprof  # Enable at top of .zshrc, then add 'zprof' at bottom

# Prevent duplicate entries in path arrays (idempotent for re-sourcing)
typeset -U path fpath cdpath manpath

# Environment variables and exports (console-output safe for instant prompt)
# Note: Core variables (EDITOR, TERM, HISTFILE, etc.) are now in .zshenv

# Tool-specific paging (interactive shell context)
export LESS="-RSic~ -x2"
export DELTA_PAGER="less"
export PSQL_PAGER="pspg"
export LESSHISTSIZE=0
export LESSCHARSET=UTF-8

# VS Code integration (interactive context)
# Unset GIT_PAGER if running inside VS Code integrated terminal
# This addresses a bug where GIT_PAGER is set to `cat` by the Copilot extension.
if [ "$TERM_PROGRAM" = "vscode" ]; then
  unset GIT_PAGER
fi

[[ $TERM_PROGRAM == "vscode" ]] && . "$(code --locate-shell-integration-path zsh)"

# Development tools (command substitution safe for interactive shells)
export COLUMNS
DOCKER_UID="$(id -u)"
DOCKER_GID="$(id -g)"
export DOCKER_UID DOCKER_GID

# Tool configuration (interactive context)
# Disable husky pre-commit hooks (slows down git)
export HUSKY_SKIP_HOOKS=1 # For legacy purposes
export HUSKY=0            # This replaces HUSKY_SKIP_HOOKS

export RIPGREP_CONFIG_PATH="$XDG_CONFIG_HOME/ripgrep/config"

# Claude Code MCP optimization features
# DO NOT ENABLE BOTH AT ONCE.
# See: https://github.com/anthropics/claude-code/issues/12836
export ENABLE_EXPERIMENTAL_MCP_CLI=false
export ENABLE_TOOL_SEARCH=true

# Homebrew - disable new casks/formula messages and analytics
export HOMEBREW_NO_ANALYTICS=1
export HOMEBREW_BOOTSNAP=1
export HOMEBREW_NO_ENV_HINTS=1
export HOMEBREW_NO_UPDATE_REPORT_FORMULAE=1
export HOMEBREW_NO_UPDATE_REPORT_CASKS=1

# Secrets from rbw (Bitwarden)
load_secrets() {
  export CONTEXT7_API_KEY="$(rbw get context7-api-key 2>/dev/null)"
}

if ! rbw unlocked 2>/dev/null; then
  print -P "%F{yellow}rbw locked - run 'load_secrets' after unlocking%f"
fi

load_secrets
