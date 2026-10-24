# Zsh completion system setup

# Completion directories must be on fpath before compinit, which records them in the dump. Oh My
# Zsh plugins (04-plugins.sh) ship _docker and _extract and generate others into ZSH_CACHE_DIR.
export ZSH_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/zsh/omz"
fpath=(
  "${XDG_DATA_HOME:-$HOME/.local/share}"/zsh-plugins/ohmyzsh/plugins/{docker,extract}(N)
  "$ZSH_CACHE_DIR/completions"
  $fpath
)

# Load completions from the dump (-C skips the fpath scan and security check). Rebuild it daily, or
# when this file changes, since it controls which directories the dump covers. compinit without -C
# keeps an existing dump whenever its file count still matches, so delete it to force a rebuild.
# Glob qualifiers do not expand inside [[ ]], so test the expanded array instead.
autoload -Uz compinit
() {
  local -a stale=(~/.zcompdump(Nmh+24))
  if (( $#stale )) || [[ ${(%):-%x} -nt ~/.zcompdump ]]; then
    rm -f ~/.zcompdump{,.zwc}
  fi
  compinit -C -u
}

# Essential completion behavior options (relevant with fzf-tab)
setopt ALWAYS_TO_END                  # Move cursor to end of completed word
setopt COMPLETE_IN_WORD               # Complete from both ends of a word
setopt AUTO_PARAM_SLASH               # Add trailing slash for directories automatically

# Basic completion styling
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"
zstyle ':completion:*' group-name ''
zstyle ':completion:*:descriptions' format '[%d]'

# fzf-tab replaces the completion menu
zstyle ':completion:*' menu no

# Completion system behavior configuration
zstyle ':completion:*' completer _complete _files

# Case-insensitive completion matching
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'

# Offer git aliases as git subcommands: `--name-only` lists alias.<name> keys, minus the prefix
zstyle ':completion:*:*:git:*' user-commands \
  ${${(f)"$(git config --name-only --get-regexp '^alias\.' 2>/dev/null)"}#alias.}

# Disable sorting for git commands to maintain natural order
zstyle ':completion:*:git:*' sort false
zstyle ':completion:*:npm:*' sort false
