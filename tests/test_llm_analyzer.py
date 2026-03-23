#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты для llm_analyzer
TDD: Тесты написаны до реализации (для нового функционала)
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_analyzer import (
    AIProvider,
    GeminiProvider,
    OpenAIProvider,
    GroqProvider,
    LMStudioProvider,
    create_provider,
    get_default_provider,
    LLMAnalyzer,
)


class TestAIProvider(unittest.TestCase):
    """Тесты базового класса AIProvider"""

    def test_provider_is_abstract(self):
        """Провайдер нельзя создать напрямую"""
        with self.assertRaises(TypeError):
            AIProvider()

    def test_provider_with_api_key(self):
        """Провайдер принимает api_key"""

        class TestProvider(AIProvider):
            def is_ready(self):
                return False

            def analyze_actions(self, actions):
                return None

            def fetch_available_models(self):
                return []

        provider = TestProvider(api_key="test_key")
        self.assertEqual(provider.api_key, "test_key")


class TestGeminiProvider(unittest.TestCase):
    """Тесты для GeminiProvider"""

    def test_create_gemini_provider(self):
        """Создание провайдера без API ключа"""
        provider = GeminiProvider()
        self.assertFalse(provider.is_ready())

    def test_gemini_provider_has_simplify_actions(self):
        """Провайдер имеет метод _simplify_actions"""
        provider = GeminiProvider()
        self.assertTrue(hasattr(provider, "_simplify_actions"))

    def test_gemini_provider_has_group_actions(self):
        """Провайдер имеет метод _group_actions"""
        provider = GeminiProvider()
        self.assertTrue(hasattr(provider, "_group_actions"))

    def test_simplify_actions_removes_mouse_move(self):
        """_simplify_actions убирает движения мыши"""
        provider = GeminiProvider()
        actions = [
            {"type": "mouse_move", "x": 100, "y": 200},
            {"type": "key_press", "key": "a"},
        ]
        result = provider._simplify_actions(actions)
        self.assertEqual(len(result), 1)
        self.assertIn("клавиша", result[0].lower())

    def test_simplify_actions_groups_repeated_keys(self):
        """_simplify_actions группирует повторяющиеся клавиши"""
        provider = GeminiProvider()
        actions = [
            {"type": "key_press", "key": "a"},
            {"type": "key_press", "key": "a"},
            {"type": "key_press", "key": "a"},
        ]
        result = provider._simplify_actions(actions)
        self.assertEqual(len(result), 1)
        self.assertIn("3 раз", result[0])

    def test_simplify_actions_limits_to_30(self):
        """_simplify_actions ограничивает результат 30 элементами"""
        provider = GeminiProvider()
        actions = [{"type": "key_press", "key": f"key_{i}"} for i in range(50)]
        result = provider._simplify_actions(actions)
        self.assertLessEqual(len(result), 30)

    def test_parse_response_extracts_json(self):
        """_parse_response извлекает JSON из ответа"""
        provider = GeminiProvider()
        response = '{"goal": "Test", "subtasks": []}'
        result = provider._parse_response(response)
        self.assertEqual(result["goal"], "Test")

    def test_parse_response_handles_markdown_json(self):
        """_parse_response обрабатывает JSON в markdown блоке"""
        provider = GeminiProvider()
        response = '```json\n{"goal": "Test", "subtasks": []}\n```'
        result = provider._parse_response(response)
        self.assertEqual(result["goal"], "Test")


class TestOpenAIProvider(unittest.TestCase):
    """Тесты для OpenAIProvider"""

    def test_create_openai_provider(self):
        """Создание провайдера OpenAI"""
        provider = OpenAIProvider(api_key="test_key")
        self.assertEqual(provider.api_key, "test_key")
        self.assertTrue(provider.is_ready())

    def test_openai_provider_without_key(self):
        """Провайдер без ключа не готов"""
        provider = OpenAIProvider()
        self.assertFalse(provider.is_ready())

    def test_openai_has_simplify_actions(self):
        """OpenAI провайдер имеет _simplify_actions"""
        provider = OpenAIProvider()
        self.assertTrue(hasattr(provider, "_simplify_actions"))


