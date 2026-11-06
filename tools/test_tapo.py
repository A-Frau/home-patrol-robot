"""Test the Tapo C210: stream, photo, pan/tilt and delay. Run on a laptop or the Pi.

Usage (from the repo root, TAPO_* set in .env):
    python3 -m tools.test_tapo            # stream + photo + pan/tilt
    python3 -m tools.test_tapo --latency  # measure the delay (laptop with a screen)

Latency test: point the camera at the laptop screen. A window shows the laptop
clock in big numbers next to the camera picture. The camera films that clock,
so the difference between the clock now and the clock in the picture is the delay.
Press any key in the window to take a screenshot (latency.jpg), q to quit.
"""

import argparse
import sys
import time

from robot import config
from robot.tapo import TapoPanTilt, rtsp_url


def check_settings():
    missing = [k for k in ("TAPO_HOST", "TAPO_USER", "TAPO_PASSWORD") if not getattr(config, k)]
    if missing:
        sys.exit(f"Missing in .env: {', '.join(missing)} (see .env.example)")


def test_stream():
    import cv2

    print(f"Opening {config.TAPO_STREAM} on {config.TAPO_HOST} ...")
    start = time.monotonic()
    cap = cv2.VideoCapture(rtsp_url(), cv2.CAP_FFMPEG)
    if not cap.isOpened():
        sys.exit("Cannot open the stream. Check IP, camera account and that the camera is on.")
    ok, img = cap.read()
    if not ok:
        sys.exit("Stream opened but no picture arrived.")
    print(f"  first frame after {time.monotonic() - start:.1f} s, size {img.shape[1]}x{img.shape[0]}")

    n, t0 = 0, time.monotonic()
    while time.monotonic() - t0 < 5:
        if cap.grab():
            n += 1
    print(f"  {n / 5:.1f} frames per second")
    cv2.imwrite("tapo_photo.jpg", img)
    print("  saved tapo_photo.jpg")
    cap.release()


def test_pan_tilt():
    print("Pan/tilt over ONVIF ...")
    try:
        pt = TapoPanTilt()
    except Exception as exc:
        print(f"  not available: {exc}")
        print("  (install onvif-zeep; ONVIF uses port 2020 and the camera account login)")
        return
    for d in ("left", "right", "up", "down"):
        print(f"  {d}")
        pt.look(d)
        time.sleep(1.5)
    print("  done. The camera should be back near where it started.")


def test_latency():
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(rtsp_url(), cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    print("Point the camera at this window. Any key = screenshot, q = quit.")
    while True:
        ok, img = cap.read()
        if not ok:
            continue
        img = cv2.resize(img, (640, 360))
        clock = np.full((360, 520, 3), 255, np.uint8)
        now = time.time()
        text = time.strftime("%H:%M:%S", time.localtime(now)) + f".{int(now * 1000) % 1000:03d}"
        cv2.putText(clock, text, (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 0), 5)
        view = np.hstack([clock, img])
        cv2.imshow("Tapo latency: clock now (left) vs clock in camera (right)", view)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key != 255:
            cv2.imwrite("latency.jpg", view)
            print("saved latency.jpg: delay = left time minus the time you read on the right")
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--latency", action="store_true", help="measure the delay")
    args = parser.parse_args()
    check_settings()
    if args.latency:
        test_latency()
    else:
        test_stream()
        test_pan_tilt()
