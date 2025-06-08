#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

# Exit early if already installed
if (Get-Command delta -ErrorAction SilentlyContinue) { exit 0 }
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) { exit 1 }

Start-Process -FilePath "choco" -ArgumentList "install", "delta", "-y" -Verb RunAs -Wait
