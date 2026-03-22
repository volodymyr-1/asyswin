"""
Модуль генерации и сохранения скриптов
Создаёт отдельные .py файлы для каждой подзадачи
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional


class ScriptGenerator:
    def __init__(self, output_dir: str = "generated_scripts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_scripts(self, analysis_result: Dict, force_new: bool = False) -> List[str]:
        """
        Генерировать скрипты из результата анализа
        
        Args:
            analysis_result: Результат от LLMAnalyzer
            force_new: Принудительно создать новый (игнорировать дубликаты)
            
        Returns:
            Список путей к созданным файлам
        """
        if not analysis_result:
            print("[GENERATOR] Нет данных для генерации")
            return []
            
        goal = analysis_result.get("goal", "Автоматизированная задача")
        subtasks = analysis_result.get("subtasks", [])
        
        if not subtasks:
            print("[GENERATOR] Нет подзадач для генерации")
            return []
            
        # Проверяем дубликаты
        if not force_new:
            existing = self._find_similar_scripts(goal, subtasks)
            if existing:
                print(f"\n{'='*60}")
                print(f"⚠️ Найден похожий скрипт!")
                print(f"{'='*60}")
                print(f"Цель: {existing['goal']}")
                print(f"Создан: {existing['created_at']}")
                print(f"Файлы: {', '.join(existing['files'])}")
                print()
                
                # Возвращаем информацию о существующем скрипте
                return {
                    "duplicate": True,
                    "existing": existing,
                    "new_analysis": analysis_result
                }
            
        created_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Создаём папку для этой сессии
        session_dir = os.path.join(self.output_dir, f"session_{timestamp}")
        os.makedirs(session_dir, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"🎯 ЦЕЛЬ: {goal}")
        print(f"{'='*60}\n")
        
        for i, subtask in enumerate(subtasks, 1):
            name = subtask.get("name", f"subtask_{i}")
            description = subtask.get("description", "")
            script_code = subtask.get("script", "")
            
            # Очищаем имя файла
            safe_name = self._sanitize_filename(name)
            filename = f"{i:02d}_{safe_name}.py"
            filepath = os.path.join(session_dir, filename)
            
            # Добавляем заголовок к скрипту
            full_script = self._add_script_header(name, description, script_code)
            
            # Сохраняем файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_script)
                
            created_files.append(filepath)
            
            print(f"📝 Подзадача {i}: {name}")
            print(f"   Описание: {description}")
            print(f"   Файл: {filepath}")
            print()
            
        # Создаём мастер-скрипт, который запускает все подзадачи
        master_path = self._create_master_script(session_dir, subtasks, goal)
        if master_path:
            created_files.append(master_path)
            
        # Сохраняем метаданные
        self._save_metadata(session_dir, goal, subtasks, created_files)
        
        print(f"✅ Создано файлов: {len(created_files)}")
        print(f"📁 Папка: {session_dir}")
        
        return created_files
        
    def _sanitize_filename(self, name: str) -> str:
        """Очистка имени файла от недопустимых символов"""
        # Заменяем недопустимые символы
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
            
        # Ограничиваем длину
        if len(name) > 50:
            name = name[:50]
            
        return name.strip()
        
    def _add_script_header(self, name: str, description: str, code: str) -> str:
        """Добавить заголовок к скрипту с валидацией"""
        # Валидируем код перед созданием скрипта
        validated_code = self._validate_script_code(code)
        
        header = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматизированный скрипт
Название: {name}
Описание: {description}
Создано: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

ВНИМАНИЕ: Этот скрипт создан автоматически.
Убедитесь, что все необходимые программы закрыты перед запуском.
"""

import time
import pyautogui
import subprocess
import sys

# Настройки безопасности pyautogui
pyautogui.FAILSAFE = True  # Переместите мышь в угол для остановки
pyautogui.PAUSE = 0.1  # Пауза между действиями

