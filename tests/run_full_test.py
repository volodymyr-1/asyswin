#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный запускной скрипт для комплексного тестирования
Запускает все тесты и создает полный отчет
"""

import unittest
import sys
import os
import time
import json
import threading
from datetime import datetime
from typing import Dict, List

# Добавляем путь к основной системе
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_cpu_monitoring import TestCPUMonitoring, TestSystemMonitorIntegration
from tests.test_performance_monitoring import TestPerformanceMonitoring, TestTDDApproach
from tests.test_file_operations_cycle import TestFileOperationsCycle
from tests.mock_file_operations import SystemMonitor


class TestRunner:
    """Запускатель тестов с отчетностью"""
    
    def __init__(self):
        self.test_results = {
            'start_time': None,
            'end_time': None,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'error_tests': 0,
            'test_details': [],
            'system_info': {},
            'performance_metrics': {}
        }
        
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("="*80)
        print("🚀 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ AsysWin")
        print("="*80)
        
        self.test_results['start_time'] = datetime.now()
        
        # Сборка тестов
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Добавляем тесты
        suite.addTests(loader.loadTestsFromTestCase(TestCPUMonitoring))
        suite.addTests(loader.loadTestsFromTestCase(TestSystemMonitorIntegration))
        suite.addTests(loader.loadTestsFromTestCase(TestPerformanceMonitoring))
        suite.addTests(loader.loadTestsFromTestCase(TestTDDApproach))
        suite.addTests(loader.loadTestsFromTestCase(TestFileOperationsCycle))
        
        # Запускаем тесты с кастомным результатом
        runner = unittest.TextTestRunner(
            verbosity=2,
            stream=sys.stdout,
            resultclass=CustomTestResult
        )
        
        result = runner.run(suite)
        
        # Сохраняем результаты
        self.test_results['end_time'] = datetime.now()
        self.test_results['total_tests'] = result.testsRun
        self.test_results['passed_tests'] = len(result.successes)
        self.test_results['failed_tests'] = len(result.failures)
        self.test_results['error_tests'] = len(result.errors)
        
        # Собираем детали
        self._collect_test_details(result)
        
        # Собираем системную информацию
        self._collect_system_info()
        
        # Собираем метрики производительности
        self._collect_performance_metrics()
        
        # Создаем отчеты
        self._create_reports()
        
        # Выводим итоги
        self._print_summary()
        
        return result.wasSuccessful()
        
    def _collect_test_details(self, result):
        """Собрать детали тестов"""
        for test, traceback in result.failures:
            self.test_results['test_details'].append({
                'test': str(test),
                'status': 'FAILED',
                'traceback': traceback
            })
            
        for test, traceback in result.errors:
            self.test_results['test_details'].append({
                'test': str(test),
                'status': 'ERROR',
                'traceback': traceback
            })
            
        for test, _ in result.successes:
            self.test_results['test_details'].append({
                'test': str(test),
                'status': 'PASSED',
                'traceback': None
            })
            
    def _collect_system_info(self):
        """Собрать системную информацию"""
        try:
            import psutil
            
            # Информация о CPU
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Информация о памяти
            memory = psutil.virtual_memory()
            
            # Информация о диске
            disk = psutil.disk_usage('/')
            
            self.test_results['system_info'] = {
                'cpu_count': cpu_count,
                'cpu_freq': cpu_freq.current if cpu_freq else 0,
                'memory_total': memory.total,
                'memory_available': memory.available,
                'memory_percent': memory.percent,
                'disk_total': disk.total,
                'disk_used': disk.used,
                'disk_percent': disk.percent
            }
            
        except ImportError:
            self.test_results['system_info'] = {'error': 'psutil not available'}
            
    def _collect_performance_metrics(self):
        """Собрать метрики производительности"""
        monitor = SystemMonitor()
        
        # Измеряем время запуска системы
        start_time = time.time()
        
        # Имитируем нагрузку
        def load_task():
            for _ in range(1000):
                sum(i * i for i in range(100))
                
        load_thread = threading.Thread(target=load_task)
        load_thread.start()
        load_thread.join()
        
        load_time = time.time() - start_time
        
        # Измеряем время мониторинга
        monitor.start_monitoring(threshold=50.0, duration=2.0)
        while monitor.monitoring_active:
            time.sleep(0.1)
            
        monitoring_time = 2.0  # Фиксированная продолжительность
        
        self.test_results['performance_metrics'] = {
            'load_test_time': load_time,
            'monitoring_time': monitoring_time,
            'cpu_history_length': len(monitor.get_cpu_history())
        }
        
    def _create_reports(self):
        """Создать отчеты"""
        # JSON отчет
        json_report = os.path.join(os.path.dirname(__file__), 'reports', 'full_test_report.json')
        os.makedirs(os.path.dirname(json_report), exist_ok=True)
        
        with open(json_report, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2, default=str)
            
        # HTML отчет
        html_report = json_report.replace('.json', '.html')
        self._create_html_report(html_report)
        
        print(f"\n📊 Отчеты сохранены:")
        print(f"   JSON: {json_report}")
        print(f"   HTML: {html_report}")
        
    def _create_html_report(self, html_file: str):
        """Создать HTML отчет"""
        success_rate = (self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Комплексный тестовый отчет AsysWin</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff; }}
        .stat-number {{ font-size: 24px; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; font-size: 12px; text-transform: uppercase; }}
        .success {{ border-left-color: #28a745; }}
        .failed {{ border-left-color: #dc3545; }}
        .error {{ border-left-color: #ffc107; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
        .test-list {{ max-height: 400px; overflow-y: auto; }}
        .test-item {{ padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }}
        .test-item:last-child {{ border-bottom: none; }}
        .status-pas {{ color: #28a745; font-weight: bold; }}
        .status-fail {{ color: #dc3545; font-weight: bold; }}
        .status-error {{ color: #ffc107; font-weight: bold; }}
        .system-info {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
        .metric-item {{ background: #f8f9fa; padding: 10px; border-radius: 5px; }}
        .footer {{ text-align: center; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Комплексный тестовый отчет AsysWin</h1>
            <p><strong>Дата:</strong> {self.test_results['start_time']}</p>
            <p><strong>Статус:</strong> <span class="{'success' if success_rate == 100 else 'failed'}">{'Все тесты пройдены' if success_rate == 100 else f'Частичный успех ({success_rate:.1f}%)'}</span></p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{self.test_results['total_tests']}</div>
                <div class="stat-label">Всего тестов</div>
            </div>
            <div class="stat-card success">
                <div class="stat-number">{self.test_results['passed_tests']}</div>
                <div class="stat-label">Успешные</div>
            </div>
            <div class="stat-card failed">
                <div class="stat-number">{self.test_results['failed_tests']}</div>
                <div class="stat-label">Проваленные</div>
            </div>
            <div class="stat-card error">
                <div class="stat-number">{self.test_results['error_tests']}</div>
                <div class="stat-label">Ошибки</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{success_rate:.1f}%</div>
                <div class="stat-label">Успешность</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{str(self.test_results['end_time'] - self.test_results['start_time'])}</div>
                <div class="stat-label">Время выполнения</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🧪 Детали тестов</h2>
            <div class="test-list">
        """
        
        for test_detail in self.test_results['test_details']:
            status_class = 'status-pas' if test_detail['status'] == 'PASSED' else 'status-fail' if test_detail['status'] == 'FAILED' else 'status-error'
            status_text = '✅ Пройден' if test_detail['status'] == 'PASSED' else '❌ Провален' if test_detail['status'] == 'FAILED' else '⚠️ Ошибка'
            
            html_content += f"""
                <div class="test-item">
                    <div>
                        <strong>{test_detail['test']}</strong>
                    </div>
                    <div class="{status_class}">{status_text}</div>
                </div>
            """
            
        html_content += """
            </div>
        </div>
        
        <div class="section">
            <h2>💻 Системная информация</h2>
            <div class="system-info">
        """
        
        system_info = self.test_results['system_info']
        if 'error' not in system_info:
            html_content += f"""
                <div class="metric-item">
                    <strong>CPU:</strong><br>
                    {system_info['cpu_count']} ядер, {system_info['cpu_freq']:.0f} MHz
                </div>
                <div class="metric-item">
                    <strong>Память:</strong><br>
                    {system_info['memory_total'] / (1024**3):.1f} GB всего<br>
                    {system_info['memory_available'] / (1024**3):.1f} GB доступно<br>
                    {system_info['memory_percent']:.1f}% использовано
                </div>
                <div class="metric-item">
                    <strong>Диск:</strong><br>
                    {system_info['disk_total'] / (1024**3):.1f} GB всего<br>
                    {system_info['disk_used'] / (1024**3):.1f} GB использовано<br>
                    {system_info['disk_percent']:.1f}% заполнено
                </div>
            """
        else:
            html_content += f"<div class='metric-item'>Ошибка получения системной информации: {system_info['error']}</div>"
            
        html_content += """
            </div>
        </div>
        
        <div class="section">
            <h2>⚡ Метрики производительности</h2>
            <div class="system-info">
        """
        
        perf_metrics = self.test_results['performance_metrics']
        html_content += f"""
            <div class="metric-item">
                <strong>Время нагрузочного теста:</strong><br>
                {perf_metrics['load_test_time']:.3f} сек
            </div>
            <div class="metric-item">
                <strong>Время мониторинга:</strong><br>
                {perf_metrics['monitoring_time']:.1f} сек
            </div>
            <div class="metric-item">
                <strong>Измерений CPU:</strong><br>
                {perf_metrics['cpu_history_length']}
            </div>
        """
        
        html_content += """
            </div>
        </div>
        
        <div class="footer">
            <p>Отчет сгенерирован автоматически системой AsysWin</p>
            <p>Для получения дополнительной информации см. JSON отчет</p>
        </div>
    </div>
</body>
</html>
        """
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
    def _print_summary(self):
        """Вывести итоги"""
        print("\n" + "="*80)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
        print("="*80)
        
        success_rate = (self.test_results['passed_tests'] / max(self.test_results['total_tests'], 1)) * 100
        
        print(f"⏱️ Время выполнения: {self.test_results['end_time'] - self.test_results['start_time']}")
        print(f"🧪 Всего тестов: {self.test_results['total_tests']}")
        print(f"✅ Успешные: {self.test_results['passed_tests']}")
        print(f"❌ Проваленные: {self.test_results['failed_tests']}")
        print(f"⚠️ Ошибки: {self.test_results['error_tests']}")
        print(f"📈 Успешность: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        elif success_rate >= 80:
            print("\n✅ ТЕСТИРОВАНИЕ ПРОЙДЕНО ЧАСТИЧНО")
        else:
            print("\n❌ ТЕСТИРОВАНИЕ ПРОВАЛЕНО")
            
        print("\n📁 Отчеты доступны в папке tests/reports/")


class CustomTestResult(unittest.TestResult):
    """Кастомный результат теста для сбора статистики"""
    
    def __init__(self, stream=None, descriptions=None, verbosity=None):
        super().__init__(stream, descriptions, verbosity)
        self.successes = []
        
    def addSuccess(self, test):
        super().addSuccess(test)
        self.successes.append((test, None))


if __name__ == '__main__':
    # Запуск комплексного тестирования
    runner = TestRunner()
    success = runner.run_all_tests()
    
    # Завершаем работу с кодом возврата
    sys.exit(0 if success else 1)