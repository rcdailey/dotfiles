#!/usr/bin/env bash
set -euo pipefail

# Dotfiles bootstrap script
# Usage: curl -fsSL https://raw.githubusercontent.com/rcdailey/dotfiles/master/install.sh | bash
#
# Environment variables:
#   DOTFILES_TEST=1     - Skip interactive prompts (for container testing)
#   DOTFILES_SKIP_SSH=1 - Skip SSH key generation
#   DOTFILES_SKIP_AGE=1 - Skip age key setup

GITHUB_USER="rcdailey"
GITHUB_REPO="dotfiles"
GITHUB_SSH_URL="https://github.com/settings/ssh/new"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

is_test_mode() { [[ "${DOTFILES_TEST:-}" == "1" ]]; }

wait_for_user() {
    if is_test_mode; then
        info "Test mode: skipping user prompt"
        return 0
    fi
    read -rp "$1 [Press Enter to continue] "
}

confirm() {
    if is_test_mode; then
        info "Test mode: auto-confirming"
        return 0
    fi
    read -rp "$1 [y/N] " response
    [[ "$response" =~ ^[Yy]$ ]]
}

command_exists() { command -v "$1" &>/dev/null; }

# Detect package manager
detect_package_manager() {
    if command_exists dnf; then
        echo "dnf"
    elif command_exists apt-get; then
        echo "apt"
    elif command_exists brew; then
        echo "brew"
    else
        error "No supported package manager found (dnf, apt, brew)"
        exit 1
    fi
}

install_packages() {
    local pm="$1"
    shift
    local packages=("$@")
    local to_install=()

    for pkg in "${packages[@]}"; do
        if ! command_exists "$pkg"; then
            to_install+=("$pkg")
        fi
    done

    if [[ ${#to_install[@]} -eq 0 ]]; then
        return 0
    fi

    info "Installing: ${to_install[*]}"
    case "$pm" in
        dnf)
            sudo dnf install -y "${to_install[@]}"
            ;;
        apt)
            sudo apt-get update
            sudo apt-get install -y "${to_install[@]}"
            ;;
        brew)
            brew install "${to_install[@]}"
            ;;
    esac
}

# Step 1: Install base dependencies
install_base_deps() {
    info "Checking base dependencies..."
    local pm
    pm=$(detect_package_manager)
    install_packages "$pm" git curl unzip
    success "Base dependencies ready"
}

# Step 2: Generate SSH key for GitHub
setup_ssh_key() {
    if [[ "${DOTFILES_SKIP_SSH:-}" == "1" ]]; then
        info "Skipping SSH key setup"
        return 0
    fi

    local ssh_key="$HOME/.ssh/id_ed25519"

    if [[ -f "$ssh_key" ]]; then
        success "SSH key already exists: $ssh_key"
        return 0
    fi

    info "Generating ed25519 SSH key for GitHub..."
    mkdir -p "$HOME/.ssh"
    chmod 700 "$HOME/.ssh"

    if is_test_mode; then
        ssh-keygen -t ed25519 -f "$ssh_key" -N "" -C "test@dotfiles"
    else
        ssh-keygen -t ed25519 -f "$ssh_key" -C "$(whoami)@$(hostname)"
    fi

    echo ""
    echo "========================================"
    echo "Add this public key to GitHub:"
    echo "========================================"
    cat "${ssh_key}.pub"
    echo ""
    echo "GitHub SSH settings: $GITHUB_SSH_URL"
    echo "========================================"
    echo ""

    wait_for_user "After adding the key to GitHub, press Enter to continue"
    success "SSH key configured"
}

# Step 3: Install and run chezmoi
setup_chezmoi() {
    if [[ -d "$HOME/.local/share/chezmoi" ]]; then
        success "chezmoi repo already initialized"
        chezmoi apply
        return 0
    fi

    info "Installing chezmoi and applying dotfiles..."
    sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply --ssh "${GITHUB_USER}/${GITHUB_REPO}"
    success "chezmoi dotfiles applied"
}

# Step 4: Age key setup
setup_age_key() {
    if [[ "${DOTFILES_SKIP_AGE:-}" == "1" ]]; then
        info "Skipping age key setup"
        return 0
    fi

    local age_key="$HOME/.config/chezmoi/key.txt"

    if [[ -f "$age_key" ]]; then
        success "Age key already exists"
        return 0
    fi

    warn "Age encryption key not found: $age_key"
    echo ""
    echo "If you have a backup of your age key, copy it to:"
    echo "  $age_key"
    echo ""
    echo "Then re-run: chezmoi apply"
    echo ""

    if ! is_test_mode; then
        wait_for_user "Press Enter to continue (age key can be added later)"
    fi
}

