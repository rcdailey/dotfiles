# Dotfiles

Modern dotfiles managed by chezmoi with automated setup, age encryption, and cross-platform support.

## Setup

### Prerequisites

Generate an SSH key and add it to GitHub:

```bash
ssh-keygen -t ed25519 && cat ~/.ssh/id_ed25519.pub
```

Add the public key at <https://github.com/settings/ssh/new>

Ensure git is installed (usually present by default on macOS and Fedora).

### Installation

Install dotfiles via chezmoi:

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply --ssh rcdailey/dotfiles
```

Run automated system setup:

```bash
setup-system
```

This installs and configures:

- Package manager (Homebrew on macOS)
- Shell (zsh) and sets as default
- Terminal (kitty) with Fira Code font
- Password manager (rbw) with your Bitwarden email
- AI coding assistant (OpenCode)
- Runtime manager (mise) and development tools

Reboot to activate zsh:

```bash
sudo reboot
```

> [!WARNING]
>
> A full reboot is required. Logout alone may not update `$SHELL`.

After reboot, launch kitty terminal. The shell will prompt for Bitwarden login and load secrets
automatically.
