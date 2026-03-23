#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенный виджет с мониторингом провайдеров и статусом подключений
"""

import customtkinter as ctk
import threading
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from enhanced_assistant_widget import EnhancedAssistantWidget
from enhanced_analyzer import EnhancedAnalyzer


class EnhancedMonitoringWidget(EnhancedAssistantWidget):
    """Улучшенный виджет с мониторингом провайдеров"""

    def __init__(self):
        super().__init__()
        self.analyzer = EnhancedAnalyzer()
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Коллбэки
        self.analyzer.on_status_change = self._on_analyzer_status_change
        self.analyzer.on_provider_switch = self._on_provider_switch
        self.analyzer.on_analysis_complete = self._on_analysis_complete

    def _create_extra_ui(self, parent):
        """Создать дополнительный UI для мониторинга"""
        self._create_provider_monitoring(parent)
        self._create_status_monitoring(parent)
        self._create_optimization_panel(parent)

    def _create_provider_monitoring(self, parent):
        """Создать панель мониторинга провайдеров"""
        monitor_frame = ctk.CTkFrame(
            parent, corner_radius=10, fg_color=("gray92", "gray18"), height=180
        )
        monitor_frame.pack(fill="x", padx=10, pady=5)
        monitor_frame.pack_propagate(False)

        header_frame = ctk.CTkFrame(monitor_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="📡 Provider Monitoring",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        title_label.pack(side="left")

        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄",
            width=30,
            height=28,
            corner_radius=6,
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"),
            font=ctk.CTkFont(size=12),
            command=self._refresh_provider_status,
        )
        refresh_btn.pack(side="right")

        self.provider_container = ctk.CTkFrame(monitor_frame, fg_color="transparent")
        self.provider_container.pack(fill="both", expand=True, padx=5, pady=5)

        self._create_provider_cards()

    def _create_provider_cards(self):
        """Создать карточки провайдеров"""
        providers = ["gemini", "openai", "groq", "lmstudio"]
        
        for i, provider in enumerate(providers):
            self._create_provider_card(provider, i)

    def _create_provider_card(self, provider_name: str, row: int):
        """Создать карточку провайдера"""
        card_frame = ctk.CTkFrame(
            self.provider_container, corner_radius=8, fg_color=("gray88", "gray22")
        )
        card_frame.grid(row=row // 2, column=row % 2, padx=5, pady=5, sticky="ew")
        card_frame.grid_columnconfigure(1, weight=1)

        # Иконка и название
        icon_label = ctk.CTkLabel(
            card_frame, text=self._get_provider_icon(provider_name), font=ctk.CTkFont(size=16)
        )
        icon_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        name_label = ctk.CTkLabel(
            card_frame,
            text=provider_name.upper(),
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        name_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Статус
        status_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        status_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        status_indicator = ctk.CTkLabel(
            status_frame, text="●", font=ctk.CTkFont(size=12), text_color="gray"
        )
        status_indicator.pack(side="left", padx=(0, 5))

        status_label = ctk.CTkLabel(
            status_frame, text="Unknown", font=ctk.CTkFont(size=10)
        )
        status_label.pack(side="left")

        # Детали
        details_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        details_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        response_label = ctk.CTkLabel(
            details_frame, text="Response: -- ms", font=ctk.CTkFont(size=9), text_color=("gray50", "gray60")
        )
        response_label.pack(side="left", padx=(0, 10))

        error_label = ctk.CTkLabel(
            details_frame, text="No errors", font=ctk.CTkFont(size=9), text_color=("gray50", "gray60")
        )
        error_label.pack(side="left")

        # Кнопки управления
        control_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        control_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        test_btn = ctk.CTkButton(
            control_frame,
            text="Test",
            width=60,
            height=25,
            corner_radius=6,
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"),
            font=ctk.CTkFont(size=10),
            command=lambda p=provider_name: self._test_provider(p),
        )
        test_btn.pack(side="left", padx=(0, 5))

        switch_btn = ctk.CTkButton(
            control_frame,
            text="Switch",
            width=60,
            height=25,
            corner_radius=6,
            fg_color=("#0078D4", "#0078D4"),
            hover_color=("#106EBE", "#106EBE"),
            font=ctk.CTkFont(size=10),
            command=lambda p=provider_name: self._switch_provider(p),
        )
        switch_btn.pack(side="left")

        # Сохраняем ссылки на элементы
        if not hasattr(self, 'provider_widgets'):
            self.provider_widgets = {}
        
        self.provider_widgets[provider_name] = {
            'card': card_frame,
            'status_indicator': status_indicator,
            'status_label': status_label,
            'response_label': response_label,
            'error_label': error_label,
            'switch_btn': switch_btn
        }

    def _get_provider_icon(self, provider_name: str) -> str:
        """Получить иконку провайдера"""
        icons = {
            "gemini": "🌟",
            "openai": "🤖",
            "groq": "⚡",
            "lmstudio": "💻"
        }
        return icons.get(provider_name, "❓")

    def _create_status_monitoring(self, parent):
        """Создать панель общего статуса"""
        status_frame = ctk.CTkFrame(
            parent, corner_radius=10, fg_color=("gray92", "gray18"), height=100
        )
        status_frame.pack(fill="x", padx=10, pady=5)
        status_frame.pack_propagate(False)

        header_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="📊 System Status",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        title_label.pack(side="left")

        self.status_container = ctk.CTkFrame(status_frame, fg_color="transparent")
        self.status_container.pack(fill="both", expand=True, padx=10, pady=5)

        self._create_status_indicators()

    def _create_status_indicators(self):
        """Создать индикаторы статуса"""
        indicators_frame = ctk.CTkFrame(self.status_container, fg_color="transparent")
        indicators_frame.pack(fill="x")

        # Активный провайдер
        self.active_provider_label = ctk.CTkLabel(
            indicators_frame,
            text="Active: Gemini",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray60"),
        )
        self.active_provider_label.pack(side="left", padx=10)

        # Мониторинг
        self.monitoring_label = ctk.CTkLabel(
            indicators_frame,
            text="Monitoring: Active",
            font=ctk.CTkFont(size=11),
            text_color=("green", "lightgreen"),
        )
        self.monitoring_label.pack(side="left", padx=10)

        # Fallback
        self.fallback_label = ctk.CTkLabel(
            indicators_frame,
            text="Fallback: Enabled",
            font=ctk.CTkFont(size=11),
            text_color=("green", "lightgreen"),
        )
        self.fallback_label.pack(side="left", padx=10)

    def _create_optimization_panel(self, parent):
        """Создать панель оптимизации"""
        opt_frame = ctk.CTkFrame(
            parent, corner_radius=10, fg_color=("gray92", "gray18"), height=120
        )
        opt_frame.pack(fill="x", padx=10, pady=5)
        opt_frame.pack_propagate(False)

        header_frame = ctk.CTkFrame(opt_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_label = ctk.CTkLabel(
            header_frame,
            text="⚡ Optimization",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        title_label.pack(side="left")

        optimize_btn = ctk.CTkButton(
            header_frame,
            text="Optimize",
            width=80,
            height=28,
            corner_radius=6,
            fg_color=("#2ecc71", "#2ecc71"),
            hover_color=("#27ae60", "#27ae60"),
            font=ctk.CTkFont(size=10),
            command=self._optimize_settings,
        )
        optimize_btn.pack(side="right")

        self.opt_container = ctk.CTkFrame(opt_frame, fg_color="transparent")
        self.opt_container.pack(fill="both", expand=True, padx=10, pady=5)

        self.recommendations_label = ctk.CTkLabel(
            self.opt_container,
            text="System optimized ✓",
            font=ctk.CTkFont(size=10),
            text_color=("green", "lightgreen"),
            wraplength=300,
        )
        self.recommendations_label.pack(fill="x", padx=5, pady=5)

    def _refresh_provider_status(self):
        """Обновить статус провайдеров"""
        if not self.is_ui_ready:
            return

        status = self.analyzer.get_provider_status()
        
        for provider_name, info in status.items():
            if provider_name in self.provider_widgets:
                widget = self.provider_widgets[provider_name]
                
                # Обновляем статус
                status_text, status_color = self._get_status_info(info["status"])
                widget["status_label"].configure(text=status_text)
                widget["status_indicator"].configure(text_color=status_color)
                
                # Обновляем время ответа
                response_time = info.get("response_time", 0)
                widget["response_label"].configure(text=f"Response: {response_time:.0f} ms")
                
                # Обновляем ошибки
                error_msg = info.get("error_message", "")
                if error_msg:
                    widget["error_label"].configure(text=error_msg[:50])
                else:
                    widget["error_label"].configure(text="No errors")

                # Обновляем кнопку Switch
                is_active = info.get("is_active", False)
                if is_active:
                    widget["switch_btn"].configure(
                        text="Active",
                        fg_color=("gray60", "gray40"),
                        state="disabled"
                    )
                else:
                    widget["switch_btn"].configure(
                        text="Switch",
                        fg_color=("#0078D4", "#0078D4"),
                        state="normal"
                    )

        # Обновляем общий статус
        stats = self.analyzer.get_analysis_stats()
        self.active_provider_label.configure(text=f"Active: {stats['active_provider'].upper()}")
        
        if stats["monitoring_active"]:
            self.monitoring_label.configure(text="Monitoring: Active", text_color=("green", "lightgreen"))
        else:
            self.monitoring_label.configure(text="Monitoring: Stopped", text_color=("red", "lightcoral"))
        
        if stats["fallback_enabled"]:
            self.fallback_label.configure(text="Fallback: Enabled", text_color=("green", "lightgreen"))
        else:
            self.fallback_label.configure(text="Fallback: Disabled", text_color=("red", "lightcoral"))

    def _get_status_info(self, status: str) -> tuple:
        """Получить информацию о статусе"""
        if status == "connected":
            return "Connected", ("green", "lightgreen")
        elif status == "error":
            return "Error", ("red", "lightcoral")
        elif status == "disconnected":
            return "Disconnected", ("orange", "lightyellow")
        elif status == "rate_limited":
            return "Rate Limited", ("orange", "lightyellow")
        elif status == "quota_exceeded":
            return "Quota Exceeded", ("red", "lightcoral")
        else:
            return "Unknown", ("gray", "gray")

    def _test_provider(self, provider_name: str):
        """Тест провайдера"""
        if not self.is_ui_ready:
            return

        self.robot_say(f"Testing {provider_name}...")
        
        def test_task():
            result = self.analyzer.test_provider(provider_name)
            if result["success"]:
                self.robot_say(f"{provider_name} OK!")
                self._refresh_provider_status()
            else:
                self.robot_say(f"{provider_name} failed")
                self._refresh_provider_status()
        
        thread = threading.Thread(target=test_task, daemon=True)
        thread.start()

    def _switch_provider(self, provider_name: str):
        """Переключиться на провайдер"""
        if not self.is_ui_ready:
            return

        self.robot_say(f"Switching to {provider_name}...")
        
        def switch_task():
            self.analyzer.switch_provider(provider_name)
            self._refresh_provider_status()
        
        thread = threading.Thread(target=switch_task, daemon=True)
        thread.start()

    def _optimize_settings(self):
        """Оптимизировать настройки"""
        if not self.is_ui_ready:
            return

        self.robot_say("Optimizing settings...")
        
        def optimize_task():
            result = self.analyzer.optimize_provider_settings()
            recommendations = result["recommendations"]
            
            if recommendations:
                text = "Recommendations:\n" + "\n".join([f"• {r}" for r in recommendations])
                self.recommendations_label.configure(text=text, text_color=("orange", "lightyellow"))
            else:
                self.recommendations_label.configure(text="System optimized ✓", text_color=("green", "lightgreen"))
        
        thread = threading.Thread(target=optimize_task, daemon=True)
        thread.start()

    def _on_analyzer_status_change(self, *args):
        """Обработчик изменения статуса анализатора"""
        self._refresh_provider_status()

    def _on_provider_switch(self, provider_name: str, model_id: str):
        """Обработчик переключения провайдера"""
        self.robot_say(f"Switched to {provider_name}")

    def _on_analysis_complete(self, result):
        """Обработчик завершения анализа"""
        if result.status == "completed":
            self.robot_say("Analysis completed!")
        else:
            self.robot_say("Analysis failed")

    def start(self):
        """Запустить виджет с мониторингом"""
        super().start()
        
        # Запускаем периодическое обновление статуса
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

    def _monitoring_loop(self):
        """Цикл мониторинга"""
        while self.monitoring_active:
            try:
                self._refresh_provider_status()
            except:
                pass
            time.sleep(10)  # Обновляем каждые 10 секунд

    def destroy(self):
        """Остановить виджет и мониторинг"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        
        self.analyzer.stop_monitoring()
        super().destroy()