# Per-tool completion registration
# Loads last: generators and `compdef` targets must be on the final PATH, which depends on
# 05-configuration.sh (~/bin, mise activate) and 06-platform.sh. compinit runs in 03-completion.sh.

# Source a generator's output from a cache file, regenerated when the binary is newer
_source_cached() {
  local cache="${XDG_CACHE_HOME:-$HOME/.cache}/zsh/$1.zsh"
  if [[ ! -s $cache || $commands[$1] -nt $cache ]]; then
    mkdir -p "${cache:h}" && "$@" >| "$cache" && zcompile -R -- "$cache.zwc" "$cache"
  fi
  source "$cache"
}

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

# Terraform only provides bash completion (via bashcompinit)
if (( $+commands[terraform] )); then
  complete -o nospace -C terraform terraform
  complete -o nospace -C terraform tf
fi

# Project-scoped tools: register once mise puts them on PATH, checked on every cd
_talosctl_completion_loaded=0
_maybe_load_talosctl_completion() {
  if (( _talosctl_completion_loaded )); then
    return
  fi
  (( $+commands[talosctl] )) || return
  eval "$(talosctl completion zsh)"
  _talosctl_completion_loaded=1
}
chpwd_functions+=(_maybe_load_talosctl_completion)
_maybe_load_talosctl_completion

_kubectl_completion_loaded=0
_maybe_load_kubectl_completion() {
  if (( _kubectl_completion_loaded )); then
    return
  fi
  (( $+commands[kubectl] )) || return
  eval "$(kubectl completion zsh)"
  _kubectl_completion_loaded=1
}
chpwd_functions+=(_maybe_load_kubectl_completion)
_maybe_load_kubectl_completion
