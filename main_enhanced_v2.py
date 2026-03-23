#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AsysWin Enhanced v2 - Улучшенная система автоматизации с мониторингом провайдеров
Записывает действия пользователя, анализирует через AI провайдеров и генерирует скрипты

Горячие клавиши:
  F9  - Начать/остановить запись
  F10 - Отправить на анализ
  F11 - Показать предсказания (топ-3 сценариев)
  F12 - Открыть мониторинг провайдеров
  ESC - Выход

Особенности улучшенной версии v2:
  🤖 Анимированный робот-ассистент с улучшенной графикой
  🎨 Профессиональная графика и анимации
  🎵 Звуковые эффекты
  🎯 Интеллектуальные рекомендации скриптов (топ-3)
  🛡️ Безопасное выполнение в песочнице
  📡 Мониторинг провайдеров в реальном времени
  🔄 Автоматический fallback при ошибках
  ⚡ Оптимизация настроек
  📊 Статистика и аналитика

Требования:
  - Установите переменные окружения для API ключей
  - Google Gemini: GEMINI_API_KEY
  - OpenAI: OPENAI_API_KEY
  - Groq: GROQ_API_KEY
  - LM Studio: Запустите сервер на localhost:1234
"""

import sys
import threading
import time
from typing import Optional

from base_application import BaseApplication
from enhanced_monitoring_widget import EnhancedMonitoringWidget
from enhanced_analyzer import EnhancedAnalyzer
from script_manager import ScriptManager
from config_manager import get_config


class AsysWinEnhancedV2(BaseApplication):
    """Улучшенная система автоматизации AsysWin v2"""

    APP_NAME = "AsysWin Enhanced v2"
    WIDGET_CLASS = EnhancedMonitoringWidget
    WIDTH = 70

    def __init__(self):
        super().__init__()
        self._load_startup_sounds()

        # Инициализация улучшенных компонентов
        self.enhanced_analyzer = EnhancedAnalyzer()
        self.script_manager = ScriptManager()
        
        # Настройка коллбэков
        self.enhanced_analyzer.on_status_change = self._on_analyzer_status_change
        self.enhanced_analyzer.on_provider_switch = self._on_provider_switch
        self.enhanced_analyzer.on_analysis_complete = self._on_analysis_complete

    def _print_banner(self):
        print("=" * self.WIDTH)
        print("🤖 AsysWin Enhanced v2 - Улучшенная система автоматизации")
        print("=" * self.WIDTH)
        print(
            "📡 Мониторинг провайдеров | 🔄 Автоматический fallback | ⚡ Оптимизация"
        )
        print()

    def _load_startup_sounds(self):
        try:
            import pygame

            pygame.mixer.init()
            self.startup_sound = self._create_startup_sound()
            if self.startup_sound:
                self.startup_sound.play()
        except:
            pass

    def _create_startup_sound(self):
        try:
            import pygame.sndarray
            import numpy as np

            duration = 1.5
            frequencies = [440, 554, 659, 880, 1175, 1568]
            sample_rate = 44100
            wave = np.array([])

            for freq in frequencies:
                samples = int(duration / 6 * sample_rate)
                part = np.sin(2 * np.pi * np.arange(samples) * freq / sample_rate)
                envelope = np.linspace(1, 0.1, samples)
                part = part * envelope
                wave = np.concatenate([wave, part])

            wave = (wave * 32767).astype(np.int16)
            return pygame.sndarray.make_sound(wave)
        except:
            return None

    def _print_help(self):
        print("\n" + "=" * self.WIDTH)
        print(f"📖 СПРАВКА - {self.APP_NAME}")
        print("=" * self.WIDTH)
        print("""
Горячие клавиши:
  F9  - Начать/остановить запись действий
  F10 - Отправить записанные действия на анализ
  F11 - Показать топ-3 часто используемых сценариев
  F12 - Открыть мониторинг провайдеров
  ESC - Выход из программы

