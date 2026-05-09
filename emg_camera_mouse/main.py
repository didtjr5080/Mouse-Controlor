"""Main integration loop for the EMG camera mouse MVP."""

import time

import cv2

import config
from emg_input_simulator import (
    DRAG_TOGGLE,
    EXIT,
    LEFT_CLICK,
    RIGHT_CLICK,
    EMGInputSimulator,
)
from gaze_tracker import GazeTracker
from hand_tracker import HandTracker
from logger import SessionLogger
from mouse_controller import MouseController


def draw_status(frame, pointer_data, screen_x, screen_y, last_event, cooldown_remaining):
    """Draw beginner-friendly runtime status text on the camera frame."""
    source_name = "Hand" if config.CONTROL_MODE == "hand" else "Gaze"
    detect_status = (
        f"{source_name} detected" if pointer_data["detected"] else f"{source_name} not detected"
    )
    cooldown_status = "ready" if cooldown_remaining <= 0 else f"{cooldown_remaining:.1f}s"

    lines = [
        f"Mode: {config.CONTROL_MODE}",
        detect_status,
        f"Simulated EMG event: {last_event or 'None'}",
        f"Cursor x, y: {screen_x}, {screen_y}",
        f"Click cooldown: {cooldown_status}",
        f"Mouse move: {'ON' if config.ENABLE_MOUSE_MOVE else 'OFF'}",
        f"Mouse click: {'ON' if config.ENABLE_MOUSE_CLICK else 'OFF'}",
        "Space=left click, R=right click, D=drag, Q/ESC=exit",
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


def main():
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)

    if not cap.isOpened():
        print("Camera could not be opened. Try changing CAMERA_INDEX in config.py.")
        return

    if config.CONTROL_MODE == "gaze":
        pointer_tracker = GazeTracker(draw=True)
    else:
        pointer_tracker = HandTracker(draw=True)

    mouse_controller = MouseController()
    emg_input = EMGInputSimulator()
    logger = SessionLogger(config.LOG_PATH)

    emg_input.start()
    last_click_time = 0.0
    last_event = None
    running = True
    screen_x, screen_y = mouse_controller.get_current_position()

    try:
        while running:
            ok, frame = cap.read()
            if not ok:
                print("Camera frame could not be read.")
                break

            # Flip horizontally so the camera behaves like a mirror.
            frame = cv2.flip(frame, 1)
            pointer_data = pointer_tracker.process(frame)

            if pointer_data["detected"]:
                screen_x, screen_y = mouse_controller.move_to_normalized(
                    pointer_data["x_norm"],
                    pointer_data["y_norm"],
                )

            event = emg_input.get_event()
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
            draw_status(frame, pointer_data, screen_x, screen_y, last_event, cooldown_remaining)

            logger.log(
                {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "hand_detected": pointer_data["detected"],
                    "hand_x": pointer_data["x_px"] if pointer_data["detected"] else "",
                    "hand_y": pointer_data["y_px"] if pointer_data["detected"] else "",
                    "screen_x": screen_x,
                    "screen_y": screen_y,
                    "event": event or "",
                }
            )

            if config.SHOW_DEBUG_WINDOW:
                cv2.imshow("EMG Camera Mouse", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:
                    running = False
            else:
                # waitKey still lets OpenCV process window events if a window exists.
                cv2.waitKey(1)

    finally:
        mouse_controller.stop_drag_if_needed()
        emg_input.stop()
        pointer_tracker.close()
        logger.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
