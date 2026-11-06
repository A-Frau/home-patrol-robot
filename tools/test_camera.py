"""Phase 0 check: take one photo with the Pi camera.

Usage: python3 tools/test_camera.py [photo.jpg]
"""

import sys
import time

from picamera2 import Picamera2

path = sys.argv[1] if len(sys.argv) > 1 else "photo.jpg"

cam = Picamera2()
cam.configure(cam.create_still_configuration())
cam.start()
time.sleep(2)  # let exposure and white balance settle
cam.capture_file(path)
cam.stop()
cam.close()
print(f"Saved {path}")