Особенности улучшенной версии v2:
  🤖 Анимированный робот-ассистент с профессиональной графикой
  🎨 Современный дизайн в стиле Windows 11/12
  🎵 Звуковые эффекты для обратной связи
  🎯 Интеллектуальные рекомендации скриптов (топ-3)
  🛡️ Безопасное выполнение скриптов в песочнице
  📡 Мониторинг провайдеров в реальном времени
  🔄 Автоматический fallback при ошибках
  ⚡ Оптимизация настроек
  📊 Статистика и аналитика
  🎛️ Выбор моделей для каждого провайдера

Как использовать:
  1. Нажмите F9 для начала записи
  2. Выполните нужные действия на компьютере
  3. Нажмите F9 для остановки записи
  4. Нажмите F10 для анализа и генерации скриптов
  5. Скрипты сохранятся в папке generated_scripts/
  6. Робот-ассистент предложит 3 наиболее вероятных скрипта для запуска

Мониторинг провайдеров:
  - Автоматическая проверка доступности
  - Fallback при ошибках
  - Оптимизация производительности
  - Статистика использования

Настройки:
  - F12 для открытия мониторинга провайдеров
  - Настройки в меню настроек (⚙️)
  - Выбор моделей для каждого провайдера
  - Автоматическая оптимизация

Провайдеры:
  - Google Gemini (рекомендуется)
  - OpenAI GPT-4
  - Groq (бесплатный, быстрый)
  - LM Studio (локальный)
