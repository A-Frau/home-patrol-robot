"""Two DC motors on a Cytron MDD3A driver, with a safety watchdog (Totmannschalter).

The MDD3A uses two PWM pins per motor and has no enable and no standby pin,
so gpiozero's Motor(..., pwm=True) drives it directly.
"""

import threading
import time

from gpiozero import Device, Motor

from robot import config

if config.MOCK_HARDWARE:
    from gpiozero.pins.mock import MockFactory, MockPWMPin

    Device.pin_factory = MockFactory(pin_class=MockPWMPin)


class Motors:
    """Drive commands: forward, backward, left, right, stop.

    The watchdog stops the motors if no command arrives within
    config.WATCHDOG_TIMEOUT_S. The web page must keep sending commands
    while a button is held.
    """

    DIRECTIONS = ("forward", "backward", "left", "right", "stop")

    def __init__(self):
        self._left = Motor(**config.LEFT_MOTOR, pwm=True)
        self._right = Motor(**config.RIGHT_MOTOR, pwm=True)
        self._lock = threading.Lock()
        self._last_command = 0.0
        self._moving = False
        self._running = True
        self._watchdog = threading.Thread(target=self._watch, daemon=True)
        self._watchdog.start()

    @property
    def moving(self):
        return self._moving

    def drive(self, direction):
        s, t = config.DRIVE_SPEED, config.TURN_SPEED
        speeds = {
            "forward": (s, s),
            "backward": (-s, -s),
            "left": (-t, t),
            "right": (t, -t),
            "stop": (0.0, 0.0),
        }
        if direction not in speeds:
            raise ValueError(f"Unknown direction: {direction}")
        with self._lock:
            self._set(*speeds[direction])
            self._moving = direction != "stop"
            self._last_command = time.monotonic()

    def stop(self):
        self.drive("stop")

    def close(self):
        self._running = False
        self._watchdog.join(timeout=1)
        self.stop()
        self._left.close()
        self._right.close()

    # --- internal ---

    def _set(self, left, right):
        if config.LEFT_INVERTED:
            left = -left
        if config.RIGHT_INVERTED:
            right = -right
        self._apply(self._left, left)
        self._apply(self._right, right)

    @staticmethod
    def _apply(motor, speed):
        if speed > 0:
            motor.forward(speed)
        elif speed < 0:
            motor.backward(-speed)
        else:
            motor.stop()

    def _watch(self):
        while self._running:
            time.sleep(0.1)
            with self._lock:
                timed_out = time.monotonic() - self._last_command > config.WATCHDOG_TIMEOUT_S
                if self._moving and timed_out:
                    self._set(0.0, 0.0)
                    self._moving = False
