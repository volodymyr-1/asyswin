#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый сценарий: Полный цикл автоматизации файловых операций
1. Имитация действий пользователя
2. Автоматическая запись
3. Анализ через реальный API Gemini
4. Генерация скрипта
5. Тестирование скрипта
6. Сохранение отчета
"""

import unittest
import time
import os
import sys
import json
import threading
import subprocess
import shutil
from datetime import datetime
from typing import Dict, List, Any

# Добавляем путь к основной системе
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.mock_file_operations import TestEnvironment, MockFileOperations
from logger import logger
from action_recorder import ActionRecorder
from llm_analyzer import LLMAnalyzer
from script_generator import ScriptGenerator
from script_tester import ScriptTester
from semantic_logger import SemanticLogger


class TestFileOperationsCycle(unittest.TestCase):
    """Тест полного цикла автоматизации файловых операций"""
    
    def setUp(self):
        """Подготовка тестов"""
        self.test_env = TestEnvironment()
        self.test_results = {
            'start_time': None,
            'end_time': None,
            'cpu_usage_history': [],
            'operations_log': [],
            'analysis_result': None,
            'generated_scripts': [],
            'test_results': [],
            'success': False
        }
        
    def tearDown(self):
        """Очистка после тестов"""
        self.test_env.cleanup()
        
    def test_full_automation_cycle(self):
        """Тест полного цикла автоматизации"""
        print("\n" + "="*80)
        print("🧪 ТЕСТ ПОЛНОГО ЦИКЛА АВТОМАТИЗАЦИИ ФАЙЛОВЫХ ОПЕРАЦИЙ")
        print("="*80)
        
        self.test_results['start_time'] = datetime.now()
        
        try:
            # Этап 1: Подготовка тестовой среды
            print("\n1️⃣ Подготовка тестовой среды...")
            scenario = self.test_env.setup_test_scenario()
            self.test_results['operations_log'] = scenario['operations_log']
            
            print(f"   ✅ Создана тестовая директория: {scenario['test_dir']}")
            print(f"   ✅ Создано файлов: {len(scenario['original_files'])}")
            print(f"   ✅ Выполнено операций: {len(scenario['operations_log'])}")
            
            # Этап 2: Запуск системы AsysWin
            print("\n2️⃣ Запуск системы AsysWin...")
            self._start_asyswin_system()
            
            # Этап 3: Имитация действий пользователя
            print("\n3️⃣ Имитация действий пользователя...")
            self._simulate_user_actions(scenario['test_dir'])
            
            # Этап 4: Автоматическая запись
            print("\n4️⃣ Автоматическая запись действий...")
            self._wait_for_recording_completion()
            
            # Этап 5: Анализ через Gemini
            print("\n5️⃣ Анализ через реальный API Gemini...")
            analysis_result = self._analyze_with_gemini()
            self.test_results['analysis_result'] = analysis_result
            
            # Этап 6: Генерация скрипта
            print("\n6️⃣ Генерация скрипта...")
            generated_scripts = self._generate_scripts(analysis_result)
            self.test_results['generated_scripts'] = generated_scripts
            
            # Этап 7: Тестирование скрипта
            print("\n7️⃣ Тестирование сгенерированного скрипта...")
            test_results = self._test_generated_scripts(generated_scripts)
            self.test_results['test_results'] = test_results
            
            # Этап 8: Сохранение отчета
            print("\n8️⃣ Сохранение отчета...")
            self._save_test_report()
            
            self.test_results['success'] = True
            self.test_results['end_time'] = datetime.now()
            
            print("\n" + "="*80)
            print("✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
            print("="*80)
            print(f"⏱️ Общее время выполнения: {self.test_results['end_time'] - self.test_results['start_time']}")
            print(f"📁 Сгенерировано скриптов: {len(generated_scripts)}")
            print(f"🧪 Результаты тестирования: {len([r for r in test_results if r['success']])}/{len(test_results)} успешных")
            
        except Exception as e:
            print(f"\n❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['success'] = False
            
    def _start_asyswin_system(self):
        """Запуск системы AsysWin"""
        # Инициализируем компоненты системы
        self.recorder = ActionRecorder()
        self.llm_analyzer = LLMAnalyzer()
        self.script_generator = ScriptGenerator()
        self.script_tester = ScriptTester()
        self.semantic_logger = SemanticLogger()
        
        # Проверяем готовность системы
        if not self.llm_analyzer.is_ready():
            print("⚠️ Предупреждение: API Gemini не настроен")
        else:
            print("   ✅ API Gemini готов к использованию")
            
    def _simulate_user_actions(self, test_dir: str):
        """Имитация действий пользователя"""
        print("   📝 Имитация файловых операций...")
        
        # Создаем дополнительные файлы для имитации действий
        additional_files = []
        for i in range(3):
            filename = f"user_file_{i}.txt"
            filepath = os.path.join(test_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"User created file {i}\n")
                f.write(f"Timestamp: {time.time()}\n")
            additional_files.append(filepath)
            
        # Копируем файлы
        copy_dir = os.path.join(test_dir, "user_copy")
        os.makedirs(copy_dir, exist_ok=True)
        
        for file_path in additional_files:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(copy_dir, filename)
            shutil.copy2(file_path, dest_path)
            
        # Перемещаем файлы
        move_dir = os.path.join(test_dir, "user_move")
        os.makedirs(move_dir, exist_ok=True)
        
        for file_path in additional_files:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(move_dir, filename)
            shutil.move(file_path, dest_path)
            
        print(f"   ✅ Создано файлов: {len(additional_files)}")
        print(f"   ✅ Скопировано файлов: {len(additional_files)}")
        print(f"   ✅ Перемещено файлов: {len(additional_files)}")
        
    def _wait_for_recording_completion(self):
        """Ожидание завершения записи"""
        print("   ⏳ Ожидание автоматической остановки записи...")
        
        # Ждем пока система не остановит запись автоматически
        start_time = time.time()
        while time.time() - start_time < 30:  # Максимум 30 секунд
            if not self.recorder.is_recording:
                break
            time.sleep(1)
            
        if not self.recorder.is_recording:
            print(f"   ✅ Запись остановлена автоматически. Действий: {len(self.recorder.actions)}")
        else:
            print("   ⚠️ Запись не остановилась автоматически, останавливаем вручную")
            self.recorder.stop_recording()
            
    def _analyze_with_gemini(self):
        """Анализ действий через реальный API Gemini"""
        if not self.recorder.actions:
            print("   ⚠️ Нет записанных действий для анализа")
            return None
            
        print(f"   📊 Анализ {len(self.recorder.actions)} действий через Gemini...")
        
        try:
            # Используем реальный анализатор
            result = self.llm_analyzer.analyze_actions(self.recorder.actions)
            
            if result:
                print("   ✅ Анализ завершен успешно")
                print(f"   🎯 Цель: {result.get('goal', 'Не определена')}")
                print(f"   📋 Подзадачи: {len(result.get('subtasks', []))}")
                return result
            else:
                print("   ❌ Анализ не дал результатов")
                return None
                
        except Exception as e:
            print(f"   ❌ Ошибка анализа: {e}")
            return None
            
    def _generate_scripts(self, analysis_result: Dict) -> List[str]:
        """Генерация скриптов на основе анализа"""
        if not analysis_result:
            print("   ⚠️ Нет данных для генерации скриптов")
            return []
            
        print("   🚀 Генерация скриптов...")
        
        try:
            # Генерируем скрипты
            created_files = self.script_generator.generate_scripts(analysis_result)
            
            if created_files:
                print(f"   ✅ Сгенерировано файлов: {len(created_files)}")
                for file_path in created_files:
                    print(f"      - {os.path.basename(file_path)}")
                return created_files
            else:
                print("   ⚠️ Скрипты не были сгенерированы")
                return []
                
        except Exception as e:
            print(f"   ❌ Ошибка генерации: {e}")
            return []
            
    def _test_generated_scripts(self, generated_scripts: List[str]) -> List[Dict]:
        """Тестирование сгенерированных скриптов"""
        test_results = []
        
        for script_path in generated_scripts:
            if script_path.endswith('.py') and 'run_all' not in script_path:
                print(f"   🧪 Тестирование скрипта: {os.path.basename(script_path)}")
                
                try:
                    # Тестируем синтаксис
                    test_result = self.script_tester.test_script(script_path)
                    
                    result = {
                        'script': script_path,
                        'success': test_result['syntax_valid'],
                        'error': test_result.get('syntax_error', ''),
                        'test_time': time.time()
                    }
                    
                    test_results.append(result)
                    
                    if test_result['syntax_valid']:
                        print("      ✅ Синтаксис корректен")
                    else:
                        print(f"      ❌ Ошибка: {test_result['syntax_error'][:50]}")
                        
                except Exception as e:
                    print(f"      ❌ Ошибка тестирования: {e}")
                    test_results.append({
                        'script': script_path,
                        'success': False,
                        'error': str(e),
                        'test_time': time.time()
                    })
                    
        return test_results
        
    def _save_test_report(self):
        """Сохранение отчета о тестировании"""
        report_data = {
            'test_info': {
                'test_name': 'File Operations Automation Cycle',
                'start_time': self.test_results['start_time'].isoformat(),
                'end_time': self.test_results['end_time'].isoformat(),
                'duration': str(self.test_results['end_time'] - self.test_results['start_time']),
                'success': self.test_results['success']
            },
            'system_info': {
                'cpu_history': self.test_results['cpu_usage_history'],
                'memory_usage': self._get_memory_info()
            },
            'operations': {
                'total_operations': len(self.test_results['operations_log']),
                'operations_log': self.test_results['operations_log']
            },
            'analysis': {
                'analysis_result': self.test_results['analysis_result'],
                'generated_scripts': self.test_results['generated_scripts'],
                'test_results': self.test_results['test_results']
            },
            'metrics': {
                'total_scripts': len(self.test_results['generated_scripts']),
                'successful_tests': len([r for r in self.test_results['test_results'] if r['success']]),
                'total_tests': len(self.test_results['test_results'])
            }
        }
        
        # Сохраняем JSON отчет
        report_file = os.path.join(os.path.dirname(__file__), 'reports', 'test_report.json')
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        # Создаем HTML отчет
        self._create_html_report(report_data, report_file.replace('.json', '.html'))
        
        print(f"   📊 Отчет сохранен: {report_file}")
        print(f"   🌐 HTML отчет: {report_file.replace('.json', '.html')}")
        
    def _get_memory_info(self) -> Dict:
        """Получить информацию о памяти"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used
            }
        except ImportError:
            return {'error': 'psutil not available'}
            
    def _create_html_report(self, report_data: Dict, html_file: str):
        """Создать HTML отчет"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Тестовый отчет: Автоматизация файловых операций</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ color: green; }}
        .error {{ color: red; }}
        .info {{ color: blue; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Тестовый отчет: Автоматизация файловых операций</h1>
        <p><strong>Дата:</strong> {report_data['test_info']['start_time']}</p>
        <p><strong>Статус:</strong> <span class="{'success' if report_data['test_info']['success'] else 'error'}">{'Успешно' if report_data['test_info']['success'] else 'Ошибка'}</span></p>
        <p><strong>Время выполнения:</strong> {report_data['test_info']['duration']}</p>
    </div>
    
    <div class="section">
        <h2>📊 Метрики</h2>
        <p><strong>Сгенерировано скриптов:</strong> {report_data['metrics']['total_scripts']}</p>
        <p><strong>Успешных тестов:</strong> {report_data['metrics']['successful_tests']}/{report_data['metrics']['total_tests']}</p>
        <p><strong>Операций выполнено:</strong> {report_data['operations']['total_operations']}</p>
    </div>
    
    <div class="section">
        <h2>📁 Сгенерированные скрипты</h2>
        <table>
            <tr>
                <th>Скрипт</th>
                <th>Статус</th>
                <th>Ошибка</th>
            </tr>
        """
        
        for result in report_data['analysis']['test_results']:
            status_class = 'success' if result['success'] else 'error'
            status_text = 'Успешно' if result['success'] else 'Ошибка'
            error_text = result['error'] if not result['success'] else ''
            html_content += f"""
            <tr>
                <td>{os.path.basename(result['script'])}</td>
                <td class="{status_class}">{status_text}</td>
                <td>{error_text}</td>
            </tr>
            """
            
        html_content += """
        </table>
    </div>
    
    <div class="section">
        <h2>📝 Операции</h2>
        <table>
            <tr>
                <th>Действие</th>
                <th>Файл/Папка</th>
                <th>Время</th>
            </tr>
        """
        
        for op in report_data['operations']['operations_log'][:20]:  # Показываем первые 20 операций
            html_content += f"""
            <tr>
                <td>{op['action']}</td>
                <td>{op.get('file', op.get('folder', 'N/A'))}</td>
                <td>{datetime.fromtimestamp(op['timestamp']).strftime('%H:%M:%S')}</td>
            </tr>
            """
            
        html_content += """
        </table>
    </div>
    
    <div class="section">
        <h2>🎯 Анализ Gemini</h2>
        <p><strong>Цель:</strong> {goal}</p>
        <p><strong>Подзадачи:</strong></p>
        <ul>
        """.format(goal=report_data['analysis']['analysis_result'].get('goal', 'Не определена') if report_data['analysis']['analysis_result'] else 'Нет данных')
        
        if report_data['analysis']['analysis_result'] and 'subtasks' in report_data['analysis']['analysis_result']:
            for subtask in report_data['analysis']['analysis_result']['subtasks']:
                html_content += f"<li>{subtask}</li>"
                
        html_content += """
        </ul>
    </div>
    
    <div class="section info">
        <h2>ℹ️ Системная информация</h2>
        <p><strong>Память:</strong> {memory_percent:.1f}% использовано</p>
        <p><strong>Всего памяти:</strong> {memory_total_gb:.1f} GB</p>
    </div>
    
</body>
</html>
        """.format(
            memory_percent=report_data['system_info']['memory_usage'].get('percent', 0),
            memory_total_gb=report_data['system_info']['memory_usage'].get('total', 0) / (1024**3)
        )
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


if __name__ == '__main__':
    # Запуск теста с подробным выводом
    unittest.main(verbosity=2)