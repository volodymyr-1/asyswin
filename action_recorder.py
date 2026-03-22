"""
Модуль записи действий пользователя
Отслеживает клавиатуру и мышь с помощью pynput
"""

import json
import time
import os
from datetime import datetime
from pynput import keyboard, mouse
from threading import Lock, Thread
from semantic_logger import SemanticLogger


class ActionRecorder:
    def __init__(self, log_dir="action_logs"):
        self.log_dir = log_dir
        self.is_recording = False
        self.actions = []
        self.lock = Lock()
        self.start_time = None

        # Создаём директорию для логов
        os.makedirs(log_dir, exist_ok=True)

        # Слушатели
        self.keyboard_listener = None
        self.mouse_listener = None

        # Горячие клавиши
        self.hotkey_callbacks = {}

        # Настройки оптимизации
        self.mouse_move_threshold = 50  # Минимальное смещение мыши для записи
        self.key_debounce_ms = 10  # Debounce клавиш (10мс - почти без задержки)
        self.last_mouse_pos = (0, 0)
        self.last_key_time = {}

        # Семантический логгер
        self.semantic_logger = SemanticLogger(log_dir)

    def start_recording(self):
        """Начать запись действий"""
        if self.is_recording:
            print("[RECORDER] Recording already in progress")
            return

        self.is_recording = True
        self.actions = []
        self.start_time = time.time()

        print("[RECORDER] Recording started")

        # Запускаем слушатели
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press, on_release=self._on_key_release
        )
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )

        self.keyboard_listener.start()
        self.mouse_listener.start()

    def stop_recording(self):
        """Остановить запись действий"""
        if not self.is_recording:
            print("[RECORDER] Recording not active")
            return

        self.is_recording = False

        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()

        print(f"[RECORDER] Recording stopped. Actions: {len(self.actions)}")

        # Сохраняем логи
        self._save_log()
        self._save_semantic_logs()

    def _on_key_press(self, key):
        """Обработчик нажатия клавиш с debounce"""
        if not self.is_recording:
            return

        try:
            key_name = key.char if hasattr(key, "char") and key.char else str(key)
        except:
            key_name = str(key)

        # Проверяем горячие клавиши
        if key_name in self.hotkey_callbacks:
            self.hotkey_callbacks[key_name]()
            return

        # Debounce: игнорируем повторы быстрее 100мс
        current_time = time.time() * 1000  # в миллисекундах
        last_time = self.last_key_time.get(key_name, 0)

        if current_time - last_time < self.key_debounce_ms:
            return

        self.last_key_time[key_name] = current_time

        action = {
            "type": "key_press",
            "key": key_name,
            "timestamp": time.time() - self.start_time,
            "datetime": datetime.now().isoformat(),
        }

        with self.lock:
            self.actions.append(action)

        # Добавляем в семантический лог
        self.semantic_logger.log_action(action)

    def _on_key_release(self, key):
        """Обработчик отпускания клавиш"""
        if not self.is_recording:
            return

        try:
            key_name = key.char if hasattr(key, "char") and key.char else str(key)
        except:
            key_name = str(key)

        action = {
            "type": "key_release",
            "key": key_name,
            "timestamp": time.time() - self.start_time,
            "datetime": datetime.now().isoformat(),
        }

        with self.lock:
            self.actions.append(action)

    def _on_mouse_move(self, x, y):
        """Обработчик движения мыши - НЕ ЗАПИСЫВАЕМ (только шум)"""
        # Обновляем позицию для других нужд, но не записываем
        self.last_mouse_pos = (x, y)
        pass

    def _on_mouse_click(self, x, y, button, pressed):
        """Обработчик кликов мыши"""
        if not self.is_recording:
            return

        action = {
            "type": "mouse_click",
            "x": x,
            "y": y,
            "button": str(button),
            "pressed": pressed,
            "timestamp": time.time() - self.start_time,
            "datetime": datetime.now().isoformat(),
        }

        with self.lock:
            self.actions.append(action)

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Обработчик скролла мыши - НЕ ЗАПИСЫВАЕМ (только шум)"""
        pass

    def _save_log(self):
        """Сохранить лог действий в файл"""
        if not self.actions:
            print("[RECORDER] No actions to save")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"actions_{timestamp}.json"
        filepath = os.path.join(self.log_dir, filename)

        log_data = {
            "recorded_at": datetime.now().isoformat(),
            "duration_seconds": self.actions[-1]["timestamp"] if self.actions else 0,
            "total_actions": len(self.actions),
            "actions": self.actions,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

        print(f"[RECORDER] Log saved: {filepath}")
        return filepath

    def _save_semantic_logs(self):
        """Сохранить семантические логи"""
        try:
            raw_path, filtered_path = self.semantic_logger.save_logs()
            summary = self.semantic_logger.get_summary()

            print(f"[RECORDER] Semantic logs saved:")
            print(f"   Raw log: {raw_path} ({summary['raw_count']} actions)")
            print(
                f"   Filtered log: {filtered_path} ({summary['filtered_count']} actions)"
            )
            print(f"   Filter ratio: {summary['filtered_ratio']:.1f}%")

        except Exception as e:
            print(f"[RECORDER] Error saving semantic logs: {e}")

    def register_hotkey(self, key_name, callback):
        """Зарегистрировать горячую клавишу"""
        self.hotkey_callbacks[key_name] = callback

    def get_actions_summary(self):
        """Получить краткую сводку действий"""
        summary = {
            "total": len(self.actions),
            "key_presses": len([a for a in self.actions if a["type"] == "key_press"]),
            "mouse_clicks": len(
                [a for a in self.actions if a["type"] == "mouse_click"]
            ),
            "mouse_moves": len([a for a in self.actions if a["type"] == "mouse_move"]),
            "scrolls": len([a for a in self.actions if a["type"] == "mouse_scroll"]),
        }
        return summary
