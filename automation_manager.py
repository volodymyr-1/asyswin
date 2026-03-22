"""
Automation Manager - manages action logs and recommended scripts
"""

import os
import json
import time
from typing import List, Dict, Optional


class AutomationManager:
    def __init__(self, log_dir: str = "action_logs"):
        self.logs = []
        self.log_dir = log_dir
        self.recommended = {
            "Auto-Login": "import pyautogui\npyautogui.write('username')\npyautogui.press('tab')\npyautogui.write('password')\npyautogui.press('enter')",
            "Report Export": "import pyautogui\nimport time\ntime.sleep(2)\npyautogui.click(x=100, y=200)\ntime.sleep(1)\npyautogui.click(x=300, y=400)",
            "System Cleanup": "import os\nimport shutil\ntemp_dir = os.getenv('TEMP')\nfor item in os.listdir(temp_dir):\n    path = os.path.join(temp_dir, item)\n    try:\n        if os.path.isfile(path):\n            os.remove(path)\n    except:\n        pass",
        }

        os.makedirs(log_dir, exist_ok=True)

    def add_log(self, action_type: str, details: str) -> Dict:
        """Add a log entry"""
        log_entry = {
            "id": time.time(),
            "time": time.strftime("%H:%M:%S"),
            "type": action_type,
            "details": details,
        }
        self.logs.append(log_entry)
        return log_entry

    def delete_log(self, index: int) -> Optional[Dict]:
        """Delete a log by index"""
        if 0 <= index < len(self.logs):
            return self.logs.pop(index)
        return None

    def clear_all(self):
        """Clear all logs"""
        self.logs = []

    def get_logs(self) -> List[Dict]:
        """Get all logs"""
        return self.logs.copy()

    def get_recommended(self, name: str) -> str:
        """Get recommended script by name"""
        return self.recommended.get(name, "# Script not found")

    def get_recommended_list(self) -> List[Dict]:
        """Get list of recommended scripts"""
        return [
            {"name": name, "script": script}
            for name, script in self.recommended.items()
        ]

    def save_logs(self, filename: str = None) -> str:
        """Save logs to file"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"logs_{timestamp}.json"

        filepath = os.path.join(self.log_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)

        return filepath
