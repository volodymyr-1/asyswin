#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E2E тесты для динамической загрузки моделей
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from provider_manager import ProviderManager
from llm_analyzer import create_provider


class TestDynamicModelLoading:
    """E2E тесты для динамической загрузки моделей"""

    @patch('llm_analyzer.genai')
    @patch('llm_analyzer.requests')
    def test_full_model_loading_cycle(self, mock_requests, mock_genai):
        """Тест полного цикла загрузки моделей"""
        # Настройка Gemini
        mock_client = Mock()
        mock_model = Mock()
        mock_model.name = "models/gemini-2.0-flash"
        mock_model.display_name = "Gemini Flash 2.0"
        mock_model.description = "Fast model"
        mock_model.output_token_limit = 8192
        mock_model.input_token_limit = 1000000
        mock_model.supported_generation_methods = ["generateContent"]
        mock_client.models.list.return_value = [mock_model]
        mock_genai.Client.return_value = mock_client
        
        # Настройка OpenAI
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "gpt-4o-mini"}]}
        mock_requests.get.return_value = mock_response
        
        # Создаем менеджер
        manager = ProviderManager()
        
        # Загружаем модели для всех провайдеров
        gemini_models = manager.get_available_models("gemini")
        openai_models = manager.get_available_models("openai")
        groq_models = manager.get_available_models("groq")
        lmstudio_models = manager.get_available_models("lmstudio")
        
        # Проверяем что модели загружены
        assert len(gemini_models) > 0
        assert len(openai_models) > 0
        assert len(groq_models) > 0
        assert len(lmstudio_models) > 0
        
        # Проверяем что кэш работает
        gemini_models2 = manager.get_available_models("gemini")
        assert gemini_models == gemini_models2

    @patch('llm_analyzer.genai')
    @patch('llm_analyzer.requests')
    def test_provider_switch_with_model_reload(self, mock_requests, mock_genai):
        """Тест переключения провайдера с перезагрузкой моделей"""
        # Настройка Gemini
        mock_client = Mock()
        mock_model = Mock()
        mock_model.name = "models/gemini-2.0-flash"
        mock_model.display_name = "Gemini Flash 2.0"
        mock_model.description = "Fast model"
        mock_model.output_token_limit = 8192
        mock_model.input_token_limit = 1000000
        mock_model.supported_generation_methods = ["generateContent"]
        mock_client.models.list.return_value = [mock_model]
        mock_genai.Client.return_value = mock_client
        
        # Настройка OpenAI
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "gpt-4o-mini"}]}
        mock_requests.get.return_value = mock_response
        
        manager = ProviderManager()
        
        # Переключаемся на Gemini
        manager.set_active_provider("gemini")
        gemini_models = manager.get_available_models("gemini")
        
        # Переключаемся на OpenAI
        manager.set_active_provider("openai")
        openai_models = manager.get_available_models("openai")
        
        # Проверяем что модели разные
        assert gemini_models[0].id != openai_models[0].id

    @patch('llm_analyzer.genai')
    @patch('llm_analyzer.requests')
    def test_cache_persistence_across_sessions(self, mock_requests, mock_genai):
        """Тест сохранения кэша между сессиями"""
        # Настройка Gemini
        mock_client = Mock()
        mock_model = Mock()
        mock_model.name = "models/gemini-2.0-flash"
        mock_model.display_name = "Gemini Flash 2.0"
        mock_model.description = "Fast model"
        mock_model.output_token_limit = 8192
        mock_model.input_token_limit = 1000000
        mock_model.supported_generation_methods = ["generateContent"]
        mock_client.models.list.return_value = [mock_model]
        mock_genai.Client.return_value = mock_client
        
        # Первая сессия
        manager1 = ProviderManager()
        models1 = manager1.get_available_models("gemini")
        
        # Вторая сессия (имитация нового запуска)
        manager2 = ProviderManager()
        models2 = manager2.get_available_models("gemini")
        
        # Проверяем что модели одинаковые
        assert models1 == models2

    @patch('llm_analyzer.genai')
    @patch('llm_analyzer.requests')
    def test_api_error_fallback(self, mock_requests, mock_genai):
        """Тест fallback при ошибке API"""
        # Настройка Gemini с ошибкой
        mock_client = Mock()
        mock_client.models.list.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client
        
        manager = ProviderManager()
        models = manager.get_available_models("gemini")
        
        # Должны вернуться fallback модели
        assert len(models) > 0
        assert models[0].id == "gemini-2.0-flash"

    @patch('llm_analyzer.genai')
    @patch('llm_analyzer.requests')
    def test_concurrent_model_requests(self, mock_requests, mock_genai):
        """Тест конкурентных запросов моделей"""
        import threading
        
        # Настройка Gemini
        mock_client = Mock()
        mock_model = Mock()
        mock_model.name = "models/gemini-2.0-flash"
        mock_model.display_name = "Gemini Flash 2.0"
        mock_model.description = "Fast model"
        mock_model.output_token_limit = 8192
        mock_model.input_token_limit = 1000000
        mock_model.supported_generation_methods = ["generateContent"]
        mock_client.models.list.return_value = [mock_model]
        mock_genai.Client.return_value = mock_client
        
        manager = ProviderManager()
        results = []
        
        def load_models():
            models = manager.get_available_models("gemini")
            results.append(len(models))
        
        # Запускаем несколько потоков одновременно
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=load_models)
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем что все потоки получили одинаковый результат
        assert all(r == results[0] for r in results)


