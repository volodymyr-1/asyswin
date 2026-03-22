"""
Activity monitor - tracks user idle/active state
"""

import time
import threading
from pynput import mouse, keyboard


class ActivityMonitor:
    def __init__(self, idle_threshold: float = 30.0):
        self.idle_threshold = idle_threshold
        self.is_monitoring = False
        self.last_activity_time = time.time()
        self.current_state = "idle"
        self.on_active = None
        self.on_idle = None
        self.mouse_listener = None
        self.keyboard_listener = None
        self.monitor_thread = None

    def start(self):
        """Start monitoring"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.last_activity_time = time.time()

        self.mouse_listener = mouse.Listener(
            on_move=self._on_activity,
            on_click=self._on_activity,
            on_scroll=self._on_activity,
        )
        self.keyboard_listener = keyboard.Listener(on_press=self._on_activity)

        self.mouse_listener.start()
        self.keyboard_listener.start()

        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        """Stop monitoring"""
        self.is_monitoring = False

        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    def _on_activity(self, *args):
        """Handle activity"""
        self.last_activity_time = time.time()

        if self.current_state == "idle":
            self.current_state = "active"
            if self.on_active:
                self.on_active()

    def _monitor_loop(self):
        """Idle monitoring loop"""
        while self.is_monitoring:
            idle_time = time.time() - self.last_activity_time

            if idle_time >= self.idle_threshold and self.current_state == "active":
                self.current_state = "idle"
                if self.on_idle:
                    self.on_idle()

            time.sleep(1)

    def get_idle_time(self) -> float:
        """Get idle time in seconds"""
        return time.time() - self.last_activity_time

    def get_status(self) -> dict:
        """Get monitoring status"""
        return {
            "is_monitoring": self.is_monitoring,
            "current_state": self.current_state,
            "idle_time": self.get_idle_time(),
            "idle_threshold": self.idle_threshold,
        }