class TestGroqProvider(unittest.TestCase):
    """Тесты для GroqProvider"""

    def test_create_groq_provider(self):
        """Создание провайдера Groq"""
        provider = GroqProvider(api_key="test_key")
        self.assertEqual(provider.api_key, "test_key")
        self.assertTrue(provider.is_ready())

    def test_groq_provider_without_key(self):
        """Провайдер без ключа не готов"""
        provider = GroqProvider()
        self.assertFalse(provider.is_ready())


class TestLMStudioProvider(unittest.TestCase):
    """Тесты для LMStudioProvider"""

    @patch("llm_analyzer.requests.get")
    def test_create_lmstudio_provider(self, mock_get):
        """Создание провайдера LM Studio"""
        mock_get.return_value.status_code = 404
        provider = LMStudioProvider()
        self.assertFalse(provider.is_ready())

    def test_create_lmstudio_with_custom_url(self):
        """LM Studio с кастомным URL"""
        provider = LMStudioProvider(api_url="http://localhost:8080/v1")
        self.assertEqual(provider.api_url, "http://localhost:8080/v1")


class TestFactory(unittest.TestCase):
    """Тесты фабрики провайдеров"""

    def test_create_gemini_provider(self):
        """Фабрика создаёт Gemini провайдер"""
        provider = create_provider("gemini")
        self.assertIsInstance(provider, GeminiProvider)

    def test_create_openai_provider(self):
        """Фабрика создаёт OpenAI провайдер"""
        provider = create_provider("openai")
        self.assertIsInstance(provider, OpenAIProvider)

    def test_create_groq_provider(self):
        """Фабрика создаёт Groq провайдер"""
        provider = create_provider("groq")
        self.assertIsInstance(provider, GroqProvider)

    def test_create_lmstudio_provider(self):
        """Фабрика создаёт LM Studio провайдер"""
        provider = create_provider("lmstudio")
        self.assertIsInstance(provider, LMStudioProvider)

    def test_create_lmstudio_alias(self):
        """Фабрика понимает lm_studio как алиас"""
        provider = create_provider("lm_studio")
        self.assertIsInstance(provider, LMStudioProvider)

    def test_create_local_alias(self):
        """Фабрика понимает local как алиас LM Studio"""
        provider = create_provider("local")
        self.assertIsInstance(provider, LMStudioProvider)

    def test_create_unknown_provider_raises(self):
        """Неизвестный провайдер вызывает ошибку"""
        with self.assertRaises(ValueError):
            create_provider("unknown_provider")

    def test_get_default_provider(self):
        """get_default_provider возвращает Gemini"""
        provider = get_default_provider()
        self.assertIsInstance(provider, GeminiProvider)


class TestBackwardCompatibility(unittest.TestCase):
    """Тесты обратной совместимости"""

    def test_llm_analyzer_is_gemini_provider(self):
        """LLMAnalyzer это алиас для GeminiProvider"""
        self.assertIs(LLMAnalyzer, GeminiProvider)

    def test_can_import_llm_analyzer(self):
        """LLMAnalyzer можно импортировать"""
        from llm_analyzer import LLMAnalyzer

        self.assertIs(LLMAnalyzer, GeminiProvider)


