"""Keyboard-based simulator for EMG events."""

import queue

from pynput import keyboard


LEFT_CLICK = "LEFT_CLICK"
RIGHT_CLICK = "RIGHT_CLICK"
DRAG_TOGGLE = "DRAG_TOGGLE"
EXIT = "EXIT"


class EMGInputSimulator:
    """Listens for keyboard input and emits simulated EMG events."""

    def __init__(self):
        self._events = queue.Queue()
        self._listener = keyboard.Listener(on_press=self._on_press)

    def start(self):
        """Start listening in a background thread."""
        self._listener.start()

    def _on_press(self, key):
        """Convert key presses into EMG-like events."""
        if key == keyboard.Key.space:
            self._events.put(LEFT_CLICK)
            return

        if key == keyboard.Key.esc:
            self._events.put(EXIT)
            return False

        try:
            char = key.char.lower()
        except AttributeError:
            return

        if char == "r":
            self._events.put(RIGHT_CLICK)
        elif char == "d":
            self._events.put(DRAG_TOGGLE)
        elif char == "q":
            self._events.put(EXIT)
            return False

    def get_event(self):
        """Return the next pending event, or None if no event is queued."""
        try:
            return self._events.get_nowait()
        except queue.Empty:
            return None

    def stop(self):
        """Stop the keyboard listener."""
        if self._listener.running:
            self._listener.stop()
