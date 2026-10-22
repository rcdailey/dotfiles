# Interactive shells get full activation, which strips the shims directory from PATH (see
# activate_aggressive in mise config.toml); `fish -c` launchers get shims instead
command -q mise; or return
if status is-interactive
    mise activate fish | source
else
    mise activate fish --shims | source
end
