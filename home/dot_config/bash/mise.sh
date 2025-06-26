# mise initialization (cross-platform)

load_mise() {
    # Check for Homebrew installation (macOS/Linux)
    if command -v brew >/dev/null 2>&1; then
        local brew_prefix
        brew_prefix="$(brew --prefix)"
        if [ -x "$brew_prefix/bin/mise" ]; then
            eval "$("$brew_prefix/bin/mise" activate bash)"
            return 0
        fi
    fi

    # Check for direct mise installation
    if command -v mise >/dev/null 2>&1; then
        eval "$(mise activate bash)"
        return 0
    fi

    # Check for local installation
    if [ -x "$HOME/.local/bin/mise" ]; then
        eval "$("$HOME/.local/bin/mise" activate bash)"
        return 0
    fi

    return 1
}

# Load mise if available
load_mise