class TestFetchAvailableModels(unittest.TestCase):
    """Тесты для метода fetch_available_models()"""

    @patch("llm_analyzer.genai.Client")
    def test_gemini_fetch_available_models(self, mock_client):
        """Тест получения моделей Gemini"""
        mock_model1 = Mock()
        mock_model1.name = "models/gemini-2.0-flash"
        mock_model1.display_name = "Gemini 2.0 Flash"
        mock_model1.description = "Fast model"
        mock_model1.output_token_limit = 8192
        mock_model1.input_token_limit = 32768
        mock_model1.supported_actions = ["generateContent"]

        mock_model2 = Mock()
        mock_model2.name = "models/gemini-pro"
        mock_model2.display_name = "Gemini Pro"
        mock_model2.description = "Pro model"
        mock_model2.output_token_limit = 8192
        mock_model2.input_token_limit = 32768
        mock_model2.supported_actions = ["generateContent"]

        mock_client.return_value.models.list.return_value = [mock_model1, mock_model2]

        provider = GeminiProvider(api_key="test_key")
        provider.client = mock_client.return_value

        models = provider.fetch_available_models()

        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]["id"], "gemini-2.0-flash")
        self.assertEqual(models[0]["name"], "Gemini 2.0 Flash")
        self.assertEqual(models[1]["id"], "gemini-pro")

    @patch("llm_analyzer.requests.get")
    def test_openai_fetch_available_models(self, mock_get):
        """Тест получения моделей OpenAI"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-4", "name": "GPT-4"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
            ]
        }
        mock_get.return_value = mock_response

        provider = OpenAIProvider(api_key="test_key")
        models = provider.fetch_available_models()

        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]["id"], "gpt-4")
        self.assertEqual(models[1]["id"], "gpt-3.5-turbo")

    @patch("llm_analyzer.requests.get")
    def test_groq_fetch_available_models(self, mock_get):
        """Тест получения моделей Groq"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "llama2-70b-4096", "name": "Llama 2 70B"},
                {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B"},
            ]
        }
        mock_get.return_value = mock_response

        provider = GroqProvider(api_key="test_key")
        models = provider.fetch_available_models()

        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]["id"], "llama2-70b-4096")

    @patch("llm_analyzer.requests.get")
    def test_lmstudio_fetch_available_models(self, mock_get):
        """Тест получения моделей LM Studio"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "llama-2-7b-chat", "name": "Llama 2 7B Chat"},
            ]
        }
        mock_get.return_value = mock_response

        provider = LMStudioProvider(api_url="http://localhost:1234/v1")
        models = provider.fetch_available_models()

        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["id"], "llama-2-7b-chat")

    def test_gemini_fetch_models_not_ready(self):
        """Тест получения моделей когда провайдер не готов"""
        provider = GeminiProvider()
        models = provider.fetch_available_models()
        self.assertEqual(models, [])

    def test_openai_fetch_models_not_ready(self):
        """Тест получения моделей OpenAI без ключа"""
        provider = OpenAIProvider()
        models = provider.fetch_available_models()
        self.assertEqual(models, [])

    @patch("llm_analyzer.requests.get")
    def test_fetch_models_api_error(self, mock_get):
        """Тест обработки ошибки API"""
        mock_get.side_effect = Exception("Network error")

        provider = OpenAIProvider(api_key="test_key")
        models = provider.fetch_available_models()

        self.assertEqual(models, [])

    @patch("llm_analyzer.requests.get")
    def test_fetch_models_http_error(self, mock_get):
        """Тест обработки HTTP ошибки"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        provider = OpenAIProvider(api_key="invalid_key")
        models = provider.fetch_available_models()

        self.assertEqual(models, [])


class TestIntegration(unittest.TestCase):
    """Интеграционные тесты"""

    @patch("llm_analyzer.genai.Client")
    def test_gemini_analyze_actions_mock(self, mock_client):
        """Тест анализа с моком API"""
        mock_client.return_value.models.generate_content.return_value.text = '{"goal": "Test Goal", "subtasks": [{"name": "Step 1", "description": "Desc", "script": "print(1)"}]}'

        provider = GeminiProvider(api_key="test_key")
        provider.client = mock_client.return_value

        actions = [{"type": "key_press", "key": "a"}]
        result = provider.analyze_actions(actions)

        self.assertIsNotNone(result)
        self.assertEqual(result["goal"], "Test Goal")
        self.assertEqual(len(result["subtasks"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
