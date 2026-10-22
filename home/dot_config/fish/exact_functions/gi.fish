function gi --description 'Print gitignore.io templates, e.g. gi python,macos'
    curl -sL "https://www.gitignore.io/api/$argv"
end
