"""
Унифицированный модуль AI провайдеров для AsysWin
Поддерживает: Google Gemini, OpenAI, Groq, LM Studio
"""

import os
import json
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any

try:
    from google import genai
except ImportError:
    genai = None
    print("[LLM] Предупреждение: google-genai не установлен")


class AIProvider(ABC):
    """Базовый класс для AI провайдеров"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key

    @abstractmethod
    def is_ready(self) -> bool:
        """Проверить готовность провайдера"""
        pass

    @abstractmethod
    def analyze_actions(self, actions: List[Dict]) -> Optional[Dict]:
        """Анализировать действия пользователя"""
        pass

    @abstractmethod
    def fetch_available_models(self) -> List[Dict[str, Any]]:
        """Получить список доступных моделей от API"""
        pass

    def _parse_response(self, response: str) -> Optional[Dict]:
        """Универсальный парсер JSON из ответа LLM"""
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]

            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[LLM] Ошибка парсинга JSON: {e}")
            return None


class GeminiProvider(AIProvider):
    """Google Gemini провайдер (основной)"""

    def __init__(self, api_key: Optional[str] = None):
        raw_key = api_key or os.environ.get("GEMINI_API_KEY", "") or ""
        self.api_key = raw_key.strip().replace('"', "").replace("'", "") or None

        self.client: Any = None
        self.model_name = "gemini-2.0-flash"

        if self.api_key and genai:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[GEMINI] Init error: {e}")

    def is_ready(self) -> bool:
        return (
            genai is not None and self.client is not None and self.api_key is not None
        )

    def analyze_actions(self, actions: List[Dict]) -> Optional[Dict]:
        """Анализировать действия через Google Gemini"""
        if not actions:
            print("[GEMINI] No actions to analyze")
            return None

        if not self.is_ready():
            print("[GEMINI] API key not configured")
            return None

        prompt = self._create_prompt(actions)

        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )
            return self._parse_response(response.text)
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print("[GEMINI] Quota exceeded! Wait and retry.")
            elif "404" in error_msg:
                print(f"[GEMINI] Model not found: {self.model_name}")
            else:
                print(f"[GEMINI] Error: {e}")
            return None

    def _create_prompt(self, actions: List[Dict]) -> str:
        """Создать промпт с умной обработкой действий"""
        simplified = self._simplify_actions(actions)

        actions_text = "\n".join(
            [f"{i + 1}. {action}" for i, action in enumerate(simplified)]
        )

        max_chars = 15000
        if len(actions_text) > max_chars:
            actions_text = "...[actions truncated]...\n" + actions_text[-max_chars:]

        return f"""You are a workflow automation assistant. 
User performed the following actions:

{actions_text}

Analyze and do the following:

1. Determine the OVERALL GOAL of these actions
2. Break into LOGICAL SUBTASKS (3-7 subtasks)
3. For each subtask, write a Python script to automate it

Use these libraries:
- pyautogui for mouse/keyboard control
- subprocess for launching programs
- time for pauses

Return answer in JSON format:
{{
    "goal": "Goal description",
    "subtasks": [
        {{
            "name": "Subtask name",
            "description": "Description",
            "script": "Python code"
        }}
    ]
}}

