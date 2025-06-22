# Linux-specific configurations

# Enable color support for ls
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
fi

# Linux Homebrew fallback
if [ -f "/home/linuxbrew/.linuxbrew/bin/brew" ]; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
fi

# ls function for aliases - this is used by the aliases in dot_bash_aliases
myls() { \ls -hF --color "$@"; }

# This is to support the migration to k8s in the nezuko repository
export DOCKER_DATA_PATH="/mnt/docker-data"
