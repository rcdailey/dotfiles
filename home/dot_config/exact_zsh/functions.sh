# Custom shell functions

# Git .gitignore function - simplified version matching original
function gi() {
    curl -sL https://www.gitignore.io/api/$@ ;
}