Important:
- Scripts must be working and ready to run
- Add pauses between actions (time.sleep)
- Scripts must be self-contained"""

    def _simplify_actions(self, actions: List[Dict]) -> List[str]:
        """Упрощение и оптимизация действий"""
        meaningful = []

        for action in actions:
            action_type = action.get("type", "")

            if action_type == "mouse_move":
                continue

            if action_type in [
                "key_press",
                "key_release",
                "mouse_click",
                "mouse_scroll",
            ]:
                meaningful.append(action)

        return self._group_actions(meaningful)

    def _group_actions(self, actions: List[Dict]) -> List[str]:
        """Группировка последовательных одинаковых действий"""
        if not actions:
            return []

        result = []
        i = 0

        while i < len(actions):
            action = actions[i]
            action_type = action.get("type", "")

            if action_type == "key_press":
                key = action.get("key", "")
                count = 1
                while (
                    i + count < len(actions)
                    and actions[i + count].get("type") == "key_press"
                    and actions[i + count].get("key") == key
                ):
                    count += 1

                if count > 1:
                    result.append(f"Нажата клавиша '{key}' ({count} раз)")
                else:
                    if len(key) == 1:
                        result.append(f"Нажата клавиша: '{key}'")
                    else:
                        result.append(f"Нажата клавиша: {key}")
                i += count

            elif action_type == "mouse_click":
                x, y = action.get("x", 0), action.get("y", 0)
                button = action.get("button", "").replace("Button.", "")
                result.append(f"Клик {button} в ({x}, {y})")
                i += 1

            elif action_type == "mouse_scroll":
                dy = action.get("dy", 0)
                direction = "вниз" if dy < 0 else "вверх"
                count = 1
                while (
                    i + count < len(actions)
                    and actions[i + count].get("type") == "mouse_scroll"
                    and (actions[i + count].get("dy", 0) < 0) == (dy < 0)
                ):
                    count += 1
                result.append(f"Скролл {direction} ({count} раз)")
                i += count
            else:
                i += 1

        return result[-30:] if len(result) > 30 else result

    def fetch_available_models(self) -> List[Dict[str, Any]]:
        """Получить список доступных моделей Gemini"""
        if not self.is_ready():
            return []

        try:
            models = []
            for model in self.client.models.list():
                supported_actions = getattr(model, "supported_actions", []) or []
                if "generateContent" in supported_actions:
                    models.append(
                        {
                            "id": model.name.replace("models/", ""),
                            "name": getattr(model, "display_name", model.name)
                            or model.name,
                            "description": getattr(model, "description", "") or "",
                            "max_tokens": getattr(model, "output_token_limit", 8192)
                            or 8192,
                            "context_window": getattr(model, "input_token_limit", 32000)
                            or 32000,
                        }
                    )
            return models
        except Exception as e:
            print(f"[GEMINI] Ошибка получения моделей: {e}")
            return []

    def predict_next_actions(
        self, actions: List[Dict], patterns: List[Dict] = None
    ) -> Optional[Dict]:
        """Предсказать следующие вероятные действия"""
        if not self.is_ready():
            return None

        simplified = self._simplify_actions(actions)
        actions_text = "\n".join([f"- {a}" for a in simplified[-10:]])

        patterns_text = ""
        if patterns:
            patterns_text = "\n".join(
                [
                    f"- {p.get('name', 'Unknown')}: {p.get('description', '')}"
                    for p in patterns[:5]
                ]
            )

        prompt = f"""Пользователь выполнил следующие действия:

{actions_text}

Исторические паттерны пользователя:
{patterns_text if patterns_text else "Нет исторических паттернов"}

Предскажи 3 наиболее вероятных следующих сценария действий пользователя.
Для каждого сценария предоставь готовый Python скрипт.

Верни ответ в формате JSON:
{{
    "predictions": [
        {{
            "name": "Название сценария",
            "description": "Описание",
            "probability": "Высокая/Средняя/Низкая",
            "script": "Python код"
        }}
    ]
}}"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )
            return self._parse_response(response.text)
        except Exception as e:
            print(f"[GEMINI] Ошибка предсказания: {e}")
            return None


class OpenAIProvider(AIProvider):
    """OpenAI провайдер (GPT-4o)"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key or os.environ.get("OPENAI_API_KEY", ""))
        self.base_url = "https://api.openai.com/v1"

    def is_ready(self) -> bool:
        return bool(self.api_key)

    def analyze_actions(self, actions: List[Dict]) -> Optional[Dict]:
        """Анализировать действия через OpenAI"""
        if not actions:
            return None

        if not self.is_ready():
            print("[OPENAI] API ключ не настроен")
            return None

        prompt = self._create_prompt(actions)

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
                timeout=120,
            )

            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return self._parse_response(content)
            else:
                print(f"[OPENAI] Ошибка API: {response.status_code}")

        except Exception as e:
            print(f"[OPENAI] Ошибка: {e}")

        return None

    def _create_prompt(self, actions: List[Dict]) -> str:
        """Создать промпт с умной обработкой действий"""
        simplified = self._simplify_actions(actions)

        actions_text = "\n".join(
            [f"{i + 1}. {action}" for i, action in enumerate(simplified)]
        )

        return f"""Проанализируй действия пользователя и создай Python скрипты для автоматизации.

