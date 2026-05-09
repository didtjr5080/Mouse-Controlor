"""Hand tracking module using MediaPipe Hands or MediaPipe Tasks."""

import os
import time
import urllib.request

import cv2
import mediapipe as mp
import numpy as np

import config


class HandTracker:
    """Detects a hand and returns the index fingertip position."""

    def __init__(
        self,
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
        draw=True,
    ):
        self.draw = draw
        self._mode = "solutions" if hasattr(mp, "solutions") else "tasks"
        self._last_timestamp_ms = 0

        if self._mode == "solutions":
            self._mp_hands = mp.solutions.hands
            self._mp_drawing = mp.solutions.drawing_utils
            self._hands = self._mp_hands.Hands(
                max_num_hands=max_num_hands,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            return

        self._setup_tasks_landmarker(
            max_num_hands,
            min_detection_confidence,
            min_tracking_confidence,
        )

    def _setup_tasks_landmarker(
        self,
        max_num_hands,
        min_detection_confidence,
        min_tracking_confidence,
    ):
        """Create a HandLandmarker for newer MediaPipe Tasks-only installs."""
        from mediapipe.tasks.python import vision

        self._download_model_if_needed()
        base_options = mp.tasks.BaseOptions(
            model_asset_path=os.path.abspath(config.HAND_LANDMARKER_MODEL_PATH)
        )
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._connections = vision.HandLandmarksConnections.HAND_CONNECTIONS

    def _download_model_if_needed(self):
        """Download the MediaPipe hand model bundle if it is not present."""
        model_path = config.HAND_LANDMARKER_MODEL_PATH
        if os.path.exists(model_path):
            return

        model_dir = os.path.dirname(model_path)
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)

        print("MediaPipe hand model not found. Downloading hand_landmarker.task...")
        try:
            urllib.request.urlretrieve(config.HAND_LANDMARKER_MODEL_URL, model_path)
        except Exception as exc:
            raise RuntimeError(
                "MediaPipe Tasks requires a local hand_landmarker.task model file. "
                f"Download it from {config.HAND_LANDMARKER_MODEL_URL} and save it as "
                f"{model_path}."
            ) from exc

    def _empty_result(self):
        return {
            "detected": False,
            "x_norm": 0.0,
            "y_norm": 0.0,
            "x_px": 0,
            "y_px": 0,
        }

    def process(self, frame):
        """Process one OpenCV BGR frame and return index fingertip data."""
        if self._mode == "solutions":
            return self._process_with_solutions(frame)
        return self._process_with_tasks(frame)

    def _process_with_solutions(self, frame):
        """Process one frame with the older MediaPipe Solutions API."""
        height, width = frame.shape[:2]

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self._hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        if not results.multi_hand_landmarks:
            return self._empty_result()

        hand_landmarks = results.multi_hand_landmarks[0]
        index_tip = hand_landmarks.landmark[8]
        x_px = int(index_tip.x * width)
        y_px = int(index_tip.y * height)

        if self.draw:
            self._mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                self._mp_hands.HAND_CONNECTIONS,
            )
            cv2.circle(frame, (x_px, y_px), 8, (0, 255, 0), -1)

        return {
            "detected": True,
            "x_norm": index_tip.x,
            "y_norm": index_tip.y,
            "x_px": x_px,
            "y_px": y_px,
        }

    def _process_with_tasks(self, frame):
        """Process one frame with the newer MediaPipe Tasks API."""
        height, width = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame = np.ascontiguousarray(rgb_frame)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # VIDEO mode requires a strictly increasing timestamp.
        timestamp_ms = int(time.time() * 1000)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms

        results = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        if not results.hand_landmarks:
            return self._empty_result()

        landmarks = results.hand_landmarks[0]
        index_tip = landmarks[8]
        x_px = int(index_tip.x * width)
        y_px = int(index_tip.y * height)

        if self.draw:
            self._draw_tasks_landmarks(frame, landmarks)
            cv2.circle(frame, (x_px, y_px), 8, (0, 255, 0), -1)

        return {
            "detected": True,
            "x_norm": index_tip.x,
            "y_norm": index_tip.y,
            "x_px": x_px,
            "y_px": y_px,
        }

    def _draw_tasks_landmarks(self, frame, landmarks):
        """Draw landmarks manually because Tasks installs do not include drawing_utils."""
        height, width = frame.shape[:2]
        points = [
            (int(landmark.x * width), int(landmark.y * height))
            for landmark in landmarks
        ]

        for connection in self._connections:
            start = points[connection.start]
            end = points[connection.end]
            cv2.line(frame, start, end, (255, 255, 255), 2)

        for point in points:
            cv2.circle(frame, point, 3, (0, 128, 255), -1)

    def close(self):
        """Release MediaPipe resources."""
        if self._mode == "solutions":
            self._hands.close()
        else:
            self._landmarker.close()