def main():
    """Главная функция"""
    print(f"Запуск: {name}")
    print(f"Описание: {description}")
    print("-" * 40)
    
    try:
{self._indent_code(validated_code, 8)}
        
        print("-" * 40)
        print("✅ Скрипт выполнен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    print("Нажмите Enter для запуска или Ctrl+C для отмены...")
    input()
    main()
'''
        return header
        
    def _validate_script_code(self, code: str) -> str:
        """Валидация и очистка кода скрипта"""
        if not code or not code.strip():
            return "# Код не сгенерирован\npass"
            
        # Убираем markdown блоки если есть
        if "```python" in code:
            start = code.find("```python") + 9
            end = code.find("```", start)
            if end > start:
                code = code[start:end].strip()
        elif "```" in code:
            start = code.find("```") + 3
            end = code.find("```", start)
            if end > start:
                code = code[start:end].strip()
                
        # Проверяем синтаксис
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            print(f"[GENERATOR] ⚠️ Ошибка синтаксиса в сгенерированном коде: {e}")
            # Возвращаем безопасный код
            return f"# Ошибка синтаксиса: {e}\nprint('Ошибка в сгенерированном коде')\n"
            
        return code
        
    def _indent_code(self, code: str, spaces: int) -> str:
        """Добавить отступы к коду"""
        lines = code.split('\n')
        indented = [' ' * spaces + line if line.strip() else line for line in lines]
        return '\n'.join(indented)
        
    def _create_master_script(self, session_dir: str, subtasks: List[Dict], goal: str) -> Optional[str]:
        """Создать мастер-скрипт для запуска всех подзадач"""
        master_path = os.path.join(session_dir, "run_all.py")
        
        imports = []
        calls = []
        
        for i, subtask in enumerate(subtasks, 1):
            name = subtask.get("name", f"subtask_{i}")
            safe_name = self._sanitize_filename(name)
            module_name = f"{i:02d}_{safe_name}"
            
            imports.append(f"import {module_name}")
            calls.append(f'    print(f"\\\\n{"="*40}")')
            calls.append(f'    print("▶ Запуск: {name}")')
            calls.append(f'    print(f"{"="*40}")')
            calls.append(f"    {module_name}.main()")
            calls.append(f"    time.sleep(1)")
            
        master_code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Мастер-скрипт
Цель: {goal}
Создано: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Запускает все подзадачи последовательно.
"""

import time
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

{chr(10).join(imports)}

def main():
    """Запуск всех подзадач"""
    print("🚀 Запуск автоматизации")
    print(f"Цель: {goal}")
    print(f"Подзадач: {len(subtasks)}")
    
    try:
{chr(10).join(calls)}
        
        print("\\n" + "="*40)
        print("✅ Все задачи выполнены!")
        print("="*40)
        
    except Exception as e:
        print(f"\\n❌ Ошибка: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    print("Нажмите Enter для запуска всех задач или Ctrl+C для отмены...")
    input()
    main()
'''
        
        try:
            with open(master_path, 'w', encoding='utf-8') as f:
                f.write(master_code)
            print(f"\n📋 Мастер-скрипт: {master_path}")
            return master_path
        except Exception as e:
            print(f"[GENERATOR] Ошибка создания мастер-скрипта: {e}")
            return None
            
    def _find_similar_scripts(self, goal: str, subtasks: List[Dict]) -> Optional[Dict]:
        """Найти похожие существующие скрипты"""
        if not os.path.exists(self.output_dir):
            return None
            
        # Создаём хэш цели для сравнения
        goal_hash = hashlib.md5(goal.lower().encode()).hexdigest()[:8]
        
        for session_name in os.listdir(self.output_dir):
            session_dir = os.path.join(self.output_dir, session_name)
            if not os.path.isdir(session_dir):
                continue
                
            metadata_path = os.path.join(session_dir, "metadata.json")
            if not os.path.exists(metadata_path):
                continue
                
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    
                # Сравниваем цели
                existing_goal = metadata.get("goal", "")
                existing_hash = hashlib.md5(existing_goal.lower().encode()).hexdigest()[:8]
                
                # Если хэши совпадают или цели очень похожи
                if goal_hash == existing_hash or self._goals_similar(goal, existing_goal):
                    return {
                        "session_dir": session_dir,
                        "goal": existing_goal,
                        "created_at": metadata.get("created_at", ""),
                        "files": metadata.get("files", []),
                        "subtasks_count": metadata.get("subtasks_count", 0)
                    }
            except:
                continue
                
        return None
        
    def _goals_similar(self, goal1: str, goal2: str) -> bool:
        """Проверить похожесть целей"""
        # Простая проверка по ключевым словам
        words1 = set(goal1.lower().split())
        words2 = set(goal2.lower().split())
        
        # Если больше 50% общих слов
        if len(words1) == 0 or len(words2) == 0:
            return False
            
        common = words1.intersection(words2)
        similarity = len(common) / max(len(words1), len(words2))
        
        return similarity > 0.5
        
    def get_script_variants(self, analysis_result: Dict) -> List[Dict]:
        """
        Получить 3 варианта скриптов для одной задачи
        
        Returns:
            Список из 3 вариантов с разными подходами
        """
        goal = analysis_result.get("goal", "")
        subtasks = analysis_result.get("subtasks", [])
        
        variants = []
        
        # Вариант 1: Оригинальный
        variants.append({
            "name": "Оригинальный",
            "description": "Стандартный подход",
            "analysis": analysis_result
        })
        
        # Вариант 2: Упрощённый (меньше шагов)
        simplified_subtasks = []
        for subtask in subtasks:
            simplified_subtasks.append({
                "name": f"Упрощённый: {subtask.get('name', '')}",
                "description": f"Быстрый вариант: {subtask.get('description', '')}",
                "script": subtask.get("script", "")
            })
            
        variants.append({
            "name": "Упрощённый",
            "description": "Меньше шагов, быстрее выполнение",
            "analysis": {
                "goal": f"{goal} (упрощённый)",
                "subtasks": simplified_subtasks[:len(subtasks)//2 + 1] if len(subtasks) > 1 else simplified_subtasks
            }
        })
        
        # Вариант 3: Расширенный (с проверками)
        extended_subtasks = []
        for subtask in subtasks:
            extended_script = subtask.get("script", "")
            # Добавляем проверки
            extended_script = f"""
# Проверка перед выполнением
print("Проверяю условия...")
time.sleep(0.5)

{extended_script}

# Проверка результата
print("Проверяю результат...")
time.sleep(0.5)
"""
            extended_subtasks.append({
                "name": f"С проверками: {subtask.get('name', '')}",
                "description": f"С проверками: {subtask.get('description', '')}",
                "script": extended_script
            })
            
        variants.append({
            "name": "С проверками",
            "description": "Добавлены проверки условий и результатов",
            "analysis": {
                "goal": f"{goal} (с проверками)",
                "subtasks": extended_subtasks
            }
        })
        
        return variants
        
    def _save_metadata(self, session_dir: str, goal: str, subtasks: List[Dict], files: List[str]):
        """Сохранить метаданные сессии"""
        metadata = {
            "created_at": datetime.now().isoformat(),
            "goal": goal,
            "subtasks_count": len(subtasks),
            "files": [os.path.basename(f) for f in files],
            "subtasks": [
                {
                    "name": s.get("name", ""),
                    "description": s.get("description", "")
                }
                for s in subtasks
            ]
        }
        
        metadata_path = os.path.join(session_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
