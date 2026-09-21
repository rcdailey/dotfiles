#!/usr/bin/env bash
# Shared launcher for the uv-managed Python tools in this repo's scripts/ dir.
#
# These tools are global: they run from any caller directory, and that
# directory's mise config is not theirs to obey. Three separate hazards follow.
#
# 1. The caller's [env] carries API keys the tools need (TAVILY_API_KEY,
#    LINEAR_API_KEY), and no shell hook applies it in a non-interactive shell,
#    where mise only installs shims. So load it explicitly, but best-effort:
#    an untrusted or malformed caller config must not break an unrelated tool,
#    and MISE_AUTO_INSTALL=false keeps the caller's toolchain out of it.
# 2. That same [env] commonly pins UV_PYTHON. uv honors ambient UV_* even with
#    --project, so a caller pinning an older Python than the project's
#    requires-python breaks the tool outright. Unset those after loading.
# 3. Bare `uv` resolves to a mise shim, which reapplies the caller's [env] and
#    restores UV_PYTHON right after the unset. Invoke the real binary instead.

# Run a scripts/ project as a module, isolated from the caller's Python pins.
# Pass the project directory name under scripts/, its Python module name, then
# the tool's arguments. The chezmoi source dir is authoritative, so edits take
# effect without an apply.
uv_tool_exec() {
  local project=$1 module=$2
  shift 2
  project="$(chezmoi source-path)/../scripts/$project"

  eval "$(MISE_AUTO_INSTALL=false mise env -s bash 2>/dev/null || true)"

  # -C keeps resolution out of the caller's config, which may be untrusted.
  local uv
  uv=$(mise -C "$HOME" which uv 2>/dev/null) || uv=uv

  exec env -u UV_PYTHON -u UV_PROJECT -u UV_PROJECT_ENVIRONMENT \
    -u VIRTUAL_ENV -u PYTHONPATH -u PYTHONHOME \
    "$uv" run --quiet --project "$project" -m "$module" "$@"
}
