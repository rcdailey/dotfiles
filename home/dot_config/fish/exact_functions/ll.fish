function ll --description 'Long listing including hidden files (lsd when installed)'
    if command -q lsd
        lsd -la --color=auto --icon=auto --group-directories-first --header $argv
    else
        command ls -lahF $argv
    end
end
