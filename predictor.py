"""
Модуль предсказания сценариев
Анализирует историю действий и предлагает топ-3 вероятных сценариев с готовыми скриптами
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from collections import Counter


class Predictor:
    def __init__(
        self, patterns_file: str = "patterns.json", scripts_dir: str = "scripts"
    ):
        self.patterns_file = patterns_file
        self.scripts_dir = scripts_dir
        self.patterns = self._load_patterns()

        os.makedirs(scripts_dir, exist_ok=True)

    def _load_patterns(self) -> List[Dict]:
        """Загрузить историю паттернов"""
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_patterns(self):
        """Сохранить паттерны"""
        with open(self.patterns_file, "w", encoding="utf-8") as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=2)

    def add_pattern(self, actions: List[Dict], goal: str, subtasks: List[Dict]):
        """
        Добавить новый паттерн из записанных действий

        Args:
            actions: Список действий
            goal: Цель действий
            subtasks: Подзадачи со скриптами
        """
        # Создаём сигнатуру паттерна (последовательность типов действий)
        signature = self._create_signature(actions)

        pattern = {
            "id": len(self.patterns) + 1,
            "signature": signature,
            "goal": goal,
            "subtasks": subtasks,
            "actions_count": len(actions),
            "created_at": datetime.now().isoformat(),
            "used_count": 1,
            "last_used": datetime.now().isoformat(),
        }

        # Проверяем, есть ли похожий паттерн
        existing = self._find_similar_pattern(signature)
        if existing:
            existing["used_count"] += 1
            existing["last_used"] = datetime.now().isoformat()
            existing["subtasks"] = subtasks  # Обновляем скрипты
            print(
                f"[PREDICTOR] 📊 Обновлён существующий паттерн (использован {existing['used_count']} раз)"
            )
        else:
            self.patterns.append(pattern)
            print(f"[PREDICTOR] ➕ Добавлен новый паттерн")

        self._save_patterns()

    def _create_signature(self, actions: List[Dict]) -> str:
        """Создать сигнатуру паттерна"""
        signature_parts = []

        for action in actions[:20]:
            action_type = action.get("type", "")
            if action_type == "key_press":
                key = action.get("key", "")
                signature_parts.append(f"K_{key}")
            elif action_type == "mouse_click":
                x, y = action.get("x", 0), action.get("y", 0)
                signature_parts.append(f"C_{x // 50}_{y // 50}")
            elif action_type == "mouse_move":
                signature_parts.append("M")
            elif action_type == "mouse_scroll":
                dy = action.get("dy", 0)
                direction = "U" if dy > 0 else "D"
                signature_parts.append(f"S_{direction}")

        return "_".join(signature_parts)

    def _find_similar_pattern(self, signature: str) -> Optional[Dict]:
        """Найти похожий паттерн по сигнатуре"""
        for pattern in self.patterns:
            if pattern["signature"] == signature:
                return pattern
        return None

    def get_top_predictions(
        self, current_actions: List[Dict] = None, limit: int = 3
    ) -> List[Dict]:
        """
        Получить топ-N предсказаний на основе истории

        Args:
            current_actions: Текущие действия (для контекста)
            limit: Количество предсказаний

        Returns:
            Список предсказаний с готовыми скриптами
        """
        if not self.patterns:
            print("[PREDICTOR] 📭 Нет истории паттернов")
            return []

        # Сортируем паттерны по частоте использования
        sorted_patterns = sorted(
            self.patterns, key=lambda p: p.get("used_count", 0), reverse=True
        )

        predictions = []

        for pattern in sorted_patterns[:limit]:
            prediction = {
                "name": pattern.get("goal", "Неизвестный сценарий"),
                "description": f"Использовалось {pattern.get('used_count', 0)} раз",
                "used_count": pattern.get("used_count", 0),
                "last_used": pattern.get("last_used", ""),
                "subtasks": pattern.get("subtasks", []),
                "script_path": self._generate_script_file(pattern),
            }
            predictions.append(prediction)

        return predictions

    def _generate_script_file(self, pattern: Dict) -> str:
        """Сгенерировать файл скрипта для паттерна"""
        goal = pattern.get("goal", "scenario")
        subtasks = pattern.get("subtasks", [])

        # Очищаем имя файла
        safe_name = "".join(c for c in goal if c.isalnum() or c in " _-").strip()
        safe_name = safe_name.replace(" ", "_")[:30]

        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{safe_name}_{timestamp}.py"
        filepath = os.path.join(self.scripts_dir, filename)

        # Генерируем скрипт
        script_code = self._create_scenario_script(goal, subtasks)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(script_code)

        return filepath

    def _create_scenario_script(self, goal: str, subtasks: List[Dict]) -> str:
        """Создать код скрипта для сценария"""

        subtask_calls = []
        for i, subtask in enumerate(subtasks, 1):
            name = subtask.get("name", f"Шаг {i}")
            script = subtask.get("script", "# Нет кода")

            subtask_calls.append(f'''
    # Шаг {i}: {name}
    print(f"\\\\n{"=" * 40}")
    print("▶ Шаг {i}: {name}")
    print(f"{"=" * 40}")
    try:
{self._indent(script, 8)}
    except Exception as e:
        print(f"❌ Ошибка на шаге {i}: {{e}}")
        if input("Продолжить? (y/n): ").lower() != 'y':
            return
    time.sleep(1)
''')

        full_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматизированный сценарий
Цель: {goal}
Создано: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Подзадач: {len(subtasks)}
"""

