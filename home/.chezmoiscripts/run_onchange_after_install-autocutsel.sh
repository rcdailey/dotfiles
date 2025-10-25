#!/bin/bash

# Install xsel for X11 clipboard synchronization
# hash: {{ include "dot_config/autostart/autocutsel.desktop" | sha256sum }}

if command -v apt-get &> /dev/null; then
  if ! dpkg -l | grep -q "^ii  xsel"; then
    echo "Installing xsel..."
    sudo apt-get update && sudo apt-get install -y xsel
  fi
elif command -v dnf &> /dev/null; then
  if ! rpm -q xsel &> /dev/null; then
    echo "Installing xsel..."
    sudo dnf install -y xsel
  fi
elif command -v pacman &> /dev/null; then
  if ! pacman -Q xsel &> /dev/null; then
    echo "Installing xsel..."
    sudo pacman -S --noconfirm xsel
  fi
fi
