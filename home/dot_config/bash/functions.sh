# Custom bash functions

# Git .gitignore function - simplified version matching original
function gi() {
    curl -sL https://www.gitignore.io/api/$@ ;
}

# Make directory and cd into it
mkcd() {
    mkdir -p "$1" && cd "$1"
}
