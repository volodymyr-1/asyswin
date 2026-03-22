#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AsysWin - Система автоматизации рабочих процессов
Записывает действия пользователя, анализирует через Google Gemini и генерирует скрипты

Горячие клавиши:
  F9  - Начать/остановить запись
  F10 - Отправить на анализ
  F11 - Показать предсказания (топ-3 сценариев)
  ESC - Выход

Требования:
  - Установите переменную окружения GEMINI_API_KEY
  - Получите ключ: https://makersuite.google.com/app/apikey
"""

import sys
from dotenv import load_dotenv

load_dotenv()

from base_application import BaseApplication
from assistant_widget_recommended import AssistantWidgetRecommended
from single_instance import check_single_instance, release_instance


class AsysWin(BaseApplication):
    """Система автоматизации AsysWin"""

    APP_NAME = "AsysWin"
    WIDGET_CLASS = AssistantWidgetRecommended
    WIDTH = 60


def main():
    if not check_single_instance():
        sys.exit(1)

    try:
        app = AsysWin()
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
