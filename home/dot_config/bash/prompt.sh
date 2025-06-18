# Bash prompt configuration

# Function to get virtual environment name
__venv_ps1() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo " ($(basename "$VIRTUAL_ENV"))"
    fi
}

# Disable default virtual environment prompt modification
export VIRTUAL_ENV_DISABLE_PROMPT=1

# Your original prompt with git integration and virtual environment support
export PS1='\n\[\e[1;32m\]\u\[\e[0;39m\]@\[\e[1;36m\]\h\[\e[0;39m\]: \[\e[1;33m\]\w\[\e[0;39m\]\[\e[1;35m\]$(__git_ps1 " (%s)")\[\e[0;39m\]\[\e[1;34m\]$(__venv_ps1)\[\e[0;39m\] \[\e[0;39m\]'$'\n$ '
