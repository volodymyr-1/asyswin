"""
Config Manager - AsysWin settings management
Saves settings to JSON file
"""

import json
import os
from typing import Dict, Any


class ConfigManager:
    def __init__(self, config_file: str = "asyswin_config.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "ai_provider": "gemini",
            "lmstudio_url": "http://localhost:1234/v1",
            "gemini_api_key": "",
            "openai_api_key": "",
            "groq_api_key": "",
            "mouse_threshold": 50,
            "key_debounce": 50,
            "auto_record": True,
            "cpu_limit": 50,
            "idle_threshold": 30,
            "theme": "system",
            "show_notifications": True,
        }

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                default = self._get_default_config()
                default.update(loaded)
                return default
            except Exception as e:
                print(f"[CONFIG] Load error: {e}")
                return self._get_default_config()
        else:
            return self._get_default_config()

    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            print(f"[CONFIG] Settings saved")
        except Exception as e:
            print(f"[CONFIG] Save error: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        self.config[key] = value

    def get_all(self) -> Dict[str, Any]:
        return self.config.copy()

    def update(self, updates: Dict[str, Any]):
        self.config.update(updates)

    def get_active_provider(self) -> str:
        return self.config.get("ai_provider", "gemini")

    def set_active_provider(self, provider: str):
        self.config["ai_provider"] = provider
        self.save_config()

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        if provider == "lmstudio":
            return {
                "api_url": self.config.get("lmstudio_url", "http://localhost:1234/v1")
            }
        elif provider == "gemini":
            return {"api_key": self.config.get("gemini_api_key", "")}
        elif provider == "openai":
            return {"api_key": self.config.get("openai_api_key", "")}
        elif provider == "groq":
            return {"api_key": self.config.get("groq_api_key", "")}
        else:
            return {}


_config_instance = None


def get_config() -> ConfigManager:
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
