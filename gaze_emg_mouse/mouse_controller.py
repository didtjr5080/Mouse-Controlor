"""Mouse movement and click control using pyautogui."""

import pyautogui

import config


class MouseController:
    """Controls mouse actions with relative movement and safety switches."""

    def __init__(self, smoothing=config.SMOOTHING):
        pyautogui.FAILSAFE = True
        self.screen_width, self.screen_height = pyautogui.size()
        self.smoothing = smoothing
        self._smooth_dx = 0.0
        self._smooth_dy = 0.0
        self._dragging = False

    def _clamp_delta(self, dx, dy):
        """Limit one-frame motion so accidental jumps are less severe."""
        max_dx = self.screen_width * 0.05
        max_dy = self.screen_height * 0.05
        dx = max(-max_dx, min(max_dx, dx))
        dy = max(-max_dy, min(max_dy, dy))
        return dx, dy

    def _keep_away_from_failsafe_corners(self, dx, dy):
        """Adjust movement so the cursor does not enter a FAILSAFE corner."""
        current_x, current_y = pyautogui.position()
        margin = config.FAILSAFE_MARGIN_PX

        # If the cursor is already in a corner, skip motion and let the user
        # move it away manually. This keeps FAILSAFE enabled.
        in_left = current_x <= margin
        in_right = current_x >= self.screen_width - 1 - margin
        in_top = current_y <= margin
        in_bottom = current_y >= self.screen_height - 1 - margin
        if (in_left or in_right) and (in_top or in_bottom):
            self._smooth_dx = 0.0
            self._smooth_dy = 0.0
            return 0.0, 0.0

        target_x = current_x + dx
        target_y = current_y + dy
        safe_x = max(margin, min(self.screen_width - 1 - margin, target_x))
        safe_y = max(margin, min(self.screen_height - 1 - margin, target_y))
        return safe_x - current_x, safe_y - current_y

    def move_relative(self, dx, dy):
        """Move the cursor by a smoothed relative delta."""
        target_dx = dx * config.MOUSE_SPEED
        target_dy = dy * config.MOUSE_SPEED

        self._smooth_dx += (target_dx - self._smooth_dx) * self.smoothing
        self._smooth_dy += (target_dy - self._smooth_dy) * self.smoothing
        move_dx, move_dy = self._clamp_delta(self._smooth_dx, self._smooth_dy)

        if config.ENABLE_MOUSE_MOVE:
            move_dx, move_dy = self._keep_away_from_failsafe_corners(move_dx, move_dy)
            if move_dx == 0 and move_dy == 0:
                return move_dx, move_dy
            try:
                pyautogui.moveRel(move_dx, move_dy, duration=0)
            except pyautogui.FailSafeException:
                self._smooth_dx = 0.0
                self._smooth_dy = 0.0
                raise

        return move_dx, move_dy

    def left_click(self):
        """Perform a left click if clicking is enabled."""
        if config.ENABLE_MOUSE_CLICK:
            pyautogui.click(button="left")

    def right_click(self):
        """Perform a right click if clicking is enabled."""
        if config.ENABLE_MOUSE_CLICK:
            pyautogui.click(button="right")

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
        """Return the current cursor position."""
        return pyautogui.position()

    def stop_drag_if_needed(self):
        """Release a held mouse button before exit."""
        if self._dragging and config.ENABLE_MOUSE_CLICK:
            pyautogui.mouseUp(button="left")
        self._dragging = False
