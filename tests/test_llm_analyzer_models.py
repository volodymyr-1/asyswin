#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit тесты для LLM Analyzer - fetch_available_models()
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_analyzer import (
    AIProvider,
    GeminiProvider,
    OpenAIProvider,
    GroqProvider,
    LMStudioProvider,
    create_provider,
)
from provider_manager import reset_provider_manager


@pytest.fixture(autouse=True)
def reset_singleton():
    """Сбросить синглтон перед каждым тестом"""
    reset_provider_manager()
    yield
    reset_provider_manager()


class TestAIProviderAbstract:
    """Тесты для абстрактного класса AIProvider"""

    def test_abstract_methods(self):
        """Тест что абстрактные методы определены"""
        # Проверяем что методы являются абстрактными
        assert hasattr(AIProvider, "is_ready")
        assert hasattr(AIProvider, "analyze_actions")
        assert hasattr(AIProvider, "fetch_available_models")


class TestGeminiProvider:
    """Тесты для GeminiProvider"""

    @patch("llm_analyzer.genai")
    def test_fetch_available_models_success(self, mock_genai):
        """Тест успешной загрузки моделей Gemini"""
        mock_client = Mock()
        mock_model1 = Mock()
        mock_model1.name = "models/gemini-2.0-flash"
        mock_model1.display_name = "Gemini Flash 2.0"
        mock_model1.description = "Fast model"
        mock_model1.output_token_limit = 8192
        mock_model1.input_token_limit = 1000000
        mock_model1.supported_actions = ["generateContent"]

        mock_model2 = Mock()
        mock_model2.name = "models/gemini-2.0-pro"
        mock_model2.display_name = "Gemini Pro 2.0"
        mock_model2.description = "Pro model"
        mock_model2.output_token_limit = 8192
        mock_model2.input_token_limit = 1000000
        mock_model2.supported_actions = ["generateContent"]

        mock_client.models.list.return_value = [mock_model1, mock_model2]
        mock_genai.Client.return_value = mock_client

        provider = GeminiProvider(api_key="test-key")
        models = provider.fetch_available_models()

        assert len(models) == 2
        assert models[0]["id"] == "gemini-2.0-flash"
        assert models[1]["id"] == "gemini-2.0-pro"

    @patch("llm_analyzer.genai")
    def test_fetch_available_models_not_ready(self, mock_genai):
        """Тест загрузки моделей когда провайдер не готов"""
        provider = GeminiProvider(api_key=None)
        models = provider.fetch_available_models()

        assert models == []

    @patch("llm_analyzer.genai")
    def test_fetch_available_models_error(self, mock_genai):
        """Тест обработки ошибки при загрузке моделей"""
        mock_client = Mock()
        mock_client.models.list.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client

        provider = GeminiProvider(api_key="test-key")
        models = provider.fetch_available_models()

        assert models == []

    @patch("llm_analyzer.genai")
    def test_fetch_available_models_filters_non_content(self, mock_genai):
        """Тест фильтрации моделей без generateContent"""
        mock_client = Mock()
        mock_model1 = Mock()
        mock_model1.name = "models/gemini-2.0-flash"
        mock_model1.display_name = "Gemini Flash 2.0"
        mock_model1.description = "Fast model"
        mock_model1.output_token_limit = 8192
        mock_model1.input_token_limit = 1000000
        mock_model1.supported_actions = ["generateContent"]

        mock_model2 = Mock()
        mock_model2.name = "models/other-model"
        mock_model2.display_name = "Other Model"
        mock_model2.description = "Other model"
        mock_model2.output_token_limit = 4096
        mock_model2.input_token_limit = 8192
        mock_model2.supported_actions = ["embedContent"]  # Не generateContent

        mock_client.models.list.return_value = [mock_model1, mock_model2]
        mock_genai.Client.return_value = mock_client

        provider = GeminiProvider(api_key="test-key")
        models = provider.fetch_available_models()

        assert len(models) == 1
        assert models[0]["id"] == "gemini-2.0-flash"


class TestOpenAIProvider:
    """Тесты для OpenAIProvider"""

    @patch("llm_analyzer.requests")
    def test_fetch_available_models_success(self, mock_requests):
        """Тест успешной загрузки моделей OpenAI"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-4o-mini"},
                {"id": "gpt-4o"},
                {"id": "gpt-4-turbo"},
                {"id": "dall-e-3"},  # Не GPT модель
            ]
        }
        mock_requests.get.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        models = provider.fetch_available_models()

        assert len(models) == 3  # Только GPT модели
        assert models[0]["id"] == "gpt-4o-mini"
        assert models[1]["id"] == "gpt-4o"
        assert models[2]["id"] == "gpt-4-turbo"

    @patch("llm_analyzer.requests")
    def test_fetch_available_models_not_ready(self, mock_requests):
        """Тест загрузки моделей когда провайдер не готов"""
        provider = OpenAIProvider(api_key=None)
        models = provider.fetch_available_models()

        assert models == []

    @patch("llm_analyzer.requests")
    def test_fetch_available_models_api_error(self, mock_requests):
        """Тест обработки ошибки API"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_requests.get.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        models = provider.fetch_available_models()

        assert models == []

    @patch("llm_analyzer.requests")
    def test_fetch_available_models_network_error(self, mock_requests):
        """Тест обработки сетевой ошибки"""
        mock_requests.get.side_effect = Exception("Network Error")

        provider = OpenAIProvider(api_key="test-key")
        models = provider.fetch_available_models()

        assert models == []


