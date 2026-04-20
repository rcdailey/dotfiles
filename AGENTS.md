# AGENTS.md

Chezmoi dotfiles repo. `.chezmoiroot` = `home/` means only `home/` contains managed dotfiles. Files
outside `home/` are repo infrastructure, not managed by chezmoi.

## Directory Structure

**Core:**

- `home/` - All managed dotfiles (chezmoi root)
- `home/dot_config/` - XDG config (~/.config)
- `home/dot_local/bin/` - Custom executables
- `home/private_dot_ssh/` - SSH config (600 perms); uses `config.d/` fragments

**Shell:**

- `home/dot_zshenv.tmpl` - XDG vars, Homebrew, mise shims (runs for ALL shell types)
- `home/dot_zshrc` - P10k instant prompt, sources numbered configs
- `home/dot_config/exact_zsh/` - Numbered configs, strict load sequence:
  - `01-environment.sh` - Shell options, PATH, tool env vars
  - `02-zinit.sh` - Zinit plugin manager bootstrap
  - `03-completion.sh` - compinit, P10k workaround (DO NOT REMOVE)
  - `04-plugins.sh` - Zinit plugin loads (fzf-tab, syntax highlighting, etc.)
  - `05-configuration.sh` - Aliases, keybinds, mise activate, tool configs
  - `06-platform.sh.tmpl` - Platform-specific settings (Linux/macOS)
- `home/dot_config/exact_zsh/functions/` - Autoloaded zsh functions (bwu, clip, gi, oc, open-here,
  pcc)

**Scripts:**

- `home/git-scripts/` - Git helper scripts and subcommands
- `scripts/` - Repo-rooted Python projects executed in-place by thin wrappers in
  `home/dot_local/bin/`. Lives outside `home/` so chezmoi does not manage Python build artifacts
  (`.venv/`, `__pycache__/`, `uv.lock`); edits take effect without `chezmoi apply`.   Wrappers
  resolve the project path via `$(chezmoi source-path)/../scripts/<name>` so the source location is
  authoritative (no hardcoded home path). Current projects: `research/` (LLM research CLI; entry:
  `executable_research`)

**Chezmoi internals:**

- `home/.chezmoiscripts/` - Lifecycle hooks; `run_onchange_` triggers on dependency changes
- `home/.chezmoitemplates/` - Reusable template snippets
- `.chezmoiexternal.toml` - External file dependencies; distributed across subdirectories (not at
  repo root). Locations: `home/dot_config/opencode/exact_skills/`, `home/git-scripts/`,
  `home/dot_local/share/zinit/`

**OpenCode (`home/dot_config/opencode/`):**

Source directories use `exact_` prefixes (chezmoi strips unmanaged files on apply), but target paths
under `~/.config/opencode/` do not have these prefixes.

- `opencode.jsonc` - Main config (model, agent overrides, LSP, formatters, providers, MCP servers)
- `AGENTS.md` - Global directives (the file at `~/.config/opencode/AGENTS.md`)
- `dcp.jsonc`, `tui.jsonc` - Additional config files
- `exact_skills/` - Skill definitions (target: `~/.config/opencode/skills/`). Each subdirectory
  contains a `SKILL.md`. Some are managed via `.chezmoiexternal.toml` in this directory.
- `exact_agents/` - Custom agent definitions (target: `~/.config/opencode/agents/`). Files:
  `architect.md.tmpl`, `build.md.tmpl`, `commit.md`, `researcher.md`, `upgrade-analyst.md`. The
  primary agents (`architect`, `build`) are chezmoi templates that include a shared partial via `{{
  template "opencode-primary-shared.md" . }}`. The partial holds directives that apply to every
  primary agent but MUST NOT leak to subagents. OpenCode loads AGENTS.md into every agent context
  regardless of mode (verified against source; no mode-based filter exists), so shared primary-only
  content cannot live in AGENTS.md and the template partial is the workaround.
- `exact_commands/` - Slash commands (target: `~/.config/opencode/commands/`). Files:
  `contrib-init.md`, `pr-review.md`, `renovate-upgrade.md`, `research.md`,
  `setup-conventional-commits.md`
- `exact_plugins/` - Plugins (target: `~/.config/opencode/plugins/`). Contains `tool-guards.ts`.
- `.chezmoitemplates/` - Reusable template partials scoped to OpenCode config. Template names share
  a global namespace across all `.chezmoitemplates/` directories in the source state; prefix names
  with `opencode-` to avoid collisions. Current partials: `opencode-primary-shared.md`.
- `.chezmoiremove` - Tracks removed files for cleanup

**Tool configs (`home/dot_config/`):** ccstatusline, commitlint, environment.d, fontconfig, git,
helmfile, k9s, kitty, lazygit, mise, opencode, powershell, karabiner (private_karabiner), rbw,
ripgrep, sx, systemd, tmux

**Terminal:** kitty (all platforms) - `home/dot_config/kitty/`

## Conventions

**Chezmoi prefixes:** `dot_` = dotfile, `private_` = 600 perms, `executable_` = +x, `exact_` =
directory matches exactly (removes unmanaged files)

**Template variables:** `.chezmoi.os` ("linux"/"darwin"/"windows"), `.chezmoi.hostname`,
`.chezmoi.username`. Custom data via `.chezmoi.toml.tmpl`.

**Platform exclusion:** Prefer `.chezmoiignore` patterns over template conditionals.

**File removal:** When removing files from directories not prefixed with `exact_`, add patterns to
`.chezmoiremove` in the same source directory as the removed files. Paths are target names relative
to that directory (e.g., `config.d/file.ssh` not `private_config.d/private_file.ssh`). This keeps
removal rules discoverable and ensures chezmoi removes the target files on apply.

## Shell Init Order (Critical)

Zsh loads: `.zshenv` -> `.zshrc` -> numbered configs in `dot_config/exact_zsh/`

- P10k instant prompt must be early in .zshrc
- fzf-tab must load after compinit, before widget-wrapping plugins
- mise split: `mise env` before instant prompt, `mise activate` after
- 03-completion contains P10k bug workaround (DO NOT REMOVE)

## Workflow

1. Edit: `chezmoi edit <file>` or directly in source
2. Preview: `chezmoi diff`
3. Test: `chezmoi apply --dry-run`
4. Apply: `chezmoi apply`

## Upstream References

### humanizer skill (upstream sync)

`home/dot_config/opencode/exact_skills/humanizer/SKILL.md` is based on
[blader/humanizer](https://github.com/blader/humanizer) with two local modifications that MUST
survive upstream syncs:

1. Tightened frontmatter description
2. `User Voice Profile` section appended at the end, delimited by `BEGIN LOCAL ADDITION` / `END
   LOCAL ADDITION` HTML comment markers. It lives inside `SKILL.md` (not a sibling file) because
   `mcp_skill` only injects `SKILL.md` content.

To sync: extract the LOCAL ADDITION block, fetch upstream via `gh api`, drop upstream's Voice
Calibration section, restore the tightened description, re-append the block. NEVER discard the block
or merge its content into upstream sections; the markers MUST remain intact for future syncs.

## Constraints

### Git Operations

NEVER run git mutations (add/commit/reset/push/rebase/merge) without explicit user approval. ASK
before running these commands unless the user's request clearly authorizes them (e.g., "commit this"
or "push to remote").
