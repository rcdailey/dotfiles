# Dotfiles

Modern dotfiles managed by chezmoi with automated setup, age encryption, and cross-platform support.

## Quick Start

```bash
curl -fsSL https://raw.githubusercontent.com/rcdailey/dotfiles/master/install.sh | bash
```

This installs everything: chezmoi, zsh, mise, fonts, Claude Code, and more. Reboot when complete.

## Features

- **Automated Installation**: Bootstrap script handles all dependencies
- **Age Encryption**: Secure handling of sensitive files
- **Modern Zsh**: Zinit plugin manager with Powerlevel10k theme
- **Tool Management**: mise for development tools
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
mise upgrade          # Update development tools
zinit update --all    # Update zsh plugins
```

## Configuration

- Uses `.chezmoiroot` set to `home/` directory
- Age encryption for sensitive files (SSH keys, etc.)
- Cross-platform support (macOS, Linux, Windows)
- Environment separation (work/personal/other)

For detailed information, see `CLAUDE.md` and individual configuration files.
