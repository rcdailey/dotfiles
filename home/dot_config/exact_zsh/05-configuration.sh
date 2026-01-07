# Aliases, functions, shell options, and PATH modifications
# Loaded after all plugins to ensure proper functionality

# Shell options for zsh functionality
setopt AUTO_CD           # cd by typing directory name if it's not a command
setopt HIST_VERIFY       # Show command with history expansion before running
setopt SHARE_HISTORY     # Share command history between sessions
setopt APPEND_HISTORY    # Append to history file, don't overwrite
setopt HIST_IGNORE_SPACE # Don't record commands that start with space
setopt HIST_IGNORE_DUPS  # Don't record duplicates in history
setopt CORRECT           # Spell correction for commands
setopt EXTENDED_GLOB     # Extended globbing features

# Add standard user directories to PATH (devbox doesn't include these by default)
if [ -d "$HOME/bin" ]; then
  export PATH="$HOME/bin:$PATH"
fi

if [ -d "$HOME/.local/bin" ]; then
  export PATH="$HOME/.local/bin:$PATH"
fi

# Append additional directories
export PATH="$PATH:$HOME:$HOME/git-scripts"

# PATH modifications for Go tools (needed in all interactive shells)
# Add Go tools to PATH if go is installed
if command -v go >/dev/null 2>&1; then
  if [[ -z $GOPATH_CACHED ]]; then
    GOPATH_CACHED="$(go env GOPATH 2>/dev/null)" || GOPATH_CACHED="$HOME/go"
    export GOPATH_CACHED
  fi
  export PATH="$GOPATH_CACHED/bin:$PATH"
fi

# .NET tools PATH
if [ -d "$HOME/.dotnet/tools" ]; then
  export PATH="$HOME/.dotnet/tools:$PATH"
fi

# Kitty terminal (installed via official installer to ~/.local/kitty.app)
if [ -d "$HOME/.local/kitty.app/bin" ]; then
  export PATH="$HOME/.local/kitty.app/bin:$PATH"
fi

# opencode CLI
if [ -d "$HOME/.opencode/bin" ]; then
  export PATH="$HOME/.opencode/bin:$PATH"
fi

# Cross-platform ls replacement with lsd
unalias ls ll 2>/dev/null
if (( $+commands[lsd] )); then
    alias ls='lsd --color=auto --icon=auto --group-directories-first'
    alias ll='lsd -la --color=auto --icon=auto --group-directories-first --header'
else
    alias ls='ls -hF'
    alias ll='ls -lahF'
fi

# Essential tool aliases
alias c="docker compose"
alias cm="chezmoi"
alias lg="lazygit"
alias oc="opencode"
alias tf="terraform"
alias pc="pre-commit"
alias pcr="pre-commit run"
alias pcra="pre-commit run --all-files"

# Git with noglob to handle refspec characters (^, @, ~)
alias git='noglob git'

# Kubernetes aliases (k alias provided by kubectl plugin, but keeping kz)
alias kz="kubectl kustomize"

# kubectl krew plugin manager PATH
export PATH="${KREW_ROOT:-$HOME/.krew}/bin:$PATH"

# Terminal utilities
alias cls="clear && clear"
alias reload='exec zsh'
alias reload-all='kitty @ send-text --match all "exec zsh\n"'
alias keygen-ed25519="ssh-keygen -t ed25519 -a 100 -P ''"

# Platform-specific aliases (Windows/WSL)
alias npp="notepad++ -multiInst -nosession -noPlugin"
alias paste="cat /dev/clipboard"

# Directory navigation (optional with zsh AUTO_CD feature)
alias 1..='cd ..'
alias 2..='cd ../..'
alias 3..='cd ../../..'
alias 4..='cd ../../../..'
alias 5..='cd ../../../../..'
alias 6..='cd ../../../../../..'
alias 7..='cd ../../../../../../..'
alias 8..='cd ../../../../../../../..'

# Enhanced tree command
alias tree='tree -Csu'

# chezmoi git shortcuts
alias cmci='chezmoi git -- caa'
alias cmst='chezmoi git -- st'

# Custom functions are autoloaded via .zshenv for all shell types

# mise activation - suppress initial cleanup errors from mise's activation script
# mise unconditionally tries to unset functions/arrays that don't exist yet
if command -v mise >/dev/null 2>&1; then
    eval "$(mise activate zsh)" 2>/dev/null
fi

# History substring search bindings moved to 04-plugins.sh atload hook
# to ensure they're set AFTER zsh-autosuggestions loads (prevents overwrite)

# Key bindings for HOME and END keys
bindkey '^[[H' beginning-of-line  # Standard ANSI HOME
bindkey '^[[F' end-of-line        # Standard ANSI END
bindkey '^[[1~' beginning-of-line # Alternative HOME sequence
bindkey '^[[4~' end-of-line       # Alternative END sequence
bindkey '^[OH' beginning-of-line  # GNOME Terminal / JetBrains IDE HOME
bindkey '^[OF' end-of-line        # GNOME Terminal / JetBrains IDE END

# Key binding for DEL key (forward delete)
bindkey '^[[3~' delete-char       # DEL key deletes character under cursor

# fzf-tab configuration
zstyle ':completion:*' menu no
zstyle ':completion:*:npm:*' sort false

# Terraform completion setup (uses terraform's native bash completion via bashcompinit)
if (( $+commands[terraform] )); then
  complete -o nospace -C terraform terraform
  # Enable completion for tf alias
  complete -o nospace -C terraform tf
fi
