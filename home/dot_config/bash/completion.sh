# Bash completion settings

# Enable programmable completion features
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

# Kubernetes completion
if command -v kubectl &> /dev/null; then
    # Source kubectl completion
    source <(kubectl completion bash)
fi
