# CLAUDE.md

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
- `home/dot_config/exact_zsh/functions/` - Autoloaded zsh functions (bwu, clip, gi, pcc, etc.)

**Scripts:**

- `home/git-scripts/` - Git helper scripts and subcommands

**Chezmoi internals:**

- `home/.chezmoiscripts/` - Lifecycle hooks; `run_onchange_` triggers on dependency changes
- `home/.chezmoitemplates/` - Reusable template snippets
- `.chezmoiexternal.toml` - External file dependencies

**Tool configs (`home/dot_config/`):** git, helmfile, k9s, kitty, lazygit, mise, opencode,
powershell, ripgrep, systemd, xremap, etc.

**Terminal:** kitty (all platforms) - `home/dot_config/kitty/`

## Conventions

**Chezmoi prefixes:** `dot_` = dotfile, `private_` = 600 perms, `executable_` = +x, `exact_` =
directory matches exactly (removes unmanaged files)

**Template variables:** `.chezmoi.os` ("linux"/"darwin"/"windows"), `.chezmoi.hostname`,
`.chezmoi.username`. Custom data via `.chezmoi.toml.tmpl`.

**Platform exclusion:** Prefer `.chezmoiignore` patterns over template conditionals.

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
