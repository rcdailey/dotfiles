function __bwu_session_valid
    set -q BW_SESSION; and bw status --session $BW_SESSION 2>/dev/null | string match -q '*unlocked*'
end

function bwu --description 'Ensure an unlocked Bitwarden session in BW_SESSION'
    if __bwu_session_valid
        echo "Bitwarden session already active"
        return 0
    end

    set -l session_file ~/.bitwarden-session
    if test -f $session_file
        # Also accepts the older `export BW_SESSION='...'` file format
        set -gx BW_SESSION (string replace -r "^export BW_SESSION='(.*)'\$" '$1' < $session_file)
        if __bwu_session_valid
            echo "Bitwarden session loaded from file"
            return 0
        end
    end

    if not bw status | string match -qr 'unlocked|logged in'
        echo "Please login to Bitwarden first: bw login --apikey"
        return 1
    end

    set -l session (bw unlock --raw 2>/dev/null)
    test -n "$session"; or return 1
    echo $session >$session_file
    chmod 600 $session_file
    set -gx BW_SESSION $session
    echo "Bitwarden session unlocked and saved"
end
