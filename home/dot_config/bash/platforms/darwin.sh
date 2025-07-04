# macOS-specific configurations

# Disable macOS zsh migration warning
export BASH_SILENCE_DEPRECATION_WARNING=1

# Enable color support
export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad

# Homebrew initialization
eval "$(/opt/homebrew/bin/brew shellenv)"
source "`brew --prefix git`/etc/bash_completion.d/git-prompt.sh"
source "`brew --prefix git`/etc/bash_completion.d/git-completion.bash"
export PATH="/opt/homebrew/opt/python/libexec/bin:$PATH"

# Bash completion
if [ -r "/opt/homebrew/etc/profile.d/bash_completion.sh" ]; then
    . "/opt/homebrew/etc/profile.d/bash_completion.sh"
fi

# ls function for aliases
myls() { gls -hF --color "$@"; }

# This is to support the migration to k8s in the nezuko repository
export DOCKER_DATA_PATH="/Volumes/docker"
