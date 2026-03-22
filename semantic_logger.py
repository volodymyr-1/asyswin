"""
Модуль семантического логирования
Двухуровневая система: сырой лог + фильтрованный лог
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class Importance(Enum):
    """Уровни важности действий"""
    CRITICAL = "critical"   # Логин, сохранение, удаление
    NORMAL = "normal"       # Обычные действия
    DEBUG = "debug"         # Только для отладки


class SemanticLogger:
    def __init__(self, log_dir: str = "action_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Белый список действий
        self.whitelist = {
            "mouse_click",  # Клики мыши
            "key_press",    # Нажатия клавиш
            "key_release",  # Отпускание клавиш
            "click",        # Клики (альтернативное)
            "type",         # Ввод текста
            "hotkey",       # Горячие клавиши
            "navigate",     # Навигация
            "open",         # Открытие приложений
            "save",         # Сохранение
            "copy",         # Копирование
            "paste",        # Вставка
        }
        
        # Чёрный список (системные события)
        self.blacklist = {
            "mouse_move",
            "mouse_scroll",
            "key_release",
            "system_notification",
        }
        
        # Паттерны для маскирования
        self.sensitive_patterns = [
            "password", "passwd", "pwd",
            "token", "api_key", "secret",
            "credit_card", "card_number",
        ]
        
        # Буферы для логов
        self.raw_buffer = []
        self.filtered_buffer = []
        
    def log_action(self, action: Dict) -> bool:
        """
        Записать действие в оба лога
        
        Args:
            action: Словарь с информацией о действии
            
        Returns:
            True если действие прошло фильтр
        """
        # Всегда добавляем в сырой лог
        self.raw_buffer.append(action)
        
        # Фильтруем для второго лога
        if self._should_filter(action):
            return False
            
        # Создаём семантическую запись
        semantic_action = self._create_semantic_entry(action)
        
        # Маскируем чувствительные данные
        semantic_action = self._mask_sensitive_data(semantic_action)
        
        # Добавляем в фильтрованный лог
        self.filtered_buffer.append(semantic_action)
        
        return True
        
    def _should_filter(self, action: Dict) -> bool:
        """Определить нужно ли фильтровать действие"""
        action_type = action.get("type", "")
        
        # Чёрный список
        if action_type in self.blacklist:
            return True
            
        # Не в белом списке
        if action_type not in self.whitelist:
            return True
            
        return False
        
    def _create_semantic_entry(self, action: Dict) -> Dict:
        """Создать семантическую запись"""
        action_type = action.get("type", "")
        
        semantic = {
            "action": action_type,
            "target": self._extract_target(action),
            "value": self._extract_value(action),
            "context": self._extract_context(action),
            "importance": self._determine_importance(action),
            "timestamp": datetime.now().isoformat(),
            "raw_data": action  # Сохраняем сырые данные
        }
        
        return semantic
        
    def _extract_target(self, action: Dict) -> str:
        """Извлечь цель действия"""
        action_type = action.get("type", "")
        
        if action_type == "click":
            x, y = action.get("x", 0), action.get("y", 0)
            return f"position:({x},{y})"
        elif action_type == "type":
            return "text_input"
        elif action_type == "hotkey":
            return f"hotkey:{action.get('key', '')}"
        elif action_type == "open":
            return f"app:{action.get('app', '')}"
        else:
            return "unknown"
            
    def _extract_value(self, action: Dict) -> str:
        """Извлечь значение действия"""
        action_type = action.get("type", "")
        
        if action_type == "type":
            return action.get("text", "")
        elif action_type == "key_press":
            return action.get("key", "")
        elif action_type == "hotkey":
            return action.get("key", "")
        else:
            return ""
            
    def _extract_context(self, action: Dict) -> str:
        """Извлечь контекст (активное окно)"""
        # TODO: Интеграция с win32gui для получения активного окна
        return action.get("window", "unknown")
        
    def _determine_importance(self, action: Dict) -> str:
        """Определить важность действия"""
        action_type = action.get("type", "")
        
        # Критические действия
        critical_keywords = ["login", "save", "delete", "submit", "confirm"]
        if any(kw in str(action).lower() for kw in critical_keywords):
            return Importance.CRITICAL.value
            
        # Отладочные действия
        if action_type in ["mouse_move", "key_release"]:
            return Importance.DEBUG.value
            
        return Importance.NORMAL.value
        
    def _mask_sensitive_data(self, action: Dict) -> Dict:
        """Маскировать чувствительные данные"""
        masked = action.copy()
        
        # Проверяем значение
        value = str(masked.get("value", "")).lower()
        target = str(masked.get("target", "")).lower()
        
        for pattern in self.sensitive_patterns:
            if pattern in value or pattern in target:
                masked["value"] = "***"
                masked["masked"] = True
                break
                
        return masked
        
    def save_logs(self):
        """Сохранить логи в файлы"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Сохраняем сырой лог
        raw_path = os.path.join(self.log_dir, f"raw_{timestamp}.json")
        with open(raw_path, 'w', encoding='utf-8') as f:
            json.dump({
                "type": "raw",
                "recorded_at": datetime.now().isoformat(),
                "total_actions": len(self.raw_buffer),
                "actions": self.raw_buffer
            }, f, ensure_ascii=False, indent=2)
            
        # Сохраняем фильтрованный лог
        filtered_path = os.path.join(self.log_dir, f"filtered_{timestamp}.json")
        with open(filtered_path, 'w', encoding='utf-8') as f:
            json.dump({
                "type": "filtered",
                "recorded_at": datetime.now().isoformat(),
                "total_actions": len(self.filtered_buffer),
                "actions": self.filtered_buffer
            }, f, ensure_ascii=False, indent=2)
            
        print(f"[LOGGER] 💾 Сырой лог: {raw_path} ({len(self.raw_buffer)} действий)")
        print(f"[LOGGER] 💾 Фильтрованный лог: {filtered_path} ({len(self.filtered_buffer)} действий)")
        
        return raw_path, filtered_path
        
    def get_summary(self) -> Dict:
        """Получить сводку по логам"""
        return {
            "raw_count": len(self.raw_buffer),
            "filtered_count": len(self.filtered_buffer),
            "filtered_ratio": len(self.filtered_buffer) / max(len(self.raw_buffer), 1) * 100
        }