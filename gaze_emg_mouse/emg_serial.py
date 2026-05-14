"""Skeleton for future Arduino EMG serial input."""

import re

import serial


class EMGSerialInput:
    """Reads numeric EMG values from an Arduino serial connection."""

    def __init__(self, port="COM11", baudrate=9600, timeout=1.0, threshold=None):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.threshold = threshold
        self._serial = None

    def connect(self):
        """Open the serial connection."""
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )
            return True
        except serial.SerialException as exc:
            print(f"Serial connection failed: {exc}")
            self._serial = None
            return False

    def read_value(self):
        """Read one line and convert it to an integer EMG value."""
        if self._serial is None or not self._serial.is_open:
            return None

        try:
            line = self._serial.readline().decode("utf-8", errors="replace").strip()
            print(line)
            if not line:
                return None

            filtered_match = re.search(r"filtered\s*:\s*(-?\d+)", line, re.IGNORECASE)
            if filtered_match:
                return int(filtered_match.group(1))

            numbers = re.findall(r"-?\d+", line)
            if not numbers:
                return None
            return int(numbers[-1])
        except (ValueError, UnicodeDecodeError) as exc:
            print(f"Invalid EMG serial value: {exc}")
            return None
        except serial.SerialException as exc:
            print(f"Serial read failed: {exc}")
            return None

    def read_triggered_value(self):
        """Read a value and return it only if it crosses the threshold."""
        value = self.read_value()
        if value is None:
            return None
        if self.threshold is None:
            return value
        return value if value >= self.threshold else None

    def close(self):
        """Close the serial connection if it is open."""
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
