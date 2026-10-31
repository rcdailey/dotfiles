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

- `home/dot_zshenv.tmpl` - XDG vars, Homebrew, PATH (every zsh); mise shims when `.zshrc` skips its
  setup
- `home/dot_zshrc` - P10k instant prompt, sources numbered configs
- `home/dot_config/exact_zsh/` - Numbered configs, strict load sequence:
  - `01-environment.sh` - Tool env vars, PATH, mise activate
  - `03-completion.sh` - Completion fpath, compinit, zstyles
  - `04-plugins.sh` - Sources plugins from `home/dot_local/share/zsh-plugins/` (chezmoi externals,
    no plugin manager) in a fixed order
  - `05-configuration.sh` - Shell options, aliases, keybinds
  - `06-platform.sh.tmpl` - Platform-specific settings (Linux/macOS)
  - `07-tool-completions.sh` - Per-tool completion registration (needs final PATH)
- `home/dot_config/exact_zsh/functions/` - Autoloaded zsh functions

**Scripts:**

- `home/git-scripts/` - Git helper scripts and subcommands
- `scripts/` - Source of the user's custom Python CLIs; fix or extend them here, not in
  `~/code/forks/` or an installed copy. Each command's wrapper in `home/dot_local/bin/` runs its
  project in-place via `uv_tool_exec` (`home/dot_local/lib/uv-tool.sh`), so edits take effect
  without `chezmoi apply`. Outside `home/` so chezmoi ignores build artifacts. Projects (command:
  path):
  - `linear`: `scripts/linear-cli/`
  - `gh-review`: `scripts/gh-review/`
  - `research`: `scripts/research/`
  - Top-level `scripts/*.sh` are repo maintenance scripts, not user commands.

**Repo infrastructure (root):** Linter/formatter configs (`biome.json`, `ruff.toml`,
`.markdownlint-cli2.yaml`, `.yamllint.yaml`, `.editorconfig`), pre-commit hooks
(`.pre-commit-config.yaml`), dev tool versions (`mise.toml`), and `docs/`.

**Chezmoi internals:**

- `home/.chezmoiscripts/` - Lifecycle hooks; `run_onchange_` triggers on dependency changes
- `home/.chezmoitemplates/` - Reusable template snippets
- `.chezmoiexternal.toml` - External file dependencies; distributed across subdirectories (not at
  repo root). Glob `**/.chezmoiexternal.toml` to find all locations.
- `.chezmoiremove` - Patterns for files chezmoi should remove from the target on apply. Can exist
  anywhere in the source state; patterns are relative to the containing directory. Glob
  `**/.chezmoiremove` to find existing ones.

**OpenCode (`home/dot_config/opencode/`):**

Source directories use `exact_` prefixes (chezmoi strips unmanaged files on apply), but target paths
under `~/.config/opencode/` do not have these prefixes.

- `opencode.jsonc` - Main config (agent overrides, LSP, formatters, providers, MCP servers)
- `virtual-models.jsonc` - Agent models per provider, applied at startup by the `virtual-models`
  plugin. A new agent needs a mapping under every provider (pre-commit enforces). MUST NOT set agent
  `model` in `opencode.jsonc` or agent files; it overrides the plugin.
- `session-permissions.jsonc` - Permission rules the `session-permissions` plugin appends to every
  session when created, forked, or prompted (never idle ones); they evaluate after all configured
  rules, including repository configs. Use only to override false-positive matches that configured
  rules cannot (e.g., a repository deny); put policy in `opencode.jsonc` `permissions`.
- `AGENTS.md` - Global directives (the file at `~/.config/opencode/AGENTS.md`)
- `dcp.jsonc`, `cli.json` - Additional config files
- `exact_skills/` - Skill definitions (target: `~/.config/opencode/skills/`). Each subdirectory
  contains a `SKILL.md`. Some are managed via `.chezmoiexternal.toml` in this directory.
- `exact_agents/` - Custom agent definitions (target: `~/.config/opencode/agents/`). `build` is the
  only primary agent (built-in `plan` is disabled so sessions never switch agents and lose prompt
  caching); build plans through the `planning` skill, which submits via Plannotator. Read-only
  `acceptance` audits completed local work with a fresh high-capability model. Other specialists
  (`researcher`, `reviewer`, `upgrade-analyst`) are plain Markdown with self-contained protocols.
- `exact_commands/` - Slash commands (target: `~/.config/opencode/commands/`)
- `exact_plugins/` - Plugins (target: `~/.config/opencode/plugins/`). Hooks that rewrite model
  requests MUST keep earlier conversation content byte-identical across requests; edits invalidate
  prompt caching and signed thinking. Inject reminders via `lib/system-reminder.ts`. Tools for
  permission-scoped agents MUST pass `options: DIRECT_TOOL` (`lib/direct-tool.ts`); Code Mode tools
  are unreachable without `execute`, which also grants unpermissioned `fetch`.
