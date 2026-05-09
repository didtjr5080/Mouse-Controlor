"""Experimental gaze direction skeleton for future expansion."""


class GazeTracker:
    """Estimates rough eye direction from Face Mesh landmarks.

    The current MVP uses face direction for cursor movement. This class exists
    so a later version can replace face-based movement with iris/pupil logic.
    """

    LEFT_EYE_INDICES = [33, 133, 159, 145]
    RIGHT_EYE_INDICES = [362, 263, 386, 374]

    def estimate_gaze_direction(self, landmarks, frame_width, frame_height):
        """Return a rough direction placeholder from available landmarks."""
        if landmarks is None:
            return {
                "available": False,
                "direction": "center",
                "confidence": 0.0,
            }

        needed = self.LEFT_EYE_INDICES + self.RIGHT_EYE_INDICES
        if max(needed) >= len(landmarks):
            return {
                "available": False,
                "direction": "center",
                "confidence": 0.0,
            }

        # This rough version only confirms eye landmarks are available.
        # Real gaze control should add iris landmarks, calibration, and filtering.
        return {
            "available": True,
            "direction": "center",
            "confidence": 0.3,
        }
