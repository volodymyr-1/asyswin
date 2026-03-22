#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AsysWin Enhanced - Улучшенная система автоматизации рабочих процессов
Записывает действия пользователя, анализирует через Google Gemini и генерирует скрипты

Горячие клавиши:
  F9  - Начать/остановить запись
  F10 - Отправить на анализ
  F11 - Показать предсказания (топ-3 сценариев)
  ESC - Выход

Особенности улучшенной версии:
  🤖 Анимированный робот-ассистент
  🎨 Профессиональная графика и анимации
  🎵 Звуковые эффекты
  🎯 Интеллектуальные рекомендации скриптов
  🛡️ Безопасное выполнение в песочнице

Требования:
  - Установите переменную окружения GEMINI_API_KEY
  - Получите ключ: https://makersuite.google.com/app/apikey
"""

import sys
from base_application import BaseApplication
from enhanced_assistant_widget import EnhancedAssistantWidget
from single_instance import check_single_instance, release_instance


class AsysWinEnhanced(BaseApplication):
    """Улучшенная система автоматизации AsysWin"""

    APP_NAME = "AsysWin Enhanced"
    WIDGET_CLASS = EnhancedAssistantWidget
    WIDTH = 70

    def __init__(self):
        super().__init__()
        self._load_startup_sounds()

    def _print_banner(self):
        print("=" * self.WIDTH)
        print("🤖 AsysWin Enhanced - Улучшенная система автоматизации")
        print("=" * self.WIDTH)
        print(
            "🎨 Профессиональная графика | 🎵 Звуковые эффекты | 🤖 Анимированный робот"
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

            duration = 1.0
            frequencies = [440, 554, 659, 880, 1175]
            sample_rate = 44100
            wave = np.array([])

            for freq in frequencies:
                samples = int(duration / 5 * sample_rate)
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
  ESC - Выход из программы

Особенности улучшенной версии:
  🤖 Анимированный робот-ассистент с профессиональной графикой
  🎨 Современный дизайн в стиле Windows 11/12
  🎵 Звуковые эффекты для обратной связи
  🎯 Интеллектуальные рекомендации скриптов (топ-3)
  🛡️ Безопасное выполнение скриптов в песочнице
  📊 Статистика и история выполнения
  🔄 Автоматический режим: запись при активности, анализ при простое

Как использовать:
  1. Нажмите F9 для начала записи
  2. Выполните нужные действия на компьютере
  3. Нажмите F9 для остановки записи
  4. Нажмите F10 для анализа и генерации скриптов
  5. Скрипты сохранятся в папке generated_scripts/
  6. Робот-ассистент предложит 3 наиболее вероятных скрипта для запуска

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
        print("💡 Улучшенный виджет-ассистент отображается в правом нижнем углу экрана")
        print("🤖 Анимированный робот поможет в работе с системой")
        print("🔄 Автоматический режим: запись при активности, анализ при простое")

        try:
            while self.is_running:
                import time

                time.sleep(0.5)
        except KeyboardInterrupt:
            self._exit()


def main():
    if not check_single_instance():
        sys.exit(1)

    try:
        app = AsysWinEnhanced()
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
