# Tapo C210 as the robot camera

The C210 sends video over WiFi (RTSP) and can turn and tilt (ONVIF).
The code is in `robot/tapo.py`. Switch with `CAMERA_SOURCE=tapo`.

## 1. Camera account (Kamera-Konto)

1. Tapo app → tap the camera → settings (gear) → **Advanced Settings** → **Camera Account**.
2. Create a username and password. This is a local login for RTSP and ONVIF, not your TP-Link cloud account.

## 2. Fixed IP address

In your router, give the camera a fixed IP (DHCP reservation). The IP is in the Tapo app under device info.

## 3. Settings file

```bash
cp .env.example .env    # then fill in TAPO_HOST, TAPO_USER, TAPO_PASSWORD
```

`.env` is in `.gitignore`, so the password never goes to GitHub.

## 4. Install

Laptop:

```bash
pip install opencv-python onvif-zeep fastapi uvicorn gpiozero
```

Pi 2 (done by `setup/install.sh`):

```bash
sudo apt install -y python3-opencv python3-lxml python3-zeep python3-pip
pip install --break-system-packages --no-deps onvif-zeep
```

`--no-deps`: zeep and lxml come from apt, so pip does not build lxml from source (very slow on the Pi 2).

WSDL files: onvif-zeep does not put its WSDL folder next to the package. On the Pi it lands in
`~/.local/lib/python3.4/site-packages/wsdl` (a path hard-coded in its setup.py, even on Python 3.13),
so the default lookup fails with `No such file: .../site-packages/wsdl/devicemgmt.wsdl`.
`robot/tapo.py` (`find_wsdl_dir`) searches the usual places. If it still fails, find the folder
and set it in `.env`:

```bash
find ~/.local /usr/local /usr -name devicemgmt.wsdl 2>/dev/null
# .env:  TAPO_WSDL_DIR=/home/praew/.local/lib/python3.4/site-packages/wsdl
```

If the files are missing, copy the `wsdl` folder from
https://github.com/FalkTannhaeuser/python-onvif-zeep.

## 5. Test

```bash
python3 -m tools.test_tapo             # stream, photo, pan/tilt
python3 -m tools.test_tapo --latency   # delay (laptop with a screen)
```

Then the drive page with the Tapo picture:

```bash
CAMERA_SOURCE=tapo ROBOT_MOCK=1 python3 -m robot.web.app
```

Camera buttons appear under the drive pad when pan/tilt works.

## Streams

| URL end | Size | Use |
|---|---|---|
| `stream2` | 640 x 360 | live view on the drive page (light enough for the Pi 2) |
| `stream1` | 2304 x 1296 (2K) | patrol photos (`capture_photo`) |

## Known limits

- Delay is usually around 1 to 2 s. Fine for patrol photos, hard for driving by video. Measure it with `--latency`.
- The camera needs its own 5 V supply (second USB port of the power bank), about 1 A.
- TP-Link firmware updates have changed local access before. If the stream or pan/tilt stops working after an update, check the camera account again first.
- If pan/tilt does not move: the code tries ONVIF RelativeMove first, then ContinuousMove. Check that ONVIF port 2020 is reachable.
