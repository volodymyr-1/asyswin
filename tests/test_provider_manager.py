#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit тесты для ProviderManager
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from provider_manager import (
    ProviderManager,
    ProviderStatus,
    ModelInfo,
    ModelsCache,
    ProviderHealth,
)


class TestModelInfo:
    """Тесты для ModelInfo"""

    def test_model_info_creation(self):
        """Тест создания ModelInfo"""
        model = ModelInfo(
            id="test-model",
            name="Test Model",
            description="Test description",
            max_tokens=4096,
            context_window=8192,
        )

        assert model.id == "test-model"
        assert model.name == "Test Model"
        assert model.description == "Test description"
        assert model.max_tokens == 4096
        assert model.context_window == 8192
        assert model.price_per_token == 0.0
        assert model.capabilities == []
        assert model.is_default is False

    def test_model_info_with_capabilities(self):
        """Тест создания ModelInfo с capabilities"""
        model = ModelInfo(
            id="test-model",
            name="Test Model",
            description="Test description",
            max_tokens=4096,
            context_window=8192,
            capabilities=["text", "code"],
        )

        assert model.capabilities == ["text", "code"]


class TestModelsCache:
    """Тесты для ModelsCache"""

    def test_cache_valid(self):
        """Тест валидности кэша"""
        models = [
            ModelInfo(
                id="test",
                name="Test",
                description="",
                max_tokens=100,
                context_window=100,
            )
        ]
        cache = ModelsCache(models=models, timestamp=time.time())

        assert cache.is_valid() is True

    def test_cache_expired(self):
        """Тест истекшего кэша"""
        models = [
            ModelInfo(
                id="test",
                name="Test",
                description="",
                max_tokens=100,
                context_window=100,
            )
        ]
        cache = ModelsCache(models=models, timestamp=time.time() - 4000, ttl=3600)

        assert cache.is_valid() is False

    def test_cache_custom_ttl(self):
        """Тест кэша с пользовательским TTL"""
        models = [
            ModelInfo(
                id="test",
                name="Test",
                description="",
                max_tokens=100,
                context_window=100,
            )
        ]
        cache = ModelsCache(models=models, timestamp=time.time(), ttl=60)

        assert cache.is_valid() is True


class TestProviderHealth:
    """Тесты для ProviderHealth"""

    def test_provider_health_creation(self):
        """Тест создания ProviderHealth"""
        health = ProviderHealth(
            status=ProviderStatus.CONNECTED, last_check=time.time(), response_time=0.5
        )

        assert health.status == ProviderStatus.CONNECTED
        assert health.response_time == 0.5
        assert health.error_message == ""


