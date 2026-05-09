"""Main integration loop for the gaze + simulated EMG mouse MVP."""

import time

import cv2
import pyautogui

import config
from emg_input_simulator import (
    DRAG_TOGGLE,
    EXIT,
    LEFT_CLICK,
    RIGHT_CLICK,
    EMGInputSimulator,
)
from face_tracker import FaceTracker
from gaze_tracker import GazeTracker
from logger import SessionLogger
from mouse_controller import MouseController


def print_startup_settings():
    """Print important safety and control settings at startup."""
    print("=== gaze_emg_mouse settings ===")
    print(f"TRACKING_MODE: {config.TRACKING_MODE}")
    print(f"ENABLE_MOUSE_MOVE: {config.ENABLE_MOUSE_MOVE}")
    print(f"ENABLE_MOUSE_CLICK: {config.ENABLE_MOUSE_CLICK}")
    print(f"DEAD_ZONE_X/Y: {config.DEAD_ZONE_X}, {config.DEAD_ZONE_Y}")
    print(f"MOUSE_SPEED: {config.MOUSE_SPEED}")
    print(f"SMOOTHING: {config.SMOOTHING}")
    print(f"FAILSAFE_MARGIN_PX: {config.FAILSAFE_MARGIN_PX}")
    print("Q or ESC exits safely.")
    print("===============================")


def apply_dead_zone(offset_x, offset_y):
    """Return zero movement inside the center dead zone."""
    dx = 0 if abs(offset_x) <= config.DEAD_ZONE_X else offset_x
    dy = 0 if abs(offset_y) <= config.DEAD_ZONE_Y else offset_y
    return dx, dy


def draw_status(frame, face_data, dx, dy, last_event, cooldown_remaining):
    """Draw runtime status on the camera frame."""
    face_status = "Detected" if face_data["detected"] else "Not detected"
    cooldown_status = "ready" if cooldown_remaining <= 0 else f"{cooldown_remaining:.1f}s"
    move_status = "enabled" if config.ENABLE_MOUSE_MOVE else "disabled"
    click_status = "enabled" if config.ENABLE_MOUSE_CLICK else "disabled"

    lines = [
        f"Face: {face_status}",
        f"Mode: {config.TRACKING_MODE}",
        f"Mouse move: {move_status}",
        f"Mouse click: {click_status}",
        f"dx, dy: {dx:.1f}, {dy:.1f}",
        f"Last event: {last_event or 'None'}",
        f"Click cooldown: {cooldown_status}",
        "Q or ESC: Exit",
    ]

    for index, line in enumerate(lines):
        y = 25 + index * 25
        cv2.putText(
            frame,
            line,
            (10, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

    height, width = frame.shape[:2]
    center_x = width // 2
    center_y = height // 2
    cv2.rectangle(
        frame,
        (center_x - config.DEAD_ZONE_X, center_y - config.DEAD_ZONE_Y),
        (center_x + config.DEAD_ZONE_X, center_y + config.DEAD_ZONE_Y),
        (255, 255, 0),
        2,
    )


def main():
    print_startup_settings()

    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)

    if not cap.isOpened():
        print("Camera could not be opened. Try changing CAMERA_INDEX in config.py.")
        return

    face_tracker = FaceTracker(draw=True)
    gaze_tracker = GazeTracker()
    mouse_controller = MouseController()
    simulator = EMGInputSimulator()
    logger = SessionLogger(config.LOG_PATH)

    simulator.start()
    last_click_time = 0.0
    last_event = None
    running = True
    dx = 0.0
    dy = 0.0

    try:
        while running:
            ok, frame = cap.read()
            if not ok:
                print("Camera frame could not be read.")
                break

            frame = cv2.flip(frame, 1)
            face_data = face_tracker.process(frame)

            if face_data["detected"]:
                frame_height, frame_width = frame.shape[:2]
                center_x = frame_width / 2
                center_y = frame_height / 2

                offset_x = face_data["x_px"] - center_x
                offset_y = face_data["y_px"] - center_y
                dx, dy = apply_dead_zone(offset_x, offset_y)

                if config.TRACKING_MODE == "gaze":
                    gaze_info = gaze_tracker.estimate_gaze_direction(
                        face_data["landmarks"],
                        frame_width,
                        frame_height,
                    )
                    last_event = f"GAZE_{gaze_info['direction'].upper()}"

                try:
                    mouse_controller.move_relative(dx, dy)
                except pyautogui.FailSafeException:
                    print("PyAutoGUI fail-safe triggered. Exiting safely.")
                    running = False
            else:
                dx = 0.0
                dy = 0.0

            event = simulator.get_event()
            if event is not None:
                last_event = event

            now = time.time()
            cooldown_remaining = max(
                0.0,
                config.CLICK_COOLDOWN_SEC - (now - last_click_time),
            )

            if event == LEFT_CLICK and cooldown_remaining <= 0:
                mouse_controller.left_click()
                last_click_time = now
            elif event == RIGHT_CLICK and cooldown_remaining <= 0:
                mouse_controller.right_click()
                last_click_time = now
            elif event == DRAG_TOGGLE and cooldown_remaining <= 0:
                dragging = mouse_controller.toggle_drag()
                last_event = f"{DRAG_TOGGLE}_{'ON' if dragging else 'OFF'}"
                last_click_time = now
            elif event == EXIT:
                running = False

            cooldown_remaining = max(
                0.0,
                config.CLICK_COOLDOWN_SEC - (time.time() - last_click_time),
            )
            draw_status(frame, face_data, dx, dy, last_event, cooldown_remaining)

            logger.log(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "face_detected": face_data["detected"],
                    "tracking_mode": config.TRACKING_MODE,
                    "face_x": face_data["x_px"] if face_data["detected"] else "",
                    "face_y": face_data["y_px"] if face_data["detected"] else "",
                    "dx": f"{dx:.2f}",
                    "dy": f"{dy:.2f}",
                    "event": event or "",
                }
            )

            if getattr(config, "SHOW_DEBUG_WINDOW", True):
                cv2.imshow("gaze_emg_mouse", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:
                    running = False
            else:
                cv2.waitKey(1)

    except KeyboardInterrupt:
        print("Interrupted by user. Exiting safely.")
    finally:
        mouse_controller.stop_drag_if_needed()
        simulator.stop()
        face_tracker.close()
        logger.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
