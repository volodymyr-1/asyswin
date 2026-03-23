#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенный анализатор с мониторингом провайдеров и fallback-механизмом
"""

import threading
import time
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from provider_manager import ProviderManager, ProviderStatus
from llm_analyzer import AIProvider
from config_manager import get_config


class AnalysisStatus(Enum):
    """Статус анализа"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    FALLBACK = "fallback"


@dataclass
class AnalysisResult:
    """Результат анализа"""
    status: AnalysisStatus
    result: Optional[Dict] = None
    error: Optional[str] = None
    provider_used: Optional[str] = None
    response_time: float = 0.0
    fallback_used: bool = False


class EnhancedAnalyzer:
    """Улучшенный анализатор с мониторингом и fallback"""

    def __init__(self):
        self.config = get_config()
        self.provider_manager = ProviderManager()
        
        # Коллбэки
        self.on_status_change: Optional[Callable] = None
        self.on_provider_switch: Optional[Callable] = None
        self.on_analysis_complete: Optional[Callable] = None
        
        # Настройки
        self.max_retries = self.config.get("max_retries", 3)
        self.connection_timeout = self.config.get("connection_timeout", 30)
        self.fallback_enabled = self.config.get("fallback_enabled", True)
        
        # Мониторинг
        self.provider_manager.on_status_change = self._on_provider_status_change
        self.provider_manager.on_fallback = self._on_fallback
        
        # Запускаем мониторинг
        if self.config.get("provider_monitoring", True):
            self.provider_manager.start_monitoring()

    def analyze_actions(self, actions: List[Dict]) -> AnalysisResult:
        """Анализировать действия с fallback-механизмом"""
        if not actions:
            return AnalysisResult(
                status=AnalysisStatus.FAILED,
                error="No actions to analyze"
            )

        self._notify_status_change("running", "Starting analysis...")

        start_time = time.time()
        
        try:
            # Используем улучшенный анализатор с fallback
            result = self.provider_manager.analyze_with_fallback(actions)
            
            response_time = time.time() - start_time
            
            if result:
                self._notify_status_change("completed", "Analysis completed successfully")
                return AnalysisResult(
                    status=AnalysisStatus.COMPLETED,
                    result=result,
                    response_time=response_time,
                    provider_used=self.provider_manager.active_provider
                )
            else:
                self._notify_status_change("failed", "Analysis failed")
                return AnalysisResult(
                    status=AnalysisStatus.FAILED,
                    error="No provider could complete the analysis",
                    response_time=response_time
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            self._notify_status_change("failed", f"Analysis error: {str(e)[:50]}")
            return AnalysisResult(
                status=AnalysisStatus.FAILED,
                error=str(e),
                response_time=response_time
            )

    def analyze_actions_async(self, actions: List[Dict], callback: Callable[[AnalysisResult], None]):
        """Асинхронный анализ с callback"""
        def analysis_task():
            result = self.analyze_actions(actions)
            if self.on_analysis_complete:
                self.on_analysis_complete(result)
            if callback:
                callback(result)
        
        thread = threading.Thread(target=analysis_task, daemon=True)
        thread.start()

    def get_provider_status(self) -> Dict[str, Any]:
        """Получить статус всех провайдеров"""
        status = {}
        for provider_name in ["gemini", "openai", "groq", "lmstudio"]:
            health = self.provider_manager.get_health_status(provider_name)
            if health:
                status[provider_name] = {
                    "status": health.status.value,
                    "response_time": health.response_time,
                    "error_message": health.error_message,
                    "last_check": health.last_check,
                    "is_active": provider_name == self.provider_manager.active_provider
                }
            else:
                status[provider_name] = {
                    "status": "unknown",
                    "response_time": 0,
                    "error_message": "",
                    "last_check": 0,
                    "is_active": False
                }
        return status

    def switch_provider(self, provider_name: str, model_id: str = None):
        """Переключиться на провайдер с моделью"""
        try:
            self.provider_manager.set_active_provider(provider_name, model_id)
            
            if self.on_provider_switch:
                self.on_provider_switch(provider_name, model_id)
                
            self._notify_status_change("provider_switched", f"Switched to {provider_name}")
            
        except Exception as e:
            self._notify_status_change("switch_failed", f"Failed to switch: {str(e)[:50]}")

    def test_provider(self, provider_name: str, model_id: str = None) -> Dict[str, Any]:
        """Тест подключения к провайдеру"""
        return self.provider_manager.test_connection(provider_name, model_id)

    def get_best_provider(self) -> str:
        """Получить лучший доступный провайдер"""
        return self.provider_manager.get_best_provider()

    def _on_provider_status_change(self, provider_name: str, status: ProviderStatus, 
                                  response_time: float, error_message: str):
        """Обработчик изменения статуса провайдера"""
        if self.on_status_change:
            self.on_status_change(provider_name, status, response_time, error_message)

    def _on_fallback(self, failed_provider: str, error: str):
        """Обработчик fallback"""
        if self.on_provider_switch:
            self.on_provider_switch("fallback", f"Failed: {failed_provider}")

    def _notify_status_change(self, status: str, message: str):
        """Уведомить об изменении статуса"""
        if self.on_status_change:
            self.on_status_change(status, message)

    def stop_monitoring(self):
        """Остановить мониторинг"""
        self.provider_manager.stop_monitoring()

    def clear_cache(self):
        """Очистить кэш подключений"""
        self.provider_manager.clear_cache()

    def get_analysis_stats(self) -> Dict[str, Any]:
        """Получить статистику анализа"""
        health_status = self.provider_manager.get_all_health_status()
        
        stats = {
            "active_provider": self.provider_manager.active_provider,
            "total_providers": len(health_status),
            "connected_providers": 0,
            "failed_providers": 0,
            "best_provider": self.get_best_provider(),
            "monitoring_active": self.provider_manager.monitoring_active,
            "fallback_enabled": self.fallback_enabled
        }
        
        for provider_name, health in health_status.items():
            if health.status == ProviderStatus.CONNECTED:
                stats["connected_providers"] += 1
            elif health.status in [ProviderStatus.ERROR, ProviderStatus.DISCONNECTED]:
                stats["failed_providers"] += 1
        
        return stats

    def optimize_provider_settings(self) -> Dict[str, Any]:
        """Оптимизировать настройки провайдеров"""
        stats = self.get_analysis_stats()
        recommendations = []
        
        # Рекомендации по провайдеру
        if stats["connected_providers"] == 0:
            recommendations.append("No providers are connected. Check API keys and network.")
        elif stats["active_provider"] not in ["gemini", "openai"]:
            recommendations.append("Consider switching to Gemini or OpenAI for better reliability.")
        
        # Рекомендации по модели
        if self.provider_manager.active_provider == "gemini":
            recommendations.append("Use gemini-2.0-flash for faster responses.")
        elif self.provider_manager.active_provider == "openai":
            recommendations.append("Use gpt-4o-mini for cost-effective analysis.")
        elif self.provider_manager.active_provider == "groq":
            recommendations.append("Use llama3-8b-8192 for faster responses.")
        
        # Рекомендации по настройкам
        if self.config.get("cpu_limit", 50) < 30:
            recommendations.append("Increase CPU limit for better performance.")
        
        if self.config.get("connection_timeout", 30) < 20:
            recommendations.append("Increase connection timeout for unstable networks.")
        
        return {
            "current_settings": stats,
            "recommendations": recommendations,
            "optimized": len(recommendations) == 0
        }