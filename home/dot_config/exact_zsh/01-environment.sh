# Prevent duplicate entries in path arrays
typeset -U path fpath cdpath manpath

# Output here would garble the p10k instant prompt. Environment variables belong in .zshenv, which
# every zsh loads; this file only configures interactive shells.

# VS Code integrated terminal: load its shell integration, and drop GIT_PAGER=cat, which the
# Copilot extension sets
if [[ $TERM_PROGRAM == vscode ]]; then
  unset GIT_PAGER
  . "$(code --locate-shell-integration-path zsh)"
fi

# zsh-autosuggestions: async fetch keeps keystrokes responsive; strategy prefers
# history over completions for faster, more relevant suggestions.
export ZSH_AUTOSUGGEST_USE_ASYNC=1
export ZSH_AUTOSUGGEST_STRATEGY=(history completion)

# mise activation, before plugins so `$+commands` checks see project tools rather than shims
# inherited from a parent shell. Its script unsets functions that do not exist yet; drop the noise.
if (( $+commands[mise] )); then
  eval "$(mise activate zsh)" 2>/dev/null
fi