class TestProviderManager:
    """Тесты для ProviderManager"""

    @patch("provider_manager.GeminiProvider")
    @patch("provider_manager.OpenAIProvider")
    @patch("provider_manager.GroqProvider")
    @patch("provider_manager.LMStudioProvider")
    def test_initialize_providers(
        self, mock_lmstudio, mock_groq, mock_openai, mock_gemini
    ):
        """Тест инициализации провайдеров"""
        manager = ProviderManager()

        assert "gemini" in manager.providers
        assert "openai" in manager.providers
        assert "groq" in manager.providers
        assert "lmstudio" in manager.providers

    @patch("provider_manager.GeminiProvider")
    def test_get_available_models_empty(self, mock_gemini):
        """Тест получения моделей когда кэш пуст"""
        mock_provider = Mock()
        mock_provider.is_ready.return_value = False
        mock_gemini.return_value = mock_provider

        manager = ProviderManager()
        models = manager.get_available_models("gemini")

        assert isinstance(models, list)

    @patch("provider_manager.GeminiProvider")
    def test_load_provider_models_from_api(self, mock_gemini):
        """Тест загрузки моделей из API"""
        mock_provider = Mock()
        mock_provider.is_ready.return_value = True
        mock_provider.fetch_available_models.return_value = [
            {
                "id": "model-1",
                "name": "Model 1",
                "description": "Test",
                "max_tokens": 4096,
                "context_window": 8192,
            }
        ]
        mock_gemini.return_value = mock_provider

        manager = ProviderManager()
        models = manager._load_provider_models("gemini")

        assert len(models) == 1
        assert models[0].id == "model-1"

    @patch("provider_manager.GeminiProvider")
    def test_load_provider_models_from_cache(self, mock_gemini):
        """Тест загрузки моделей из кэша"""
        mock_provider = Mock()
        mock_provider.is_ready.return_value = True
        mock_provider.fetch_available_models.return_value = [
            {
                "id": "model-1",
                "name": "Model 1",
                "description": "Test",
                "max_tokens": 4096,
                "context_window": 8192,
            }
        ]
        mock_gemini.return_value = mock_provider

        manager = ProviderManager()

        # Первый запрос - загрузка из API
        models1 = manager._load_provider_models("gemini")

        # Второй запрос - должен быть из кэша
        models2 = manager._load_provider_models("gemini")

        # Проверяем что API вызывался только один раз
        assert mock_provider.fetch_available_models.call_count == 1

    @patch("provider_manager.GeminiProvider")
    def test_load_provider_models_force_refresh(self, mock_gemini):
        """Тест принудительного обновления моделей"""
        mock_provider = Mock()
        mock_provider.is_ready.return_value = True
        mock_provider.fetch_available_models.return_value = [
            {
                "id": "model-1",
                "name": "Model 1",
                "description": "Test",
                "max_tokens": 4096,
                "context_window": 8192,
            }
        ]
        mock_gemini.return_value = mock_provider

        manager = ProviderManager()

        # Первый запрос
        models1 = manager._load_provider_models("gemini")

        # Принудительное обновление
        models2 = manager._load_provider_models("gemini", force_refresh=True)

        # Проверяем что API вызывался дважды
        assert mock_provider.fetch_available_models.call_count == 2

    @patch("provider_manager.GeminiProvider")
    def test_load_provider_models_api_error(self, mock_gemini):
        """Тест обработки ошибки API"""
        mock_provider = Mock()
        mock_provider.is_ready.return_value = True
        mock_provider.fetch_available_models.side_effect = Exception("API Error")
        mock_gemini.return_value = mock_provider

        manager = ProviderManager()
        models = manager._load_provider_models("gemini")

        # Должны вернуться fallback модели
        assert len(models) > 0
        assert models[0].id == "gemini-2.0-flash"

    @patch("provider_manager.GeminiProvider")
    def test_get_fallback_models(self, mock_gemini):
        """Тест получения fallback моделей"""
        manager = ProviderManager()

        gemini_models = manager._get_fallback_models("gemini")
        openai_models = manager._get_fallback_models("openai")
        groq_models = manager._get_fallback_models("groq")
        lmstudio_models = manager._get_fallback_models("lmstudio")

        assert len(gemini_models) > 0
        assert len(openai_models) > 0
        assert len(groq_models) > 0
        assert len(lmstudio_models) > 0

    @patch("provider_manager.GeminiProvider")
    def test_refresh_models(self, mock_gemini):
        """Тест обновления моделей"""
        mock_provider = Mock()
        mock_provider.is_ready.return_value = True
        mock_provider.fetch_available_models.return_value = [
            {
                "id": "model-1",
                "name": "Model 1",
                "description": "Test",
                "max_tokens": 4096,
                "context_window": 8192,
            }
        ]
        mock_gemini.return_value = mock_provider

        manager = ProviderManager()

        # Обновляем модели для конкретного провайдера
        models = manager.refresh_models("gemini")

        assert "gemini" in models
        assert len(models["gemini"]) > 0

    @patch("provider_manager.GeminiProvider")
    def test_get_default_model(self, mock_gemini):
        """Тест получения модели по умолчанию"""
        mock_provider = Mock()
        mock_provider.is_ready.return_value = True
        mock_provider.fetch_available_models.return_value = [
            {
                "id": "model-1",
                "name": "Model 1",
                "description": "Test",
                "max_tokens": 4096,
                "context_window": 8192,
            },
            {
                "id": "model-2",
                "name": "Model 2",
                "description": "Test",
                "max_tokens": 4096,
                "context_window": 8192,
            },
        ]
        mock_gemini.return_value = mock_provider

        manager = ProviderManager()
        default_model = manager.get_default_model("gemini")

        assert default_model is not None
        assert default_model.is_default is True

    @patch("provider_manager.GeminiProvider")
    def test_analyze_with_fallback(self, mock_gemini):
        """Тест анализа с fallback"""
        mock_provider = Mock()
        mock_provider.is_ready.return_value = True
        mock_provider.analyze_actions.return_value = {"goal": "test", "subtasks": []}
        mock_provider.fetch_available_models.return_value = [
            {
                "id": "model-1",
                "name": "Model 1",
                "description": "Test",
                "max_tokens": 4096,
                "context_window": 8192,
            }
        ]
        mock_gemini.return_value = mock_provider

        manager = ProviderManager()
        # Directly set the mock provider in the providers dict
        manager.providers["gemini"] = mock_provider
        # Clear the connection cache to ensure our provider is used
        manager.connection_cache.clear()
        # Устанавливаем статус провайдера как CONNECTED
        manager.health_status["gemini"] = ProviderHealth(
            status=ProviderStatus.CONNECTED, last_check=time.time(), response_time=0.5
        )
        result = manager.analyze_with_fallback([{"type": "test"}])

        # Проверяем что analyze_actions был вызван
        mock_provider.analyze_actions.assert_called_once()
        assert result is not None
        assert result["goal"] == "test"

    @patch("provider_manager.GeminiProvider")
    def test_analyze_with_fallback_error(self, mock_gemini):
        """Тест анализа с fallback при ошибке"""
        mock_provider = Mock()
        mock_provider.is_ready.return_value = True
        mock_provider.analyze_actions.side_effect = Exception("API Error")
        mock_gemini.return_value = mock_provider

        manager = ProviderManager()
        result = manager.analyze_with_fallback([{"type": "test"}])

        # Должен вернуться None при ошибке всех провайдеров
        assert result is None

    @patch("provider_manager.GeminiProvider")
    def test_get_best_provider(self, mock_gemini):
        """Тест получения лучшего провайдера"""
        mock_provider = Mock()
        mock_provider.is_ready.return_value = True
        mock_gemini.return_value = mock_provider

        manager = ProviderManager()
        best_provider = manager.get_best_provider()

        assert best_provider in ["gemini", "openai", "groq", "lmstudio"]

    @patch("provider_manager.GeminiProvider")
    def test_test_connection(self, mock_gemini):
        """Тест проверки подключения"""
        mock_provider = Mock()
        mock_provider.is_ready.return_value = True
        mock_provider.analyze_actions.return_value = {"result": "ok"}
        mock_provider.fetch_available_models.return_value = [
            {
                "id": "model-1",
                "name": "Model 1",
                "description": "Test",
                "max_tokens": 4096,
                "context_window": 8192,
            }
        ]
        mock_gemini.return_value = mock_provider

        manager = ProviderManager()
        # Directly set the mock provider in the providers dict
        manager.providers["gemini"] = mock_provider
        # Clear the connection cache
        manager.connection_cache.clear()
        result = manager.test_connection("gemini")

        # Проверяем что analyze_actions был вызван с правильными аргументами
        mock_provider.analyze_actions.assert_called_once_with(
            [{"type": "test", "action": "connection_test"}]
        )
        assert result["success"] is True
        # Response time will be a small positive number
        assert result["response_time"] >= 0

    @patch("provider_manager.GeminiProvider")
    def test_clear_cache(self, mock_gemini):
        """Тест очистки кэша"""
        manager = ProviderManager()
        manager.connection_cache["test"] = Mock()

        manager.clear_cache()

        assert len(manager.connection_cache) == 0

    @patch("provider_manager.get_config")
    @patch("provider_manager.create_provider")
    def test_reload_providers(self, mock_create_provider, mock_get_config):
        """Тест перезагрузки провайдеров из конфига"""
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default="": {
            "gemini_api_key": "test-gemini-key",
            "openai_api_key": "test-openai-key",
            "groq_api_key": "test-groq-key",
            "lmstudio_url": "http://localhost:1234/v1",
        }.get(key, default)
        mock_get_config.return_value = mock_config

        mock_provider = Mock()
        mock_provider.is_ready.return_value = False
        mock_create_provider.return_value = mock_provider

        manager = ProviderManager()
        original_providers = manager.providers.copy()

        manager.reload_providers()

        assert mock_create_provider.call_count >= 4
        assert "gemini" in manager.providers
        assert "openai" in manager.providers
        assert "groq" in manager.providers
        assert "lmstudio" in manager.providers


