# Essential tool aliases
alias c="docker compose"
alias cm="chezmoi"
alias tf="terraform"
alias pc="pre-commit"
alias pcr="pre-commit run"
alias pcra="pre-commit run --all-files"

# Kubernetes aliases (k alias provided by kubectl plugin, but keeping kz)
alias kz="kubectl kustomize"

# Terminal utilities
alias cls="clear && clear"
alias keygen-ed25519="ssh-keygen -t ed25519 -a 100 -P ''"

# Platform-specific aliases (Windows/WSL)
alias npp="notepad++ -multiInst -nosession -noPlugin"
alias clip="cat > /dev/clipboard"
alias paste="cat /dev/clipboard"

# Directory navigation (optional with zsh AUTO_CD feature)
alias 1..='cd ..'
alias 2..='cd ../..'
alias 3..='cd ../../..'
alias 4..='cd ../../../..'
alias 5..='cd ../../../../..'
alias 6..='cd ../../../../../..'
alias 7..='cd ../../../../../../..'
alias 8..='cd ../../../../../../../..'

# Enhanced tree command
alias tree='tree -Csu'

# Claude Code function
claude() {
    if [[ -x "$HOME/.claude/local/claude" ]]; then
        "$HOME/.claude/local/claude" "$@"
    else
        command claude "$@"
    fi
}

# chezmoi git shortcuts
alias cmci='chezmoi git -- caa'
alias cmst='chezmoi git -- st'

#-------------------------------------------------------------
# Note on Simplified ls Aliases
#-------------------------------------------------------------
# With zsh globbing, many ls variations become unnecessary:
# Instead of `lr` (recursive ls), use: ls **/*
# Instead of `lk` (by size), use: ls -l *(L+10M) for files >10MB
# Instead of `lt` (by time), use: ls -l *(om) for newest first
#
# Platform-specific ls configurations are in platforms/ files
