# Dotfiles

Modern dotfiles managed by chezmoi with automated setup, age encryption, and cross-platform support.

## Quick Start

```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply --ssh rcdailey/dotfiles
```

This installs chezmoi, clones the repo, and applies all configurations automatically.

## Environment Secrets

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
