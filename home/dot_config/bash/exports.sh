# Environment variables and exports

# Editor and paging
export EDITOR="code"
export LESS="-RSic~ -x2"
export PAGER="less"
export PSQL_PAGER="pspg"
export LESSHISTSIZE=0
export LESSCHARSET=UTF-8

# History control
export HISTCONTROL=ignoreboth
export HISTSIZE=1000
export HISTFILESIZE=2000

# Development
export COLUMNS
export DOCKER_UID="$(id -u)"
export DOCKER_GID="$(id -g)"

# Disable husky pre-commit hooks (slows down git)
export HUSKY_SKIP_HOOKS=1 # For legacy purposes
export HUSKY=0 # This replaces HUSKY_SKIP_HOOKS

# In some cases TMPDIR is not defined, such as VS Code integrated terminal on Windows
if [[ -z "$TMPDIR" ]]; then
    export TMPDIR=/tmp
fi
