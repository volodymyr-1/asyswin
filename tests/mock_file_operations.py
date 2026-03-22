#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock-объекты для изолированного тестирования
Симуляция файловых операций и системных процессов
"""

import os
import time
import threading
import psutil
import shutil
from typing import List, Dict, Optional
import tempfile
import subprocess


class MockFileOperations:
    """Mock для файловых операций"""
    
    def __init__(self, test_dir: str = None):
        self.test_dir = test_dir or tempfile.mkdtemp(prefix="asyswin_test_")
        self.operations_log = []
        
    def create_test_files(self, count: int = 5):
        """Создать тестовые файлы"""
        source_dir = os.path.join(self.test_dir, "source")
        os.makedirs(source_dir, exist_ok=True)
        
        files = []
        for i in range(count):
            filename = f"test_file_{i}.txt"
            filepath = os.path.join(source_dir, filename)
            
            # Создаем файл с тестовым содержимым
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Test content for file {i}\n")
                f.write(f"Created at: {time.time()}\n")
                f.write("This is test data for automation testing.\n")
            
            files.append(filepath)
            self.operations_log.append({
                'action': 'create_file',
                'file': filepath,
                'timestamp': time.time()
            })
            
        return files
        
    def copy_files(self, source_files: List[str], dest_dir: str = None):
        """Скопировать файлы"""
        if dest_dir is None:
            dest_dir = os.path.join(self.test_dir, "destination")
        os.makedirs(dest_dir, exist_ok=True)
        
        copied_files = []
        for source_file in source_files:
            filename = os.path.basename(source_file)
            dest_file = os.path.join(dest_dir, filename)
            
            shutil.copy2(source_file, dest_file)
            copied_files.append(dest_file)
            
            self.operations_log.append({
                'action': 'copy_file',
                'source': source_file,
                'destination': dest_file,
                'timestamp': time.time()
            })
            
        return copied_files
        
    def move_files(self, source_files: List[str], dest_dir: str):
        """Переместить файлы"""
        os.makedirs(dest_dir, exist_ok=True)
        
        moved_files = []
        for source_file in source_files:
            filename = os.path.basename(source_file)
            dest_file = os.path.join(dest_dir, filename)
            
            shutil.move(source_file, dest_file)
            moved_files.append(dest_file)
            
            self.operations_log.append({
                'action': 'move_file',
                'source': source_file,
                'destination': dest_file,
                'timestamp': time.time()
            })
            
        return moved_files
        
    def delete_files(self, files: List[str]):
        """Удалить файлы"""
        deleted_files = []
        for file_path in files:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(file_path)
                
                self.operations_log.append({
                    'action': 'delete_file',
                    'file': file_path,
                    'timestamp': time.time()
                })
                
        return deleted_files
        
    def create_folders(self, folder_names: List[str]):
        """Создать папки"""
        created_folders = []
        for folder_name in folder_names:
            folder_path = os.path.join(self.test_dir, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            created_folders.append(folder_path)
            
            self.operations_log.append({
                'action': 'create_folder',
                'folder': folder_path,
                'timestamp': time.time()
            })
            
        return created_folders
        
    def delete_folders(self, folders: List[str]):
        """Удалить папки"""
        deleted_folders = []
        for folder_path in folders:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                deleted_folders.append(folder_path)
                
                self.operations_log.append({
                    'action': 'delete_folder',
                    'folder': folder_path,
                    'timestamp': time.time()
                })
                
        return deleted_folders
        
    def get_operations_log(self):
        """Получить лог операций"""
        return self.operations_log.copy()
        
    def clear_log(self):
        """Очистить лог операций"""
        self.operations_log = []
        
    def cleanup(self):
        """Очистка тестовой директории"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        self.operations_log = []


