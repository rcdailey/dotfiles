# Windows-specific configurations

# Prepend Chocolatey bin to PATH to prioritize it over Git for Windows tools
export PATH="$HOME/AppData/Local/UniGetUI/Chocolatey/bin:$PATH"

# Node.js platform check bypass for Windows environments
export NODE_SKIP_PLATFORM_CHECK=1

# ls function for aliases (using standard ls with color support)
myls() { command ls -hF --color "$@"; }
