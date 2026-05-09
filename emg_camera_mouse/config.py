"""Project-wide settings for the EMG camera mouse MVP."""

CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# "hand": MediaPipe hand tracking, "gaze": webcam face/eye based gaze estimate.
CONTROL_MODE = "gaze"

# Smaller values make the cursor smoother but slower to follow the finger.
SMOOTHING = 0.25

# Prevent repeated click events from firing too quickly.
CLICK_COOLDOWN_SEC = 0.6

LOG_PATH = "logs/session_log.csv"
SHOW_DEBUG_WINDOW = True

# MediaPipe 0.10.35+ uses the Tasks API and needs a local model bundle.
HAND_LANDMARKER_MODEL_PATH = "models/hand_landmarker.task"
HAND_LANDMARKER_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)

# Turn these off during early tests if you only want to verify hand tracking.
ENABLE_MOUSE_MOVE = True
ENABLE_MOUSE_CLICK = True


# Gaze mode is a webcam-only approximation. Tune these values per user/camera.
GAZE_SENSITIVITY_X = 1.8
GAZE_SENSITIVITY_Y = 1.4
GAZE_DEADZONE = 0.04
