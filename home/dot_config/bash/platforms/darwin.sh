# macOS-specific configurations

# Enable color support
export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad

# Homebrew initialization
eval "$(/opt/homebrew/bin/brew shellenv)"
source "`brew --prefix git`/etc/bash_completion.d/git-prompt.sh"
source "`brew --prefix git`/etc/bash_completion.d/git-completion.bash"
export PATH="/opt/homebrew/opt/python/libexec/bin:$PATH"

# GNU tools if available
if command -v gls &> /dev/null; then
    alias ls='gls --color=auto'
fi

# Bash completion
if [ -r "/opt/homebrew/etc/profile.d/bash_completion.sh" ]; then
    . "/opt/homebrew/etc/profile.d/bash_completion.sh"
fi

# ls function for aliases
myls() { gls -hF --color "$@"; }
