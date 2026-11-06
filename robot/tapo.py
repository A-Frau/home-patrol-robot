"""TP-Link Tapo C210 as the robot camera: RTSP video + ONVIF pan/tilt.

Same interface as robot.camera.Camera (available, frames, capture_photo, close),
plus pan/tilt: look(direction).

Setup in the Tapo app: camera > settings > Advanced Settings > Camera Account.
That username/password is what goes into TAPO_USER / TAPO_PASSWORD.
"""

import logging
import os
import threading
import time
from urllib.parse import quote

from robot import config

log = logging.getLogger(__name__)

# RTSP over TCP: fewer broken frames on WiFi than UDP
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")


def rtsp_url(stream=None):
    user = quote(config.TAPO_USER, safe="")
    password = quote(config.TAPO_PASSWORD, safe="")
    return (
        f"rtsp://{user}:{password}@{config.TAPO_HOST}:{config.TAPO_RTSP_PORT}/"
        f"{stream or config.TAPO_STREAM}"
    )


class TapoPanTilt:
    """Pan/tilt through ONVIF. Tries RelativeMove, falls back to ContinuousMove + Stop."""

    MOVES = {
        "left": (-1, 0),
        "right": (1, 0),
        "up": (0, 1),
        "down": (0, -1),
    }

    def __init__(self):
        from onvif import ONVIFCamera  # pip: onvif-zeep

        cam = ONVIFCamera(
            config.TAPO_HOST, config.TAPO_ONVIF_PORT, config.TAPO_USER, config.TAPO_PASSWORD
        )
        self._ptz = cam.create_ptz_service()
        self._token = cam.create_media_service().GetProfiles()[0].token
        self._use_relative = True

    def look(self, direction):
        if direction not in self.MOVES:
            raise ValueError(f"Unknown direction: {direction}")
        sx, sy = self.MOVES[direction]
        dx, dy = sx * config.TAPO_PAN_STEP, sy * config.TAPO_TILT_STEP
        if self._use_relative:
            try:
                req = self._ptz.create_type("RelativeMove")
                req.ProfileToken = self._token
                req.Translation = {"PanTilt": {"x": dx, "y": dy}}
                self._ptz.RelativeMove(req)
                return
            except Exception as exc:
                log.info("RelativeMove not supported (%s), using ContinuousMove", exc)
                self._use_relative = False
        req = self._ptz.create_type("ContinuousMove")
        req.ProfileToken = self._token
        req.Velocity = {"PanTilt": {"x": sx * 0.5, "y": sy * 0.5}}
        self._ptz.ContinuousMove(req)
        time.sleep(0.3)
        self._ptz.Stop({"ProfileToken": self._token})


class TapoCamera:
    def __init__(self):
        self.available = False
        self.pan_tilt = None
        self._frame = None
        self._condition = threading.Condition()
        self._running = False
        self._thread = None

        if not config.TAPO_HOST or not config.TAPO_USER:
            log.warning("Tapo camera: TAPO_HOST / TAPO_USER not set")
            return
        try:
            import cv2  # noqa: F401  (pip: opencv-python, apt: python3-opencv)
        except ImportError as exc:
            log.warning("Tapo camera needs OpenCV: %s", exc)
            return

        self._running = True
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()
        self.available = True

        try:
            self.pan_tilt = TapoPanTilt()
        except Exception as exc:  # no onvif-zeep, ONVIF off, wrong login
            log.warning("Tapo pan/tilt not available: %s", exc)

    # --- video ---

    def _reader(self):
        import cv2

        period = 1.0 / config.TAPO_FPS
        while self._running:
            cap = cv2.VideoCapture(rtsp_url(), cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not cap.isOpened():
                log.warning("Tapo: cannot open RTSP stream, retrying in 3 s")
                time.sleep(3)
                continue
            last_sent = 0.0
            while self._running:
                ok = cap.grab()  # always grab, so old frames do not pile up (less lag)
                if not ok:
                    log.warning("Tapo: stream lost, reconnecting")
                    break
                now = time.monotonic()
                if now - last_sent < period:
                    continue
                ok, img = cap.retrieve()
                if not ok:
                    continue
                ok, jpg = cv2.imencode(
                    ".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, config.TAPO_JPEG_QUALITY]
                )
                if ok:
                    with self._condition:
                        self._frame = jpg.tobytes()
                        self._condition.notify_all()
                    last_sent = now
            cap.release()
            time.sleep(1)

    def frames(self):
        """Yield JPEG frames as they arrive. Stops if the camera goes quiet."""
        while self.available:
            with self._condition:
                if not self._condition.wait(timeout=5):
                    return
                frame = self._frame
            yield frame

    def capture_photo(self, path):
        """Save a full-resolution photo (2K main stream) for patrol checks."""
        import cv2

        cap = cv2.VideoCapture(rtsp_url("stream1"), cv2.CAP_FFMPEG)
        try:
            for _ in range(5):  # skip the first frames, they can be grey
                ok, img = cap.read()
            if not ok:
                raise RuntimeError("Tapo: no photo received")
            cv2.imwrite(str(path), img)
        finally:
            cap.release()

    def look(self, direction):
        if self.pan_tilt is None:
            raise RuntimeError("Pan/tilt not available")
        self.pan_tilt.look(direction)

    def close(self):
        self._running = False
        self.available = False
        if self._thread is not None:
            self._thread.join(timeout=3)
