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

# Also added in .zshenv for all shells; re-prepend so macOS /etc/zprofile path_helper,
# which moves system directories first, cannot demote it
if [ -d "$HOME/.local/bin" ]; then
  export PATH="$HOME/.local/bin:$PATH"
fi

# Append additional directories
export PATH="$PATH:$HOME/git-scripts"

# Go tools; GOPATH defaults to ~/go. Skips `go env GOPATH` (~30 ms), so a GOPATH set only through
# `go env -w` is not seen.
export PATH="${GOPATH:-$HOME/go}/bin:$PATH"

# .NET tools PATH
if [ -d "$HOME/.dotnet/tools" ]; then
  export PATH="$HOME/.dotnet/tools:$PATH"
fi

# Kitty terminal (installed via official installer to ~/.local/kitty.app)
if [ -d "$HOME/.local/kitty.app/bin" ]; then
  export PATH="$HOME/.local/kitty.app/bin:$PATH"
fi

# Essential tool aliases
alias c="docker compose"
alias lg="lazygit"
alias tf="terraform"
alias pc="pre-commit"
alias pcr="pre-commit run"
alias pcra="pre-commit run --all-files"

# Git with noglob to handle refspec characters (^, @, ~)
alias git='noglob git'

# Kubernetes aliases (k alias provided by kubectl plugin, but keeping kz)
alias kz="kubectl kustomize"

# Terminal utilities
alias cls="clear && clear"
alias reload='exec zsh'
alias reload-all='kitty @ send-text --match all "exec zsh\n"'
alias keygen-ed25519="ssh-keygen -t ed25519 -a 100 -P ''"

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

# mise activation - suppress initial cleanup errors from mise's activation script
# mise unconditionally tries to unset functions/arrays that don't exist yet
if (( $+commands[mise] )); then
    eval "$(mise activate zsh)" 2>/dev/null
fi

# Cross-platform ls replacement with lsd (after mise activate: lsd is mise-managed)
unalias ls ll 2>/dev/null
if (( $+commands[lsd] )); then
    alias ls='lsd --color=auto --icon=auto --group-directories-first'
    alias ll='lsd -la --color=auto --icon=auto --group-directories-first --header'
else
    alias ls='ls -hF'
    alias ll='ls -lahF'
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

# A TUI that crashes without restoring the terminal leaves mouse tracking on, so mouse
# movement prints escape codes at the prompt. Disable tracking modes (1000/1002/1003) and
# SGR encoding (1006) before each prompt; precmd never runs while a foreground TUI owns the TTY.
_reset_mouse_tracking() { print -n '\e[?1000l\e[?1002l\e[?1003l\e[?1006l'; }
autoload -Uz add-zsh-hook
add-zsh-hook precmd _reset_mouse_tracking

# herdr scratch popup (ctrl+shift+s): Esc exits the shell, which closes the popup. Unset so
# shells started inside it keep normal Esc behavior.
if [[ -n $HERDR_SCRATCH_SHELL ]]; then
    unset HERDR_SCRATCH_SHELL
    _herdr_scratch_exit() { BUFFER=exit; zle accept-line; }
    zle -N _herdr_scratch_exit
    bindkey '^[' _herdr_scratch_exit
    # Esc also prefixes multi-key sequences, so zsh waits KEYTIMEOUT (default 0.4s) before
    # treating it as a bare Esc; 10ms still lets terminal sequences like arrows arrive whole
    KEYTIMEOUT=1
fi
