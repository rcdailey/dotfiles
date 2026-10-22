# `cm update` also re-runs the config template to ask new prompt*Once questions
function cm --wraps chezmoi --description 'Run chezmoi'
    if test "$argv[1]" = update
        chezmoi update --init $argv[2..]
        return
    end
    chezmoi $argv
end