import time
import pyautogui
import subprocess
import sys

# Настройки безопасности
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

def main():
    """Выполнение сценария"""
    print("🚀 Запуск сценария")
    print(f"Цель: {goal}")
    print(f"Шагов: {len(subtasks)}")
    print("="*40)
    
    start_time = time.time()
    
{"".join(subtask_calls)}
    
    elapsed = time.time() - start_time
    print("\\n" + "="*40)
    print(f"✅ Сценарий выполнен за {{elapsed:.1f}} секунд")
    print("="*40)

if __name__ == "__main__":
    print("\\nНажмите Enter для запуска или Ctrl+C для отмены...")
    input()
    main()
'''
        return full_script

    def _indent(self, code: str, spaces: int) -> str:
        """Добавить отступы к коду"""
        lines = code.split("\n")
        indented = [" " * spaces + line if line.strip() else line for line in lines]
        return "\n".join(indented)

    def display_predictions(self, predictions: List[Dict]):
        """Отобразить предсказания в консоли"""
        if not predictions:
            print("\n📭 Нет сохранённых сценариев")
            print("Выполните несколько задач, и система запомнит ваши паттерны!")
            return

        print("\n" + "=" * 60)
        print("🔮 ТОП-3 ЧАСТО ИСПОЛЬЗУЕМЫХ СЦЕНАРИЯ")
        print("=" * 60)

        for i, pred in enumerate(predictions, 1):
            print(f"\n{'─' * 50}")
            print(f"📊 #{i}: {pred['name']}")
            print(f"   Использовано: {pred['used_count']} раз")
            print(f"   Последний раз: {pred['last_used'][:16]}")
            print(f"   Шагов: {len(pred.get('subtasks', []))}")
            print(f"   📁 Скрипт: {pred['script_path']}")
            print(f'   ▶ Запуск: python "{pred["script_path"]}"')

        print(f"\n{'─' * 50}")
        print("💡 Совет: Скрипты можно запускать напрямую или модифицировать")

    def get_statistics(self) -> Dict:
        """Получить статистику по паттернам"""
        if not self.patterns:
            return {"total_patterns": 0, "total_uses": 0}

        total_uses = sum(p.get("used_count", 0) for p in self.patterns)

        return {
            "total_patterns": len(self.patterns),
            "total_uses": total_uses,
            "most_used": max(self.patterns, key=lambda p: p.get("used_count", 0)).get(
                "goal", ""
            ),
            "average_uses": total_uses / len(self.patterns) if self.patterns else 0,
        }
