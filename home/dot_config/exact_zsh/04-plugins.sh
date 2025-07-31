# Plugin loading with strict timing requirements
# CRITICAL: fzf-tab must load after compinit, before widget-wrapping plugins

# Load Powerlevel10k theme (immediate loading for instant prompt compatibility)
# Disable P10k configuration wizard (config managed via dotfiles)
export POWERLEVEL9K_DISABLE_CONFIGURATION_WIZARD=true

zinit ice depth=1
zinit light romkatv/powerlevel10k

# Load plugins that need to be available immediately (NO turbo mode)
zinit load "zsh-users/zsh-history-substring-search"

# Load fzf and fzf-tab first (CRITICAL TIMING: after compinit, before widget plugins)
zinit load "junegunn/fzf"
zinit load "Aloxaf/fzf-tab"

# Use built-in lazy loading instead of `ice wait lucid` because the zinit
# lazy loading results in `node` being not found.
export NVM_LAZY_LOAD=true
zinit load "lukechilds/zsh-nvm"

# Load other plugins with turbo mode for performance (widget-wrapping plugins)
# These can be safely deferred as they don't have strict timing requirements
zinit ice wait lucid for \
    "zsh-users/zsh-autosuggestions" \
    "zsh-users/zsh-syntax-highlighting"

# Enable fzf-tab after loading
enable-fzf-tab

# Load Oh-My-Zsh functionality via snippets with turbo mode (can be deferred)
zinit ice wait"2" lucid for \
    "OMZP::git" \
    "OMZP::kubectl" \
    "OMZP::docker" \
    "OMZP::brew" \
    "OMZP::terraform" \
    "OMZP::colored-man-pages" \
    "OMZP::extract"
