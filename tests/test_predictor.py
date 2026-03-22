#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тесты для predictor
TDD: Тесты для системы предсказаний
"""

import unittest
import json
import os
import tempfile
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from predictor import Predictor


class TestPredictor(unittest.TestCase):
    """Тесты для Predictor"""

    def setUp(self):
        """Создаём временный файл для паттернов"""
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        self.temp_file.close()
        self.predictor = Predictor(patterns_file=self.temp_file.name)

    def tearDown(self):
        """Удаляем временный файл"""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass

    def test_predictor_creates_patterns_file(self):
        """Predictor создаёт файл паттернов"""
        self.assertTrue(os.path.exists(self.predictor.patterns_file))

    def test_predictor_loads_empty_patterns(self):
        """Predictor загружает пустые паттерны"""
        self.assertEqual(len(self.predictor.patterns), 0)

    def test_add_pattern_creates_pattern(self):
        """add_pattern создаёт новый паттерн"""
        actions = [
            {"type": "key_press", "key": "a"},
            {"type": "mouse_click", "x": 100, "y": 200},
        ]
        goal = "Test Goal"
        subtasks = [{"name": "Step 1", "description": "Test", "script": "print(1)"}]

        self.predictor.add_pattern(actions, goal, subtasks)

        self.assertEqual(len(self.predictor.patterns), 1)
        self.assertEqual(self.predictor.patterns[0]["goal"], goal)
        self.assertEqual(len(self.predictor.patterns[0]["subtasks"]), 1)

    def test_add_pattern_updates_existing(self):
        """add_pattern обновляет существующий паттерн"""
        actions = [{"type": "key_press", "key": "a"}]
        goal = "Test Goal"
        subtasks = [{"name": "Step 1", "description": "Test", "script": "print(1)"}]

        # Добавляем первый раз
        self.predictor.add_pattern(actions, goal, subtasks)
        first_count = self.predictor.patterns[0]["used_count"]

        # Добавляем второй раз - должен обновиться
        self.predictor.add_pattern(actions, goal, subtasks)
        second_count = self.predictor.patterns[0]["used_count"]

        self.assertEqual(len(self.predictor.patterns), 1)
        self.assertEqual(second_count, first_count + 1)

    def test_get_top_predictions_empty(self):
        """get_top_predictions возвращает пустой список без паттернов"""
        predictions = self.predictor.get_top_predictions()
        self.assertEqual(predictions, [])

    def test_get_top_predictions_returns_sorted(self):
        """get_top_predictions возвращает отсортированные предсказания"""
        # Добавляем паттерны с разным used_count
        actions1 = [{"type": "key_press", "key": "a"}]
        actions2 = [{"type": "key_press", "key": "b"}]
        actions3 = [{"type": "key_press", "key": "c"}]

        self.predictor.add_pattern(actions1, "Goal 1", [{"name": "S1", "script": "p1"}])
        self.predictor.add_pattern(actions2, "Goal 2", [{"name": "S2", "script": "p2"}])
        self.predictor.add_pattern(actions3, "Goal 3", [{"name": "S3", "script": "p3"}])

        # Добавляем второй раз для Goal 2
        self.predictor.add_pattern(actions2, "Goal 2", [{"name": "S2", "script": "p2"}])

        predictions = self.predictor.get_top_predictions(limit=3)

        self.assertEqual(len(predictions), 3)
        # Goal 2 должен быть первым (больше использований)
        self.assertEqual(predictions[0]["name"], "Goal 2")
        self.assertEqual(predictions[0]["used_count"], 2)

    def test_get_top_predictions_respects_limit(self):
        """get_top_predictions ограничивает количество"""
        for i in range(5):
            actions = [{"type": "key_press", "key": str(i)}]
            self.predictor.add_pattern(
                actions, f"Goal {i}", [{"name": f"S{i}", "script": f"p{i}"}]
            )

        predictions = self.predictor.get_top_predictions(limit=3)
        self.assertEqual(len(predictions), 3)

    def test_create_signature(self):
        """_create_signature создаёт сигнатуру из действий"""
        actions = [
            {"type": "key_press", "key": "a"},
            {"type": "key_press", "key": "a"},
            {"type": "mouse_click"},
            {"type": "mouse_scroll", "dy": -1},
        ]

        signature = self.predictor._create_signature(actions)

        self.assertIsInstance(signature, str)
        self.assertIn("K_a", signature)
        self.assertIn("C_", signature)
        self.assertIn("S_", signature)

    def test_find_similar_pattern(self):
        """_find_similar_pattern находит похожий паттерн"""
        actions = [{"type": "key_press", "key": "test"}]
        self.predictor.add_pattern(actions, "Test", [{"name": "S", "script": "p"}])

        signature = self.predictor._create_signature(actions)
        found = self.predictor._find_similar_pattern(signature)

        self.assertIsNotNone(found)
        self.assertEqual(found["goal"], "Test")

    def test_find_similar_pattern_not_found(self):
        """_find_similar_pattern возвращает None если не найден"""
        found = self.predictor._find_similar_pattern("nonexistent_signature")
        self.assertIsNone(found)

    def test_prediction_has_required_fields(self):
        """Предсказание содержит все необходимые поля"""
        actions = [{"type": "key_press", "key": "a"}]
        self.predictor.add_pattern(actions, "Test", [{"name": "S", "script": "p"}])

        predictions = self.predictor.get_top_predictions()
        prediction = predictions[0]

        required_fields = [
            "name",
            "description",
            "used_count",
            "subtasks",
            "script_path",
        ]
        for field in required_fields:
            self.assertIn(field, prediction)

    def test_display_predictions_no_crash(self):
        """display_predictions не падает с пустым списком"""
        self.predictor.display_predictions([])

    def test_display_predictions_with_data(self):
        """display_predictions работает с данными"""
        actions = [{"type": "key_press", "key": "a"}]
        self.predictor.add_pattern(actions, "Test", [{"name": "S", "script": "p"}])

        predictions = self.predictor.get_top_predictions()
        self.predictor.display_predictions(predictions)

    def test_get_statistics_empty(self):
        """get_statistics с пустыми паттернами"""
        stats = self.predictor.get_statistics()

        self.assertEqual(stats["total_patterns"], 0)
        self.assertEqual(stats["total_uses"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
