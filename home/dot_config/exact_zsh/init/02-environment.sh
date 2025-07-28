# Environment setup that must happen after instant prompt
# This includes tools that may produce console output during initialization

# Initialize mise (rtx) if available
if command -v mise >/dev/null 2>&1; then
    eval "$(mise activate zsh)" >/dev/null 2>&1
fi
