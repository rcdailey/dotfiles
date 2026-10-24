# Per-tool completion registration
# Loads last: generators and `compdef` targets must be on the final PATH, which depends on
# 01-environment.sh (~/bin, mise activate) and 06-platform.sh. compinit runs in 03-completion.sh.

# Source a generator's output from a cache file. Its first line records the resolved binary; a
# different path (mise and Homebrew install each version separately) or a newer binary (in-place
# self-update) regenerates it. mtime alone misses upgrades, since mise keeps the archive's mtime.
_source_cached() {
  local cache="${XDG_CACHE_HOME:-$HOME/.cache}/zsh/$1.zsh" bin=${commands[$1]:A} stamp=
  [[ -r $cache ]] && read -r stamp < "$cache"
  if [[ $stamp != "# $bin" || $bin -nt $cache ]]; then
    mkdir -p "${cache:h}"
    # A failed run leaves no cache, so the next shell retries
    if ! { print -r -- "# $bin" && "$@" } >| "$cache"; then
      rm -f "$cache" "$cache.zwc"
      return 1
    fi
    zcompile -R -- "$cache.zwc" "$cache"
  fi
  source "$cache"
  # Some generators (e.g. infisical) define _tool but rely on fpath autoloading to register it
  if (( $+functions[_$1] && ! $+_comps[$1] )); then
    compdef _$1 $1
  fi
}

# fzf key bindings: Ctrl-R history, Ctrl-T files, Alt-C directories
(( $+commands[fzf] )) && _source_cached fzf --zsh
(( $+commands[mise] )) && _source_cached mise completion zsh
(( $+commands[task] )) && _source_cached task --completion zsh

# chezmoi is a standalone binary without a packaged completion; `cm` reuses it
if (( $+commands[chezmoi] )); then
  _source_cached chezmoi completion zsh
  compdef cm=chezmoi
fi

# worktrunk shell integration (directory switching + completions)
if (( $+commands[wt] )); then
  _source_cached wt config shell init zsh
fi

# Terraform only provides bash completion
if (( $+commands[terraform] )); then
  autoload -U +X bashcompinit && bashcompinit
  complete -o nospace -C terraform terraform
  complete -o nospace -C terraform tf
fi

# Tools that may be on PATH only inside some mise projects (e.g. home-ops): register each once it
# appears, checked at startup and on every cd. Value: generator arguments after the tool name.
typeset -gA _pending_completions=(
  flux 'completion zsh'
  gh 'completion -s zsh'
  helm 'completion zsh'
  helmfile 'completion zsh'
  infisical 'completion zsh'
  kubectl 'completion zsh'
  kustomize 'completion zsh'
  talosctl 'completion zsh'
  yq 'completion zsh'
)
_load_project_completions() {
  local tool
  for tool in ${(k)_pending_completions}; do
    (( $+commands[$tool] )) || continue
    _source_cached $tool ${(z)_pending_completions[$tool]}
    # Oh My Zsh kubectl aliases (k, kgp, ...); the plugin returns early without kubectl on PATH
    [[ $tool == kubectl ]] && _zsource "$_zsh_plugins/ohmyzsh/plugins/kubectl/kubectl.plugin.zsh"
    unset "_pending_completions[$tool]"
  done
  (( $#_pending_completions )) || chpwd_functions=(${chpwd_functions:#$0})
}
chpwd_functions+=(_load_project_completions)
_load_project_completions
