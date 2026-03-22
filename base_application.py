#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Базовый класс приложения AsysWin
Общая логика для AsysWin и AsysWinEnhanced
"""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict

from logger import logger
from action_recorder import ActionRecorder
from llm_analyzer import LLMAnalyzer
from script_generator import ScriptGenerator
from background_analyzer import BackgroundAnalyzer
from predictor import Predictor
from activity_monitor import ActivityMonitor
from script_tester import ScriptTester
from settings_window import SettingsWindow
from semantic_logger import SemanticLogger


class BaseApplication:
    """Базовый класс приложения AsysWin"""

    APP_NAME = "AsysWin"
    WIDGET_CLASS = None  # Переопределяется в наследниках
    WIDTH = 60

    def __init__(self):
        self._print_banner()

        # Инициализация модулей
        self.recorder = ActionRecorder()
        self.llm_analyzer = LLMAnalyzer()
        self.script_generator = ScriptGenerator()
        self.background_analyzer = BackgroundAnalyzer(cpu_limit=50.0)
        self.predictor = Predictor()

        # Модули автоматизации
        self.activity_monitor = ActivityMonitor(idle_threshold=30.0)
        self.script_tester = ScriptTester(timeout=10)

        # Семантическое логирование
        self.semantic_logger = SemanticLogger()

        # Инициализация виджета
        if self.WIDGET_CLASS:
            self.widget = self.WIDGET_CLASS()
        else:
            raise NotImplementedError("WIDGET_CLASS must be defined")

        self._setup_widget_callbacks()
        self._setup_activity_monitor()

        # Состояние
        self.is_running = True
        self.last_analysis_result = None
        self.auto_mode = True

        # Настройка горячих клавиш
        self._setup_hotkeys()

        # Callback для фонового анализатора
        self.background_analyzer.set_on_complete(self._on_analysis_complete)

    def _print_banner(self):
        """Вывести баннер приложения - переопределяется"""
        print("=" * self.WIDTH)
        print(f"🤖 {self.APP_NAME} - Система автоматизации рабочих процессов")
        print("=" * self.WIDTH)
        print()

    def _setup_activity_monitor(self):
        self.activity_monitor.on_active = self._on_user_active
        self.activity_monitor.on_idle = self._on_user_idle

    def _on_user_active(self):
        if self.auto_mode and not self.recorder.is_recording:
            self.recorder.start_recording()
            self.widget.set_recording(True)
            self._print_status("🔴 Автозапись: пользователь активен")

    def _on_user_idle(self):
        if self.auto_mode and self.recorder.is_recording and self.recorder.actions:
            self.recorder.stop_recording()
            self.widget.set_recording(False)
            self._print_status("⏸ Автоостановка: простой > 30с")
            self._send_to_analysis()

    def _setup_widget_callbacks(self):
        self.widget.on_toggle_recording = self._toggle_recording
        self.widget.on_analyze = self._send_to_analysis
        self.widget.on_show_predictions = self._show_predictions
        self.widget.on_open_scripts_folder = self._open_scripts_folder
        self.widget.on_open_settings = self._open_settings

    def _open_settings(self):
        settings = SettingsWindow()
        settings.on_save = self._on_settings_saved
        settings.show()

    def _on_settings_saved(self, config):
        self.recorder.mouse_move_threshold = config.get("mouse_threshold", 50)
        self.recorder.key_debounce_ms = config.get("key_debounce", 100)
        self.auto_mode = config.get("auto_record", True)

        self._print_status("⚙️ Настройки сохранены")
        logger.info("Настройки обновлены", "CONFIG")

    def _open_scripts_folder(self):
        import subprocess

        scripts_dir = os.path.abspath("generated_scripts")
        if os.path.exists(scripts_dir):
            subprocess.Popen(f'explorer "{scripts_dir}"')
        else:
            self.widget.notify_error("Папка не найдена")

    def _setup_hotkeys(self):
        from pynput import keyboard

        self.hotkey_listener = keyboard.Listener(on_press=self._on_hotkey_press)
        self.hotkey_listener.start()

    def _on_hotkey_press(self, key):
        try:
            key_name = key.name if hasattr(key, "name") else str(key)
        except:
            return

        if key_name == "f9":
            self._toggle_recording()
        elif key_name == "f10":
            self._send_to_analysis()
        elif key_name == "f11":
            self._show_predictions()
        elif key_name == "esc":
            self._exit()

    def _toggle_recording(self):
        if self.recorder.is_recording:
            self.recorder.stop_recording()
            self.widget.set_recording(False)
            self._print_status("⏹ Запись остановлена")
            logger.log_action(
                "STOP_RECORDING", f"Действий: {len(self.recorder.actions)}"
            )
        else:
            self.recorder.start_recording()
            self.widget.set_recording(True)
            self._print_status("🔴 Запись начата")
            logger.log_action("START_RECORDING", "Запись начата")

    def _send_to_analysis(self):
        try:
            if not self.recorder.actions:
                self._print_status("⚠️ Нет записанных действий для анализа")
                self.widget.notify_error("Нет записанных действий")
                logger.warning("Попытка анализа без записанных действий", "ANALYSIS")
                return

            actions = self.recorder.actions.copy()
            summary = self.recorder.get_actions_summary()

            self._print_status(f"📤 Отправка на анализ ({summary['total']} действий)")
            self.widget.set_analyzing(True)
            logger.log_analysis("START", f"Действий: {summary['total']}")

            self.background_analyzer.add_task(
                task_data=actions, analyzer_func=self.llm_analyzer.analyze_actions
            )
        except Exception as e:
            self._print_status(f"❌ Ошибка отправки на анализ: {e}")
            self.widget.set_analyzing(False)
            self.widget.notify_error(f"Ошибка: {str(e)[:50]}")
            logger.error(f"Ошибка отправки на анализ: {e}", "ANALYSIS")

    def _on_analysis_complete(self, result):
        try:
            self.last_analysis_result = result

            if result:
                generation_result = self.script_generator.generate_scripts(result)

                if isinstance(generation_result, dict) and generation_result.get(
                    "duplicate"
                ):
                    existing = generation_result["existing"]
                    self._print_status(f"⚠️ Найден похожий скрипт: {existing['goal']}")
                    self.widget.robot_say("Нашёл похожий скрипт! Хотите создать новый?")

                    variants = self.script_generator.get_script_variants(result)
                    self._show_variant_selection(variants)
                    return

                created_files = generation_result

                goal = result.get("goal", "Автоматизированная задача")
                subtasks = result.get("subtasks", [])
                self.predictor.add_pattern(self.recorder.actions, goal, subtasks)

                if created_files:
                    self._print_status("🧪 Тестирование сгенерированных скриптов...")
                    self.widget.robot_say("Тестирую скрипты...")
                    logger.log_analysis(
                        "TESTING", f"Тестирование {len(created_files)} скриптов"
                    )
                    for script_path in created_files:
                        if script_path.endswith(".py") and "run_all" not in script_path:
                            test_result = self.script_tester.test_script(script_path)
                            if test_result["syntax_valid"]:
                                self._print_status(
                                    f"  ✅ {os.path.basename(script_path)}"
                                )
                                logger.info(
                                    f"Скрипт прошёл тест: {os.path.basename(script_path)}",
                                    "TEST",
                                )
                            else:
                                error = test_result["syntax_error"]
                                self._print_status(
                                    f"  ❌ {os.path.basename(script_path)}: {error[:50]}"
                                )
                                logger.error(
                                    f"Скрипт не прошёл тест: {os.path.basename(script_path)} - {error}",
                                    "TEST",
                                )

                self.widget.set_analyzing(False)
                self.widget.notify_analysis_complete(len(created_files))
                self._print_status(
                    f"✅ Анализ завершён. Создано файлов: {len(created_files)}"
                )
                logger.log_analysis("COMPLETE", f"Создано файлов: {len(created_files)}")
            else:
                self.widget.set_analyzing(False)
                self.widget.notify_error("Анализ не удался")
                self.widget.robot_say("Что-то пошло не так...")
                self._print_status("❌ Анализ не удался")
                logger.log_analysis("FAILED", "Анализ не удался")
        except Exception as e:
            self._print_status(f"❌ Ошибка обработки результата: {e}")
            self.widget.set_analyzing(False)
            self.widget.notify_error(f"Ошибка: {str(e)[:50]}")
            logger.error(f"Ошибка обработки результата анализа: {e}", "ANALYSIS")

    def _show_variant_selection(self, variants: List[Dict]):
        print("\n" + "=" * self.WIDTH)
        print("📋 ВЫБЕРИТЕ ВАРИАНТ СКРИПТА:")
        print("=" * self.WIDTH)

        for i, variant in enumerate(variants, 1):
            print(f"\n{i}. {variant['name']}")
            print(f"   {variant['description']}")

        print("\n" + "=" * self.WIDTH)
        print("Введите номер варианта (1-3) или 'new' для нового анализа:")

        self._apply_variant(variants[0])

    def _apply_variant(self, variant: Dict):
        analysis = variant["analysis"]
        created_files = self.script_generator.generate_scripts(analysis, force_new=True)

        if created_files:
            self.widget.notify_analysis_complete(len(created_files))
            self.widget.robot_say(f"Создал вариант: {variant['name']}!")

    def _show_predictions(self):
        predictions = self.predictor.get_top_predictions(limit=3)
        self.predictor.display_predictions(predictions)

    def _exit(self):
        self._print_status("👋 Завершение работы...")
        self.is_running = False

        if self.recorder.is_recording:
            self.recorder.stop_recording()

        self.activity_monitor.stop()
        self.background_analyzer.stop()
        self.hotkey_listener.stop()

        sys.exit(0)

    def _print_status(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] {message}")

    def _print_help(self):
        print("\n" + "=" * self.WIDTH)
        print(f"📖 СПРАВКА - {self.APP_NAME}")
        print("=" * self.WIDTH)
        print("""
