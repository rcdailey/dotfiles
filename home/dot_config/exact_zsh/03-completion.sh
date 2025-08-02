# Zsh completion system setup

# Skip security check and initialize zsh completion system
# Reason: Single user machines, no security risk, improves automation
# Daily cache optimization: only rebuild completion dump once per day
autoload -Uz compinit
if [[ ~/.zcompdump(#qNmh+24) ]]; then
  compinit -u
else
  compinit -C -u
fi

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

# Git alias completion support for fzf-tab
# This ensures git aliases appear in tab completions
zstyle ':completion:*:*:git:*' user-commands "$(git config --get-regexp '^alias\.' | cut -c7- | cut -d' ' -f1 2>/dev/null)"

# Disable sorting for git commands to maintain natural order
zstyle ':completion:*:git:*' sort false

# CRITICAL: Workaround for Powerlevel10k bug - GitHub issue #2887
# https://github.com/romkatv/powerlevel10k/issues/2887
# Malformed pattern (utf|UTF)(-|)8 causes infinite error loop during tab completion
# This suppresses stderr from affected p9k functions until the upstream bug is fixed

# List of known affected functions
local p9k_buggy_functions=(
  '_p9k_on_expand'
  '_p9k__dir'
  '_p9k__shorten_dir'
  '_p9k_prompt_dir_init'
)

for func in $p9k_buggy_functions; do
  if (( $+functions[$func] )); then
    functions[${func}_orig]=$functions[$func]
    eval "
    $func() {
      { ${func}_orig \"\$@\"; } 2>/dev/null || true
    }
    "
  fi
done
