#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты для action_recorder
TDD: Тесты для системы записи действий
"""

import unittest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from action_recorder import ActionRecorder


class TestActionRecorder(unittest.TestCase):
    """Тесты для ActionRecorder"""

    def setUp(self):
        """Создаём recorder"""
        self.recorder = ActionRecorder()

    def test_recorder_initial_state(self):
        """Recorder имеет правильное начальное состояние"""
        self.assertFalse(self.recorder.is_recording)
        self.assertEqual(len(self.recorder.actions), 0)

    def test_recorder_has_log_dir(self):
        """Recorder имеет log_dir"""
        self.assertTrue(hasattr(self.recorder, "log_dir"))
        self.assertEqual(self.recorder.log_dir, "action_logs")

    def test_recorder_has_lock(self):
        """Recorder имеет lock"""
        self.assertTrue(hasattr(self.recorder, "lock"))

    def test_recorder_starts_not_recording(self):
        """Recorder по умолчанию не записывает"""
        self.assertFalse(self.recorder.is_recording)

    def test_get_actions_summary_empty(self):
        """get_actions_summary с пустым списком"""
        summary = self.recorder.get_actions_summary()

        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["key_presses"], 0)
        self.assertEqual(summary["mouse_clicks"], 0)
        self.assertEqual(summary["mouse_moves"], 0)
        self.assertEqual(summary["scrolls"], 0)

    def test_get_actions_summary_with_data(self):
        """get_actions_summary с данными"""
        self.recorder.actions = [
            {"type": "key_press", "key": "a"},
            {"type": "key_press", "key": "b"},
            {"type": "mouse_click", "x": 100, "y": 200},
            {"type": "mouse_move", "x": 150, "y": 250},
            {"type": "mouse_scroll", "dy": -1},
        ]

        summary = self.recorder.get_actions_summary()

        self.assertEqual(summary["total"], 5)
        self.assertEqual(summary["key_presses"], 2)
        self.assertEqual(summary["mouse_clicks"], 1)
        self.assertEqual(summary["mouse_moves"], 1)
        self.assertEqual(summary["scrolls"], 1)

    def test_mouse_move_threshold(self):
        """mouse_move_threshold по умолчанию"""
        self.assertEqual(self.recorder.mouse_move_threshold, 50)

    def test_key_debounce_ms(self):
        """key_debounce_ms по умолчанию"""
        self.assertEqual(self.recorder.key_debounce_ms, 10)

    def test_last_key_time_initial(self):
        """last_key_time инициализируется"""
        self.assertIsNotNone(self.recorder.last_key_time)
        self.assertEqual(len(self.recorder.last_key_time), 0)

    def test_last_mouse_pos_initial(self):
        """last_mouse_pos инициализируется"""
        self.assertIsNotNone(self.recorder.last_mouse_pos)
        self.assertEqual(self.recorder.last_mouse_pos, (0, 0))

    def test_has_hotkey_callbacks(self):
        """Recorder имеет hotkey_callbacks"""
        self.assertTrue(hasattr(self.recorder, "hotkey_callbacks"))
        self.assertEqual(len(self.recorder.hotkey_callbacks), 0)


class TestActionRecorderCallbacks(unittest.TestCase):
    """Тесты callback методов ActionRecorder"""

    def setUp(self):
        self.recorder = ActionRecorder()
        self.recorder.is_recording = True
        self.recorder.start_time = 0

    def test_on_key_press_adds_action(self):
        """_on_key_press добавляет действие"""
        key = Mock()
        key.char = "a"

        self.recorder._on_key_press(key)

        self.assertEqual(len(self.recorder.actions), 1)
        self.assertEqual(self.recorder.actions[0]["type"], "key_press")

    def test_on_key_release_adds_action(self):
        """_on_key_release добавляет действие"""
        key = Mock()
        key.char = "a"

        self.recorder._on_key_release(key)

        self.assertEqual(len(self.recorder.actions), 1)
        self.assertEqual(self.recorder.actions[0]["type"], "key_release")

    def test_on_mouse_click_adds_action(self):
        """_on_mouse_click добавляет действие"""
        from pynput import mouse

        self.recorder._on_mouse_click(100, 200, mouse.Button.left, True)

        self.assertEqual(len(self.recorder.actions), 1)
        self.assertEqual(self.recorder.actions[0]["type"], "mouse_click")
        self.assertEqual(self.recorder.actions[0]["x"], 100)
        self.assertEqual(self.recorder.actions[0]["y"], 200)

    def test_on_mouse_scroll_is_recorded(self):
        """_on_mouse_scroll не записывает (заглушка)"""
        initial_count = len(self.recorder.actions)
        self.recorder._on_mouse_scroll(100, 200, 0, -1)
        self.assertEqual(len(self.recorder.actions), initial_count)

    def test_on_key_press_respects_hotkey(self):
        """_on_key_press вызывает hotkey callback"""
        callback = Mock()
        self.recorder.hotkey_callbacks["a"] = callback

        key = Mock()
        key.char = "a"

        self.recorder._on_key_press(key)

        callback.assert_called_once()


class TestActionRecorderState(unittest.TestCase):
    """Тесты состояния recorder"""

    @patch("action_recorder.keyboard.Listener")
    @patch("action_recorder.mouse.Listener")
    def test_start_recording_changes_state(self, mock_mouse, mock_keyboard):
        """start_recording меняет состояние"""
        mock_key_instance = MagicMock()
        mock_mouse_instance = MagicMock()
        mock_keyboard.return_value = mock_key_instance
        mock_mouse.return_value = mock_mouse_instance

        recorder = ActionRecorder()
        self.assertFalse(recorder.is_recording)

        recorder.start_recording()

        self.assertTrue(recorder.is_recording)
        mock_key_instance.start.assert_called_once()
        mock_mouse_instance.start.assert_called_once()

    @patch("action_recorder.keyboard.Listener")
    @patch("action_recorder.mouse.Listener")
    def test_stop_recording_changes_state(self, mock_mouse, mock_keyboard):
        """stop_recording меняет состояние"""
        mock_key_instance = MagicMock()
        mock_mouse_instance = MagicMock()
        mock_keyboard.return_value = mock_key_instance
        mock_mouse.return_value = mock_mouse_instance

        recorder = ActionRecorder()
        recorder.start_recording()
        self.assertTrue(recorder.is_recording)

        recorder.stop_recording()

        self.assertFalse(recorder.is_recording)
        mock_key_instance.stop.assert_called()
        mock_mouse_instance.stop.assert_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
