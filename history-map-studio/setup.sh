#!/usr/bin/env bash
# One-time setup: Python 3.10+ and ffmpeg required. Windows: run inside WSL or Git Bash.
set -e
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo "Install ffmpeg first (mac: brew install ffmpeg | ubuntu: sudo apt install ffmpeg | windows: winget install ffmpeg)"; exit 1; }
python3 -m pip install -r pipeline/requirements.txt
mkdir -p pipeline/build pipeline/out
echo "Setup OK. Next: python3 produce.py voice   (choose free or premium voice)"
echo "Test render: python3 produce.py build demo_chaldiran"
