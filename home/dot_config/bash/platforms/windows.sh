# Windows-specific configurations

# Node.js platform check bypass for Windows environments
export NODE_SKIP_PLATFORM_CHECK=1

# ls function for aliases (using standard ls with color support)
myls() { ls -hF --color "$@"; }
