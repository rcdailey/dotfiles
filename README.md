# Dotfiles

Modern dotfiles managed by chezmoi with automated setup, age encryption, and cross-platform support.

## Quick Start

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply --ssh rcdailey/dotfiles
```

This installs chezmoi, clones the repo, and applies all configurations automatically.

## Features

- **Automated Installation**: Scripts handle Homebrew, mise, and shell setup
- **Age Encryption**: Secure handling of sensitive files
- **Modern Zsh**: Zinit plugin manager with Powerlevel10k theme
- **Tool Management**: mise for development tools, minimal Homebrew
- **Claude Code Integration**: Custom hooks and commands
- **Git Utilities**: 20+ custom git scripts and extensive aliases

## Key Tools

- **chezmoi**: Dotfile management with templating
- **mise**: Development tool version management
- **Zinit**: Fast zsh plugin manager
- **age**: Modern file encryption
- **Claude Code**: AI-powered development assistant

## Daily Commands

```bash
# chezmoi management
chezmoi status         # Check for changes
chezmoi diff          # Preview changes
chezmoi apply         # Apply changes
chezmoi update        # Pull and apply

# Tool updates
brew upgrade          # Update system packages
mise upgrade          # Update development tools
zinit update --all    # Update zsh plugins
```

## Configuration

- Uses `.chezmoiroot` set to `home/` directory
- Age encryption for sensitive files (SSH keys, etc.)
- Cross-platform support (macOS, Linux, Windows)
- Environment separation (work/personal/other)

For detailed information, see `CLAUDE.md` and individual configuration files.
