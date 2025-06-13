# Dotfiles

Personal dotfiles cheat sheet for quick setup and daily use.

## 🚀 Initial Setup

### Package Manager Installation

**macOS/Linux - Homebrew:**

```bash
sudo apt update && sudo apt install -y build-essential procps curl file git
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Windows - Chocolatey (PowerShell as Admin):**

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### chezmoi Installation & Setup

**Install chezmoi (macOS/Linux):**

```bash
brew install chezmoi
```

**Install chezmoi (Windows):**

```powershell
choco install chezmoi
```

**Initialize and apply dotfiles:**

```bash
chezmoi init rcdailey --ssh --apply
```

## 🔄 Daily Commands

```bash
# Quick status check
chezmoi status

# Preview changes
chezmoi diff

# Apply changes
chezmoi apply

# Edit a dotfile
chezmoi edit ~/.bashrc

# Add new file
chezmoi add ~/.vimrc

# Update from remote
chezmoi update
```
