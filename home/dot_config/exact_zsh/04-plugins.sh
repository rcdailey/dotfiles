# Plugins live in ~/.local/share/zsh-plugins (chezmoi externals) and load in this order:
# compinit (03) -> fzf-tab -> other widgets -> syntax highlighting -> history substring search
# (its README requires highlighting first) -> autosuggestions. Nothing is deferred: deferral only
# moves cost and leaves the first command without highlighting.

_zsh_plugins="${XDG_DATA_HOME:-$HOME/.local/share}/zsh-plugins"

# Source a plugin file through its zcompile'd form, recompiling when the source is newer
_zsource() {
  [[ -r $1 ]] || return 0
  [[ $1.zwc -nt $1 ]] || zcompile -R -- "$1.zwc" "$1" 2>/dev/null
  source "$1"
}

# Disable P10k configuration wizard (config managed via dotfiles)
export POWERLEVEL9K_DISABLE_CONFIGURATION_WIZARD=true
_zsource "$_zsh_plugins/powerlevel10k/powerlevel10k.zsh-theme"

# fzf-tab wraps the completion widget, so it loads after compinit and before widget wrappers
_zsource "$_zsh_plugins/fzf-tab/fzf-tab.plugin.zsh"

# Oh My Zsh plugins without the framework. The docker plugin caches its completion under
# ZSH_CACHE_DIR and moves files with zf_mv.
export ZSH_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/zsh/omz"
zmodload -F zsh/files b:zf_mv
fpath=("$_zsh_plugins"/ohmyzsh/plugins/{docker,extract}(N) "$ZSH_CACHE_DIR/completions" $fpath)
for _omz_plugin in kubectl git docker brew terraform colored-man-pages extract; do
  _zsource "$_zsh_plugins/ohmyzsh/plugins/$_omz_plugin/$_omz_plugin.plugin.zsh"
done
unset _omz_plugin

_zsource "$_zsh_plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
_zsource "$_zsh_plugins/zsh-history-substring-search/zsh-history-substring-search.zsh"
_zsource "$_zsh_plugins/zsh-autosuggestions/zsh-autosuggestions.zsh"

# After autosuggestions, which would otherwise rebind the arrows (zsh-autosuggestions#678)
bindkey "$terminfo[kcuu1]" history-substring-search-up
bindkey "$terminfo[kcud1]" history-substring-search-down
