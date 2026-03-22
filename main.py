#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AsysWin - Automation System
Records user actions, analyzes via Google Gemini and generates scripts

Hotkeys:
  F9  - Start/stop recording
  F10 - Send to analysis
  F11 - Show predictions (top-3)
  ESC - Exit

Requirements:
  - Set GEMINI_API_KEY in .env file
  - Get key: https://makersuite.google.com/app/apikey
"""

import sys
from dotenv import load_dotenv

load_dotenv()

from base_application import BaseApplication
from assistant_widget_recommended import AssistantWidgetRecommended
from single_instance import check_single_instance, release_instance
from automation_manager import AutomationManager


class AsysWin(BaseApplication):
    """AsysWin Automation System"""

    APP_NAME = "AsysWin"
    WIDGET_CLASS = AssistantWidgetRecommended
    WIDTH = 60

    def __init__(self):
        super().__init__()
        self.auto_manager = AutomationManager()


def main():
    if not check_single_instance():
        sys.exit(1)

    try:
        app = AsysWin()
        app.run()
    except Exception as e:
        print(f"\n[!] Critical error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        release_instance()


if __name__ == "__main__":
    main()