class TestProviderManagerIntegration:
    """Интеграционные тесты для ProviderManager"""

    @patch("provider_manager.GeminiProvider")
    @patch("provider_manager.OpenAIProvider")
    def test_multiple_providers(self, mock_openai, mock_gemini):
        """Тест работы с несколькими провайдерами"""
        mock_gemini_provider = Mock()
        mock_gemini_provider.is_ready.return_value = True
        mock_gemini_provider.fetch_available_models.return_value = [
            {
                "id": "gemini-model",
                "name": "Gemini",
                "description": "Test",
                "max_tokens": 4096,
                "context_window": 8192,
            }
        ]
        mock_gemini.return_value = mock_gemini_provider

        mock_openai_provider = Mock()
        mock_openai_provider.is_ready.return_value = True
        mock_openai_provider.fetch_available_models.return_value = [
            {
                "id": "openai-model",
                "name": "OpenAI",
                "description": "Test",
                "max_tokens": 4096,
                "context_window": 8192,
            }
        ]
        mock_openai.return_value = mock_openai_provider

        manager = ProviderManager()

        gemini_models = manager.get_available_models("gemini")
        openai_models = manager.get_available_models("openai")

        assert len(gemini_models) > 0
        assert len(openai_models) > 0
        assert gemini_models[0].id == "gemini-model"
        assert openai_models[0].id == "openai-model"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
