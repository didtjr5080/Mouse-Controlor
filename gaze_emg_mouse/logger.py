"""CSV session logging for face tracking and simulated EMG events."""

import csv
import os


class SessionLogger:
    """Writes tracking and event data to a CSV file."""

    FIELDNAMES = [
        "timestamp",
        "face_detected",
        "tracking_mode",
        "face_x",
        "face_y",
        "dx",
        "dy",
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
        """Write one row using the expected columns."""
        row = {field: row_dict.get(field, "") for field in self.FIELDNAMES}
        self._writer.writerow(row)
        self._file.flush()

    def close(self):
        """Close the CSV file."""
        self._file.close()