- `.chezmoitemplates/` - Reusable template partials scoped to OpenCode config. Template names share
  a global namespace across all `.chezmoitemplates/` directories in the source state; prefix names
  with `opencode-` to avoid collisions. Current partials: `opencode-coding-directives.md`
  (development, tools, git, architecture), `opencode-testing-directives.md` (behavioral testing and
  failure diagnosis).

**Tool configs:** `home/dot_config/` contains per-tool configuration directories (git, kitty, mise,
lazygit, etc.). Browse the directory to discover what's managed.

## Conventions

**Test ownership:**

- Self-contained projects keep tests in their own `tests/` directory (e.g.,
  `scripts/<project>/tests/`).
- Managed code without a project-level test directory uses root `tests/<component>/`, grouped by
  tool or purpose, not language. Create directories only when adding tests.
- Durable tests cover only code with its own logic: `scripts/<project>/`, directory plugins
  (`*.test.ts` beside their modules), and the suites under Test execution. Verify everything else
  (tool installs, config values, delegating wrappers, agents, skills, commands, single-file plugins
  and extensions) by template rendering, `chezmoi apply --dry-run`, pre-commit, or a disposable
  check. Global test-first rules apply only inside this scope. MUST NOT run OpenCode to verify any
  plugin.
- A test that pins a config value, package ID, or path is a defect, not precedent: delete it when a
  change touches that value; never update it.

**Test execution:**

- Run affected behavioral suites separately; pre-commit is for static checks, not test execution.
- OpenCode plugin integration: run `bun test tests/opencode` from the repo root.
- OpenCode test dependencies: run `bun install --cwd tests/opencode --frozen-lockfile` first.
- OpenCode directory plugins: run `bun test home/dot_config/opencode/exact_plugins`.
- Commit workflow: run `python -m unittest discover -s tests/commit` (requires commitlint and yq).
- Document new root-suite commands here; project-owned commands belong in that project's guidance.

**Commit messages:** Conventional Commits, enforced by commitlint (`commitlint.config.mjs`; `wip`
subjects bypass it). Scopes name a broad area, never a single tool; omit the scope when a commit
spans areas:

- `agents` - OpenCode and its agents, skills, commands, and plugins
- `scripts` - custom CLIs in `scripts/` and `home/dot_local/bin/`
- `shell` - zsh startup, functions, and prompt
- `terminal` - terminal emulator and multiplexer
- `git` - git config, git helpers, and git UIs
- `tooling` - tool installation, updates, and per-app configs
- `repo` - repo infrastructure: linters, pre-commit, Renovate, `docs/`, root tests

Classify the semantic outcome first; paths only decide the type when no behavior changes:

- `docs:` - `docs/**`, `*.md`, including AGENTS.md and skill or agent prose
- `chore:` - root linter, formatter, pre-commit, and `mise.toml` config
- `test:` - `tests/**`, `scripts/*/tests/**`
- `feat:` / `fix:` / `refactor:` / `perf:` - managed dotfiles, scripts, plugins, and agent or skill
  behavior, judged by what changes for the user or agent at runtime

Use `!` for changes that break an existing workflow or require manual migration after apply.

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

- P10k instant prompt must be early in .zshrc; nothing after it may print or read the terminal
- Completion dirs join fpath before compinit (03); fzf-tab loads after compinit and before
  widget-wrapping plugins (04)
- mise split: shims in `.zshenv` for shells that skip `.zshrc`, full `mise activate` in 01 for
  interactive ones. OpenCode shell commands get their directory's mise env from the `mise-env`
  plugin, not shell startup files.
- Tool-presence checks (`$+commands[x]`) for mise-managed tools must run after `mise activate`
- Cache generator output with `_source_cached` (07) instead of `eval "$(tool ...)"`

## Workflow

1. Edit: `chezmoi edit <file>` or directly in source
2. Preview: `chezmoi diff`
3. Test: `chezmoi apply --dry-run`
4. Apply: `chezmoi apply`

## Upstream References

### humanizer skill (upstream sync)

`home/dot_config/opencode/exact_skills/humanizer/SKILL.md` is a semantic compression of
[blader/humanizer](https://github.com/blader/humanizer), not a verbatim copy. Sync it with
`.opencode/commands/sync-humanizer.md`. MUST merge upstream detection behavior into the local
structure; MUST NOT overwrite the skill. Preserve every local-owned section exactly, especially the
marked `User Voice Profile` block.

## Constraints

### Git Operations

NEVER run git mutations (add/commit/reset/push/rebase/merge) without explicit user approval. ASK
before running these commands unless the user's request clearly authorizes them (e.g., "commit this"
or "push to remote").
