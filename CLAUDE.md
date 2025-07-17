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

**Shell Configuration (Modular Bash Setup):**
- `home/dot_bashrc` - Main bash configuration that sources modular files
- `home/dot_config/bash/` - Modular bash configuration directory:
  - `completion.sh` - Bash completion settings
  - `exports.sh` - Environment variables and exports
  - `functions.sh` - Custom bash functions
  - `mise.sh` - Mise (formerly rtx) tool activation
  - `nvm.sh` - Node Version Manager setup
  - `path.sh` - PATH modifications
  - `platform.sh.tmpl` - Platform-specific configurations
  - `prompt.sh` - Shell prompt configuration
  - `platforms/` - Platform-specific overrides (darwin.sh, linux.sh, windows.sh)

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

**Tool Configurations:**
- `home/dot_config/k9s/` - Kubernetes dashboard configuration
- `home/dot_config/helmfile/` - Helm configuration
- `home/dot_config/karabiner/` - macOS key remapping (if applicable)

### Templating System
Files ending in `.tmpl` are chezmoi templates that can:
- Include conditional content based on OS, environment variables, etc.
- Use `{{ if eq .chezmoi.os "linux" }}` for OS-specific sections
- Use `{{ if eq .env "work" }}` for environment-specific configurations

### Key Features

- **Cross-platform compatibility** with platform-specific overrides
- **Modular bash configuration** preventing monolithic shell files
- **Extensive git alias system** for productivity
- **Professional development environment** with tool integrations
- **Secure handling** of private files and SSH configurations

## Development Workflow

When making changes:
1. Edit files in the chezmoi source directory (`chezmoi edit <file>`)
2. Preview changes with `chezmoi diff`
3. Apply changes with `chezmoi apply`
4. Commit changes to the repository using `chezmoi git` commands

For new files:
1. Add them with `chezmoi add <file>`
2. Use appropriate prefixes (`dot_`, `private_`, `executable_`) for the target behavior
