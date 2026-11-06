"""Phase 1 check: turn each motor briefly. Lift the robot so the wheels spin freely.

Usage: python3 -m tools.test_motors   (from the repo root)
"""

import time

from robot import config
from robot.motors import Motors

# Long enough for the test, still protected by the watchdog
config.WATCHDOG_TIMEOUT_S = 3.0

motors = Motors()
try:
    for direction in ("forward", "backward", "left", "right"):
        print(direction)
        motors.drive(direction)
        time.sleep(1.5)
        motors.stop()
        time.sleep(0.5)
finally:
    motors.close()
print("Done. If a wheel turned the wrong way, flip LEFT_INVERTED / RIGHT_INVERTED in config.py.")
