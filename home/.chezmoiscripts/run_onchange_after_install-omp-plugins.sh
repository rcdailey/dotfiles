#!/usr/bin/env bash

set -euo pipefail

mise x github:can1357/oh-my-pi@latest -- \
  omp plugin install @plannotator/pi-extension@latest
