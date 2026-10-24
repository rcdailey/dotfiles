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
~/.local/bin/setup-system
```

This installs and configures:

- Package manager (Homebrew on macOS and Fedora)
- Shell (zsh) and sets it as the login shell
- Terminal (kitty) with Fira Code font
- Password manager (rbw; chezmoi already configured it)
- Runtime manager (mise) and its tools, including OpenCode

It is safe to rerun. Log out and back in (or reboot) to start using zsh, then launch kitty.
