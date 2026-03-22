#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер скриптов для AsysWin
Управление, запуск и рекомендация скриптов
"""

import os
import json
import time
import subprocess
import threading
import psutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class ScriptInfo:
    """Информация о скрипте"""

    path: str
    name: str
    description: str
    script_type: str  # python, powershell, batch
    created_at: str
    last_run: Optional[str]
    run_count: int
    success_count: int
    total_duration: float
    avg_duration: float
    tags: List[str]
    parameters: Dict[str, Any]

    @property
    def success_rate(self) -> float:
        """Процент успешных запусков"""
        if self.run_count == 0:
            return 0.0
        return (self.success_count / self.run_count) * 100

    @property
    def is_recent(self) -> bool:
        """Был ли запущен в последние 24 часа"""
        if not self.last_run:
            return False
        last_run_time = datetime.fromisoformat(self.last_run.replace("Z", "+00:00"))
        return datetime.now() - last_run_time < timedelta(hours=24)


@dataclass
class ExecutionResult:
    """Результат выполнения скрипта"""

    success: bool
    duration: float
    output: str
    error: Optional[str]
    exit_code: int
    execution_id: str


@dataclass
class ExecutionProgress:
    """Прогресс выполнения"""

    execution_id: str
    status: str  # running, completed, failed, stopped
    progress: float  # 0.0 - 100.0
    current_step: str
    elapsed_time: float


class ScriptManager:
    """Менеджер скриптов"""

    def __init__(self, scripts_dir: str = "generated_scripts"):
        self.scripts_dir = scripts_dir
        self.execution_history_file = os.path.join(
            scripts_dir, "execution_history.json"
        )
        self.execution_progress = {}  # execution_id -> ExecutionProgress
        self.active_executions = {}  # execution_id -> process

        # Создаем директорию если не существует
        os.makedirs(scripts_dir, exist_ok=True)

        # Загружаем историю выполнения
        self.execution_history = self._load_execution_history()

    def get_all_scripts(self) -> List[ScriptInfo]:
        """Получить все доступные скрипты"""
        scripts = []

        if not os.path.exists(self.scripts_dir):
            return scripts

        for session_name in os.listdir(self.scripts_dir):
            session_dir = os.path.join(self.scripts_dir, session_name)
            if not os.path.isdir(session_dir):
                continue

            # Ищем скрипты в сессии
            for filename in os.listdir(session_dir):
                if filename.endswith((".py", ".ps1", ".bat", ".cmd")):
                    script_path = os.path.join(session_dir, filename)
                    script_info = self._analyze_script(script_path)
                    if script_info:
                        scripts.append(script_info)

        return sorted(scripts, key=lambda x: x.created_at, reverse=True)

    def get_top_scripts(self, limit: int = 3) -> List[ScriptInfo]:
        """Получить топ-N скриптов для рекомендации"""
        all_scripts = self.get_all_scripts()

        # Рассчитываем рейтинг для каждого скрипта
        scored_scripts = []
        for script in all_scripts:
            score = self._calculate_script_score(script)
            scored_scripts.append((score, script))

        # Сортируем по рейтингу и возвращаем топ-N
        scored_scripts.sort(key=lambda x: x[0], reverse=True)
        return [script for score, script in scored_scripts[:limit]]

    def _calculate_script_score(self, script: ScriptInfo) -> float:
        """Рассчитать рейтинг скрипта для рекомендации"""
        # Базовые коэффициенты
        FREQUENCY_WEIGHT = 0.3
        RECENCY_WEIGHT = 0.3
        SUCCESS_WEIGHT = 0.3
        TIME_WEIGHT = 0.1

        # Частота использования (нормализуем до 0-1)
        frequency_score = min(script.run_count / 10.0, 1.0)

        # Актуальность по времени (экспоненциальное затухание)
        recency_score = 0.0
        if script.last_run:
            last_run_time = datetime.fromisoformat(
                script.last_run.replace("Z", "+00:00")
            )
            hours_ago = (datetime.now() - last_run_time).total_seconds() / 3600
            recency_score = max(0, 1.0 - (hours_ago / 168))  # За неделю

        # Успешность выполнения
        success_score = script.success_rate / 100.0

        # Временная релевантность (учитываем время суток и день недели)
        time_score = self._get_time_relevance_bonus(script)

        # Итоговый рейтинг
        total_score = (
            frequency_score * FREQUENCY_WEIGHT
            + recency_score * RECENCY_WEIGHT
            + success_score * SUCCESS_WEIGHT
            + time_score * TIME_WEIGHT
        )

        return total_score

    def _get_time_relevance_bonus(self, script: ScriptInfo) -> float:
        """Получить бонус за временнУю релевантность"""
        now = datetime.now()
        current_hour = now.hour
        current_weekday = now.weekday()  # 0-6 (пн-вс)

        # Анализируем историю запусков для определения паттернов
        script_history = self.execution_history.get(script.path, [])

        if not script_history:
            return 0.5  # Нейтральный бонус для новых скриптов

        # Анализируем часы запусков
        hour_counts = [0] * 24
        weekday_counts = [0] * 7

        for record in script_history:
            run_time = datetime.fromisoformat(
                record["timestamp"].replace("Z", "+00:00")
            )
            hour_counts[run_time.hour] += 1
            weekday_counts[run_time.weekday()] += 1

        # Рассчитываем вероятность для текущего времени
        hour_probability = hour_counts[current_hour] / len(script_history)
        weekday_probability = weekday_counts[current_weekday] / len(script_history)

        # Возвращаем среднюю вероятность
        return (hour_probability + weekday_probability) / 2

    def _analyze_script(self, script_path: str) -> Optional[ScriptInfo]:
        """Анализировать скрипт и создать ScriptInfo"""
        try:
            # Определяем тип скрипта по расширению
            ext = os.path.splitext(script_path)[1].lower()
            if ext == ".py":
                script_type = "python"
            elif ext in [".ps1"]:
                script_type = "powershell"
            elif ext in [".bat", ".cmd"]:
                script_type = "batch"
            else:
                return None

            # Получаем базовую информацию
            stat = os.stat(script_path)
            created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()

            # Читаем метаданные из комментариев (если есть)
            description = self._extract_description(script_path)
            tags = self._extract_tags(script_path)
            parameters = self._extract_parameters(script_path)

            # Получаем информацию из истории выполнения
            history = self.execution_history.get(script_path, [])
            run_count = len(history)
            success_count = sum(1 for r in history if r.get("success", False))
            total_duration = sum(r.get("duration", 0) for r in history)
            avg_duration = total_duration / run_count if run_count > 0 else 0

            # Определяем последний запуск
            last_run = None
            if history:
                last_run = sorted(history, key=lambda x: x["timestamp"], reverse=True)[
                    0
                ]["timestamp"]

            return ScriptInfo(
                path=script_path,
                name=os.path.basename(script_path),
                description=description,
                script_type=script_type,
                created_at=created_at,
                last_run=last_run,
                run_count=run_count,
                success_count=success_count,
                total_duration=total_duration,
                avg_duration=avg_duration,
                tags=tags,
                parameters=parameters,
            )

        except Exception as e:
            print(f"Ошибка анализа скрипта {script_path}: {e}")
            return None

    def _extract_description(self, script_path: str) -> str:
        """Извлечь описание из комментариев скрипта"""
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Ищем описание в первых строках
            for line in lines[:20]:
                line = line.strip()
                if line.startswith('"""') or line.startswith("'''"):
                    # Ищем многострочный комментарий
                    description_lines = []
                    in_docstring = True
                    for next_line in lines[lines.index(line) + 1 :]:
                        if next_line.strip().endswith(
                            '"""'
                        ) or next_line.strip().endswith("'''"):
                            in_docstring = False
                            break
                        if next_line.strip():
                            description_lines.append(next_line.strip())
                    return " ".join(description_lines)[:200]
                elif line.startswith("#"):
                    # Однострочный комментарий
                    return line[1:].strip()[:200]

        except:
            pass

        return f"Скрипт {os.path.basename(script_path)}"

    def _extract_tags(self, script_path: str) -> List[str]:
        """Извлечь теги из скрипта"""
        tags = []
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read().lower()

            # Простой анализ по ключевым словам
            if "copy" in content or "копиру" in content:
                tags.append("копирование")
            if "move" in content or "перемещ" in content:
                tags.append("перемещение")
            if "send" in content or "отправ" in content or "email" in content:
                tags.append("email")
            if "archive" in content or "архив" in content:
                tags.append("архивация")
            if "backup" in content or "резервн" in content:
                tags.append("резервное копирование")

        except:
            pass

        return tags

    def _extract_parameters(self, script_path: str) -> Dict[str, Any]:
        """Извлечь параметры скрипта"""
        # Пока возвращаем пустой словарь
        # В будущем можно анализировать аргументы командной строки
        return {}

    def execute_script(
        self, script_path: str, timeout: int = 300, parameters: Dict = None
    ) -> ExecutionResult:
        """Выполнить скрипт в песочнице"""
        execution_id = self._generate_execution_id()

        # Создаем запись о выполнении
        progress = ExecutionProgress(
            execution_id=execution_id,
            status="running",
            progress=0.0,
            current_step="Инициализация",
            elapsed_time=0.0,
        )
        self.execution_progress[execution_id] = progress

        start_time = time.time()

        try:
            # Определяем команду запуска в зависимости от типа скрипта
            if script_path.endswith(".py"):
                cmd = ["python", script_path]
            elif script_path.endswith(".ps1"):
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
            elif script_path.endswith((".bat", ".cmd")):
                cmd = [script_path]
            else:
                raise ValueError(f"Неподдерживаемый тип скрипта: {script_path}")

            # Добавляем параметры если есть
            if parameters:
                for key, value in parameters.items():
                    cmd.extend([f"--{key}", str(value)])

            # Запускаем процесс
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(script_path),
            )

            self.active_executions[execution_id] = process

            # Ожидаем завершения с таймаутом
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                exit_code = process.returncode
                success = exit_code == 0

            except subprocess.TimeoutExpired:
                # Превышено время выполнения
                process.kill()
                stdout, stderr = process.communicate()
                exit_code = -1
                success = False
                stderr = f"Таймаут выполнения ({timeout}s)\n{stderr}"

            finally:
                if execution_id in self.active_executions:
                    del self.active_executions[execution_id]

            duration = time.time() - start_time

            # Обновляем прогресс
            progress.status = "completed" if success else "failed"
            progress.progress = 100.0
            progress.elapsed_time = duration

            # Сохраняем результат в историю
            self._save_execution_result(
                script_path, success, duration, stdout, stderr, exit_code
            )

            return ExecutionResult(
                success=success,
                duration=duration,
                output=stdout,
                error=stderr,
                exit_code=exit_code,
                execution_id=execution_id,
            )

        except Exception as e:
            duration = time.time() - start_time
            progress.status = "failed"
            progress.progress = 0.0
            progress.elapsed_time = duration

            self._save_execution_result(script_path, False, duration, "", str(e), -1)

            return ExecutionResult(
                success=False,
                duration=duration,
                output="",
                error=str(e),
                exit_code=-1,
                execution_id=execution_id,
            )

    def stop_execution(self, execution_id: str) -> bool:
        """Остановить выполнение скрипта"""
        if execution_id in self.active_executions:
            try:
                process = self.active_executions[execution_id]
                process.terminate()

                # Ждем завершения процесса
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

                # Обновляем прогресс
                if execution_id in self.execution_progress:
                    self.execution_progress[execution_id].status = "stopped"
                    self.execution_progress[execution_id].progress = 0.0

                return True
            except Exception:
                return False
        return False

    def get_execution_progress(self, execution_id: str) -> Optional[ExecutionProgress]:
        """Получить прогресс выполнения"""
        return self.execution_progress.get(execution_id)

    def get_script_history(self, script_path: str) -> List[Dict]:
        """Получить историю выполнения скрипта"""
        return self.execution_history.get(script_path, [])

    def _generate_execution_id(self) -> str:
        """Сгенерировать уникальный ID выполнения"""
        timestamp = str(time.time())
        return hashlib.md5(timestamp.encode()).hexdigest()[:16]

    def _save_execution_result(
        self,
        script_path: str,
        success: bool,
        duration: float,
        output: str,
        error: str,
        exit_code: int,
    ):
        """Сохранить результат выполнения в историю"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "duration": duration,
            "output": output[:1000],  # Ограничиваем размер
            "error": error[:1000] if error else None,
            "exit_code": exit_code,
        }

        if script_path not in self.execution_history:
            self.execution_history[script_path] = []

        self.execution_history[script_path].append(record)

        # Ограничиваем историю 100 записями
        if len(self.execution_history[script_path]) > 100:
            self.execution_history[script_path] = self.execution_history[script_path][
                -100:
            ]

        self._save_execution_history()

    def _load_execution_history(self) -> Dict:
        """Загрузить историю выполнения"""
        if os.path.exists(self.execution_history_file):
            try:
                with open(self.execution_history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_execution_history(self):
        """Сохранить историю выполнения"""
        try:
            with open(self.execution_history_file, "w", encoding="utf-8") as f:
                json.dump(self.execution_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения истории выполнения: {e}")

    def validate_script(self, script_path: str) -> Dict[str, Any]:
        """Проверить скрипт на безопасность и корректность"""
        result = {
            "valid": False,
            "warnings": [],
            "errors": [],
            "script_type": None,
            "estimated_duration": 0,
        }

        try:
            # Проверяем существование файла
            if not os.path.exists(script_path):
                result["errors"].append("Файл не существует")
                return result

            # Определяем тип скрипта
            ext = os.path.splitext(script_path)[1].lower()
            if ext == ".py":
                result["script_type"] = "python"
                # Проверяем синтаксис Python
                try:
                    with open(script_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    compile(code, script_path, "exec")
                except SyntaxError as e:
                    result["errors"].append(f"Синтаксическая ошибка: {e}")
                    return result
            elif ext in [".ps1"]:
                result["script_type"] = "powershell"
            elif ext in [".bat", ".cmd"]:
                result["script_type"] = "batch"
            else:
                result["errors"].append("Неподдерживаемый тип скрипта")
                return result

            # Проверяем на опасные операции
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read().lower()

            dangerous_patterns = [
                ("format c:", "Опасная операция: форматирование диска"),
                ("del /s /q", "Опасная операция: массовое удаление файлов"),
                ("rm -rf", "Опасная операция: рекурсивное удаление"),
                ("format", "Возможная опасная операция: форматирование"),
                ("shutdown", "Возможная опасная операция: выключение системы"),
            ]

            for pattern, warning in dangerous_patterns:
                if pattern in content:
                    result["warnings"].append(warning)

            # Оценка времени выполнения
            if result["script_type"] == "python":
                lines = content.count("\n")
                if lines < 50:
                    result["estimated_duration"] = 10
                elif lines < 200:
                    result["estimated_duration"] = 60
                else:
                    result["estimated_duration"] = 300

            result["valid"] = True

        except Exception as e:
            result["errors"].append(f"Check error: {e}")

        return result

    def delete_script(self, script_path: str) -> dict:
        """Delete a single script file and clean up history"""
        result = {"success": False, "message": "", "files_removed": 0}

        try:
            if not os.path.exists(script_path):
                result["message"] = "Script file not found"
                return result

            session_dir = os.path.dirname(script_path)

            if os.path.exists(script_path):
                os.remove(script_path)
                result["files_removed"] += 1

            if script_path in self.execution_history:
                del self.execution_history[script_path]
                self._save_execution_history()

            remaining_files = [
                f
                for f in os.listdir(session_dir)
                if f.endswith((".py", ".ps1", ".bat", ".cmd"))
            ]
            if not remaining_files:
                import shutil

                shutil.rmtree(session_dir)
                result["files_removed"] += 1

            result["success"] = True
            result["message"] = "Script deleted successfully"

        except Exception as e:
            result["message"] = f"Error deleting script: {e}"

        return result

    def delete_session(self, session_dir: str) -> dict:
        """Delete entire session folder"""
        result = {"success": False, "message": "", "files_removed": 0}

        try:
            if not os.path.exists(session_dir):
                result["message"] = "Session directory not found"
                return result

            files_in_session = [
                f
                for f in os.listdir(session_dir)
                if f.endswith((".py", ".ps1", ".bat", ".cmd"))
            ]
            result["files_removed"] = len(files_in_session)

            for script_path in files_in_session:
                full_path = os.path.join(session_dir, script_path)
                if full_path in self.execution_history:
                    del self.execution_history[full_path]

            self._save_execution_history()

            import shutil

            shutil.rmtree(session_dir)

            result["success"] = True
            result["message"] = f"Session deleted: {result['files_removed']} files"

        except Exception as e:
            result["message"] = f"Error deleting session: {e}"

        return result
