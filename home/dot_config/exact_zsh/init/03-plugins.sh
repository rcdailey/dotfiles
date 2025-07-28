# Zinit plugin loading
# Load plugins that may produce console output first, then others

# Node version management (may produce output on first install)
zinit ice silent
zinit load "lukechilds/zsh-nvm"             # Full NVM integration + auto-switching

# Load essential plugins (fish-style features)
zinit load "zsh-users/zsh-autosuggestions"
zinit load "zsh-users/zsh-syntax-highlighting"
zinit load "zsh-users/zsh-history-substring-search"

# Load Oh-My-Zsh functionality via snippets
zinit snippet "OMZP::git"                    # Git aliases + completion
zinit snippet "OMZP::kubectl"               # k8s completion + aliases
zinit snippet "OMZP::docker"                # Docker completion + aliases
zinit snippet "OMZP::brew"                  # Homebrew completion
zinit snippet "OMZP::terraform"             # tf completion
zinit snippet "OMZP::colored-man-pages"     # Prettier man pages
zinit snippet "OMZP::extract"               # Smart archive extraction

# Modern theme with excellent dark terminal support
zinit ice depth=1
zinit load romkatv/powerlevel10k
