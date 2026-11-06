"""All pins and settings live here. This is the only file to change when swapping the Pi."""

import os
from pathlib import Path


def _load_env_file():
    """Read KEY=value lines from .env in the repo root (secrets stay out of git)."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()

# Run without real hardware (laptop development): ROBOT_MOCK=1
MOCK_HARDWARE = os.environ.get("ROBOT_MOCK") == "1"

# --- Motor driver Cytron MDD3A (BCM pin numbers) ---
# The MDD3A takes two PWM pins per motor and has no enable and no standby pin:
# PWM on "forward" with "backward" low turns one way, the other way round reverses.
# Both pins low = stop.
LEFT_MOTOR = {"forward": 17, "backward": 27}   # M1A, M1B
RIGHT_MOTOR = {"forward": 23, "backward": 24}  # M2A, M2B
# Note: 4 PWM pins means software PWM (the Pi has only 2 hardware PWM channels).
# If the motors hum or run rough, install pigpio and use its pin factory:
#   sudo apt install pigpio python3-pigpio && sudo systemctl enable --now pigpiod
#   export GPIOZERO_PIN_FACTORY=pigpio

# Flip if a wheel turns the wrong way (instead of rewiring)
LEFT_INVERTED = False
RIGHT_INVERTED = False

# Speeds from 0.0 to 1.0
DRIVE_SPEED = 0.6
TURN_SPEED = 0.45

# Safety: stop motors if no drive command arrives within this time
WATCHDOG_TIMEOUT_S = 1.0

# --- Camera ---
# "pi"   = camera on the Pi camera port (IMX219 / Camera v2)
# "tapo" = TP-Link Tapo C210 over WiFi (RTSP video + ONVIF pan/tilt)
CAMERA_SOURCE = os.environ.get("CAMERA_SOURCE", "pi")
CAMERA_RESOLUTION = (640, 480)
CAMERA_FRAMERATE = 15

# --- Tapo C210 ---
# Login = the "camera account" created in the Tapo app, NOT your TP-Link cloud login.
# Put these in the environment or a .env file, never in git.
TAPO_HOST = os.environ.get("TAPO_HOST", "")          # e.g. 192.168.1.50 (fix it in the router)
TAPO_USER = os.environ.get("TAPO_USER", "")
TAPO_PASSWORD = os.environ.get("TAPO_PASSWORD", "")
TAPO_STREAM = os.environ.get("TAPO_STREAM", "stream2")  # stream2 = small (640x360), stream1 = 2K
TAPO_RTSP_PORT = 554
TAPO_ONVIF_PORT = 2020
TAPO_FPS = 10            # frames per second sent to the web page (saves CPU on the Pi 2)
TAPO_JPEG_QUALITY = 75
TAPO_PAN_STEP = 0.1      # one button press moves this far (ONVIF range is -1 to 1)
TAPO_TILT_STEP = 0.1
# Folder with the ONVIF WSDL files (devicemgmt.wsdl, ...). Empty = search the usual
# install places (see robot/tapo.py find_wsdl_dir).
TAPO_WSDL_DIR = os.environ.get("TAPO_WSDL_DIR", "")

# --- Web server ---
WEB_HOST = "0.0.0.0"
WEB_PORT = 8000
