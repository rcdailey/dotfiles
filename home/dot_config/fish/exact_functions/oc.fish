# Route `oc upgrade` through mise so its postinstall hook refreshes the service and plugins
function oc --wraps opencode --description 'Launch opencode'
    if test "$argv[1]" = upgrade
        mise upgrade npm:@opencode/cli $argv[2..]
        return
    end
    opencode $argv
end
