# Claude Instructions

## 🚨 IMPORTANT: Always ask permission before making any file changes

When a user reports an issue or asks about a problem, analyze and discuss potential solutions first.
Only make changes after the user explicitly requests or approves them.

## 🚨 Always refer to <https://www.chezmoi.io> for authoritative information

chezmoi manages dotfiles across multiple machines using templates and scripts.

## Essential Knowledge

- `.chezmoiignore` files are already treated as templates, so they do not need `.tmpl` extensions.
- Chezmoi requires all chezmoi-specific files except `.chezmoiroot` to be in the `home/` dir.
- All paths in `.chezmoiignore` must represent the paths in the actual system home directory (e.g.
  `.ssh/config`), not the path in the chezmoi repo (e.g. `private_dot_ssh/private_config`).

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

## Scripts

Scripts go in `home/.chezmoiscripts/` and are executed in alphabetical order according to the chezmoi documentation. This is why numbering is used in script filenames (e.g., `run_01_install_packages.sh`, `run_02_configure_tools.sh`).

### Script Types

- `run_`: Execute every time on `chezmoi apply`
- `run_onchange_`: Execute only when script content changes
- `run_once_`: Execute once per unique content version (tracked by SHA256 hash)
- `run_before_`: Execute before file operations
- `run_after_`: Execute after file operations

### Script Execution Order

- Scripts are sorted alphabetically before execution
- Each script type (`run_`, `run_onchange_`, `run_once_`, etc.) is sorted independently
- Use numeric prefixes to control execution order within each script type based on dependencies
- Consider what needs to run first (package installation, tool setup, configuration)
- Name scripts descriptively while maintaining proper ordering

### Examples

```text
home/.chezmoiscripts/
├── run_01_early_setup.sh
├── run_02_late_setup.sh
├── run_after_01_cleanup.sh
├── run_after_02_final_tasks.sh
├── run_before_01_prepare.sh
├── run_before_02_validate.sh
├── run_onchange_01_install_homebrew.sh
├── run_onchange_02_install_packages.sh
├── run_once_01_configure_git.sh
└── run_once_02_setup_ssh.sh
```

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

## Repository Structure & Patterns

### Key Directories
- `home/` - All chezmoi-managed files (required by chezmoi)
- `home/.chezmoitemplates/` - Custom templates (e.g., `powershell-profile.ps1`)
- `home/.chezmoiscripts/` - Install/setup scripts with platform detection
- `home/git-scripts/` - Custom git utility commands (all executable)
- `home/private_dot_ssh/` - SSH configuration with private permissions
- `home/dot_config/` - Application configurations organized by tool
- `home/dot_local/bin/` - Custom executable scripts

### Existing Configuration Files
- `home/dot_bash_aliases` - Bash aliases including `cm="chezmoi"`
- `home/dot_gitconfig.tmpl` - Git configuration with template variables
- `home/.chezmoi.toml.tmpl` - Main chezmoi config with interactive prompts
- `home/.chezmoiexternal.toml` - External file/repo management
- `home/.chezmoiignore` - Global ignore patterns

### Platform-Specific Patterns
- **Bash**: Uses `home/dot_config/bash/platform.sh.tmpl` to include platform-specific files
  - `platforms/darwin.sh` - macOS-specific (Homebrew, LSCOLORS)
  - `platforms/linux.sh` - Linux-specific configurations  
  - `platforms/windows.sh` - Windows/WSL-specific configurations
- **PowerShell**: Dual profile locations for compatibility
  - `Documents/PowerShell/Microsoft.PowerShell_profile.ps1.tmpl`
  - `dot_config/powershell/Microsoft.PowerShell_profile.ps1.tmpl`
- **Scripts**: Cross-platform install scripts (`.sh` and `.ps1` versions)

### Alias Patterns
- **Bash**: `alias name="command"` (in `dot_bash_aliases`)
- **PowerShell**: `function Name { command @args }; New-Alias alias Name -Force`

### Template Data Available
Based on `.chezmoi.toml.tmpl`, templates have access to:
- `.email` - User email address (prompted during init)
- `.env` - Environment: "work", "personal", or "other"  
- `.ssh_azure_hosts` - Additional Azure DevOps hostnames (work env only)
- Standard chezmoi variables (`.chezmoi.os`, `.chezmoi.hostname`, etc.)

### Security Patterns
- `private_` prefix for owner-only permissions (SSH configs)
- Modular SSH config in `config.d/` directory
- Interactive prompts for sensitive data rather than hardcoding

### Git Utility Scripts
The `git-scripts/` directory contains numerous custom git commands:
- Branch management (`git-ff-branch`, `git-push-current`)
- Repository analysis (`git-find-large-files.sh`, `git-commit-stats`)
- Cleanup utilities (`git-nuke.sh`, `git-merged`)

## Git Configuration Notes

- Git's `[color "decorate"]` settings only apply to automatic decorations with `--decorate`, not to
  custom pretty formats using `%d`. Custom pretty formats require manual color coding or
  post-processing to achieve different colors for local vs remote branches.