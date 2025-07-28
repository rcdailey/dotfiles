#!/bin/zsh

# Auto-reload zsh configuration after chezmoi apply
# Only reload if we're in an interactive session
if [[ -o INTERACTIVE && -n "$ZSH_VERSION" ]]; then
    echo "🔄 Reloading zsh configuration..."
    source ~/.zshrc
    echo "✅ Zsh configuration reloaded!"
fi
