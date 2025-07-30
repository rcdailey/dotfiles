# Zsh + Zinit Getting Started Guide

This guide covers the modern zsh setup in this dotfiles repository, using Zinit plugin manager for
optimal performance and automation.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Shell Setup Instructions](#shell-setup-instructions)
  - [iTerm2 (macOS)](#iterm2-macos)
  - [WSL2 (Windows)](#wsl2-windows)
  - [VS Code Integrated Terminal](#vs-code-integrated-terminal)
  - [Verification Steps](#verification-steps)
- [Key Features Gained](#key-features-gained)
  - [Fish-Style Interactive Features](#1-fish-style-interactive-features)
  - [Enhanced Completions](#2-enhanced-completions)
  - [Advanced Navigation](#3-advanced-navigation)
  - [Powerful Globbing](#4-powerful-globbing)
- [Zinit Plugin System](#zinit-plugin-system)
  - [Essential Plugins](#essential-plugins-pre-configured)
  - [Oh-My-Zsh Functionality](#oh-my-zsh-functionality-via-snippets)
  - [Adding New Plugins](#adding-new-plugins)
- [Configuration Structure](#configuration-structure)
- [Customization](#customization)
  - [Changing Theme](#changing-theme)
  - [Adding Custom Aliases](#adding-custom-aliases)
  - [Platform-Specific Customizations](#platform-specific-customizations)
- [Troubleshooting](#troubleshooting)
  - [Slow Startup](#slow-startup)
  - [Plugin Issues](#plugin-issues)
  - [Completion Problems](#completion-problems)
  - [Migration Issues](#migration-issues)
- [Performance Tips](#performance-tips)
- [Migration Benefits Summary](#migration-benefits-summary)
- [Next Steps](#next-steps)
- [Resources](#resources)

## Overview

This setup migrated from bash to zsh with:

- **Zinit plugin manager** - 50-80% faster than Oh-My-Zsh
- **Automated installation** via chezmoi externals
- **Fish-style features** - autosuggestions, syntax highlighting
- **Oh-My-Zsh compatibility** - can load any OMZ plugin via snippets

## Quick Start

```bash
# Apply dotfiles on new machine
chezmoi init --apply https://github.com/yourusername/dotfiles

# Zinit and all plugins install automatically
# Follow shell switching instructions below to complete setup
```

## Shell Setup Instructions

### **iTerm2 (macOS)**

**1. Install recommended font:**

```bash
# Install Nerd Font for best theme experience
brew install --cask font-fira-code-nerd-font
```

**2. Set zsh as default shell:**

```bash
chsh -s $(which zsh)
```

**3. Configure iTerm2:**

- Open iTerm2 → Preferences (⌘,) → Profiles
- Select your profile → General tab
- Set "Command" to "Login shell" (default)
- Go to Text tab → Font section → Click "Change Font"
- Search for "FiraCode" and select "FiraCodeNerdFont-Regular"
- Set size to 12-14pt
- Click OK

**4. Restart iTerm2** - you'll now have full zsh + Zinit functionality

### **WSL2 (Windows)**

**1. In your WSL2 distribution:**

```bash
# Install zsh if not present
sudo apt update && sudo apt install zsh

# Set as default shell
chsh -s $(which zsh)
```

**2. Configure Windows Terminal:**

- Open Windows Terminal → Settings (Ctrl+,)
- Select your WSL profile from the sidebar
- Ensure "Command line" is set to default or: `wsl.exe -d YourDistroName`
- For fonts: Go to Appearance tab
- Download "Cascadia Code PL" or install via:

  ```powershell
  # In PowerShell as Administrator
  winget install Microsoft.CascadiaCode
  ```

- Set Font face to "Cascadia Code PL" or "CascadiaCode NF"

**3. Restart WSL2** - open new Windows Terminal tab

### **VS Code Integrated Terminal**

**1. Update VS Code settings (Ctrl+,):** Search for "terminal integrated default profile" and set:

- **macOS**: Select "zsh"
- **Linux**: Select "zsh"
- **Windows**: Keep "PowerShell" (for PowerShell) or "zsh" (for WSL)

**Or manually edit settings.json:**

```json
{
    "terminal.integrated.defaultProfile.osx": "zsh",
    "terminal.integrated.defaultProfile.linux": "zsh",
    "terminal.integrated.profiles.osx": {
        "zsh": {
            "path": "/bin/zsh",
            "args": ["-l"]
        }
    },
    "terminal.integrated.profiles.linux": {
        "zsh": {
            "path": "/bin/zsh",
            "args": ["-l"]
        }
    }
}
```

**2. Recommended VS Code extensions:**

- "Zsh" by Dieter Meirbach - syntax highlighting for zsh files
- "Zinit" by Dieter Meirbach - Zinit configuration support

**3. Reload VS Code** or open new integrated terminal

### **Verification Steps**

After switching on any platform:

**1. Test basic functionality:**

```bash
echo $SHELL          # Should show /bin/zsh or similar
which zinit          # Should show zinit function is loaded
```

**2. Test Zinit features:**

```bash
git st               # Should autocomplete to "git status"
ls **/*.md           # Test recursive globbing
cd -                 # Should show directory stack
```

**3. Test interactive features:**

- Type a command and see syntax highlighting (green = valid, red = invalid)
- Start typing and see autosuggestions (gray text from history)
- Press ↑ after typing "git" to see history substring search

**4. Apply your dotfiles and reload:**

```bash
chezmoi apply
source ~/.zshrc
```

**5. Test font/icons (if using Nerd Font):**

```bash
echo "   "  # Should show various icons
```

## Key Features Gained

### 1. Fish-Style Interactive Features

**Autosuggestions** (gray text as you type):

```bash
git st[TAB]  # suggests "git status" from history
```

**Syntax Highlighting** (colors as you type):

- Valid commands = green
- Invalid commands = red
- Strings, options highlighted

**History Substring Search**:

```bash
git [↑]  # cycles through git commands in history
```

### 2. Enhanced Completions

**Smart Tab Completion**:

```bash
kubectl get [TAB]  # shows pods, services, deployments with descriptions
docker run [TAB]   # shows available images
cd [TAB]           # shows only directories
```

**Case-Insensitive Matching**:

```bash
cd DOC[TAB]  # matches Documents/
```

### 3. Advanced Navigation

**Auto-cd** (type directory name to cd):

```bash
Documents      # equivalent to: cd Documents
..             # equivalent to: cd ..
```

**Directory Stack**:

```bash
cd -[TAB]      # shows numbered directory history
cd -2          # go to 2nd recent directory
```

### 4. Powerful Globbing

**Recursive Patterns**:

```bash
ls **/*.txt           # all .txt files recursively
ls **/*.{js,ts}       # all JS/TS files recursively
```

**File Attribute Matching**:

```bash
ls *(.)               # only files (not directories)
ls *(/)               # only directories
ls *(m-1)             # files modified in last day
ls *(L+100M)          # files larger than 100MB
ls -ld *(/om[1,3])    # 3 newest directories
```

**Replace Complex Aliases**:

```bash
# Instead of custom lr alias:
ls **/*               # recursive listing

# Instead of custom lk alias:
ls -l *(L+10M)        # files larger than 10MB

# Instead of custom lt alias:
ls -l *(om)           # newest files first
```

## Zinit Plugin System

### Essential Plugins (Pre-configured)

**zsh-autosuggestions**: Fish-style command suggestions **zsh-syntax-highlighting**: Real-time
command validation **zsh-history-substring-search**: Better history navigation

### Oh-My-Zsh Functionality (Via Snippets)

```bash
# Git plugin provides 100+ aliases:
gst                   # git status
gco                   # git checkout
gcm                   # git commit -m
gp                    # git push
gl                    # git pull
glog                  # git log --oneline --decorate --graph

# Kubectl plugin provides k8s shortcuts:
k                     # kubectl
kg                    # kubectl get
kd                    # kubectl describe

# Docker plugin provides shortcuts:
dps                   # docker ps
dpa                   # docker ps -a
di                    # docker images
```

### Adding New Plugins

Edit `~/.zshrc` and add:

```bash
# For community plugins:
zinit load "username/plugin-name"

# For Oh-My-Zsh plugins:
zinit snippet "OMZP::plugin-name"
```

Then reload: `source ~/.zshrc`

## Configuration Structure

```txt
~/.config/zsh/
├── aliases.sh          # Custom aliases and functions
├── completion.sh       # Completion settings
├── exports.sh          # Environment variables
├── functions.sh        # Custom functions
├── mise.sh            # Mise tool activation
├── nvm.sh             # Node version manager
├── path.sh            # PATH modifications
├── platform.sh.tmpl   # Platform detection
└── platforms/         # Platform-specific configs
    ├── darwin.sh      # macOS settings
    ├── linux.sh       # Linux settings
    └── windows.sh     # Windows/WSL settings
```

## Customization

### Changing Theme

The setup uses `sindresorhus/pure` theme. To change:

```bash
# In ~/.zshrc, replace the theme lines:
zinit ice compile'(pure|async).zsh' pick'async.zsh' src'pure.zsh'
zinit load sindresorhus/pure

# With another theme, e.g., Powerlevel10k:
zinit ice depth=1
zinit load romkatv/powerlevel10k
```

### Adding Custom Aliases

Edit `~/.config/zsh/aliases.sh`:

```bash
# Add your custom aliases
alias myalias="command"
```

### Platform-Specific Customizations

Edit the appropriate platform file:

- macOS: `~/.config/zsh/platforms/darwin.sh`
- Linux: `~/.config/zsh/platforms/linux.sh`
- Windows/WSL: `~/.config/zsh/platforms/windows.sh`

## Troubleshooting

### Slow Startup

Use the performance analysis tool noted in CLAUDE.md:

```bash
git clone https://github.com/romkatv/zsh-bench
cd zsh-bench
./zsh-bench
```

### Plugin Issues

```bash
# Reload zinit and plugins
zinit self-update
zinit update --all
source ~/.zshrc
```

### Completion Problems

```bash
# Rebuild completion cache
rm ~/.zcompdump*
autoload -Uz compinit
compinit
```

### Migration Issues

**Array indexing**: Zsh arrays start at 1, not 0

```bash
# Add to ~/.zshrc if needed:
setopt KSH_ARRAYS  # Use bash-style array indexing
```

**Globbing errors**: Zsh fails on unmatched globs

```bash
# Add to ~/.zshrc if needed:
setopt NULL_GLOB   # Return empty for unmatched globs
```

## Performance Tips

1. **Use `zinit load` for plugins you always need**
2. **Use `zinit ice lucid` for faster loading**
3. **Minimize plugins** - start with essentials, add as needed
4. **Use `zsh-bench`** to identify bottlenecks

## Migration Benefits Summary

| Feature            | Bash           | Zsh + Zinit                   |
| ------------------ | -------------- | ----------------------------- |
| Startup time       | ~200ms         | ~100ms (50% faster)           |
| Completions        | Manual setup   | Automatic via plugins         |
| History search     | Basic          | Substring + highlighting      |
| Command validation | None           | Real-time syntax highlighting |
| Suggestions        | None           | Fish-style autosuggestions    |
| Globbing           | Basic          | Advanced patterns             |
| Navigation         | Manual aliases | Auto-cd + directory stack     |
| Maintenance        | Custom scripts | Community plugins             |

## Next Steps

1. **Test the setup**: Open new terminal, verify all features work
2. **Customize theme**: Try Powerlevel10k for more visual information
3. **Add project-specific completions**: For tools not covered by plugins
4. **Explore advanced globbing**: Replace manual find commands
5. **Performance tune**: Use zsh-bench if startup becomes slow

## Resources

- [Zinit Documentation](https://github.com/zdharma-continuum/zinit)
- [Zsh Documentation](http://zsh.sourceforge.net/Doc/)
- [Pure Theme](https://github.com/sindresorhus/pure)
- [Performance Analysis](https://github.com/romkatv/zsh-bench)
- [Oh-My-Zsh Plugin List](https://github.com/ohmyzsh/ohmyzsh/wiki/Plugins)
