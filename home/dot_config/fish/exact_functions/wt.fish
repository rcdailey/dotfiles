# worktrunk shell integration (output of `wt config shell install fish --dry-run`); replaces itself
# with the full integration from the binary on first use so it can change this shell's directory
function wt
    # Completion mode: let the binary emit completions directly, or a stale third-party completion
    # that calls bare `wt` with COMPLETE set recurses into this stub
    if set -q COMPLETE
        command wt $argv
        return
    end
    command wt config shell init fish | source
    # If source fails, the function isn't replaced and calling wt again would loop
    set -l wt_status $pipestatus[1]
    set -l source_status $pipestatus[2]
    test $wt_status -eq 0; or return $wt_status
    test $source_status -eq 0; or return $source_status
    wt $argv
end