Горячие клавиши:
  F9  - Начать/остановить запись действий
  F10 - Отправить записанные действия на анализ
  F11 - Показать топ-3 часто используемых сценариев
  ESC - Выход из программы

Как использовать:
  1. Нажмите F9 для начала записи
  2. Выполните нужные действия на компьютере
  3. Нажмите F9 для остановки записи
  4. Нажмите F10 для анализа и генерации скриптов
  5. Скрипты сохранятся в папке generated_scripts/

Фоновый анализ:
  - Анализ выполняется в фоновом режиме
  - Нагрузка на CPU ограничена 50%
  - Результаты появляются автоматически

Предсказания:
  - Система запоминает ваши паттерны
  - Нажмите F11 для просмотра топ-3 сценариев
  - Готовые скрипты сохраняются в папке scripts/
""")
        print("=" * self.WIDTH)

    def run(self):
        if not self.llm_analyzer.is_ready():
            print("⚠️ API ключ Google Gemini не настроен!")
            print("   Установите переменную окружения GEMINI_API_KEY")
            print("   Получите ключ: https://makersuite.google.com/app/apikey")
            print("   Анализ работать не будет.\n")

        self.activity_monitor.start()
        self.background_analyzer.start()
        self.widget.start()

        self._print_help()

        print("\n🟢 Система готова к работе. Ожидание команд...\n")
        print("💡 Виджет-ассистент отображается в правом нижнем углу экрана")
        print("🔄 Автоматический режим: запись при активности, анализ при простое")

        try:
            while self.is_running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self._exit()
