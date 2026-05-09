"""Face landmark tracking based on MediaPipe Face Mesh / Face Landmarker."""

import os
import time
import urllib.request

import cv2
import mediapipe as mp
import numpy as np

import config


class FaceTracker:
    """Tracks a face and returns a nose-tip reference point."""

    NOSE_TIP_INDEX = 1

    def __init__(
        self,
        max_num_faces=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
        draw=True,
    ):
        self.draw = draw
        self._last_timestamp_ms = 0
        self._mode = "solutions" if hasattr(mp, "solutions") else "tasks"

        if self._mode == "solutions":
            self._mp_face_mesh = mp.solutions.face_mesh
            self._mp_drawing = mp.solutions.drawing_utils
            self._face_mesh = self._mp_face_mesh.FaceMesh(
                max_num_faces=max_num_faces,
                refine_landmarks=True,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            return

        self._setup_tasks_landmarker(
            max_num_faces,
            min_detection_confidence,
            min_tracking_confidence,
        )

    def _setup_tasks_landmarker(
        self,
        max_num_faces,
        min_detection_confidence,
        min_tracking_confidence,
    ):
        """Create a FaceLandmarker for MediaPipe Tasks-only installs."""
        from mediapipe.tasks.python import vision

        self._download_model_if_needed()
        base_options = mp.tasks.BaseOptions(
            model_asset_path=os.path.abspath(config.FACE_LANDMARKER_MODEL_PATH)
        )
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_faces=max_num_faces,
            min_face_detection_confidence=min_detection_confidence,
            min_face_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)

    def _download_model_if_needed(self):
        """Download the MediaPipe face model bundle if it is missing."""
        model_path = config.FACE_LANDMARKER_MODEL_PATH
        if os.path.exists(model_path):
            return

        model_dir = os.path.dirname(model_path)
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)

        print("MediaPipe face model not found. Downloading face_landmarker.task...")
        try:
            urllib.request.urlretrieve(config.FACE_LANDMARKER_MODEL_URL, model_path)
        except Exception as exc:
            raise RuntimeError(
                "MediaPipe Face Landmarker needs a local model file. "
                f"Download {config.FACE_LANDMARKER_MODEL_URL} and save it as "
                f"{model_path}."
            ) from exc

    def _empty_result(self):
        return {
            "detected": False,
            "x_norm": 0.0,
            "y_norm": 0.0,
            "x_px": 0,
            "y_px": 0,
            "landmarks": None,
        }

    def process(self, frame):
        """Process one OpenCV BGR frame and return nose-tip face data."""
        if self._mode == "solutions":
            return self._process_with_solutions(frame)
        return self._process_with_tasks(frame)

    def _process_with_solutions(self, frame):
        """Process one frame with the older MediaPipe Face Mesh API."""
        height, width = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self._face_mesh.process(rgb_frame)
        rgb_frame.flags.writeable = True

        if not results.multi_face_landmarks:
            return self._empty_result()

        landmarks = results.multi_face_landmarks[0].landmark
        nose = landmarks[self.NOSE_TIP_INDEX]
        x_px = int(nose.x * width)
        y_px = int(nose.y * height)

        if self.draw:
            cv2.circle(frame, (x_px, y_px), 8, (0, 255, 255), -1)
            self._draw_sparse_landmarks(frame, landmarks)

        return {
            "detected": True,
            "x_norm": max(0.0, min(1.0, nose.x)),
            "y_norm": max(0.0, min(1.0, nose.y)),
            "x_px": x_px,
            "y_px": y_px,
            "landmarks": landmarks,
        }

    def _process_with_tasks(self, frame):
        """Process one frame with the newer MediaPipe Tasks API."""
        height, width = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame = np.ascontiguousarray(rgb_frame)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        timestamp_ms = int(time.time() * 1000)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms

        results = self._landmarker.detect_for_video(mp_image, timestamp_ms)
        if not results.face_landmarks:
            return self._empty_result()

        landmarks = results.face_landmarks[0]
        nose = landmarks[self.NOSE_TIP_INDEX]
        x_px = int(nose.x * width)
        y_px = int(nose.y * height)

        if self.draw:
            cv2.circle(frame, (x_px, y_px), 8, (0, 255, 255), -1)
            self._draw_sparse_landmarks(frame, landmarks)

        return {
            "detected": True,
            "x_norm": max(0.0, min(1.0, nose.x)),
            "y_norm": max(0.0, min(1.0, nose.y)),
            "x_px": x_px,
            "y_px": y_px,
            "landmarks": landmarks,
        }

    def _draw_sparse_landmarks(self, frame, landmarks):
        """Draw a few face points so beginners can see tracking is working."""
        height, width = frame.shape[:2]
        key_indices = [1, 33, 133, 263, 362, 10, 152, 234, 454]
        for index in key_indices:
            if index >= len(landmarks):
                continue
            landmark = landmarks[index]
            x_px = int(landmark.x * width)
            y_px = int(landmark.y * height)
            cv2.circle(frame, (x_px, y_px), 2, (0, 180, 255), -1)

    def close(self):
        """Release MediaPipe resources."""
        if self._mode == "solutions":
            self._face_mesh.close()
        else:
            self._landmarker.close()
