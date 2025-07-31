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

# PATH modifications moved to .zprofile for performance

# Cross-platform ls replacement with eza
if (( $+commands[eza] )); then
    alias ls='eza --color=auto --icons=auto --group-directories-first'
    alias ll='eza -la --color=auto --icons=auto --group-directories-first --header'
else
    alias ls='ls -hF'
    alias ll='ls -la'
fi

# Essential tool aliases
alias c="docker compose"
alias cm="chezmoi"
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
alias keygen-ed25519="ssh-keygen -t ed25519 -a 100 -P ''"

# Platform-specific aliases (Windows/WSL)
alias npp="notepad++ -multiInst -nosession -noPlugin"
alias clip="cat > /dev/clipboard"
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

# Custom shell functions

# Git .gitignore function - simplified version matching original
function gi() {
  curl -sL "https://www.gitignore.io/api/$*"
}

# Key bindings for history substring search
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down

# Key bindings for HOME and END keys
bindkey '^[[H' beginning-of-line  # Standard ANSI HOME
bindkey '^[[F' end-of-line        # Standard ANSI END
bindkey '^[[1~' beginning-of-line # Alternative HOME sequence
bindkey '^[[4~' end-of-line       # Alternative END sequence

# Key binding for DEL key (forward delete)
bindkey '^[[3~' delete-char       # DEL key deletes character under cursor
