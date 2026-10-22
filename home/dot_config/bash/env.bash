# Sourced by non-interactive bash through BASH_ENV (exported by fish conf.d/00-env.fish). Puts mise
# shims on PATH so project-pinned tools resolve in agent shell commands and scripts, which inherit
# an interactive PATH that has no shims.
if command -v mise >/dev/null; then
    eval "$(mise activate bash --shims)"
fi
