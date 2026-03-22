#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенный анимированный робот-ассистент
Профессиональная графика, плавные анимации, звуковые эффекты
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import math
import random
from PIL import Image, ImageDraw, ImageTk, ImageFilter
import pygame  # Для звуковых эффектов


class EnhancedRobotWidget(tk.Frame):
    """Улучшенный анимированный робот-ассистент"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.canvas = None
        self.robot_parts = {}
        self.animations = {}
        self.current_state = "idle"
        self.target_state = "idle"
        self.animation_progress = 0
        self.is_animating = False
        
        # Загрузка звуков
        self.load_sounds()
        
        # Создание робота
        self.create_robot()
        
        # Запуск анимаций
        self.start_animations()
        
    def load_sounds(self):
        """Загрузка звуковых эффектов"""
        try:
            pygame.mixer.init()
            self.sounds = {
                'startup': self.create_sound_effect('startup'),
                'beep': self.create_sound_effect('beep'),
                'success': self.create_sound_effect('success'),
                'error': self.create_sound_effect('error'),
                'recording': self.create_sound_effect('recording'),
                'analyzing': self.create_sound_effect('analyzing')
            }
        except:
            self.sounds = {}
            
    def create_sound_effect(self, sound_type):
        """Создание звукового эффекта"""
        try:
            import pygame.sndarray
            import numpy as np
            
            # Создаем простые звуковые эффекты
            if sound_type == 'startup':
                # Восходящая синусоида
                duration = 0.5
                frequency = 440
                sample_rate = 44100
                samples = int(duration * sample_rate)
                wave = np.sin(2 * np.pi * np.arange(samples) * frequency / sample_rate)
                wave = (wave * 32767).astype(np.int16)
                return pygame.sndarray.make_sound(wave)
                
            elif sound_type == 'beep':
                # Короткий писк
                duration = 0.1
                frequency = 880
                sample_rate = 44100
                samples = int(duration * sample_rate)
                wave = np.sin(2 * np.pi * np.arange(samples) * frequency / sample_rate)
                wave = (wave * 32767).astype(np.int16)
                return pygame.sndarray.make_sound(wave)
                
            elif sound_type == 'success':
                # Радостная мелодия
                duration = 0.3
                frequencies = [523, 659, 784, 1047]  # C5, E5, G5, C6
                sample_rate = 44100
                wave = np.array([])
                for freq in frequencies:
                    samples = int(duration/4 * sample_rate)
                    part = np.sin(2 * np.pi * np.arange(samples) * freq / sample_rate)
                    wave = np.concatenate([wave, part])
                wave = (wave * 32767).astype(np.int16)
                return pygame.sndarray.make_sound(wave)
                
            elif sound_type == 'error':
                # Низкий звук ошибки
                duration = 0.5
                frequency = 110
                sample_rate = 44100
                samples = int(duration * sample_rate)
                wave = np.sin(2 * np.pi * np.arange(samples) * frequency / sample_rate)
                wave = (wave * 32767).astype(np.int16)
                return pygame.sndarray.make_sound(wave)
                
        except:
            return None
            
    def create_robot(self):
        """Создание улучшенного робота"""
        # Создаем холст для робота
        self.canvas = tk.Canvas(
            self, 
            width=300, 
            height=300,
            bg='#2c3e50',  # Используем цвет тела робота как фон
            highlightthickness=0
        )
        self.canvas.pack(expand=True, fill='both')
        
        # Создаем робота с градиентами и тенями
        self.draw_robot()
        
    def draw_robot(self):
        """Рисование робота с улучшенной графикой"""
        # Основные цвета
        body_color = '#2c3e50'
        head_color = '#34495e'
        accent_color = '#3498db'
        eye_color = '#e74c3c'
        
        # Тело робота
        self.robot_parts['body'] = self.canvas.create_oval(
            80, 120, 220, 260,
            fill=body_color,
            outline='#1a252f',
            width=3
        )
        
        # Голова робота
        self.robot_parts['head'] = self.canvas.create_oval(
            100, 60, 200, 140,
            fill=head_color,
            outline='#2c3e50',
            width=3
        )
        
        # Глаза робота
        self.robot_parts['left_eye'] = self.canvas.create_oval(
            120, 85, 140, 105,
            fill=eye_color,
            outline='#000000'
        )
        
        self.robot_parts['right_eye'] = self.canvas.create_oval(
            160, 85, 180, 105,
            fill=eye_color,
            outline='#000000'
        )
        
        # Рот робота (будет анимироваться)
        self.robot_parts['mouth'] = self.canvas.create_line(
            130, 120, 170, 120,
            fill='#ffffff',
            width=2
        )
        
        # Антенна
        self.robot_parts['antenna'] = self.canvas.create_line(
            150, 60, 150, 40,
            fill=accent_color,
            width=2
        )
        
        self.robot_parts['antenna_tip'] = self.canvas.create_oval(
            145, 35, 155, 45,
            fill=accent_color,
            outline='#000000'
        )
        
        # Руки
        self.robot_parts['left_arm'] = self.canvas.create_line(
            80, 160, 60, 180,
            fill=body_color,
            width=8,
            capstyle='round'
        )
        
        self.robot_parts['right_arm'] = self.canvas.create_line(
            220, 160, 240, 180,
            fill=body_color,
            width=8,
            capstyle='round'
        )
        
        # Ноги
        self.robot_parts['left_leg'] = self.canvas.create_line(
            120, 260, 110, 290,
            fill=body_color,
            width=8,
            capstyle='round'
        )
        
        self.robot_parts['right_leg'] = self.canvas.create_line(
            180, 260, 190, 290,
            fill=body_color,
            width=8,
            capstyle='round'
        )
        
        # Свечение вокруг робота
        self.robot_parts['glow'] = self.canvas.create_oval(
            70, 110, 230, 270,
            outline='',
            fill=''
        )
        
        # Создаем градиентное свечение
        self.create_glow_effect()
        
    def create_glow_effect(self):
        """Создание эффекта свечения"""
        # Создаем изображение для градиента
        width, height = 300, 300
        gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)
        
        # Рисуем градиентное свечение
        for i in range(20):
            alpha = max(0, 100 - i * 5)
            color = (52, 152, 219, alpha)
            draw.ellipse(
                [70 - i, 110 - i, 230 + i, 270 + i],
                outline=color
            )
        
        # Конвертируем в PhotoImage
        self.glow_image = ImageTk.PhotoImage(gradient)
        self.robot_parts['glow_img'] = self.canvas.create_image(150, 190, image=self.glow_image)
        
    def start_animations(self):
        """Запуск анимаций"""
        self.animation_loop()
        
    def animation_loop(self):
        """Главный цикл анимаций"""
        if self.is_animating:
            self.update_animation()
        
        # Дыхательная анимация (плавное масштабирование)
        self.breathing_animation()
        
        # Мигание глаз
        self.blink_animation()
        
        # Свечение антенны
        self.antenna_glow()
        
        self.parent.after(50, self.animation_loop)
        
    def breathing_animation(self):
        """Анимация "дыхания" - плавное масштабирование"""
        scale = 1 + 0.02 * math.sin(time.time() * 2)
        
        # Масштабируем все части робота
        for part_id in self.robot_parts.values():
            if isinstance(part_id, int):  # Это canvas item
                coords = self.canvas.coords(part_id)
                if len(coords) >= 4:
                    cx, cy = 150, 190  # Центр робота
                    new_coords = []
                    for i in range(0, len(coords), 2):
                        x, y = coords[i], coords[i+1]
                        new_x = cx + (x - cx) * scale
                        new_y = cy + (y - cy) * scale
                        new_coords.extend([new_x, new_y])
                    self.canvas.coords(part_id, *new_coords)
                    
    def blink_animation(self):
        """Анимация мигания глаз"""
        current_time = time.time()
        
        # Мигаем каждые 3-5 секунд
        if current_time % 4 < 0.1:
            # Закрываем глаза
            self.canvas.itemconfig(self.robot_parts['left_eye'], state='hidden')
            self.canvas.itemconfig(self.robot_parts['right_eye'], state='hidden')
        else:
            # Открываем глаза
            self.canvas.itemconfig(self.robot_parts['left_eye'], state='normal')
            self.canvas.itemconfig(self.robot_parts['right_eye'], state='normal')
            
    def antenna_glow(self):
        """Анимация свечения антенны"""
        glow_intensity = 0.5 + 0.5 * math.sin(time.time() * 4)
        
        # Меняем цвет антенны в зависимости от "активности"
        if self.current_state == 'analyzing':
            color = f'#{int(255*glow_intensity):02x}{int(100*glow_intensity):02x}00'
        elif self.current_state == 'recording':
            color = f'#00{int(255*glow_intensity):02x}00'
        else:
            color = f'#00{int(100*glow_intensity):02x}{int(255*glow_intensity):02x}'
            
        self.canvas.itemconfig(self.robot_parts['antenna'], fill=color)
        self.canvas.itemconfig(self.robot_parts['antenna_tip'], fill=color)
        
    def update_animation(self):
        """Обновление анимации перехода между состояниями"""
        if self.animation_progress < 1:
            self.animation_progress += 0.1
            
            # Интерполируем между состояниями
            if self.target_state == 'speaking':
                self.animate_speaking()
            elif self.target_state == 'recording':
                self.animate_recording()
            elif self.target_state == 'analyzing':
                self.animate_analyzing()
            elif self.target_state == 'happy':
                self.animate_happy()
            elif self.target_state == 'error':
                self.animate_error()
                
            if self.animation_progress >= 1:
                self.is_animating = False
                self.current_state = self.target_state
                
    def animate_speaking(self):
        """Анимация "говорит" - движение рта"""
        mouth_y = 120 + 5 * math.sin(time.time() * 10)
        
        # Двигаем рот вверх-вниз
        self.canvas.coords(self.robot_parts['mouth'], 130, mouth_y, 170, mouth_y)
        
        # Мигаем глазами быстрее
        if time.time() % 0.5 < 0.1:
            self.canvas.itemconfig(self.robot_parts['left_eye'], state='hidden')
            self.canvas.itemconfig(self.robot_parts['right_eye'], state='hidden')
        else:
            self.canvas.itemconfig(self.robot_parts['left_eye'], state='normal')
            self.canvas.itemconfig(self.robot_parts['right_eye'], state='normal')
            
    def animate_recording(self):
        """Анимация "запись" - вращение антенны"""
        angle = time.time() * 2
        
        # Вращаем антенну
        cx, cy = 150, 60
        x = cx + 20 * math.cos(angle)
        y = cy + 20 * math.sin(angle)
        
        self.canvas.coords(self.robot_parts['antenna'], 150, 60, x, y)
        
        # Меняем цвет глаз на зеленый
        self.canvas.itemconfig(self.robot_parts['left_eye'], fill='#2ecc71')
        self.canvas.itemconfig(self.robot_parts['right_eye'], fill='#2ecc71')
        
    def animate_analyzing(self):
        """Анимация "анализ" - пульсация"""
        scale = 1 + 0.1 * math.sin(time.time() * 5)
        
        # Пульсируем телом
        for part_id in [self.robot_parts['body'], self.robot_parts['head']]:
            coords = self.canvas.coords(part_id)
            cx, cy = 150, 190
            new_coords = []
            for i in range(0, len(coords), 2):
                x, y = coords[i], coords[i+1]
                new_x = cx + (x - cx) * scale
                new_y = cy + (y - cy) * scale
                new_coords.extend([new_x, new_y])
            self.canvas.coords(part_id, *new_coords)
            
        # Меняем цвет на синий
        self.canvas.itemconfig(self.robot_parts['left_eye'], fill='#3498db')
        self.canvas.itemconfig(self.robot_parts['right_eye'], fill='#3498db')
        
    def animate_happy(self):
        """Анимация "радость" - прыжки"""
        jump_height = 10 * math.sin(time.time() * 4)
        
        # Подпрыгиваем
        for part_id in self.robot_parts.values():
            if isinstance(part_id, int):
                coords = self.canvas.coords(part_id)
                new_coords = [c for c in coords]
                for i in range(1, len(new_coords), 2):
                    new_coords[i] -= jump_height
                self.canvas.coords(part_id, *new_coords)
                
        # Радужные глаза
        hue = (time.time() * 50) % 360
        color = self.hsv_to_hex(hue, 1, 1)
        self.canvas.itemconfig(self.robot_parts['left_eye'], fill=color)
        self.canvas.itemconfig(self.robot_parts['right_eye'], fill=color)
        
    def animate_error(self):
        """Анимация "ошибка" - тряска"""
        shake = random.randint(-3, 3)
        
        # Трясем роботом
        for part_id in self.robot_parts.values():
            if isinstance(part_id, int):
                coords = self.canvas.coords(part_id)
                new_coords = [c + shake for c in coords]
                self.canvas.coords(part_id, *new_coords)
                
        # Красные глаза
        self.canvas.itemconfig(self.robot_parts['left_eye'], fill='#e74c3c')
        self.canvas.itemconfig(self.robot_parts['right_eye'], fill='#e74c3c')
        
    def hsv_to_hex(self, h, s, v):
        """Конвертация HSV в HEX цвет"""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h/360, s, v)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
        
    def set_state(self, state, message=""):
        """Установка состояния робота"""
        if state != self.current_state:
            self.target_state = state
            self.animation_progress = 0
            self.is_animating = True
            
            # Проигрываем соответствующий звук
            if state in self.sounds and self.sounds[state]:
                self.sounds[state].play()
                
            # Сбрасываем антенну в исходное положение
            self.canvas.coords(self.robot_parts['antenna'], 150, 60, 150, 40)
            
    def speak(self, text):
        """Робот говорит текст"""
        self.set_state('speaking', text)
        
    def happy(self):
        """Радостное состояние"""
        self.set_state('happy')
        
    def error(self):
        """Состояние ошибки"""
        self.set_state('error')
        
    def recording(self, message=""):
        """Состояние записи"""
        self.set_state('recording', message)
        
    def thinking(self, message=""):
        """Состояние анализа"""
        self.set_state('analyzing', message)
        
    def idle(self):
        """Состояние ожидания"""
        self.set_state('idle')
        
    def destroy(self):
        """Уничтожение робота"""
        if self.canvas:
            self.canvas.destroy()