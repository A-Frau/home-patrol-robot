"""Pi camera as an MJPEG stream (picamera2). Works without a camera: available = False."""

import io
import logging
import threading

from robot import config

log = logging.getLogger(__name__)


class _StreamingOutput(io.BufferedIOBase):
    """Keeps the latest JPEG frame and wakes up waiting stream clients."""

    def __init__(self):
        self.frame = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()
        return len(buf)


class Camera:
    def __init__(self):
        self.available = False
        self._cam = None
        self._output = _StreamingOutput()
        if config.MOCK_HARDWARE:
            return
        try:
            from picamera2 import Picamera2
            from picamera2.encoders import MJPEGEncoder
            from picamera2.outputs import FileOutput

            self._cam = Picamera2()
            video_config = self._cam.create_video_configuration(
                main={"size": config.CAMERA_RESOLUTION},
                controls={"FrameRate": config.CAMERA_FRAMERATE},
            )
            self._cam.configure(video_config)
            self._cam.start_recording(MJPEGEncoder(), FileOutput(self._output))
            self.available = True
        except Exception as exc:  # no camera, no picamera2, cable loose
            log.warning("Camera not available: %s", exc)

    def frames(self):
        """Yield JPEG frames as they arrive. Stops if the camera goes quiet."""
        while self.available:
            with self._output.condition:
                if not self._output.condition.wait(timeout=2):
                    return
                frame = self._output.frame
            yield frame

    def capture_photo(self, path):
        """Save a full photo while streaming (used in phase 3)."""
        if not self.available:
            raise RuntimeError("Camera not available")
        self._cam.capture_file(str(path))

    def close(self):
        if self._cam is not None:
            try:
                if self.available:
                    self._cam.stop_recording()
            finally:
                self._cam.close()
        self.available = False
