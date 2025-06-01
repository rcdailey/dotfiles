# Copilot Instructions for chezmoi

## 🚨 Always refer to <https://www.chezmoi.io> for authoritative information

chezmoi manages dotfiles across multiple machines using templates and scripts.

## File Naming

### Prefixes

- `dot_`: Files starting with `.` (e.g., `dot_bashrc` → `.bashrc`)
- `private_`: Owner-only permissions
- `executable_`: Make executable
- `encrypted_`: Encrypted files
- `exact_`: Remove unmanaged files from target directory
- `symlink_`: Create symbolic links
- `run_`: Scripts executed during apply
- `run_once_`: Execute once per content hash
- `run_onchange_`: Execute when content changes
- `run_before_`: Execute before file operations
- `run_after_`: Execute after file operations

### Suffixes

- `.tmpl`: Process as template
- `.literal`: Bypass name processing

## Key Files

- `chezmoi.toml`: Main configuration
- `.chezmoidata.toml`: Template data
- `.chezmoiignore`: Ignore patterns
- `.chezmoiexternal.toml`: External files/repos

## Essential Commands

```bash
# Initialize
chezmoi init
chezmoi init --apply https://github.com/user/dotfiles.git

# Add files
chezmoi add ~/.bashrc
chezmoi add --template ~/.gitconfig

# Edit and apply
chezmoi edit ~/.bashrc
chezmoi diff
chezmoi apply --dry-run
chezmoi apply

# Status and updates
chezmoi status
chezmoi update

# Git operations
chezmoi git add .
chezmoi git commit -m "Update"
```

## Templates

Use Go templates with `.tmpl` suffix:

```go
{{ if eq .chezmoi.os "linux" }}
# Linux config
{{ else if eq .chezmoi.os "darwin" }}
# macOS config
{{ end }}

# Common variables
{{ .chezmoi.hostname }}
{{ .chezmoi.os }}
{{ .chezmoi.username }}
{{ .chezmoi.homeDir }}
```

## Custom Data

Define in `.chezmoidata.toml`:

```toml
email = "user@example.com"
[work]
    email = "user@company.com"
```

Use in templates:

```go
email = {{ .email }}
{{ if .work }}
work_email = {{ .work.email }}
{{ end }}
```

## Security

```bash
# Encrypt sensitive files
chezmoi add --encrypt ~/.ssh/key

# Password managers
{{ bitwarden "item" }}
{{ onepassword "item" }}
```

## Guidelines

- Use `--dry-run` before applying changes
- Start simple, add complexity gradually
- Test on multiple machines
- Keep secrets encrypted or in password managers