# Step 5: Install and set zsh as default
setup_zsh() {
    local pm
    pm=$(detect_package_manager)
    local current_shell
    current_shell=$(getent passwd "$USER" | cut -d: -f7)
    local zsh_path

    if ! command_exists zsh; then
        info "Installing zsh..."
        install_packages "$pm" zsh
    fi

    zsh_path=$(which zsh)

    if [[ "$current_shell" == "$zsh_path" ]]; then
        success "zsh is already the default shell"
        return 0
    fi

    info "Setting zsh as default shell..."
    if is_test_mode; then
        info "Test mode: skipping chsh (requires password)"
    else
        chsh -s "$zsh_path"
        success "Default shell changed to zsh"
    fi
}

# Step 6: Install mise
setup_mise() {
    if command_exists mise; then
        success "mise already installed"
    else
        info "Installing mise..."
        curl https://mise.run | sh
    fi

    export PATH="$HOME/.local/bin:$PATH"

    info "Running mise trust and upgrade..."
    mise trust --all 2>/dev/null || true
    mise upgrade --yes 2>/dev/null || mise install --yes
    success "mise tools installed"
}

# Step 7: Install rbw (Bitwarden CLI)
setup_rbw() {
    local pm
    pm=$(detect_package_manager)

    if command_exists rbw; then
        success "rbw already installed"
        return 0
    fi

    info "Installing rbw (Bitwarden CLI)..."
    case "$pm" in
        dnf)
            sudo dnf install -y rbw
            ;;
        apt)
            warn "rbw not in apt repos - install manually or use snap"
            return 0
            ;;
        brew)
            brew install rbw
            ;;
    esac

    if ! is_test_mode && command_exists rbw; then
        echo ""
        echo "Configure rbw with your Bitwarden account:"
        echo "  rbw config set email YOUR_EMAIL"
        echo "  rbw login"
        echo ""
        wait_for_user "Configure rbw now, then press Enter to continue"
    fi

    success "rbw installed"
}

# Step 8: Install FiraCode Nerd Font
setup_fonts() {
    local font_dir="$HOME/.local/share/fonts"
    local font_check="$font_dir/FiraCodeNerdFont-Regular.ttf"

    if [[ -f "$font_check" ]]; then
        success "FiraCode Nerd Font already installed"
        return 0
    fi

    info "Installing FiraCode Nerd Font..."
    mkdir -p "$font_dir"
    curl -fLo /tmp/FiraCode.zip https://github.com/ryanoasis/nerd-fonts/releases/latest/download/FiraCode.zip
    unzip -o /tmp/FiraCode.zip -d "$font_dir"
    rm /tmp/FiraCode.zip

    if command_exists fc-cache; then
        fc-cache -fv "$font_dir"
    fi

    success "FiraCode Nerd Font installed"
}

# Step 9: Install lsd
setup_lsd() {
    local pm
    pm=$(detect_package_manager)

    if command_exists lsd; then
        success "lsd already installed"
        return 0
    fi

    info "Installing lsd..."
    install_packages "$pm" lsd
    success "lsd installed"
}

# Step 10: Install Claude Code
setup_claude_code() {
    if command_exists claude; then
        success "Claude Code already installed"
        return 0
    fi

    info "Installing Claude Code..."
    curl -fsSL https://claude.ai/install.sh | bash
    success "Claude Code installed"
}

# Step 11: GitHub CLI auth
setup_gh_auth() {
    export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"

    if ! command_exists gh; then
        warn "gh not found - run 'mise upgrade' after reboot"
        return 0
    fi

    if gh auth status &>/dev/null; then
        success "GitHub CLI already authenticated"
        return 0
    fi

    if is_test_mode; then
        info "Test mode: skipping gh auth"
        return 0
    fi

    info "Authenticating GitHub CLI..."
    gh auth login
    success "GitHub CLI authenticated"
}

# Main
main() {
    echo ""
    echo "=================================="
    echo "  Dotfiles Bootstrap Script"
    echo "=================================="
    echo ""

    if is_test_mode; then
        warn "Running in TEST MODE - interactive prompts disabled"
        echo ""
    fi

    install_base_deps
    setup_ssh_key
    setup_chezmoi
    setup_age_key
    setup_zsh
    setup_mise
    setup_rbw
    setup_fonts
    setup_lsd
    setup_claude_code
    setup_gh_auth

    echo ""
    echo "=================================="
    success "Bootstrap complete!"
    echo "=================================="
    echo ""
    warn "IMPORTANT: You must REBOOT (not just log out) for all changes to take effect."
    echo ""
}

main "$@"
