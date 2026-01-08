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

# Node.js will be installed via Homebrew instead of nvm

# Load other plugins with turbo mode for performance (widget-wrapping plugins)
# These can be safely deferred as they don't have strict timing requirements
# IMPORTANT: history-substring-search bindings must be set AFTER autosuggestions loads
# to prevent autosuggestions from overwriting them (see GitHub issue #678)
zinit ice wait lucid atload'bindkey "$terminfo[kcuu1]" history-substring-search-up; bindkey "$terminfo[kcud1]" history-substring-search-down'
zinit light zsh-users/zsh-autosuggestions
zinit ice wait lucid
zinit light zsh-users/zsh-syntax-highlighting

# Enable fzf-tab after loading
enable-fzf-tab

# Generate mise completions with conditional installation
# Only reinstalls completion if symlink is missing or source is newer
zinit ice as"completion" id-as"mise" \
  atclone"mise completion zsh > _mise" \
  atpull"%atclone" \
  atload'[[ ! -L "${ZINIT[COMPLETIONS_DIR]}/_mise" ]] && zinit creinstall mise'
zinit load zdharma-continuum/null

# Task completions - deferred until mise tools are available
zinit ice wait lucid nocompile atload'eval "$(task --completion zsh)"'
zinit load zdharma-continuum/null

# Just completions - use bash completions via bashcompinit (zsh module completion is broken upstream)
# See: https://github.com/casey/just/issues/2912
zinit ice wait lucid nocompile atload'eval "$(just --completions bash)"'
zinit load zdharma-continuum/null


# Load Oh-My-Zsh functionality via snippets
# kubectl loaded immediately to ensure 'k' alias is available
zinit lucid for \
    "OMZP::kubectl"

# Other OMZ plugins with turbo mode (can be deferred)
zinit ice wait"2" lucid for \
    "OMZP::git" \
    "OMZP::docker" \
    "OMZP::brew" \
    "OMZP::terraform" \
    "OMZP::colored-man-pages" \
    "OMZP::extract"
