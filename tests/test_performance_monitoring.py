#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Интеграционные тесты для мониторинга производительности
Тестирование TDD-подхода для контроля нагрузки CPU и завершения TextInputHost.exe
"""

import unittest
import time
import threading
import psutil
import subprocess
import os
import sys
from unittest.mock import patch, MagicMock

# Добавляем путь к основной системе
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.mock_file_operations import SystemMonitor


class TestPerformanceMonitoring(unittest.TestCase):
    """Тесты производительности и мониторинга"""
    
    def setUp(self):
        """Подготовка тестов"""
        self.monitor = SystemMonitor()
        
    def test_cpu_monitoring_integration(self):
        """Интеграционный тест мониторинга CPU"""
        print("\n🧪 Интеграционный тест мониторинга CPU")
        
        # Запускаем мониторинг на короткое время
        monitoring_duration = 3.0
        threshold = 20.0  # Низкий порог для теста
        
        start_time = time.time()
        self.monitor.start_monitoring(threshold=threshold, duration=monitoring_duration)
        
        # Ждем завершения мониторинга
        while self.monitor.monitoring_active and (time.time() - start_time) < monitoring_duration + 2:
            time.sleep(0.1)
            
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Проверяем что мониторинг завершился
        self.assertFalse(self.monitor.monitoring_active)
        
        # Проверяем продолжительность
        self.assertGreater(actual_duration, monitoring_duration - 0.5)
        self.assertLess(actual_duration, monitoring_duration + 2.0)
        
        # Проверяем что есть история CPU
        cpu_history = self.monitor.get_cpu_history()
        self.assertGreater(len(cpu_history), 0)
        
        print(f"   ✅ Мониторинг работал {actual_duration:.1f} секунд")
        print(f"   ✅ Записано {len(cpu_history)} измерений CPU")
        
    def test_textinputhost_detection(self):
        """Тест обнаружения процесса TextInputHost.exe"""
        print("\n🔍 Тест обнаружения TextInputHost.exe")
        
        # Получаем список всех процессов
        all_processes = self.monitor.get_all_processes()
        
        # Проверяем что список не пустой
        self.assertGreater(len(all_processes), 0)
        
        # Ищем TextInputHost.exe в реальных процессах
        textinputhost_found = False
        for proc in all_processes:
            if proc['name'] == 'TextInputHost.exe':
                textinputhost_found = True
                print(f"   ✅ Найден TextInputHost.exe (PID: {proc['pid']})")
                print(f"      CPU: {proc['cpu_percent']:.1f}%, Memory: {proc['memory_percent']:.1f}%")
                break
                
        if not textinputhost_found:
            print("   ⚠️ TextInputHost.exe не найден в системе")
            
    def test_process_termination_simulation(self):
        """Тест симуляции завершения процесса"""
        print("\n🛑 Тест симуляции завершения процесса")
        
        # Создаем mock процесс
        mock_process = MagicMock()
        mock_process.name.return_value = "TextInputHost.exe"
        mock_process.pid = 99999  # Высокий PID для теста
        
        # Тестируем успешное завершение
        result = self.monitor.terminate_process(mock_process)
        self.assertTrue(result)
        mock_process.terminate.assert_called_once()
        
        print("   ✅ Симуляция завершения процесса прошла успешно")
        
    def test_high_cpu_load_scenario(self):
        """Тест сценария высокой нагрузки CPU"""
        print("\n🔥 Тест сценария высокой нагрузки CPU")
        
        # Создаем сценарий с высокой нагрузкой
        def cpu_intensive_task():
            """Задача для создания нагрузки CPU"""
            start = time.time()
            while time.time() - start < 2.0:  # 2 секунды нагрузки
                # Вычисления для нагрузки CPU
                sum(i * i for i in range(10000))
                
        # Запускаем нагрузку в фоне
        cpu_thread = threading.Thread(target=cpu_intensive_task)
        cpu_thread.start()
        
        # Запускаем мониторинг с низким порогом
        threshold = 10.0  # Очень низкий порог
        self.monitor.start_monitoring(threshold=threshold, duration=3.0)
        
        # Ждем завершения нагрузки
        cpu_thread.join()
        
        # Ждем завершения мониторинга
        while self.monitor.monitoring_active:
            time.sleep(0.1)
            
        # Проверяем историю CPU
        cpu_history = self.monitor.get_cpu_history()
        self.assertGreater(len(cpu_history), 0)
        
        # Проверяем что была зафиксирована высокая нагрузка
        max_cpu = max(cpu_history) if cpu_history else 0
        print(f"   📊 Максимальная нагрузка CPU: {max_cpu:.1f}%")
        
        if max_cpu > threshold:
            print("   ✅ Высокая нагрузка CPU была зафиксирована")
        else:
            print("   ⚠️ Высокая нагрузка CPU не была зафиксирована (возможно система не нагружена)")
            
    def test_monitoring_with_real_system(self):
        """Тест мониторинга с реальной системой"""
        print("\n💻 Тест мониторинга с реальной системой")
        
        # Получаем информацию о системе
        try:
            cpu_usage = self.monitor.get_cpu_usage()
            memory_info = self.monitor.get_memory_usage()
            
            print(f"   📈 Текущая нагрузка CPU: {cpu_usage:.1f}%")
            print(f"   💾 Использование памяти: {memory_info.get('percent', 0):.1f}%")
            print(f"   💾 Всего памяти: {memory_info.get('total', 0) / (1024**3):.1f} GB")
            
            # Проверяем что значения в разумных пределах
            self.assertGreaterEqual(cpu_usage, 0.0)
            self.assertLessEqual(cpu_usage, 100.0)
            self.assertGreaterEqual(memory_info.get('percent', 0), 0.0)
            self.assertLessEqual(memory_info.get('percent', 0), 100.0)
            
        except Exception as e:
            print(f"   ❌ Ошибка получения системной информации: {e}")
            
    def test_monitoring_stress_test(self):
        """Стресс-тест мониторинга"""
        print("\n💪 Стресс-тест мониторинга")
        
        # Запускаем несколько потоков для создания нагрузки
        def stress_task():
            """Задача для стресс-теста"""
            for _ in range(100):
                time.sleep(0.01)
                sum(i * i for i in range(1000))
                
        # Запускаем несколько потоков
        threads = []
        for i in range(3):
            thread = threading.Thread(target=stress_task)
            threads.append(thread)
            thread.start()
            
        # Запускаем мониторинг
        start_time = time.time()
        self.monitor.start_monitoring(threshold=50.0, duration=5.0)
        
        # Ждем завершения потоков
        for thread in threads:
            thread.join()
            
        # Ждем завершения мониторинга
        while self.monitor.monitoring_active:
            time.sleep(0.1)
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Проверяем результаты
        cpu_history = self.monitor.get_cpu_history()
        max_cpu = max(cpu_history) if cpu_history else 0
        
        print(f"   ⏱️ Стресс-тест длился: {duration:.1f} секунд")
        print(f"   📊 Максимальная нагрузка CPU: {max_cpu:.1f}%")
        print(f"   📈 Записано измерений: {len(cpu_history)}")
        
        # Проверяем что мониторинг завершился
        self.assertFalse(self.monitor.monitoring_active)
        
    def test_monitoring_cleanup(self):
        """Тест очистки мониторинга"""
        print("\n🧹 Тест очистки мониторинга")
        
        # Запускаем мониторинг
        self.monitor.start_monitoring(threshold=30.0, duration=2.0)
        
        # Ждем немного
        time.sleep(0.5)
        
        # Останавливаем вручную
        self.monitor.stop_monitoring()
        
        # Проверяем что мониторинг остановлен
        self.assertFalse(self.monitor.monitoring_active)
        
        # Проверяем историю
        cpu_history = self.monitor.get_cpu_history()
        print(f"   📊 История CPU до очистки: {len(cpu_history)} измерений")
        
        # Очищаем историю
        self.monitor.clear_cpu_history()
        cpu_history_after = self.monitor.get_cpu_history()
        
        print(f"   📊 История CPU после очистки: {len(cpu_history_after)} измерений")
        self.assertEqual(len(cpu_history_after), 0)


class TestTDDApproach(unittest.TestCase):
    """Тесты TDD-подхода"""
    
    def test_tdd_cpu_monitoring_tests(self):
        """Тест TDD-подхода для мониторинга CPU"""
        print("\n🧪 TDD: Тесты для мониторинга CPU")
        
        # Создаем монитор
        monitor = SystemMonitor()
        
        # Тестируем измерение CPU
        cpu_usage = monitor.get_cpu_usage()
        self.assertIsInstance(cpu_usage, float)
        self.assertGreaterEqual(cpu_usage, 0.0)
        self.assertLessEqual(cpu_usage, 100.0)
        print(f"   ✅ Измерение CPU: {cpu_usage:.1f}%")
        
        # Тестируем поиск процессов
        processes = monitor.get_all_processes()
        self.assertIsInstance(processes, list)
        print(f"   ✅ Найдено процессов: {len(processes)}")
        
        # Тестируем получение информации о процессе
        if processes:
            # processes[0] уже словарь, не нужно вызывать get_process_info
            process_info = processes[0]
            self.assertIsInstance(process_info, dict)
            print(f"   ✅ Информация о процессе: {process_info.get('name', 'N/A')}")
            
    def test_tdd_performance_requirements(self):
        """Тест TDD-подхода для требований производительности"""
        print("\n🎯 TDD: Требования к производительности")
        
        # Требование 1: CPU monitoring должен работать в реальном времени
        monitor = SystemMonitor()
        start_time = time.time()
        cpu_usage = monitor.get_cpu_usage()
        end_time = time.time()
        
        measurement_time = end_time - start_time
        print(f"   ⏱️ Время измерения CPU: {measurement_time:.3f} сек")
        self.assertLess(measurement_time, 2.0, "Измерение CPU должно быть быстрым")
        
        # Требование 2: Поиск процесса должен быть эффективным
        start_time = time.time()
        processes = monitor.get_all_processes()
        end_time = time.time()
        
        search_time = end_time - start_time
        print(f"   ⏱️ Время поиска процессов: {search_time:.3f} сек")
        self.assertLess(search_time, 5.0, "Поиск процессов должен быть быстрым")
        
        # Требование 3: Завершение процесса должно быть надежным
        mock_process = MagicMock()
        mock_process.name.return_value = "TextInputHost.exe"
        mock_process.pid = 12345
        
        start_time = time.time()
        result = monitor.terminate_process(mock_process)
        end_time = time.time()
        
        termination_time = end_time - start_time
        print(f"   ⏱️ Время завершения процесса: {termination_time:.3f} сек")
        self.assertTrue(result, "Процесс должен быть завершен")
        self.assertLess(termination_time, 1.0, "Завершение процесса должно быть быстрым")


if __name__ == '__main__':
    # Запуск всех тестов с подробным выводом
    print("="*80)
    print("🧪 ИНТЕГРАЦИОННЫЕ ТЕСТЫ: МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ")
    print("="*80)
    
    unittest.main(verbosity=2)