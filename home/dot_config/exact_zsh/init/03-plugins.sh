# Zinit plugin loading
# Load plugins that may produce console output first, then others

# Load plugins that need to be available immediately
zinit ice silent
zinit load "zsh-users/zsh-history-substring-search"

# Load fzf and fzf-tab first (fzf-tab needs to load after compinit but before other widgets)
zinit ice silent
zinit load "junegunn/fzf"

# Load fzf-tab (options are set in .zshrc)
zinit ice silent
zinit load "Aloxaf/fzf-tab"

# Enable fzf-tab after loading
enable-fzf-tab

# Load other plugins with wait to avoid instant prompt conflicts
zinit ice silent wait lucid for \
    "lukechilds/zsh-nvm" \
    "zsh-users/zsh-autosuggestions" \
    "zsh-users/zsh-syntax-highlighting"

# Load Oh-My-Zsh functionality via snippets
zinit snippet "OMZP::git"                    # Git aliases + completion
zinit snippet "OMZP::kubectl"               # k8s completion + aliases
zinit snippet "OMZP::docker"                # Docker completion + aliases
zinit snippet "OMZP::brew"                  # Homebrew completion
zinit snippet "OMZP::terraform"             # tf completion
zinit snippet "OMZP::colored-man-pages"     # Prettier man pages
zinit snippet "OMZP::extract"               # Smart archive extraction

# Load theme with specific ice
zinit ice depth=1
zinit load romkatv/powerlevel10k
