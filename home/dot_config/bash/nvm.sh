# NVM initialization (cross-platform)

load_nvm() {
    # Check for Homebrew installation (macOS/Linux)
    if command -v brew >/dev/null 2>&1; then
        local brew_prefix
        brew_prefix="$(brew --prefix)"
        if [ -s "$brew_prefix/opt/nvm/nvm.sh" ]; then
            \. "$brew_prefix/opt/nvm/nvm.sh"
            [ -s "$brew_prefix/opt/nvm/etc/bash_completion.d/nvm" ] && \
                \. "$brew_prefix/opt/nvm/etc/bash_completion.d/nvm"
            return 0
        fi
    fi

    # Check for direct NVM installation
    if [ -s "$HOME/.nvm/nvm.sh" ]; then
        \. "$HOME/.nvm/nvm.sh"
        [ -s "$HOME/.nvm/bash_completion" ] && \. "$HOME/.nvm/bash_completion"
        return 0
    fi

    # Check if nvm command exists (Chocolatey, etc.)
    if command -v nvm >/dev/null 2>&1; then
        return 0
    fi

    return 1
}

# Load NVM and apply Node.js optimizations
if load_nvm; then
    # Increase Node.js memory limit for development
    export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}"
fi
