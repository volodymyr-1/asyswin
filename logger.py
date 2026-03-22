"""
Logger for AsysWin
"""

import os
from datetime import datetime
from typing import Optional


class Logger:
    def __init__(self, log_file: str = "asyswin.log"):
        self.log_file = log_file
        self._ensure_log_file()

    def _ensure_log_file(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(f"=== AsysWin Log Started: {datetime.now()} ===\n")

    def _log(self, level: str, message: str, category: str = ""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        category_str = f"[{category}] " if category else ""
        log_line = f"[{timestamp}] [{level}] {category_str}{message}\n"

        print(log_line.strip())

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            print(f"[LOG ERROR] Cannot write to log: {e}")

    def info(self, message: str, category: str = ""):
        self._log("INFO", message, category)

    def warning(self, message: str, category: str = ""):
        self._log("WARNING", message, category)

    def error(self, message: str, category: str = ""):
        self._log("ERROR", message, category)

    def log_action(self, action: str, details: str = ""):
        self._log("ACTION", f"{action}: {details}", "USER")

    def log_analysis(self, status: str, details: str = ""):
        self._log("ANALYSIS", f"{status} - {details}", "AI")


logger = Logger()
