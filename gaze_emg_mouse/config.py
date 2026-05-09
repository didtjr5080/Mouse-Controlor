"""Project-wide settings for gaze_emg_mouse."""

CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Start disabled for safe first tests. Turn these on only after tracking is stable.
ENABLE_MOUSE_MOVE = True
ENABLE_MOUSE_CLICK = True

SHOW_DEBUG_WINDOW = True

TRACKING_MODE = "face"
# Possible values:
# "face": face/nose center based relative cursor movement
# "gaze": experimental eye direction mode for later expansion

SMOOTHING = 0.25
DEAD_ZONE_X = 45
DEAD_ZONE_Y = 35 
MOUSE_SPEED = 0.08
FAILSAFE_MARGIN_PX = 12

CLICK_COOLDOWN_SEC = 0.6

LOG_PATH = "logs/session_log.csv"

# Newer MediaPipe packages may expose only the Tasks API, which needs a model.
FACE_LANDMARKER_MODEL_PATH = "models/face_landmarker.task"
FACE_LANDMARKER_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)
