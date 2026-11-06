# Home Patrol Robot

A small 3D-printed robot on a Raspberry Pi. It streams live video to the phone, avoids obstacles and later patrols the flat on its own, for example to check if a window is open. The final phase adds an LLM agent that controls the robot through an MCP server.

**Status:** Phase 0 (setup). Phase 1 drive page is already in the code.

## Features (planned)

| Phase | What |
|---|---|
| 0 | Headless Pi setup, camera test |
| 1 | Drive from the phone with live MJPEG stream, safety watchdog |
| 2 | Obstacle sensors and auto mode |
| 3 | Scheduled patrol with timestamped photos |
| 4 | Pi 4/5 upgrade, window open / closed classifier vs vision LLM |
| 5 | LLM agent with MCP tools, guardrails, evaluation |
| 6 | 2D LiDAR mapping with ROS 2 (optional) |

## Stack

Python 3 · FastAPI · gpiozero · picamera2 · OpenCV · ONVIF · Raspberry Pi OS Lite

## Run

On the Pi (after `bash setup/install.sh`):

```bash
python3 -m robot.web.app
```

On a laptop without hardware (mock mode):

```bash
pip install -r requirements.txt
ROBOT_MOCK=1 python3 -m robot.web.app
```

Open `http://<host>:8000`. Hold an arrow button to drive. Releasing it, or losing the connection for 1 s, stops the motors.

## Cameras

Two camera options, set with `CAMERA_SOURCE`:

- `pi`: IMX219 on the Pi camera port, low delay, for driving.
- `tapo`: TP-Link Tapo C210 over WiFi (RTSP video, ONVIF pan/tilt), for patrol photos. See `docs/tapo-c210.md`.

## Structure

```
robot/          hardware classes (Motors, Camera) and config.py
robot/web/      FastAPI app and drive page
tools/          hardware test scripts
setup/          Pi install script
docs/           setup guide, wiring diagram, architecture
```

## Safety

- Motors and Pi run on separate batteries.
- A watchdog stops the motors when no drive command arrives within 1 s.