""")
        print("=" * self.WIDTH)

    def _setup_widget_callbacks(self):
        """Настроить коллбэки виджета"""
        super()._setup_widget_callbacks()
        
        # Добавляем новый коллбэк для мониторинга
        if hasattr(self.widget, 'on_open_monitoring'):
            self.widget.on_open_monitoring = self._open_monitoring

    def _open_monitoring(self):
        """Открыть мониторинг провайдеров"""
        if hasattr(self.widget, '_refresh_provider_status'):
            self.widget._refresh_provider_status()

    def _on_analyzer_status_change(self, *args):
        """Обработчик изменения статуса анализатора"""
        if hasattr(self.widget, '_refresh_provider_status'):
            self.widget._refresh_provider_status()

    def _on_provider_switch(self, provider_name: str, model_id: str):
        """Обработчик переключения провайдера"""
        if hasattr(self.widget, 'robot_say'):
            self.widget.robot_say(f"Switched to {provider_name}")

    def _on_analysis_complete(self, result):
        """Обработчик завершения анализа"""
        if hasattr(self.widget, 'notify_analysis_complete'):
            if result.status == "completed":
                self.widget.notify_analysis_complete(1)
            else:
                self.widget.notify_error("Analysis failed")

    def _send_to_analysis(self):
        """Отправить на анализ с улучшенной логикой"""
        if self._analysis_in_progress:
            return
        self._analysis_in_progress = True

        try:
            if not self.recorder.actions:
                self._print_status("[WARN] No recorded actions for analysis")
                if hasattr(self.widget, 'notify_error'):
                    self.widget.notify_error("No recorded actions")
                return

            actions = self.recorder.actions.copy()
            summary = self.recorder.get_actions_summary()

            self._print_status(
                f"[SEND] Sending for analysis ({summary['total']} actions)"
            )
            
            if hasattr(self.widget, 'set_analyzing'):
                self.widget.set_analyzing(True)
            
            logger.log_analysis("START", f"Actions: {summary['total']}")

            # Используем улучшенный анализатор
            thread = threading.Thread(
                target=self._run_enhanced_analysis, args=(actions,), daemon=True
            )
            thread.start()
        except Exception as e:
            self._print_status(f"[ERROR] Send to analysis failed: {e}")
            if hasattr(self.widget, 'set_analyzing'):
                self.widget.set_analyzing(False)
            if hasattr(self.widget, 'notify_error'):
                self.widget.notify_error(f"Error: {str(e)[:50]}")
        finally:
            self._analysis_in_progress = False

    def _run_enhanced_analysis(self, actions: list):
        """Запустить улучшенный анализ"""
        try:
            result = self.enhanced_analyzer.analyze_actions(actions)
            
            if result.status == "completed" and result.result:
                # Генерируем скрипты
                generation_result = self.script_generator.generate_scripts(result.result)
                
                if isinstance(generation_result, dict) and generation_result.get("duplicate"):
                    existing = generation_result["existing"]
                    self._print_status(f"[WARN] Similar script found: {existing['goal']}")
                    if hasattr(self.widget, 'robot_say'):
                        self.widget.robot_say("Found similar script! Create new one?")
                    return

                created_files = generation_result
                goal = result.result.get("goal", "Автоматизированная задача")
                subtasks = result.result.get("subtasks", [])
                self.predictor.add_pattern(self.recorder.actions, goal, subtasks)

                if created_files:
                    self._print_status("[TEST] Testing generated scripts...")
                    if hasattr(self.widget, 'robot_say'):
                        self.widget.robot_say("Testing scripts...")
                    
                    for script_path in created_files:
                        if script_path.endswith(".py") and "run_all" not in script_path:
                            test_result = self.script_tester.test_script(script_path)
                            if test_result["syntax_valid"]:
                                self._print_status(f"  [OK] {os.path.basename(script_path)}")
                            else:
                                error = test_result["syntax_error"]
                                self._print_status(f"  [FAIL] {os.path.basename(script_path)}: {error[:50]}")

                if hasattr(self.widget, 'set_analyzing'):
                    self.widget.set_analyzing(False)
                if hasattr(self.widget, 'notify_analysis_complete'):
                    self.widget.notify_analysis_complete(len(created_files))
                
                self._print_status(f"[OK] Analysis complete. Files created: {len(created_files)}")
                logger.log_analysis("COMPLETE", f"Создано файлов: {len(created_files)}")
            else:
                if hasattr(self.widget, 'set_analyzing'):
                    self.widget.set_analyzing(False)
                if hasattr(self.widget, 'notify_error'):
                    self.widget.notify_error("Analysis failed")
                if hasattr(self.widget, 'robot_say'):
                    self.widget.robot_say("Something went wrong...")
                self._print_status("[FAIL] Analysis failed")
                
        except Exception as e:
            self._print_status(f"[ERROR] Result processing error: {e}")
            if hasattr(self.widget, 'set_analyzing'):
                self.widget.set_analyzing(False)
            if hasattr(self.widget, 'notify_error'):
                self.widget.notify_error(f"Ошибка: {str(e)[:50]}")

    def run(self):
        """Запустить приложение"""
        if not self.enhanced_analyzer.provider_manager.get_best_provider():
            print("⚠️ No AI providers configured!")
            print("    Configure providers in settings")
            print("    Analysis will not work.\n")

        self.activity_monitor.start()
        self.background_analyzer.start()
        self.widget.start()

        self._print_help()

        print("\n🟢 Система готова к работе. Ожидание команд...\n")
        print("💡 Улучшенный виджет-ассистент отображается в правом нижнем углу экрана")
        print("🤖 Анимированный робот поможет в работе с системой")
        print("📡 Мониторинг провайдеров активен")
        print("🔄 Автоматический режим: запись при активности, анализ при простое")

        try:
            while self.is_running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self._exit()

    def _exit(self):
        """Завершить работу"""
        self._print_status("[BYE] Shutting down...")
        self.is_running = False

        if self.recorder.is_recording:
            self.recorder.stop_recording()

        self.activity_monitor.stop()
        self.background_analyzer.stop()
        self.hotkey_listener.stop()
        
        # Останавливаем улучшенный анализатор
        self.enhanced_analyzer.stop_monitoring()

        sys.exit(0)


def main():
    """Главная функция"""
    if not check_single_instance():
        sys.exit(1)

    try:
        app = AsysWinEnhancedV2()
        app.run()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        release_instance()


if __name__ == "__main__":
    main()