#!/usr/bin/env bash
# Install everything on the Pi from the system packages (apt).
# apt instead of pip: the Pi 2 (ARMv7) often has no ready pip wheels,
# and building them on the Pi takes very long.
set -euo pipefail

sudo apt update
sudo apt install -y git python3-gpiozero python3-lgpio python3-fastapi python3-uvicorn
sudo apt install -y --no-install-recommends python3-picamera2

# Tapo C210: OpenCV for RTSP video, zeep + lxml for ONVIF pan/tilt
sudo apt install -y python3-opencv python3-lxml python3-zeep python3-pip
# onvif-zeep is not in apt. --no-deps: its dependencies (zeep, lxml) come from apt above,
# so pip does not try to build lxml from source on the Pi 2 (takes hours).
# Its WSDL files land in ~/.local/lib/python3.4/site-packages/wsdl; robot/tapo.py finds them there.
pip install --break-system-packages --no-deps onvif-zeep

echo "Done. Test the camera:  python3 tools/test_camera.py"
