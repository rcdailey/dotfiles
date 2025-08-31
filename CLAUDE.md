# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## Overview

This is a personal dotfiles repository managed by chezmoi, a dotfile manager that handles templating
and cross-platform configuration management. The repository contains shell configurations, git
settings, aliases, custom scripts, and various tool configurations.

## Architecture

### Directory Structure

**Important:** This repository uses `.chezmoiroot` set to `home/`, meaning only the `home/`
directory contains chezmoi-managed dotfiles. Files outside `home/` are infrastructure/support files
specific to this repository and are not managed by chezmoi.

- `home/` - The chezmoi root directory containing all managed dotfiles
- `home/dot_*` - Files that start with `dot_` become `.filename` in the target
- `home/private_*` - Files with `private_` prefix get restrictive permissions (600)
- `home/executable_*` - Files with `executable_` prefix become executable
- Files outside `home/` (e.g., `README.md`, `scripts/`) - Repository infrastructure, not managed by
  chezmoi

### Key Configuration Areas

**Shell Configuration (Modern Zsh Setup with Optimal Initialization Order):**

- `home/dot_zshenv.tmpl` - XDG Base Directory variables with platform-specific paths (loaded before
  .zshrc)
- `home/dot_zprofile` - Profile-level initialization for login shells
- `home/dot_zshrc` - Main zsh configuration with critical timing optimizations
- `home/dot_config/exact_zsh/` - Numbered configuration files loaded in strict sequence:
  - `01-environment.sh` - Environment variables and exports (console-safe)
  - `02-zinit.sh` - Zinit plugin manager initialization
  - `03-completion.sh` - Completion system + Powerlevel10k bug workaround
  - `04-plugins.sh` - Plugin loading with strict timing (fzf-tab critical order)
  - `05-configuration.sh` - Aliases, functions, shell options, PATH modifications
  - `06-platform.sh.tmpl` - Consolidated platform-specific configurations

**CRITICAL Initialization Order Requirements:**

- XDG variables must be in .zshenv.tmpl (before .zshrc processing)
- Powerlevel10k instant prompt must be early in .zshrc
- fzf-tab MUST load after compinit, before widget-wrapping plugins
- mise split: `mise env` before instant prompt, `mise activate` after
- Never modify this loading order without understanding timing dependencies
- PREFER adding lazy-loadable plugins to existing `wait lucid for \` lists for performance

**Essential Bug Workaround (DO NOT REMOVE):**

- `03-completion.sh` contains critical Powerlevel10k bug fix for GitHub issue #2887
- Workaround prevents infinite "bad pattern: (utf|UTF)(-|)8" error loop during tab completion
- Function wrapper suppresses stderr from _p9k_on_expand until upstream fix is available
- Removing this workaround will break tab completion completely

**Git Configuration:**

- `home/dot_gitconfig.tmpl` - Comprehensive git configuration with:
  - Extensive alias system for common operations
  - Delta pager configuration for better diffs
  - WSL-specific Beyond Compare integration
  - Custom pretty-print formats for log viewing

**Custom Scripts:**

- `home/git-scripts/` - Collection of git utility scripts:
  - `git-*` commands become available as git subcommands
  - Includes branch management, cleanup, and analysis tools

**Package Management:**

- `home/Brewfile.tmpl` - Homebrew package definitions with templating support
- `home/.chezmoiscripts/run_onchange_before_01_install-homebrew.sh.tmpl` - Homebrew installation
- `home/.chezmoiscripts/run_onchange_before_02_install-mise.sh.tmpl` - Mise tool installation
- `home/.chezmoiscripts/run_onchange_before_03_remove-old-brew-packages.sh.tmpl` - Package cleanup
- `home/.chezmoiscripts/run_onchange_after_03_setup-zsh-shell.sh.tmpl` - Zsh shell setup
- `home/.chezmoiscripts/run_onchange_after_01_install-mise-tools.sh.tmpl` - Mise tool installation
- `home/.chezmoiscripts/run_onchange_after_02_install-homebrew-packages.sh.tmpl` - Homebrew package
  installation

**Tool Configurations:**

- `home/dot_config/k9s/` - Kubernetes dashboard configuration
- `home/dot_config/helmfile/` - Helm configuration
- `home/dot_config/karabiner/` - macOS key remapping (if applicable)

### Templating System

Files ending in `.tmpl` are chezmoi templates that can:

- Include conditional content based on OS, environment variables, etc.
- Use `{{ if eq .chezmoi.os "linux" }}` for OS-specific sections
- Use `{{ if eq .env "work" }}` for environment-specific configurations

### File Removal Management

**`.chezmoiremove` File Handling:**

- A `.chezmoiremove` file (with optional `.tmpl` extension) contains a list of targets to remove
  from the destination
- Always interpreted as a template regardless of extension
- **IMPORTANT**: This repository has an existing `home/.chezmoiremove` file with organized sections

**Organization Strategy:**

- Group entries by year-month with clear section headers
- Include "PRUNE AFTER" dates for each section (typically 30+ days after changes)
- Add inline comments showing where files moved (`# → new-location`)
- Include context about why changes were made
- Use template at bottom for consistent future additions

**Maintenance:**

- Review periodically and remove old entries after prune dates
- Longer retention for major reorganizations (60-90 days)
- Keep recent entries until confirmed working on all target systems

### Key Features

- **Cross-platform compatibility** with platform-specific overrides
- **Modular zsh configuration** preventing monolithic shell files
- **Extensive git alias system** for productivity
- **Professional development environment** with tool integrations
- **Secure handling** of private files and SSH configurations

### Platform-Specific File Management

**Platform exclusion using `.chezmoiignore`:**

- Use `.chezmoiignore` patterns to exclude files on specific platforms
- Pattern: `{{ if ne .chezmoi.os "target_os" }}` to exclude files when NOT on target OS
- Example: Linux-only files excluded on macOS/Windows:

```txt
{{ if ne .chezmoi.os "linux" }}
.local/bin/setup-xremap
.config/xremap/**
{{ end }}
```

- Common OS values: `"linux"`, `"darwin"` (macOS), `"windows"`
- PREFER `.chezmoiignore` over template conditionals for entire file exclusion

## Development Workflow

When making changes:

1. Edit files in the chezmoi source directory (`chezmoi edit <file>`)
2. Preview changes with `chezmoi diff`
3. Apply changes with `chezmoi apply`
4. Commit changes to the repository using `chezmoi git` commands

For new files:

1. Add them with `chezmoi add <file>`
2. Use appropriate prefixes (`dot_`, `private_`, `executable_`) for the target behavior

## Performance Optimization

- FOR zsh performance issues, use <https://github.com/romkatv/zsh-bench> for analysis and
  optimization.
