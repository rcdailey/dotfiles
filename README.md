# Dotfiles

Modern dotfiles managed by chezmoi with automated setup, age encryption, and cross-platform support.

## Setup

### Prerequisites

Generate an SSH key and add it to GitHub:

```bash
ssh-keygen -t ed25519 && cat ~/.ssh/id_ed25519.pub
```

Add the public key at <https://github.com/settings/ssh/new>

Install zsh and set as default shell (Fedora):

```bash
sudo dnf install -y zsh && chsh -s $(which zsh)
```

Install Fira Code font for kitty terminal:

```bash
brew install font-fira-code  # macOS
```

```bash
sudo dnf install fira-code-fonts  # Fedora
```

kitty uses Fira Code with `postscript_name` syntax for reliable cross-platform font matching. Icons
are provided by kitty's bundled Symbols Nerd Font fallback.

Then reboot:

```bash
sudo reboot
```

> [!WARNING]
>
> A full reboot is required. Logout alone may not update `$SHELL`.

### Installation

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply --ssh rcdailey/dotfiles
```

This installs chezmoi, clones the repo, and applies all configurations automatically.

## Configuration

### Environment Secrets

MCP servers and other tools require secrets stored in Bitwarden, accessed via rbw.

Install rbw (Fedora):

```bash
sudo dnf install rbw
```

Configure with your Bitwarden email:

```bash
rbw config set email <email>
```

Log in and unlock the vault:

```bash
rbw login
```

Export secrets to the current shell:

```bash
load_secrets
```

New terminals will show a warning if rbw is locked. Run `load_secrets` after unlocking to reload
secrets without restarting the shell.
