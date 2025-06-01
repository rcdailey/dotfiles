# PATH modifications

# Add user's private bin to PATH if it exists
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi

if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi

# Append home dir to path so we can access scripts in there
export PATH=$PATH:~:~/git-scripts
