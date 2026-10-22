# Interactive setup only; environment and PATH live in conf.d so `fish -c` gets them too
status is-interactive; or return

set -g fish_greeting
set -gx GPG_TTY (tty)

# The VS Code Copilot extension sets GIT_PAGER=cat in its integrated terminal
test "$TERM_PROGRAM" = vscode; and set -e GIT_PAGER

command -q starship; and starship init fish | source
command -q fzf; and fzf --fish | source

# Open the completion pager in search mode so typing filters it instead of dismissing it
bind tab complete-and-search

abbr -a c docker compose
abbr -a lg lazygit
abbr -a tf terraform
abbr -a k kubectl
abbr -a kz kubectl kustomize
abbr -a pc pre-commit
abbr -a pcr pre-commit run
abbr -a pcra pre-commit run --all-files
abbr -a cmci chezmoi git -- caa
abbr -a cmst chezmoi git -- st
abbr -a cls 'clear && clear'
abbr -a keygen-ed25519 "ssh-keygen -t ed25519 -a 100 -P ''"
abbr -a reload-all 'kitty @ send-text --match all "exec fish\n"'
abbr -a !! --position anywhere --function last_history_item
abbr -a dotdot --regex '^\.\.+$' --function multicd

# A TUI that crashes without restoring the terminal leaves mouse tracking on, so mouse movement
# prints escape codes at the prompt. Disable tracking modes (1000/1002/1003) and SGR encoding (1006)
# before each prompt; the prompt never draws while a foreground TUI owns the TTY.
function __reset_mouse_tracking --on-event fish_prompt
    printf '\e[?1000l\e[?1002l\e[?1003l\e[?1006l'
end

# herdr scratch popup (ctrl+shift+s): Esc exits the shell, which closes the popup. Unset so shells
# started inside it keep normal Esc behavior.
if set -q HERDR_SCRATCH_SHELL
    set -e HERDR_SCRATCH_SHELL
    bind escape exit
end
