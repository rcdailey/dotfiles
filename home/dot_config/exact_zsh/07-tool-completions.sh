# Per-tool completion registration
# Loads last: generators and `compdef` targets must be on the final PATH, which depends on
# 05-configuration.sh (~/bin, mise activate) and 06-platform.sh. compinit runs in 03-completion.sh.

# Cached generators: regenerated when `zinit update -u` re-runs atpull (see topgrade.toml)
zinit ice as"completion" id-as"mise" \
  atclone"mise completion zsh > _mise && zinit creinstall mise" \
  atpull"%atclone"
zinit load zdharma-continuum/null

zinit ice as"completion" id-as"just" \
  atclone"just --completions zsh > _just && zinit creinstall just" \
  atpull"%atclone"
zinit load zdharma-continuum/null

# Task completions, deferred until after the first prompt
zinit ice wait lucid nocompile atload'eval "$(task --completion zsh 2>/dev/null)"'
zinit load zdharma-continuum/null

# chezmoi is a standalone binary without a packaged completion; `cm` reuses it
if (( $+commands[chezmoi] )); then
  eval "$(chezmoi completion zsh)"
  compdef cm=chezmoi
fi

# worktrunk shell integration (directory switching + completions)
if (( $+commands[wt] )); then
  eval "$(wt config shell init zsh)"
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
  mise which talosctl &>/dev/null || return
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
  mise which kubectl &>/dev/null || return
  eval "$(kubectl completion zsh)"
  _kubectl_completion_loaded=1
}
chpwd_functions+=(_maybe_load_kubectl_completion)
_maybe_load_kubectl_completion
