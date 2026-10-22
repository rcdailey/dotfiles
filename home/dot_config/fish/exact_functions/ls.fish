function ls --description 'List directory contents (lsd when installed)'
    if command -q lsd
        lsd --color=auto --icon=auto --group-directories-first $argv
    else
        command ls -hF $argv
    end
end
