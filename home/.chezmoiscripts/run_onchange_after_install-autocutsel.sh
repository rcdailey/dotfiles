#!/bin/bash

# Install autocutsel for X11 clipboard synchronization
# hash: {{ include "dot_config/autostart/autocutsel.desktop" | sha256sum }}

if command -v apt-get &> /dev/null; then
  if ! dpkg -l | grep -q "^ii  autocutsel"; then
    echo "Installing autocutsel..."
    sudo apt-get update && sudo apt-get install -y autocutsel
  fi
elif command -v dnf &> /dev/null; then
  if ! rpm -q autocutsel &> /dev/null; then
    echo "Installing autocutsel..."
    sudo dnf install -y autocutsel
  fi
elif command -v pacman &> /dev/null; then
  if ! pacman -Q autocutsel &> /dev/null; then
    echo "Installing autocutsel..."
    sudo pacman -S --noconfirm autocutsel
  fi
fi