Действия:
{actions_text}

Верни JSON:
{{
    "goal": "Цель",
    "subtasks": [
        {{"name": "Название", "description": "Описание", "script": "Python код"}}
    ]
}}"""

    def fetch_available_models(self) -> List[Dict[str, Any]]:
        """Получить список доступных моделей OpenAI"""
        if not self.is_ready():
            return []

        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("data", []):
                    model_id = model.get("id", "")
                    # Фильтруем только GPT модели
                    if "gpt" in model_id.lower():
                        models.append(
                            {
                                "id": model_id,
                                "name": model_id.replace("-", " ").title(),
                                "description": f"OpenAI {model_id}",
                                "max_tokens": 16384,
                                "context_window": 128000,
                            }
                        )
                return models
            else:
                print(f"[OPENAI] Ошибка получения моделей: {response.status_code}")
                return []
        except Exception as e:
            print(f"[OPENAI] Ошибка получения моделей: {e}")
            return []

    def _simplify_actions(self, actions: List[Dict]) -> List[str]:
        """Упрощение действий"""
        simplified = []
        for action in actions[:50]:
            action_type = action.get("type", "")
            if action_type == "mouse_move":
                continue
            elif action_type == "key_press":
                key = action.get("key", "")
                simplified.append(f"Нажата клавиша: {key}")
            elif action_type == "mouse_click":
                x, y = action.get("x", 0), action.get("y", 0)
                button = action.get("button", "").replace("Button.", "")
                simplified.append(f"Клик {button} в ({x}, {y})")
            elif action_type == "mouse_scroll":
                dy = action.get("dy", 0)
                direction = "вниз" if dy < 0 else "вверх"
                simplified.append(f"Скролл {direction}")
        return simplified[-30:] if len(simplified) > 30 else simplified


class GroqProvider(AIProvider):
    """Groq провайдер (быстрый, бесплатный)"""

    def __init__(self, api_key: str = None):
        super().__init__(api_key or os.environ.get("GROQ_API_KEY", ""))
        self.base_url = "https://api.groq.com/openai/v1"

    def is_ready(self) -> bool:
        return bool(self.api_key)

    def analyze_actions(self, actions: List[Dict]) -> Optional[Dict]:
        """Анализировать действия через Groq"""
        if not actions:
            return None

        if not self.is_ready():
            print("[GROQ] API ключ не настроен")
            return None

        prompt = self._create_prompt(actions)

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama3-8b-8192",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
                timeout=60,
            )

            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return self._parse_response(content)
            else:
                print(f"[GROQ] Ошибка API: {response.status_code}")

        except Exception as e:
            print(f"[GROQ] Ошибка: {e}")

        return None

    def _create_prompt(self, actions: List[Dict]) -> str:
        """Создать промпт с умной обработкой действий"""
        simplified = self._simplify_actions(actions)

        actions_text = "\n".join(
            [f"{i + 1}. {action}" for i, action in enumerate(simplified)]
        )

        return f"""Проанализируй действия пользователя и создай Python скрипты для автоматизации.

Действия:
{actions_text}

