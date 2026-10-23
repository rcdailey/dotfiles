function __run_buffer_in_bash --description 'Run the command line as a bash script'
    set -l code (commandline | string collect)
    test -n "$code"; or return
    commandline -r -- "bash -c "(string escape -- $code)
    commandline -f execute
end
