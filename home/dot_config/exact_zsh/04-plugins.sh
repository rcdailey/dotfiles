# Plugin loading with strict timing requirements
# CRITICAL: fzf-tab must load after compinit, before widget-wrapping plugins

# Load Powerlevel10k theme (immediate loading for instant prompt compatibility)
zinit ice depth=1
zinit load romkatv/powerlevel10k

# Load plugins that need to be available immediately (NO turbo mode)
zinit load "zsh-users/zsh-history-substring-search"

# Load fzf and fzf-tab first (CRITICAL TIMING: after compinit, before widget plugins)
zinit load "junegunn/fzf"
zinit load "Aloxaf/fzf-tab"

# Load other plugins with wait/lucid for performance (widget-wrapping plugins)
# These can be safely deferred as they don't have strict timing requirements
zinit load "lukechilds/zsh-nvm"
zinit load "zsh-users/zsh-autosuggestions"
zinit load "zsh-users/zsh-syntax-highlighting"

# Enable fzf-tab after loading
enable-fzf-tab

# Load Oh-My-Zsh functionality via snippets (can be deferred)
zinit snippet "OMZP::git"               # Git aliases + completion
zinit snippet "OMZP::kubectl"           # k8s completion + aliases
zinit snippet "OMZP::docker"            # Docker completion + aliases
zinit snippet "OMZP::brew"              # Homebrew completion
zinit snippet "OMZP::terraform"         # tf completion
zinit snippet "OMZP::colored-man-pages" # Prettier man pages
zinit snippet "OMZP::extract"           # Smart archive extraction
