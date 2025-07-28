# macOS-specific configurations

# Enable color support
export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad

# Homebrew initialization
eval "$(/opt/homebrew/bin/brew shellenv)"
export PATH="/opt/homebrew/opt/python/libexec/bin:$PATH"

# Simplified ls setup (zsh globbing reduces need for complex aliases)
# Use GNU ls if available (installed via brew install coreutils)
if command -v gls >/dev/null 2>&1; then
    alias ls='gls -hF --color=auto'
    alias ll='gls -la --color=auto --group-directories-first'
else
    alias ls='ls -hF -G'
    alias ll='ls -la -G'
fi

# Docker configuration for specific projects
export DOCKER_DATA_PATH="/Volumes/docker"
