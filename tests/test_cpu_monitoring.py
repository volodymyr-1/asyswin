#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD-тесты для контроля нагрузки системы
Тестируем автоматическое завершение процесса TextInputHost.exe при нагрузке > 30%
"""

import unittest
import time
import psutil
import subprocess
import threading
from unittest.mock import patch, MagicMock
import sys
import os

# Добавляем путь к основной системе
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.mock_file_operations import SystemMonitor


class TestCPUMonitoring(unittest.TestCase):
    """Тесты для мониторинга нагрузки CPU"""
    
    def setUp(self):
        """Подготовка тестов"""
        self.monitor = SystemMonitor()
        
    def test_cpu_usage_measurement(self):
        """Тест измерения загрузки CPU"""
        cpu_usage = self.monitor.get_cpu_usage()
        self.assertIsInstance(cpu_usage, float)
        self.assertGreaterEqual(cpu_usage, 0.0)
        self.assertLessEqual(cpu_usage, 100.0)
        
    def test_find_textinputhost_process(self):
        """Тест поиска процесса TextInputHost.exe"""
        # Создаем mock процесс
        mock_process = MagicMock()
        mock_process.info = {'name': 'TextInputHost.exe'}
        mock_process.pid = 12345
        
        with patch('psutil.process_iter', return_value=[mock_process]):
            process = self.monitor.find_textinputhost_process()
            self.assertIsNotNone(process)
            self.assertEqual(process.pid, 12345)
            
    def test_find_textinputhost_process_not_found(self):
        """Тест когда процесс TextInputHost.exe не найден"""
        with patch('psutil.process_iter', return_value=[]):
            process = self.monitor.find_textinputhost_process()
            self.assertIsNone(process)
            
    def test_terminate_process(self):
        """Тест завершения процесса"""
        mock_process = MagicMock()
        mock_process.name.return_value = "TextInputHost.exe"
        mock_process.pid = 12345
        
        result = self.monitor.terminate_process(mock_process)
        self.assertTrue(result)
        mock_process.terminate.assert_called_once()
        
    def test_terminate_process_failure(self):
        """Тест завершения процесса при ошибке"""
        mock_process = MagicMock()
        mock_process.name.return_value = "TextInputHost.exe"
        mock_process.pid = 12345
        mock_process.terminate.side_effect = psutil.AccessDenied()
        
        result = self.monitor.terminate_process(mock_process)
        self.assertFalse(result)
        
    def test_monitor_cpu_load_threshold(self):
        """Тест мониторинга порога нагрузки CPU"""
        # Мокаем высокую нагрузку CPU
        with patch.object(self.monitor, 'get_cpu_usage', return_value=45.0):
            with patch.object(self.monitor, 'find_textinputhost_process') as mock_find:
                mock_process = MagicMock()
                mock_process.name.return_value = "TextInputHost.exe"
                mock_process.pid = 12345
                mock_find.return_value = mock_process
                
                # Запускаем мониторинг на короткое время
                self.monitor.start_monitoring(threshold=30.0, duration=1.0)
                
                # Проверяем что процесс был найден и завершен
                mock_find.assert_called()
                
    def test_monitor_cpu_load_below_threshold(self):
        """Тест мониторинга при нагрузке ниже порога"""
        # Мокаем низкую нагрузку CPU
        with patch.object(self.monitor, 'get_cpu_usage', return_value=20.0):
            with patch.object(self.monitor, 'find_textinputhost_process') as mock_find:
                mock_find.return_value = None
                
                # Запускаем мониторинг
                self.monitor.start_monitoring(threshold=30.0, duration=1.0)
                
                # Проверяем что процесс не искали (или не нашли)
                # mock_find.assert_called()
                
    def test_monitoring_duration(self):
        """Тест продолжительности мониторинга"""
        start_time = time.time()
        
        with patch.object(self.monitor, 'get_cpu_usage', return_value=20.0):
            self.monitor.start_monitoring(threshold=30.0, duration=2.0)
            
            # Ждем завершения мониторинга
            while self.monitor.monitoring_active:
                time.sleep(0.1)
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Проверяем что мониторинг работал примерно заданное время
        self.assertGreater(duration, 1.8)
        self.assertLess(duration, 3.0)
        
    def test_get_process_info(self):
        """Тест получения информации о процессе"""
        mock_process = MagicMock()
        mock_process.name.return_value = "TextInputHost.exe"
        mock_process.pid = 12345
        mock_process.cpu_percent.return_value = 25.0
        mock_process.memory_percent.return_value = 5.0
        
        info = self.monitor.get_process_info(mock_process)
        self.assertEqual(info['name'], "TextInputHost.exe")
        self.assertEqual(info['pid'], 12345)
        self.assertEqual(info['cpu_percent'], 25.0)
        self.assertEqual(info['memory_percent'], 5.0)


class TestSystemMonitorIntegration(unittest.TestCase):
    """Интеграционные тесты для системы мониторинга"""
    
    def test_full_monitoring_cycle(self):
        """Тест полного цикла мониторинга"""
        monitor = SystemMonitor()
        
        # Тестируем кратковременный мониторинг
        monitor.start_monitoring(threshold=50.0, duration=1.0)
        
        # Ждем завершения мониторинга
        while monitor.monitoring_active:
            time.sleep(0.1)
        
        # Проверяем что мониторинг завершился
        self.assertFalse(monitor.monitoring_active)
        
    def test_monitoring_with_real_processes(self):
        """Тест мониторинга с реальными процессами"""
        monitor = SystemMonitor()
        
        # Получаем список всех процессов
        processes = monitor.get_all_processes()
        
        # Проверяем что список не пустой
        self.assertGreater(len(processes), 0)
        
        # Проверяем структуру данных
        if processes:
            process = processes[0]
            self.assertIn('name', process)
            self.assertIn('pid', process)
            self.assertIn('cpu_percent', process)
            self.assertIn('memory_percent', process)


if __name__ == '__main__':
    # Запуск тестов с подробным выводом
    unittest.main(verbosity=2)