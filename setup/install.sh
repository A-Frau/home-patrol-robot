#!/usr/bin/env bash
# Install everything on the Pi from the system packages (apt).
# apt instead of pip: the Pi 2 (ARMv7) often has no ready pip wheels,
# and building them on the Pi takes very long.
set -euo pipefail

sudo apt update
sudo apt install -y git python3-gpiozero python3-lgpio python3-fastapi python3-uvicorn
sudo apt install -y --no-install-recommends python3-picamera2

echo "Done. Test the camera:  python3 tools/test_camera.py"
