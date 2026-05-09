"""CSV session logging for hand tracking and input events."""

import csv
import os


class SessionLogger:
    """Writes one row per loop iteration to a CSV file."""

    FIELDNAMES = [
        "timestamp",
        "hand_detected",
        "hand_x",
        "hand_y",
        "screen_x",
        "screen_y",
        "event",
    ]

    def __init__(self, log_path):
        self.log_path = log_path
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_exists = os.path.exists(log_path)
        self._file = open(log_path, "a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self.FIELDNAMES)

        if not file_exists or os.path.getsize(log_path) == 0:
            self._writer.writeheader()
            self._file.flush()

    def log(self, row_dict):
        """Write a row using only the expected CSV columns."""
        row = {field: row_dict.get(field, "") for field in self.FIELDNAMES}
        self._writer.writerow(row)
        self._file.flush()

    def close(self):
        """Close the CSV file."""
        self._file.close()
