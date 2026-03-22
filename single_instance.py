"""
Single instance checker
Prevents multiple instances of AsysWin
"""

import os
import sys
import tempfile
import atexit


class SingleInstance:
    def __init__(self, lock_file: str = "asyswin.lock"):
        self.lock_file = os.path.join(tempfile.gettempdir(), lock_file)
        self.lock_fd = None
        self.is_locked = False

    def acquire(self) -> bool:
        """Acquire lock"""
        try:
            if os.path.exists(self.lock_file):
                try:
                    with open(self.lock_file, "r") as f:
                        pid = f.read().strip()
                    if self._is_process_running(int(pid)):
                        return False
                    else:
                        os.remove(self.lock_file)
                except:
                    os.remove(self.lock_file)

            self.lock_fd = open(self.lock_file, "w")
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            self.is_locked = True
            atexit.register(self.release)
            return True

        except Exception as e:
            print(f"[SINGLE_INSTANCE] Lock error: {e}")
            return False

    def _is_process_running(self, pid: int) -> bool:
        """Check if process is running"""
        try:
            if sys.platform == "win32":
                import ctypes

                kernel32 = ctypes.windll.kernel32
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                handle = kernel32.OpenProcess(
                    PROCESS_QUERY_LIMITED_INFORMATION, False, pid
                )
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                os.kill(pid, 0)
                return True
        except:
            return False

    def release(self):
        """Release lock"""
        if self.is_locked and self.lock_fd:
            try:
                self.lock_fd.close()
                os.remove(self.lock_file)
            except:
                pass
            self.is_locked = False


_instance = SingleInstance()


def check_single_instance() -> bool:
    """Check if another instance is running"""
    return _instance.acquire()


def release_instance():
    """Release instance lock"""
    global _instance
    if _instance:
        _instance.release()
