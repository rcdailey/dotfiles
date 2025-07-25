# PATH modifications

# Add user's private bin to PATH if it exists
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi

if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi

# Go tools PATH - add if go is installed
if command -v go >/dev/null 2>&1; then
    export PATH="$(go env GOPATH)/bin:$PATH"
fi

# Append home dir to path so we can access scripts in there
export PATH=$PATH:~:~/git-scripts