class SystemMonitor:
    """Мониторинг системы и процессов"""
    
    def __init__(self):
        self.monitoring_active = False
        self.monitoring_thread = None
        self.cpu_history = []
        
    def get_cpu_usage(self) -> float:
        """Получить текущую загрузку CPU"""
        return psutil.cpu_percent(interval=1)
        
    def get_memory_usage(self) -> Dict:
        """Получить информацию о памяти"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent,
            'used': memory.used
        }
        
    def find_textinputhost_process(self) -> Optional[psutil.Process]:
        """Найти процесс TextInputHost.exe"""
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'TextInputHost.exe':
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        return None
        
    def terminate_process(self, process: psutil.Process) -> bool:
        """Завершить процесс"""
        try:
            process.terminate()
            # Ждем завершения процесса
            process.wait(timeout=5)
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            return False
            
    def get_process_info(self, process: psutil.Process) -> Dict:
        """Получить информацию о процессе"""
        try:
            return {
                'name': process.name(),
                'pid': process.pid,
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'status': process.status()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}
            
    def get_all_processes(self) -> List[Dict]:
        """Получить список всех процессов"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    if info['name']:  # Исключаем процессы без имени
                        processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
        return processes
        
    def monitor_cpu_threshold(self, threshold: float = 30.0, callback=None):
        """Мониторинг порога CPU"""
        while self.monitoring_active:
            cpu_usage = self.get_cpu_usage()
            self.cpu_history.append(cpu_usage)
            
            # Проверяем порог
            if cpu_usage > threshold:
                process = self.find_textinputhost_process()
                if process:
                    process_info = self.get_process_info(process)
                    if callback:
                        callback(cpu_usage, process_info)
                    self.terminate_process(process)
                    
            time.sleep(1)
            
    def start_monitoring(self, threshold: float = 30.0, duration: float = 60.0):
        """Запустить мониторинг"""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_worker,
            args=(threshold, duration)
        )
        self.monitoring_thread.start()
        
    def _monitoring_worker(self, threshold: float, duration: float):
        """Рабочий процесс мониторинга"""
        start_time = time.time()
        
        while self.monitoring_active and (time.time() - start_time) < duration:
            cpu_usage = self.get_cpu_usage()
            self.cpu_history.append(cpu_usage)
            
            # Проверяем порог
            if cpu_usage > threshold:
                process = self.find_textinputhost_process()
                if process:
                    process_info = self.get_process_info(process)
                    print(f"[MONITOR] ⚠️ CPU {cpu_usage:.1f}% > {threshold}%. Завершаю TextInputHost.exe (PID: {process.pid})")
                    self.terminate_process(process)
                    
            time.sleep(1)
            
        self.monitoring_active = False
        
    def stop_monitoring(self):
        """Остановить мониторинг"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
            
    def get_cpu_history(self) -> List[float]:
        """Получить историю CPU"""
        return self.cpu_history.copy()
        
    def clear_cpu_history(self):
        """Очистить историю CPU"""
        self.cpu_history = []


class MockGeminiAPI:
    """Mock для Gemini API"""
    
    def __init__(self):
        self.responses = []
        
    def analyze_actions(self, actions: List[Dict]) -> Dict:
        """Анализ действий (mock версия)"""
        # Возвращаем mock ответ
        response = {
            "goal": "Automate file operations",
            "subtasks": [
                "Create test files",
                "Copy files between directories", 
                "Move files to destination",
                "Clean up test files"
            ],
            "script_content": '''
import os
import shutil
import time

def automate_file_operations():
    """Automated file operations script"""
    source_dir = "source_files"
    dest_dir = "destination_files"
    
    # Create directories
    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(dest_dir, exist_ok=True)
    
    # Create test files
    for i in range(5):
        with open(f"{source_dir}/file_{i}.txt", "w") as f:
            f.write(f"Test content {i}")
    
    # Copy files
    for filename in os.listdir(source_dir):
        shutil.copy2(f"{source_dir}/{filename}", f"{dest_dir}/{filename}")
    
    # Move files
    for filename in os.listdir(dest_dir):
        shutil.move(f"{dest_dir}/{filename}", f"{source_dir}/{filename}")
    
    print("File operations completed!")

if __name__ == "__main__":
    automate_file_operations()
''',
            "analysis_time": time.time()
        }
        
        self.responses.append(response)
        return response
        
    def get_response_count(self) -> int:
        """Получить количество ответов"""
        return len(self.responses)


class TestEnvironment:
    """Тестовая среда"""
    
    def __init__(self):
        self.file_ops = MockFileOperations()
        self.system_monitor = SystemMonitor()
        self.gemini_mock = MockGeminiAPI()
        
    def setup_test_scenario(self):
        """Настроить тестовый сценарий"""
        # Создаем тестовые файлы
        files = self.file_ops.create_test_files(3)
        
        # Выполняем файловые операции
        copied_files = self.file_ops.copy_files(files)
        moved_files = self.file_ops.move_files(copied_files, os.path.join(self.file_ops.test_dir, "moved"))
        
        return {
            'test_dir': self.file_ops.test_dir,
            'original_files': files,
            'copied_files': copied_files,
            'moved_files': moved_files,
            'operations_log': self.file_ops.get_operations_log()
        }
        
    def cleanup(self):
        """Очистка тестовой среды"""
        self.file_ops.cleanup()
        self.system_monitor.stop_monitoring()


if __name__ == '__main__':
    # Тестирование mock-объектов
    env = TestEnvironment()
    scenario = env.setup_test_scenario()
    
    print("Test scenario created:")
    print(f"Test directory: {scenario['test_dir']}")
    print(f"Original files: {len(scenario['original_files'])}")
    print(f"Copied files: {len(scenario['copied_files'])}")
    print(f"Moved files: {len(scenario['moved_files'])}")
    print(f"Operations: {len(scenario['operations_log'])}")
    
    env.cleanup()
    print("Test environment cleaned up.")