#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Менеджер AI провайдеров с динамической загрузкой моделей
"""

import os
import time
import requests
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

from llm_analyzer import (
    AIProvider,
    create_provider,
    GeminiProvider,
    OpenAIProvider,
    GroqProvider,
    LMStudioProvider,
)
from config_manager import get_config


class ProviderStatus(Enum):
    """Статус провайдера"""

    UNKNOWN = "unknown"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    QUOTA_EXCEEDED = "quota_exceeded"
    RATE_LIMITED = "rate_limited"


@dataclass
class ModelInfo:
    """Информация о модели"""

    id: str
    name: str
    description: str
    max_tokens: int
    context_window: int
    price_per_token: float = 0.0  # USD per 1000 tokens
    capabilities: List[str] = field(default_factory=list)
    is_default: bool = False


@dataclass
class ModelsCache:
    """Кэш моделей провайдера"""

    models: List[ModelInfo]
    timestamp: float
    ttl: float = 3600.0  # 1 час по умолчанию

    def is_valid(self) -> bool:
        """Проверить валидность кэша"""
        return time.time() - self.timestamp < self.ttl


@dataclass
class ProviderHealth:
    """Информация о здоровье провайдера"""

    status: ProviderStatus
    last_check: float
    response_time: float
    error_message: str = ""
    quota_used: int = 0
    quota_limit: int = 0
    rate_limit_reset: float = 0


class ProviderManager:
    """Менеджер AI провайдеров с улучшенным подключением"""

    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self.health_status: Dict[str, ProviderHealth] = {}
        self.models: Dict[str, List[ModelInfo]] = {}
        self.models_cache: Dict[str, ModelsCache] = {}
        self.active_provider: str = "gemini"
        self.fallback_providers: List[str] = ["gemini", "openai", "groq", "lmstudio"]

        # Кэширование подключений
        self.connection_cache: Dict[str, AIProvider] = {}
        self.connection_lock = threading.Lock()

        # Мониторинг
        self.monitoring_thread = None
        self.monitoring_active = False

        # Коллбэки
        self.on_status_change: Optional[Callable] = None
        self.on_fallback: Optional[Callable] = None

        self._initialize_providers()

    def _initialize_providers(self):
        """Инициализировать всех провайдеров с ключами из конфига"""
        config = get_config()

        gemini_key = config.get("gemini_api_key", "")
        openai_key = config.get("openai_api_key", "")
        groq_key = config.get("groq_api_key", "")
        lmstudio_url = config.get("lmstudio_url", "http://localhost:1234/v1")

        self.providers["gemini"] = (
            create_provider("gemini", api_key=gemini_key)
            if gemini_key
            else GeminiProvider()
        )
        self.health_status["gemini"] = ProviderHealth(
            status=ProviderStatus.UNKNOWN, last_check=0, response_time=0
        )

        self.providers["openai"] = (
            create_provider("openai", api_key=openai_key)
            if openai_key
            else OpenAIProvider()
        )
        self.health_status["openai"] = ProviderHealth(
            status=ProviderStatus.UNKNOWN, last_check=0, response_time=0
        )

        self.providers["groq"] = (
            create_provider("groq", api_key=groq_key) if groq_key else GroqProvider()
        )
        self.health_status["groq"] = ProviderHealth(
            status=ProviderStatus.UNKNOWN, last_check=0, response_time=0
        )

        self.providers["lmstudio"] = create_provider("lmstudio", api_url=lmstudio_url)
        self.health_status["lmstudio"] = ProviderHealth(
            status=ProviderStatus.UNKNOWN, last_check=0, response_time=0
        )

        # Загрузка моделей
        self._load_models()

    def reload_providers(self):
        """Перезагрузить провайдеров из конфига"""
        self._initialize_providers()

    def _load_models(self):
        """Загрузить информацию о моделях из кэша или API"""
        for provider_name in self.providers.keys():
            self._load_provider_models(provider_name)

    def _load_provider_models(
        self, provider_name: str, force_refresh: bool = False
    ) -> List[ModelInfo]:
        """Загрузить модели для конкретного провайдера"""
        # Проверяем кэш
        if not force_refresh and provider_name in self.models_cache:
            cache = self.models_cache[provider_name]
            if cache.is_valid():
                self.models[provider_name] = cache.models
                return cache.models

        # Загружаем из API
        provider = self.providers.get(provider_name)
        if not provider or not provider.is_ready():
            # Fallback на минимальный список моделей
            fallback_models = self._get_fallback_models(provider_name)
            self.models[provider_name] = fallback_models
            return fallback_models

        try:
            raw_models = provider.fetch_available_models()
            models = []

            for i, model_data in enumerate(raw_models):
                model = ModelInfo(
                    id=model_data.get("id", ""),
                    name=model_data.get("name", model_data.get("id", "")),
                    description=model_data.get("description", ""),
                    max_tokens=model_data.get("max_tokens", 4096),
                    context_window=model_data.get("context_window", 32000),
                    price_per_token=model_data.get("price_per_token", 0.0),
                    capabilities=model_data.get("capabilities", ["text", "code"]),
                    is_default=(i == 0),  # Первая модель по умолчанию
                )
                models.append(model)

            # Сохраняем в кэш
            self.models_cache[provider_name] = ModelsCache(
                models=models, timestamp=time.time()
            )
            self.models[provider_name] = models

            print(f"[PROVIDER] Loaded {len(models)} models for {provider_name}")
            return models

        except Exception as e:
            print(f"[PROVIDER] Error loading models for {provider_name}: {e}")
            # Fallback на минимальный список моделей
            fallback_models = self._get_fallback_models(provider_name)
            self.models[provider_name] = fallback_models
            return fallback_models

    def _get_fallback_models(self, provider_name: str) -> List[ModelInfo]:
        """Получить fallback модели при ошибке API"""
        fallback_data = {
            "gemini": [
                {
                    "id": "gemini-2.0-flash",
                    "name": "Gemini Flash 2.0",
                    "description": "Fast model",
                    "max_tokens": 8192,
                    "context_window": 1000000,
                }
            ],
            "openai": [
                {
                    "id": "gpt-4o-mini",
                    "name": "GPT-4o Mini",
                    "description": "Economical model",
                    "max_tokens": 16384,
                    "context_window": 128000,
                }
            ],
            "groq": [
                {
                    "id": "llama3-8b-8192",
                    "name": "Llama 3 8B",
                    "description": "Fast model",
                    "max_tokens": 8192,
                    "context_window": 8192,
                }
            ],
            "lmstudio": [
                {
                    "id": "auto",
                    "name": "Auto-detect",
                    "description": "Local model",
                    "max_tokens": 4096,
                    "context_window": 32000,
                }
            ],
        }

        models_data = fallback_data.get(provider_name, [])
        return [
            ModelInfo(
                id=m["id"],
                name=m["name"],
                description=m["description"],
                max_tokens=m["max_tokens"],
                context_window=m["context_window"],
                is_default=(i == 0),
            )
            for i, m in enumerate(models_data)
        ]

    def refresh_models(self, provider_name: str = None) -> Dict[str, List[ModelInfo]]:
        """Обновить модели (принудительно загрузить из API)"""
        if provider_name:
            self._load_provider_models(provider_name, force_refresh=True)
        else:
            for name in self.providers.keys():
                self._load_provider_models(name, force_refresh=True)
        return self.models

    def get_available_models(self, provider_name: str) -> List[ModelInfo]:
        """Получить доступные модели для провайдера"""
        if provider_name not in self.models:
            self._load_provider_models(provider_name)
        return self.models.get(provider_name, [])

    def get_default_model(self, provider_name: str) -> Optional[ModelInfo]:
        """Получить модель по умолчанию для провайдера"""
        models = self.get_available_models(provider_name)
        for model in models:
            if model.is_default:
                return model
        return models[0] if models else None

    def set_active_provider(self, provider_name: str, model_id: str = None):
        """Установить активный провайдер и модель"""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")

        self.active_provider = provider_name

        # Если указана модель, устанавливаем её
        if model_id:
            provider = self._get_provider_with_model(provider_name, model_id)
        else:
            provider = self._get_provider(provider_name)

        # Проверяем подключение
        self._check_provider_health(provider_name)

    def _get_provider_with_model(self, provider_name: str, model_id: str) -> AIProvider:
        """Получить провайдера с указанной моделью"""
        cache_key = f"{provider_name}:{model_id}"

        with self.connection_lock:
            if cache_key in self.connection_cache:
                return self.connection_cache[cache_key]

            # Создаем провайдера с указанной моделью
            if provider_name == "gemini":
                provider = GeminiProvider()
                provider.model_name = model_id
            elif provider_name == "openai":
                provider = OpenAIProvider()
                # Для OpenAI модель указывается в запросе
            elif provider_name == "groq":
                provider = GroqProvider()
                provider.model_name = model_id
            elif provider_name == "lmstudio":
                provider = LMStudioProvider()
                # Для LM Studio модель указывается в запросе
            else:
                provider = self.providers[provider_name]

            self.connection_cache[cache_key] = provider
            return provider

    def _get_provider(self, provider_name: str) -> AIProvider:
        """Получить провайдера (с кэшированием)"""
        with self.connection_lock:
            if provider_name in self.connection_cache:
                return self.connection_cache[provider_name]

            provider = self.providers[provider_name]
            self.connection_cache[provider_name] = provider
            return provider

    def analyze_with_fallback(self, actions: list) -> Optional[dict]:
        """Анализировать действия с fallback-механизмом"""
        providers_to_try = self._get_providers_by_priority()

        for provider_name in providers_to_try:
            try:
                provider = self._get_provider(provider_name)

                # Проверяем статус провайдера
                health = self.health_status.get(provider_name)
                if health and health.status in [
                    ProviderStatus.DISCONNECTED,
                    ProviderStatus.ERROR,
                ]:
                    continue

                # Проверяем квоту (только если quota_limit > 0)
                if (
                    health
                    and health.quota_limit > 0
                    and health.quota_used >= health.quota_limit
                ):
                    self._update_health_status(
                        provider_name, ProviderStatus.QUOTA_EXCEEDED
                    )
                    continue

                # Проверяем rate limit
                if health and time.time() < health.rate_limit_reset:
                    self._update_health_status(
                        provider_name, ProviderStatus.RATE_LIMITED
                    )
                    continue

                # Пробуем анализ
                result = provider.analyze_actions(actions)

                if result:
                    self._update_health_status(provider_name, ProviderStatus.CONNECTED)
                    return result
                else:
                    self._update_health_status(
                        provider_name, ProviderStatus.ERROR, "No result"
                    )

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    self._update_health_status(
                        provider_name, ProviderStatus.RATE_LIMITED, error_msg
                    )
                elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                    self._update_health_status(
                        provider_name, ProviderStatus.QUOTA_EXCEEDED, error_msg
                    )
                else:
                    self._update_health_status(
                        provider_name, ProviderStatus.ERROR, error_msg
                    )

                # Вызываем callback о fallback
                if self.on_fallback:
                    self.on_fallback(provider_name, str(e))

        return None

    def _get_providers_by_priority(self) -> List[str]:
        """Получить провайдеров по приоритету"""
        # Сначала активный провайдер
        priority = [self.active_provider]

        # Затем остальные в порядке fallback
        for provider in self.fallback_providers:
            if provider != self.active_provider and provider not in priority:
                priority.append(provider)

        return priority

    def _check_provider_health(self, provider_name: str):
        """Проверить здоровье провайдера"""
        provider = self._get_provider(provider_name)

        start_time = time.time()

        try:
            # Простой тестовый запрос
            test_result = provider.analyze_actions(
                [{"type": "test", "action": "health_check"}]
            )

            response_time = time.time() - start_time

            if test_result:
                self._update_health_status(
                    provider_name, ProviderStatus.CONNECTED, response_time
                )
            else:
                self._update_health_status(
                    provider_name, ProviderStatus.ERROR, "No response"
                )

        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)

            if "429" in error_msg:
                self._update_health_status(
                    provider_name, ProviderStatus.RATE_LIMITED, error_msg
                )
            elif "quota" in error_msg.lower():
                self._update_health_status(
                    provider_name, ProviderStatus.QUOTA_EXCEEDED, error_msg
                )
            else:
                self._update_health_status(
                    provider_name, ProviderStatus.ERROR, error_msg
                )

            # Обновляем информацию о квоте если доступна
            self._update_quota_info(provider_name, e)

    def _update_health_status(
        self,
        provider_name: str,
        status: ProviderStatus,
        response_time: float = 0,
        error_message: str = "",
    ):
        """Обновить статус здоровья провайдера"""
        health = self.health_status.get(provider_name)
        if not health:
            health = ProviderHealth(
                status=status,
                last_check=time.time(),
                response_time=response_time,
                error_message=error_message,
            )
            self.health_status[provider_name] = health
        else:
            health.status = status
            health.last_check = time.time()
            health.response_time = response_time
            health.error_message = error_message

        # Вызываем callback
        if self.on_status_change:
            self.on_status_change(provider_name, status, response_time, error_message)

    def _update_quota_info(self, provider_name: str, error: Exception):
        """Обновить информацию о квоте"""
        # Пока заглушка - в реальной системе нужно парсить ответы API
        pass

    def start_monitoring(self):
        """Запустить мониторинг провайдеров"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Остановить мониторинг"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

    def _monitoring_loop(self):
        """Цикл мониторинга провайдеров"""
        while self.monitoring_active:
            for provider_name in self.providers.keys():
                try:
                    self._check_provider_health(provider_name)
                except Exception:
                    pass

            time.sleep(30)  # Проверяем каждые 30 секунд

    def get_health_status(self, provider_name: str) -> Optional[ProviderHealth]:
        """Получить статус здоровья провайдера"""
        return self.health_status.get(provider_name)

    def get_all_health_status(self) -> Dict[str, ProviderHealth]:
        """Получить статусы всех провайдеров"""
        return self.health_status.copy()

    def clear_cache(self):
        """Очистить кэш подключений"""
        with self.connection_lock:
            self.connection_cache.clear()

    def get_best_provider(self) -> str:
        """Получить лучший доступный провайдер"""
        best_provider = self.active_provider

        # Проверяем активный провайдер
        health = self.health_status.get(self.active_provider)
        if health and health.status == ProviderStatus.CONNECTED:
            return self.active_provider

        # Ищем лучший альтернативный провайдер
        for provider_name in self.fallback_providers:
            if provider_name == self.active_provider:
                continue

            health = self.health_status.get(provider_name)
            if health and health.status == ProviderStatus.CONNECTED:
                return provider_name

        return self.active_provider

    def test_connection(
        self, provider_name: str, model_id: str = None
    ) -> Dict[str, Any]:
        """Тест подключения к провайдеру"""
        try:
            if model_id:
                provider = self._get_provider_with_model(provider_name, model_id)
            else:
                provider = self._get_provider(provider_name)

            start_time = time.time()
            test_result = provider.analyze_actions(
                [{"type": "test", "action": "connection_test"}]
            )
            response_time = time.time() - start_time

            if test_result:
                return {
                    "success": True,
                    "response_time": response_time,
                    "message": "Connection successful",
                }
            else:
                return {
                    "success": False,
                    "response_time": response_time,
                    "message": "No response from provider",
                }

        except Exception as e:
            return {"success": False, "response_time": 0, "message": str(e)}

    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Получить информацию о провайдере"""
        health = self.health_status.get(provider_name)

        return {
            "name": provider_name,
            "status": health.status.value if health else "unknown",
            "response_time": health.response_time if health else 0,
            "error_message": health.error_message if health else "",
            "last_check": health.last_check if health else 0,
            "models": [
                asdict(model) for model in self.get_available_models(provider_name)
            ],
            "is_active": provider_name == self.active_provider,
        }
