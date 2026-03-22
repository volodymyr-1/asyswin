"""
Script tester for validating generated scripts
"""

import os
import sys
import ast
import subprocess
import threading


class ScriptTester:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def test_script(self, script_path: str) -> dict:
        """Test a script for syntax errors"""
        result = {
            "path": script_path,
            "syntax_valid": False,
            "syntax_error": None,
            "runtime_result": None,
        }

        if not os.path.exists(script_path):
            result["syntax_error"] = "File not found"
            return result

        try:
            with open(script_path, "r", encoding="utf-8") as f:
                code = f.read()

            ast.parse(code)
            result["syntax_valid"] = True

        except SyntaxError as e:
            result["syntax_error"] = f"Line {e.lineno}: {e.msg}"
        except Exception as e:
            result["syntax_error"] = str(e)

        return result

    def run_script(self, script_path: str) -> dict:
        """Run script in a subprocess"""
        result = {"success": False, "output": "", "error": None, "return_code": None}

        try:
            proc = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                stdout, stderr = proc.communicate(timeout=self.timeout)
                result["output"] = stdout
                result["error"] = stderr
                result["return_code"] = proc.returncode
                result["success"] = proc.returncode == 0
            except subprocess.TimeoutExpired:
                proc.kill()
                result["error"] = f"Script timed out after {self.timeout}s"

        except Exception as e:
            result["error"] = str(e)

        return result
