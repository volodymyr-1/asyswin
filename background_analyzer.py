"""
Background analyzer with CPU load limiting
Analyzes actions in background mode, not exceeding 50% CPU
"""

import time
import threading
import psutil
from typing import List, Dict, Optional, Callable
from queue import Queue


class BackgroundAnalyzer:
    def __init__(self, cpu_limit: float = 50.0):
        self.cpu_limit = cpu_limit
        self.is_running = False
        self.analysis_thread = None
        self.task_queue = Queue()
        self.results = []
        self.on_complete_callback = None

    def start(self):
        """Start background analyzer"""
        if self.is_running:
            return

        self.is_running = True
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()

    def stop(self):
        """Stop background analyzer"""
        self.is_running = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)

    def add_task(self, task_data: Dict, analyzer_func: Callable):
        """Add analysis task"""
        self.task_queue.put(
            {"data": task_data, "func": analyzer_func, "added_at": time.time()}
        )

    def set_on_complete(self, callback: Callable):
        """Set callback for result handling"""
        self.on_complete_callback = callback

    def _analysis_loop(self):
        """Main analysis loop"""
        while self.is_running:
            cpu_percent = psutil.cpu_percent(interval=0.5)

            if cpu_percent > self.cpu_limit:
                time.sleep(2)
                continue

            if self.task_queue.empty():
                time.sleep(1)
                continue

            try:
                task = self.task_queue.get(timeout=1)
            except:
                continue

            try:
                result = task["func"](task["data"])

                if result:
                    self.results.append(
                        {
                            "result": result,
                            "completed_at": time.time(),
                            "task_data": task["data"],
                        }
                    )

                    if self.on_complete_callback:
                        self.on_complete_callback(result)
                else:
                    if self.on_complete_callback:
                        self.on_complete_callback(None)

            except Exception as e:
                print(f"[BACKGROUND] Analysis error: {e}")

            time.sleep(1)

    def get_results(self) -> List[Dict]:
        """Get all analysis results"""
        return self.results.copy()

    def get_latest_result(self) -> Optional[Dict]:
        """Get latest result"""
        if self.results:
            return self.results[-1]
        return None

    def clear_results(self):
        """Clear results"""
        self.results.clear()
