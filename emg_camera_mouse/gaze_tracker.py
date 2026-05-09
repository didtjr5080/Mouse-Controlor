"""Webcam-only gaze estimate using OpenCV face and eye detection."""

import cv2

import config


class GazeTracker:
    """Estimates a screen target from face and eye position.

    This is not medical-grade eye tracking. A normal webcam does not provide
    corneal reflection or calibrated pupil geometry, so this class gives a
    practical approximation for an MVP.
    """

    def __init__(self, draw=True):
        self.draw = draw
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

    def _empty_result(self):
        return {
            "detected": False,
            "x_norm": 0.0,
            "y_norm": 0.0,
            "x_px": 0,
            "y_px": 0,
        }

    def _apply_deadzone(self, value):
        if abs(value) < config.GAZE_DEADZONE:
            return 0.0
        return value

    def process(self, frame):
        """Return an approximate gaze target in the same shape as HandTracker."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        height, width = frame.shape[:2]

        faces = self._face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(120, 120),
        )
        if len(faces) == 0:
            return self._empty_result()

        # Use the largest detected face because it is usually the user.
        x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
        face_center_x = x + w / 2
        face_center_y = y + h / 2

        upper_face_gray = gray[y : y + int(h * 0.6), x : x + w]
        eyes = self._eye_cascade.detectMultiScale(
            upper_face_gray,
            scaleFactor=1.1,
            minNeighbors=8,
            minSize=(24, 24),
        )

        # Face position gives stable head pointing. Eye centers refine it a bit.
        target_x_norm = face_center_x / width
        target_y_norm = face_center_y / height

        if len(eyes) >= 2:
            sorted_eyes = sorted(eyes, key=lambda eye: eye[0])[:2]
            eye_centers = []
            for ex, ey, ew, eh in sorted_eyes:
                eye_centers.append((x + ex + ew / 2, y + ey + eh / 2))
                if self.draw:
                    cv2.rectangle(
                        frame,
                        (x + ex, y + ey),
                        (x + ex + ew, y + ey + eh),
                        (255, 0, 0),
                        2,
                    )

            avg_eye_x = sum(point[0] for point in eye_centers) / len(eye_centers)
            avg_eye_y = sum(point[1] for point in eye_centers) / len(eye_centers)
            eye_offset_x = (avg_eye_x - face_center_x) / max(w, 1)
            eye_offset_y = (avg_eye_y - (y + h * 0.38)) / max(h, 1)

            eye_offset_x = self._apply_deadzone(eye_offset_x)
            eye_offset_y = self._apply_deadzone(eye_offset_y)

            target_x_norm += eye_offset_x * config.GAZE_SENSITIVITY_X
            target_y_norm += eye_offset_y * config.GAZE_SENSITIVITY_Y

        target_x_norm = max(0.0, min(1.0, target_x_norm))
        target_y_norm = max(0.0, min(1.0, target_y_norm))
        target_x_px = int(target_x_norm * width)
        target_y_px = int(target_y_norm * height)

        if self.draw:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (target_x_px, target_y_px), 8, (0, 255, 255), -1)

        return {
            "detected": True,
            "x_norm": target_x_norm,
            "y_norm": target_y_norm,
            "x_px": target_x_px,
            "y_px": target_y_px,
        }

    def close(self):
        """Keep the same interface as HandTracker."""
        return