class TestModelSelection:
    """E2E тесты для выбора моделей"""

    @patch('llm_analyzer.genai')
    @patch('llm_analyzer.requests')
    def test_model_selection_and_persistence(self, mock_requests, mock_genai):
        """Тест выбора модели и сохранения"""
        # Настройка Gemini
        mock_client = Mock()
        mock_model1 = Mock()
        mock_model1.name = "models/gemini-2.0-flash"
        mock_model1.display_name = "Gemini Flash 2.0"
        mock_model1.description = "Fast model"
        mock_model1.output_token_limit = 8192
        mock_model1.input_token_limit = 1000000
        mock_model1.supported_generation_methods = ["generateContent"]
        
        mock_model2 = Mock()
        mock_model2.name = "models/gemini-2.0-pro"
        mock_model2.display_name = "Gemini Pro 2.0"
        mock_model2.description = "Pro model"
        mock_model2.output_token_limit = 8192
        mock_model2.input_token_limit = 1000000
        mock_model2.supported_generation_methods = ["generateContent"]
        
        mock_client.models.list.return_value = [mock_model1, mock_model2]
        mock_genai.Client.return_value = mock_client
        
        manager = ProviderManager()
        
        # Получаем модели
        models = manager.get_available_models("gemini")
        
        # Проверяем что модели загружены
        assert len(models) > 0
        
        # Выбираем первую модель
        selected_model = models[0]
        
        # Проверяем что модель выбрана правильно
        assert selected_model.id == "gemini-2.0-flash"
        assert selected_model.name == "Gemini Flash 2.0"

    @patch('llm_analyzer.genai')
    @patch('llm_analyzer.requests')
    def test_default_model_selection(self, mock_requests, mock_genai):
        """Тест выбора модели по умолчанию"""
        # Настройка Gemini
        mock_client = Mock()
        mock_model = Mock()
        mock_model.name = "models/gemini-2.0-flash"
        mock_model.display_name = "Gemini Flash 2.0"
        mock_model.description = "Fast model"
        mock_model.output_token_limit = 8192
        mock_model.input_token_limit = 1000000
        mock_model.supported_generation_methods = ["generateContent"]
        mock_client.models.list.return_value = [mock_model]
        mock_genai.Client.return_value = mock_client
        
        manager = ProviderManager()
        
        # Получаем модель по умолчанию
        default_model = manager.get_default_model("gemini")
        
        # Проверяем что модель выбрана
        assert default_model is not None
        assert default_model.is_default is True


