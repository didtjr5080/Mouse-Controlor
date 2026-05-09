"""Skeleton for future Arduino EMG serial input."""

import serial


class EMGSerialInput:
    """Reads numeric EMG values from an Arduino serial connection."""

    def __init__(self, port="COM3", baudrate=115200, timeout=1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
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
            line = self._serial.readline().decode("utf-8").strip()
            if not line:
                return None
            return int(line)
        except (ValueError, UnicodeDecodeError) as exc:
            print(f"Invalid EMG serial value: {exc}")
            return None
        except serial.SerialException as exc:
            print(f"Serial read failed: {exc}")
            return None

    def close(self):
        """Close the serial connection if it is open."""
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