class TestGroqProvider:
    """Тесты для GroqProvider"""

    @patch("llm_analyzer.requests")
    def test_fetch_available_models_success(self, mock_requests):
        """Тест успешной загрузки моделей Groq"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "llama3-8b-8192", "max_tokens": 8192, "context_window": 8192},
                {"id": "llama3-70b-8192", "max_tokens": 8192, "context_window": 8192},
                {
                    "id": "mixtral-8x7b-32768",
                    "max_tokens": 32768,
                    "context_window": 32768,
                },
            ]
        }
        mock_requests.get.return_value = mock_response

        provider = GroqProvider(api_key="test-key")
        models = provider.fetch_available_models()

        assert len(models) == 3
        assert models[0]["id"] == "llama3-8b-8192"
        assert models[1]["id"] == "llama3-70b-8192"
        assert models[2]["id"] == "mixtral-8x7b-32768"

    @patch("llm_analyzer.requests")
    def test_fetch_available_models_not_ready(self, mock_requests):
        """Тест загрузки моделей когда провайдер не готов"""
        provider = GroqProvider(api_key=None)
        models = provider.fetch_available_models()

        assert models == []

    @patch("llm_analyzer.requests")
    def test_fetch_available_models_api_error(self, mock_requests):
        """Тест обработки ошибки API"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_requests.get.return_value = mock_response

        provider = GroqProvider(api_key="test-key")
        models = provider.fetch_available_models()

        assert models == []


class TestLMStudioProvider:
    """Тесты для LMStudioProvider"""

    @patch("llm_analyzer.requests")
    def test_fetch_available_models_success(self, mock_requests):
        """Тест успешной загрузки моделей LM Studio"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "llama-3.2-3b", "max_tokens": 4096, "context_window": 128000},
                {"id": "phi-4", "max_tokens": 4096, "context_window": 128000},
            ]
        }
        mock_requests.get.return_value = mock_response

        provider = LMStudioProvider(api_url="http://localhost:1234/v1")
        models = provider.fetch_available_models()

        assert len(models) == 2
        assert models[0]["id"] == "llama-3.2-3b"
        assert models[1]["id"] == "phi-4"

    @patch("llm_analyzer.requests")
    def test_fetch_available_models_not_ready(self, mock_requests):
        """Тест загрузки моделей когда провайдер не готов"""
        mock_requests.get.side_effect = Exception("Connection refused")

        provider = LMStudioProvider(api_url="http://localhost:1234/v1")
        models = provider.fetch_available_models()

        assert models == []

    @patch("llm_analyzer.requests")
    def test_fetch_available_models_api_error(self, mock_requests):
        """Тест обработки ошибки API"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.get.return_value = mock_response

        provider = LMStudioProvider(api_url="http://localhost:1234/v1")
        models = provider.fetch_available_models()

        assert models == []


class TestCreateProvider:
    """Тесты для фабрики провайдеров"""

    def test_create_gemini_provider(self):
        """Тест создания Gemini провайдера"""
        provider = create_provider("gemini", api_key="test-key")

        assert isinstance(provider, GeminiProvider)

    def test_create_openai_provider(self):
        """Тест создания OpenAI провайдера"""
        provider = create_provider("openai", api_key="test-key")

        assert isinstance(provider, OpenAIProvider)

    def test_create_groq_provider(self):
        """Тест создания Groq провайдера"""
        provider = create_provider("groq", api_key="test-key")

        assert isinstance(provider, GroqProvider)

    def test_create_lmstudio_provider(self):
        """Тест создания LM Studio провайдера"""
        provider = create_provider("lmstudio", api_url="http://localhost:1234/v1")

        assert isinstance(provider, LMStudioProvider)

    def test_create_unknown_provider(self):
        """Тест создания неизвестного провайдера"""
        with pytest.raises(ValueError):
            create_provider("unknown", api_key="test-key")


class TestProviderIntegration:
    """Интеграционные тесты провайдеров"""

    @patch("llm_analyzer.genai")
    @patch("llm_analyzer.requests")
    def test_all_providers_fetch_models(self, mock_requests, mock_genai):
        """Тест загрузки моделей всеми провайдерами"""
        # Настройка Gemini
        mock_client = Mock()
        mock_model = Mock()
        mock_model.name = "models/gemini-2.0-flash"
        mock_model.display_name = "Gemini Flash 2.0"
        mock_model.description = "Fast model"
        mock_model.output_token_limit = 8192
        mock_model.input_token_limit = 1000000
        mock_model.supported_actions = ["generateContent"]
        mock_client.models.list.return_value = [mock_model]
        mock_genai.Client.return_value = mock_client

        # Настройка OpenAI
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "gpt-4o-mini"}]}
        mock_requests.get.return_value = mock_response

        # Тестируем все провайдеры
        gemini = create_provider("gemini", api_key="test")
        openai = create_provider("openai", api_key="test")
        groq = create_provider("groq", api_key="test")
        lmstudio = create_provider("lmstudio", api_url="http://localhost:1234/v1")

        gemini_models = gemini.fetch_available_models()
        openai_models = openai.fetch_available_models()
        groq_models = groq.fetch_available_models()
        lmstudio_models = lmstudio.fetch_available_models()

        assert len(gemini_models) > 0
        assert len(openai_models) > 0
        assert len(groq_models) > 0
        assert len(lmstudio_models) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
