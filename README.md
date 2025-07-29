# Dotfiles

Personal dotfiles repository managed by chezmoi, featuring a modern zsh configuration with Zinit
plugin manager, Powerlevel10k theme, and comprehensive development tools.

## Architecture

This repository uses chezmoi with `.chezmoiroot` set to `home/`, meaning only the `home/` directory
contains managed dotfiles. Key features:

- **Modular zsh configuration** with Zinit plugin manager
- **Powerlevel10k theme** with instant prompt support
- **Cross-platform compatibility** with platform-specific overrides
- **Comprehensive git configuration** with extensive aliases
- **Custom development scripts** and utilities

### Directory Structure

```txt
home/
├── dot_zshrc                    # Main zsh configuration
├── dot_config/exact_zsh/        # Modular zsh configuration
│   ├── init/                    # Initialization scripts (load order)
│   │   ├── 01-zinit.sh          # Zinit plugin manager setup
│   │   ├── 02-environment.sh    # Environment variables
│   │   └── 03-plugins.sh        # Plugin loading configuration
│   ├── aliases.sh               # Command aliases
│   ├── completion.sh            # Completion settings
│   ├── functions.sh             # Custom functions
│   └── platforms/               # Platform-specific overrides
├── dot_gitconfig.tmpl           # Git configuration with aliases
├── git-scripts/                 # Custom git utilities
└── dot_p10k.zsh                 # Powerlevel10k theme configuration
```

## Initial Setup

### Prerequisites

**macOS/Linux - Homebrew:**

```zsh
sudo apt update && sudo apt install -y build-essential procps curl file git
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Windows - Chocolatey (PowerShell as Admin):**

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### chezmoi Installation & Setup

**Install chezmoi:**

```zsh
# macOS/Linux
brew install chezmoi

# Windows
choco install chezmoi
```

**Initialize and apply dotfiles:**

```zsh
chezmoi init rcdailey --ssh --apply
```

### Post-Installation

After applying dotfiles, your zsh will automatically:

- Install Zinit plugin manager on first run
- Load Powerlevel10k theme with instant prompt
- Configure fzf-tab enhanced completion
- Set up development tool integrations

## Shell Configuration

### Zsh Features

- **Zinit Plugin Manager**: Fast, feature-rich plugin management
- **Powerlevel10k Theme**: High-performance, customizable prompt
- **Enhanced Completion**: fzf-tab for interactive completions
- **History Optimization**: Shared history with deduplication
- **Smart Aliases**: Essential development shortcuts

### Key Plugins

- `zsh-history-substring-search`: Arrow key history navigation
- `zsh-autosuggestions`: Command completion suggestions
- `zsh-syntax-highlighting`: Syntax highlighting for commands
- `fzf-tab`: Interactive fuzzy completion
- `lukechilds/zsh-nvm`: Node version management

### Aliases & Functions

```zsh
# Essential shortcuts
cm        # chezmoi
c         # docker compose
tf        # terraform
k         # kubectl (from oh-my-zsh plugin)

# Navigation
1..       # cd ..
2..       # cd ../..
# ... up to 8..

# Development
gi        # gitignore.io integration
claude    # Claude Code with local override support
```

## Daily Commands

### chezmoi Management

```zsh
# Quick status check
chezmoi status

# Preview changes
chezmoi diff

# Apply changes
chezmoi apply

# Edit a dotfile
chezmoi edit ~/.zshrc

# Add new file
chezmoi add ~/.vimrc

# Update from remote
chezmoi update

# Git operations
chezmoi git -- status
chezmoi git -- add .
chezmoi git -- commit -m "Update config"
```

### Zsh-Specific Commands

```zsh
# Reload configuration
exec zsh

# Configure Powerlevel10k theme
p10k configure

# Plugin management
zinit update --all
zinit status

# Performance analysis
zsh-bench  # Run performance benchmark
```
