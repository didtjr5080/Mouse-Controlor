"""Mouse movement and click control using pyautogui."""

import time

import pyautogui

import config


class MouseController:
    """Converts normalized hand coordinates into screen mouse actions."""

    def __init__(self, smoothing=config.SMOOTHING):
        pyautogui.FAILSAFE = True
        self.screen_width, self.screen_height = pyautogui.size()
        self.smoothing = smoothing
        self._last_x = None
        self._last_y = None
        self._dragging = False
        self._last_click_time = 0.0

    def _clamp(self, value, minimum, maximum):
        return max(minimum, min(maximum, value))

    def _normalized_to_screen(self, x_norm, y_norm):
        x_norm = self._clamp(x_norm, 0.0, 1.0)
        y_norm = self._clamp(y_norm, 0.0, 1.0)
        screen_x = int(x_norm * (self.screen_width - 1))
        screen_y = int(y_norm * (self.screen_height - 1))
        return screen_x, screen_y

    def move_to_normalized(self, x_norm, y_norm):
        """Move cursor toward a normalized coordinate with smoothing."""
        target_x, target_y = self._normalized_to_screen(x_norm, y_norm)

        if self._last_x is None or self._last_y is None:
            smooth_x = target_x
            smooth_y = target_y
        else:
            smooth_x = int(self._last_x + (target_x - self._last_x) * self.smoothing)
            smooth_y = int(self._last_y + (target_y - self._last_y) * self.smoothing)

        smooth_x = self._clamp(smooth_x, 0, self.screen_width - 1)
        smooth_y = self._clamp(smooth_y, 0, self.screen_height - 1)

        self._last_x = smooth_x
        self._last_y = smooth_y

        if config.ENABLE_MOUSE_MOVE:
            pyautogui.moveTo(smooth_x, smooth_y)

        return smooth_x, smooth_y

    def left_click(self):
        """Perform a left click if mouse clicking is enabled."""
        if config.ENABLE_MOUSE_CLICK:
            pyautogui.click(button="left")
        self._last_click_time = time.time()

    def right_click(self):
        """Perform a right click if mouse clicking is enabled."""
        if config.ENABLE_MOUSE_CLICK:
            pyautogui.click(button="right")
        self._last_click_time = time.time()

    def toggle_drag(self):
        """Toggle left-button drag mode."""
        if not config.ENABLE_MOUSE_CLICK:
            self._dragging = not self._dragging
            return self._dragging

        if self._dragging:
            pyautogui.mouseUp(button="left")
            self._dragging = False
        else:
            pyautogui.mouseDown(button="left")
            self._dragging = True
        return self._dragging

    def get_current_position(self):
        """Return the current cursor position as (x, y)."""
        return pyautogui.position()

    def stop_drag_if_needed(self):
        """Release the mouse button before the program exits."""
        if self._dragging and config.ENABLE_MOUSE_CLICK:
            pyautogui.mouseUp(button="left")
        self._dragging = False
