function pcc --description 'Run pre-commit against files changed in a git commit range'
    set -l range $argv[1]
    if test -z "$range"
        echo "Usage: pcc <range>"
        echo "Examples:"
        echo "  pcc @^!              # Last commit"
        echo "  pcc HEAD~3           # HEAD~3..HEAD"
        echo "  pcc HEAD~3..HEAD     # Explicit range"
        echo "  pcc main..feature    # Between branches"
        return 1
    end

    # A single ref (or special syntax like @^!) means <ref>^..<ref>
    set -l refs (string split -m1 .. -- $range)
    if test (count $refs) -eq 1
        set refs "$range^" $range
    end

    set -l resolved
    for ref in $refs
        set -a resolved (git rev-parse --verify $ref 2>/dev/null)
        or begin
            echo "Invalid ref: $ref"
            return 1
        end
    end

    pre-commit run --from-ref $resolved[1] --to-ref $resolved[2]
end
