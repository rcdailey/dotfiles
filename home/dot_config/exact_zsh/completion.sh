# Zsh completion settings
# Note: Zinit plugins handle most completions automatically

# Initialize zsh completion system
autoload -Uz compinit
compinit

# Completion options
zstyle ':completion:*' menu select
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'

# Custom completions (if needed)
# Add any project-specific completions here
