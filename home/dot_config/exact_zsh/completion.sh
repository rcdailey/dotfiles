# Zsh completion settings
# Note: Zinit plugins handle most completions automatically

# Initialize zsh completion system
autoload -Uz compinit
compinit

# Essential completion behavior options (relevant with fzf-tab)
setopt ALWAYS_TO_END                  # Move cursor to end of completed word
setopt COMPLETE_IN_WORD               # Complete from both ends of a word
setopt AUTO_PARAM_SLASH               # Add trailing slash for directories automatically

# Basic completion styling
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*' group-name ''
zstyle ':completion:*:descriptions' format '[%d]'

# Case-insensitive completion matching
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'

# fzf-tab will use its default configuration
# Explicit configuration commented out to prefer defaults over manual settings
# zstyle ':completion:*' menu no                    # Disable default menu for fzf-tab
# zstyle ':completion:*:descriptions' format '[%d]' # Set descriptions format to enable group support
# zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}  # Enable filename colorizing
# zstyle ':completion:*:git-checkout:*' sort false  # Disable sort when completing git checkout
# zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --color=always $realpath 2>/dev/null || ls -1 --color=always $realpath'
# zstyle ':fzf-tab:*' switch-group '<' '>'          # Switch group using < and >




# Workaround for Powerlevel10k bug: malformed pattern (utf|UTF)(-|)8 in __p9k_intro_locale
# This suppresses stderr from _p9k_on_expand until the upstream bug is fixed
# See: hardcoded pattern in __p9k_intro_locale variable causes "bad pattern" errors
if (( $+functions[_p9k_on_expand] )); then
    functions[_p9k_on_expand_orig]=$functions[_p9k_on_expand]
    _p9k_on_expand() {
        { _p9k_on_expand_orig "$@" } 2>/dev/null
    }
fi

# Custom completions (if needed)
# Add any project-specific completions here

# =============================================================================
# ADVANCED fzf-tab CONFIGURATION (COMMENTED OUT - MAY REVISIT LATER)
# =============================================================================
# The following configuration was based on research but may be overly complex
# for initial setup. It includes advanced features like custom keybindings,
# extensive previews, and styling options. We may uncomment/modify these later
# as we become more familiar with fzf-tab.

# # Core fzf-tab settings
# zstyle ':fzf-tab:*' fzf-command fzf
# zstyle ':fzf-tab:*' fzf-flags --height=50% --layout=reverse --border=rounded --cycle --keep-right
# zstyle ':fzf-tab:*' fzf-min-height 15
# zstyle ':fzf-tab:*' fzf-pad 4

# # Enhanced UX settings
# zstyle ':fzf-tab:*' switch-group F1 F2           # Use F1/F2 to switch between completion groups
# zstyle ':fzf-tab:*' continuous-trigger '/'       # Continue completion when typing /
# zstyle ':fzf-tab:*' print-query alt-enter        # Print query with alt-enter
# zstyle ':fzf-tab:*' accept-line enter            # Accept with enter
# zstyle ':fzf-tab:*' query-string prefix input first  # Smart query generation
# zstyle ':fzf-tab:*' show-group full              # Show all group descriptions
# zstyle ':fzf-tab:*' prefix '·'                   # Prefix for entries
# zstyle ':fzf-tab:*' single-group color header    # Single group display style

# # Keybindings for better control
# zstyle ':fzf-tab:*' fzf-bindings \
#     'ctrl-j:accept' \
#     'ctrl-a:toggle-all' \
#     'ctrl-space:toggle+down' \
#     'space:accept'

# # Preview configurations for different commands
# zstyle ':fzf-tab:complete:git-(add|diff|restore):*' fzf-preview 'git diff $word 2>/dev/null'
# zstyle ':fzf-tab:complete:git-log:*' fzf-preview 'git log --color=always $word 2>/dev/null'
# zstyle ':fzf-tab:complete:git-show:*' fzf-preview 'git show --color=always $word 2>/dev/null'

# # Environment variables preview
# zstyle ':fzf-tab:complete:(-command-|-parameter-|-brace-parameter-|export|unset|expand):*' \
#     fzf-preview 'echo ${(P)word}'

# # Commands preview with fallbacks
# zstyle ':fzf-tab:complete:-command-:*' fzf-preview \
#     '(which "$word" 2>/dev/null && echo "Command: $word") || echo "Unknown command: $word"'

# # Group colors for better visual distinction
# FZF_TAB_GROUP_COLORS=(
#     '\033[94m' '\033[32m' '\033[33m' '\033[35m' '\033[31m'
#     '\033[36m' '\033[38;5;100m' '\033[38;5;98m'
# )
# zstyle ':fzf-tab:*' group-colors $FZF_TAB_GROUP_COLORS
