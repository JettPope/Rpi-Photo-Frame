#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Updating APT and installing system packages (if apt-packages.txt exists)..."
if [ -f apt-packages.txt ]; then
  sudo apt update
  xargs -a apt-packages.txt sudo apt install -y
fi

echo "Creating Python virtual environment (venv) if missing..."
if [ ! -d venv ]; then
  python3 -m venv venv
fi

echo "Activating venv and upgrading pip..."
# shellcheck disable=SC1091
source venv/bin/activate
python -m pip install --upgrade pip

if [ -f requirements.txt ]; then
  echo "Installing Python packages from requirements.txt into venv..."
  pip install -r requirements.txt
fi

echo "Setup complete. Activate the venv with: source venv/bin/activate"
