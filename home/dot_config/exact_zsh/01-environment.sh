# Prevent duplicate entries in path arrays
typeset -U path fpath cdpath manpath

# Output here would garble the p10k instant prompt; variables needed by every shell live in .zshenv

# GPG/pinentry TTY (use $TTY variable, not $(tty) command which fails during P10k instant prompt)
export GPG_TTY=$TTY

# Tool-specific paging (interactive shell context)
export LESS="-RSic~ -x2"
export DELTA_PAGER="less"
export PSQL_PAGER="pspg"
export LESSHISTSIZE=0
export LESSCHARSET=UTF-8

# VS Code integrated terminal: load its shell integration, and drop GIT_PAGER=cat, which the
# Copilot extension sets
if [[ $TERM_PROGRAM == vscode ]]; then
  unset GIT_PAGER
  . "$(code --locate-shell-integration-path zsh)"
fi

export DOCKER_UID=$UID DOCKER_GID=$GID

# Tool configuration (interactive context)
# Disable husky pre-commit hooks (slows down git)
export HUSKY_SKIP_HOOKS=1 # For legacy purposes
export HUSKY=0            # This replaces HUSKY_SKIP_HOOKS

export RIPGREP_CONFIG_PATH="$XDG_CONFIG_HOME/ripgrep/config"

# rumdl defaults to a .rumdl_cache directory in the working directory
export RUMDL_CACHE_DIR="$XDG_CACHE_HOME/rumdl"

# Point Terraform (and other Go net/netrc consumers) at a dedicated netrc file. Siggy (the Statsig
# CLI) hardcodes ~/.netrc and writes non-RFC keywords that break Terraform parsing.
export NETRC="$HOME/.netrc.terraform"

# zsh-autosuggestions: async fetch keeps keystrokes responsive; strategy prefers
# history over completions for faster, more relevant suggestions.
export ZSH_AUTOSUGGEST_USE_ASYNC=1
export ZSH_AUTOSUGGEST_STRATEGY=(history completion)

# Homebrew - disable new casks/formula messages and analytics
export HOMEBREW_NO_ANALYTICS=1
export HOMEBREW_BOOTSNAP=1
export HOMEBREW_NO_ENV_HINTS=1
export HOMEBREW_NO_UPDATE_REPORT_FORMULAE=1
export HOMEBREW_NO_UPDATE_REPORT_CASKS=1
# Casks with auto_updates true (Vivaldi, Docker Desktop) update themselves; --greedy still
# upgrades them on demand
export HOMEBREW_NO_UPGRADE_AUTO_UPDATES_CASKS=1

# Add standard user directories to PATH (devbox doesn't include these by default)
[[ -d "$HOME/bin" ]] && path=("$HOME/bin" $path)

# Also added in .zshenv for all shells; re-prepend so macOS /etc/zprofile path_helper, which moves
# system directories first, cannot demote it
[[ -d "$HOME/.local/bin" ]] && path=("$HOME/.local/bin" $path)

path+=("$HOME/git-scripts")

# Go tools; GOPATH defaults to ~/go. Skips `go env GOPATH` (~30 ms), so a GOPATH set only through
# `go env -w` is not seen.
path=("${GOPATH:-$HOME/go}/bin" $path)

[[ -d "$HOME/.dotnet/tools" ]] && path=("$HOME/.dotnet/tools" $path)

# Kitty terminal (installed via official installer to ~/.local/kitty.app)
[[ -d "$HOME/.local/kitty.app/bin" ]] && path=("$HOME/.local/kitty.app/bin" $path)

# mise activation, before plugins so `$+commands` checks see project tools rather than shims
# inherited from a parent shell. Its script unsets functions that do not exist yet; drop the noise.
if (( $+commands[mise] )); then
  eval "$(mise activate zsh)" 2>/dev/null
fi

# Inside herdr, worktrunk's post-switch hook opens the worktree in its own child space, so the
# calling shell stays put (wt switch --cd overrides)
[[ -n "$HERDR_ENV" ]] && export WORKTRUNK_SWITCH__CD=false