Верни JSON:
{{
    "goal": "Цель",
    "subtasks": [
        {{"name": "Название", "description": "Описание", "script": "Python код"}}
    ]
}}"""

    def fetch_available_models(self) -> List[Dict[str, Any]]:
        """Получить список доступных моделей Groq"""
        if not self.is_ready():
            return []

        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("data", []):
                    model_id = model.get("id", "")
                    models.append(
                        {
                            "id": model_id,
                            "name": model_id.replace("-", " ").title(),
                            "description": f"Groq {model_id}",
                            "max_tokens": model.get("max_tokens", 8192),
                            "context_window": model.get("context_window", 8192),
                        }
                    )
                return models
            else:
                print(f"[GROQ] Ошибка получения моделей: {response.status_code}")
                return []
        except Exception as e:
            print(f"[GROQ] Ошибка получения моделей: {e}")
            return []

    def _simplify_actions(self, actions: List[Dict]) -> List[str]:
        """Упрощение действий"""
        simplified = []
        for action in actions[:50]:
            action_type = action.get("type", "")
            if action_type == "mouse_move":
                continue
            elif action_type == "key_press":
                key = action.get("key", "")
                simplified.append(f"Нажата клавиша: {key}")
            elif action_type == "mouse_click":
                x, y = action.get("x", 0), action.get("y", 0)
                button = action.get("button", "").replace("Button.", "")
                simplified.append(f"Клик {button} в ({x}, {y})")
            elif action_type == "mouse_scroll":
                dy = action.get("dy", 0)
                direction = "вниз" if dy < 0 else "вверх"
                simplified.append(f"Скролл {direction}")
        return simplified[-30:] if len(simplified) > 30 else simplified


class LMStudioProvider(AIProvider):
    """LM Studio провайдер (локальный)"""

    def __init__(self, api_url: str = "http://localhost:1234/v1"):
        super().__init__(api_key=None)
        self.api_url = api_url

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of LM Studio connection"""
        status = {
            "connected": False,
            "models": [],
            "loaded_model": None,
            "server_info": None,
        }
        base_url = self.api_url.rstrip("/").replace("/v1", "").replace("/v1beta", "")

        endpoints_to_try = [
            f"{base_url}/api/v0/models",
            f"{base_url}/v1/models",
            f"{self.api_url}/models",
        ]

        for endpoint in endpoints_to_try:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    status["connected"] = True
                    data = response.json()
                    status["models"] = [
                        {
                            "id": m.get("id"),
                            "loaded": m.get("loaded", False),
                        }
                        for m in data.get("data", [])
                    ]
                    for m in data.get("data", []):
                        if m.get("loaded", False):
                            status["loaded_model"] = m.get("id")
                            break
                    if not status["loaded_model"] and status["models"]:
                        status["loaded_model"] = status["models"][0].get("id")
                    break
            except Exception as e:
                status["error"] = str(e)

        try:
            health_resp = requests.get(f"{self.api_url.rstrip('/')}/health", timeout=2)
            if health_resp.status_code == 200:
                status["server_info"] = health_resp.json()
        except:
            pass

        return status

    def is_ready(self) -> bool:
        """Проверить доступность LM Studio"""
        base_url = self.api_url.rstrip("/").replace("/v1", "").replace("/v1beta", "")
        endpoints_to_try = [
            f"{base_url}/api/v0/models",
            f"{self.api_url}/models",
        ]
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(endpoint, timeout=2)
                if response.status_code == 200:
                    return True
            except:
                pass
        return False

    def _get_loaded_model(self) -> Optional[str]:
        """Get the currently loaded model from LM Studio"""
        base_url = self.api_url.rstrip("/").replace("/v1", "").replace("/v1beta", "")
        endpoints_to_try = [
            f"{base_url}/api/v0/models",
            f"{base_url}/v1/models",
            f"{self.api_url}/models",
        ]
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    models_data = data.get("data", [])
                    if models_data:
                        for model in models_data:
                            if model.get("loaded", False):
                                return model.get("id")
                        return models_data[0].get("id")
            except Exception as e:
                print(f"[LMSTUDIO] Model list error ({endpoint}): {e}")
        return None

    def analyze_actions(self, actions: List[Dict]) -> Optional[Dict]:
        """Анализировать действия через LM Studio"""
        if not actions:
            return None

        if not self.is_ready():
            print("[LMSTUDIO] LM Studio не запущен")
            return None

        prompt = self._create_prompt(actions)
        model_id = self._get_loaded_model()
        print(f"[LMSTUDIO] Using model: {model_id}")

        request_data = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
        if model_id:
            request_data["model"] = model_id

        base_url = self.api_url.rstrip("/")
        chat_endpoint = f"{base_url}/v1/chat/completions"

        try:
            response = requests.post(
                chat_endpoint,
                json=request_data,
                timeout=120,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return self._parse_response(content)
            else:
                print(
                    f"[LMSTUDIO] Error: {response.status_code} - {response.text[:300]}"
                )

        except Exception as e:
            print(f"[LMSTUDIO] Error: {e}")

        return None

    def _create_prompt(self, actions: List[Dict]) -> str:
        """Создать промпт с умной обработкой действий"""
        simplified = self._simplify_actions(actions)

        actions_text = "\n".join(
            [f"{i + 1}. {action}" for i, action in enumerate(simplified)]
        )

        return f"""Проанализируй действия пользователя и создай Python скрипты для автоматизации.

Действия:
{actions_text}

Верни JSON:
{{
    "goal": "Цель",
    "subtasks": [
        {{"name": "Название", "description": "Описание", "script": "Python код"}}
    ]
}}"""

    def fetch_available_models(self) -> List[Dict[str, Any]]:
        """Получить список доступных моделей LM Studio"""
        if not self.is_ready():
            return []

        base_url = self.api_url.rstrip("/").replace("/v1", "")

        endpoints_to_try = [
            f"{base_url}/api/v0/models",
            f"{self.api_url}/models",
        ]

        for endpoint in endpoints_to_try:
            try:
                response = requests.get(endpoint, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    models = []
                    for model in data.get("data", []):
                        model_id = model.get("id", "")
                        models.append(
                            {
                                "id": model_id,
                                "name": model_id,
                                "description": f"Local model: {model_id}",
                                "max_tokens": model.get("max_tokens", 4096),
                                "context_window": model.get("context_window", 32000),
                            }
                        )
                    if models:
                        return models
                elif response.status_code != 404:
                    print(
                        f"[LMSTUDIO] Endpoint {endpoint} returned {response.status_code}"
                    )
            except Exception as e:
                print(f"[LMSTUDIO] Error trying {endpoint}: {e}")

        return []

    def _simplify_actions(self, actions: List[Dict]) -> List[str]:
        """Упрощение действий"""
        simplified = []
        for action in actions[:50]:
            action_type = action.get("type", "")
            if action_type == "mouse_move":
                continue
            elif action_type == "key_press":
                key = action.get("key", "")
                simplified.append(f"Нажата клавиша: {key}")
            elif action_type == "mouse_click":
                x, y = action.get("x", 0), action.get("y", 0)
                button = action.get("button", "").replace("Button.", "")
                simplified.append(f"Клик {button} в ({x}, {y})")
            elif action_type == "mouse_scroll":
                dy = action.get("dy", 0)
                direction = "вниз" if dy < 0 else "вверх"
                simplified.append(f"Скролл {direction}")
        return simplified[-30:] if len(simplified) > 30 else simplified


# Фабрика провайдеров
def create_provider(
    provider_name: str, api_key: str = None, api_url: str = None
) -> AIProvider:
    """
    Создать AI провайдер по имени

    Args:
        provider_name: Название провайдера (gemini, openai, groq, lmstudio)
        api_key: API ключ (для cloud провайдеров)
        api_url: URL API (для lmstudio)

    Returns:
        Экземпляр AI провайдера

    Raises:
        ValueError: Если провайдер неизвестен
    """
    providers = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
        "groq": GroqProvider,
        "lmstudio": LMStudioProvider,
        "lm_studio": LMStudioProvider,
        "local": LMStudioProvider,
    }

    name_lower = provider_name.lower()

    if name_lower not in providers:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Неизвестный провайдер: {provider_name}. Доступны: {available}"
        )

    provider_class = providers[name_lower]

    if name_lower in ["lmstudio", "lm_studio", "local"]:
        return provider_class(api_url or "http://localhost:1234/v1")
    else:
        return provider_class(api_key)


def get_default_provider() -> AIProvider:
    """
    Получить провайдер по умолчанию (Gemini)
    """
    return GeminiProvider()


# Обратная совместимость
LLMAnalyzer = GeminiProvider
