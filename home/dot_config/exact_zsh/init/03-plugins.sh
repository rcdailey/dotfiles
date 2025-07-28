# Zinit plugin loading
# Load plugins that may produce console output first, then others

# Set silent as default for all subsequent commands to avoid instant prompt warnings
zinit default-ice silent

# Load ALL plugins with wait to avoid instant prompt conflicts
zinit wait lucid for \
    "lukechilds/zsh-nvm" \
    "junegunn/fzf" \
    "Aloxaf/fzf-tab" \
    "zsh-users/zsh-autosuggestions" \
    "zsh-users/zsh-syntax-highlighting" \
    "zsh-users/zsh-history-substring-search"

# Load Oh-My-Zsh functionality via snippets
zinit snippet "OMZP::git"                    # Git aliases + completion
zinit snippet "OMZP::kubectl"               # k8s completion + aliases
zinit snippet "OMZP::docker"                # Docker completion + aliases
zinit snippet "OMZP::brew"                  # Homebrew completion
zinit snippet "OMZP::terraform"             # tf completion
zinit snippet "OMZP::colored-man-pages"     # Prettier man pages
zinit snippet "OMZP::extract"               # Smart archive extraction

# Clear default ice and set specific ice for theme
zinit default-ice --clear
zinit ice depth=1
zinit load romkatv/powerlevel10k