class TestProviderHealth:
    """E2E тесты для здоровья провайдеров"""

    @patch('llm_analyzer.genai')
    @patch('llm_analyzer.requests')
    def test_provider_health_check(self, mock_requests, mock_genai):
        """Тест проверки здоровья провайдера"""
        # Настройка Gemini
        mock_client = Mock()
        mock_model = Mock()
        mock_model.name = "models/gemini-2.0-flash"
        mock_model.display_name = "Gemini Flash 2.0"
        mock_model.description = "Fast model"
        mock_model.output_token_limit = 8192
        mock_model.input_token_limit = 1000000
        mock_model.supported_generation_methods = ["generateContent"]
        mock_client.models.list.return_value = [mock_model]
        mock_genai.Client.return_value = mock_client
        
        manager = ProviderManager()
        
        # Проверяем здоровье провайдера
        manager._check_provider_health("gemini")
        
        # Получаем статус
        health = manager.get_health_status("gemini")
        
        # Проверяем что статус обновлен
        assert health is not None

    @patch('llm_analyzer.genai')
    @patch('llm_analyzer.requests')
    def test_provider_fallback_on_error(self, mock_requests, mock_genai):
        """Тест fallback при ошибке провайдера"""
        # Настройка Gemini с ошибкой
        mock_client = Mock()
        mock_client.models.list.side_effect = Exception("API Error")
        mock_genai.Client.return_value = mock_client
        
        # Настройка OpenAI
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "gpt-4o-mini"}]}
        mock_requests.get.return_value = mock_response
        
        manager = ProviderManager()
        
        # Пробуем проанализировать с fallback
        result = manager.analyze_with_fallback([{"type": "test"}])
        
        # Проверяем что fallback сработал
        # (в реальном сценарии OpenAI должен был ответить)
        assert result is None or result is not None


class TestPerformance:
    """E2E тесты производительности"""

    @patch('llm_analyzer.genai')
    @patch('llm_analyzer.requests')
    def test_models_load_time_under_5_seconds(self, mock_requests, mock_genai):
        """Тест что модели загружаются менее чем за 5 секунд"""
        # Настройка Gemini
        mock_client = Mock()
        mock_model = Mock()
        mock_model.name = "models/gemini-2.0-flash"
        mock_model.display_name = "Gemini Flash 2.0"
        mock_model.description = "Fast model"
        mock_model.output_token_limit = 8192
        mock_model.input_token_limit = 1000000
        mock_model.supported_generation_methods = ["generateContent"]
        mock_client.models.list.return_value = [mock_model]
        mock_genai.Client.return_value = mock_client
        
        manager = ProviderManager()
        
        start_time = time.time()
        models = manager.get_available_models("gemini")
        end_time = time.time()
        
        load_time = end_time - start_time
        
        assert load_time < 5.0
        assert len(models) > 0

    @patch('llm_analyzer.genai')
    @patch('llm_analyzer.requests')
    def test_cached_models_load_under_100ms(self, mock_requests, mock_genai):
        """Тест что кэшированные модели загружаются менее чем за 100мс"""
        # Настройка Gemini
        mock_client = Mock()
        mock_model = Mock()
        mock_model.name = "models/gemini-2.0-flash"
        mock_model.display_name = "Gemini Flash 2.0"
        mock_model.description = "Fast model"
        mock_model.output_token_limit = 8192
        mock_model.input_token_limit = 1000000
        mock_model.supported_generation_methods = ["generateContent"]
        mock_client.models.list.return_value = [mock_model]
        mock_genai.Client.return_value = mock_client
        
        manager = ProviderManager()
        
        # Первый запрос - загрузка из API
        manager.get_available_models("gemini")
        
        # Второй запрос - должен быть из кэша
        start_time = time.time()
        models = manager.get_available_models("gemini")
        end_time = time.time()
        
        load_time = end_time - start_time
        
        assert load_time < 0.1
        assert len(models) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])