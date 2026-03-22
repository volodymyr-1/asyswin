"""
Анимированный робот Eilik - ассистент AsysWin
Рисуется на Canvas с анимациями и эмоциями
"""

import tkinter as tk
import math
import time
import threading
from typing import Optional, Callable


class EilikRobot:
    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.canvas = None
        self.state = "idle"
        self.message = ""
        self.animation_id = None
        self.frame = 0
        
        # Цвета робота
        self.colors = {
            "body": "#4A90D9",      # Синий корпус
            "body_dark": "#3570B0",  # Тёмно-синий
            "eyes": "#FFFFFF",       # Белые глаза
            "pupils": "#1A1A1A",     # Чёрные зрачки
            "mouth": "#FF6B6B",      # Розовый рот
            "hands": "#4A90D9",      # Руки
            "antenna": "#FFD700",    # Жёлтая антенна
            "glow": "#00FF88",       # Зелёное свечение
        }
        
        # Состояния анимации
        self.animations = {
            "idle": self._animate_idle,
            "recording": self._animate_recording,
            "thinking": self._animate_thinking,
            "happy": self._animate_happy,
            "error": self._animate_error,
            "speaking": self._animate_speaking,
        }
        
    def create(self, width: int = 200, height: int = 280):
        """Создать Canvas с роботом"""
        self.canvas = tk.Canvas(
            self.parent,
            width=width,
            height=height,
            bg="#1a1a2e",
            highlightthickness=0
        )
        self.canvas.pack(pady=10)
        
        # Запускаем анимацию
        self._start_animation()
        
        return self.canvas
        
    def set_state(self, state: str, message: str = ""):
        """Установить состояние робота"""
        if state in self.animations:
            self.state = state
            self.message = message
            self.frame = 0
            
    def _start_animation(self):
        """Запустить цикл анимации"""
        if self.canvas:
            self._animate()
            
    def _animate(self):
        """Главный цикл анимации"""
        if not self.canvas:
            return
            
        self.canvas.delete("all")
        
        # Рисуем робота в зависимости от состояния
        if self.state in self.animations:
            self.animations[self.state]()
        else:
            self._animate_idle()
            
        # Рисуем сообщение
        if self.message:
            self._draw_speech_bubble(self.message)
            
        self.frame += 1
        self.animation_id = self.canvas.after(50, self._animate)
        
    def _draw_robot_base(self, x: int, y: int, body_offset: int = 0):
        """Базовая форма робота"""
        # Тень
        self.canvas.create_oval(
            x - 35, y + 75, x + 35, y + 85,
            fill="#000000", stipple="gray50", outline=""
        )
        
        # Тело
        body_y = y + body_offset
        self.canvas.create_rounded_rectangle(
            x - 40, body_y - 50, x + 40, body_y + 50,
            radius=20, fill=self.colors["body"], outline=self.colors["body_dark"], width=3
        )
        
        # Живот (панель)
        self.canvas.create_rounded_rectangle(
            x - 25, body_y - 10, x + 25, body_y + 30,
            radius=10, fill=self.colors["body_dark"], outline=""
        )
        
        # Индикатор на животе
        glow_color = self.colors["glow"] if self.state == "recording" else "#666666"
        self.canvas.create_oval(
            x - 8, body_y + 5, x + 8, body_y + 20,
            fill=glow_color, outline=""
        )
        
        return x, body_y
        
    def _draw_head(self, x: int, y: int, head_offset: int = 0, eye_state: str = "open"):
        """Голова робота"""
        head_y = y - 60 + head_offset
        
        # Голова
        self.canvas.create_rounded_rectangle(
            x - 35, head_y - 30, x + 35, head_y + 30,
            radius=15, fill=self.colors["body"], outline=self.colors["body_dark"], width=3
        )
        
        # Антенна
        antenna_sway = math.sin(self.frame * 0.1) * 5
        self.canvas.create_line(
            x, head_y - 30, x + antenna_sway, head_y - 50,
            fill=self.colors["antenna"], width=3
        )
        self.canvas.create_oval(
            x + antenna_sway - 5, head_y - 55, x + antenna_sway + 5, head_y - 45,
            fill=self.colors["antenna"], outline=""
        )
        
        # Глаза
        if eye_state == "open":
            # Левый глаз
            self.canvas.create_oval(
                x - 22, head_y - 15, x - 8, head_y + 5,
                fill=self.colors["eyes"], outline=self.colors["body_dark"], width=2
            )
            self.canvas.create_oval(
                x - 18, head_y - 8, x - 12, head_y + 2,
                fill=self.colors["pupils"], outline=""
            )
            
            # Правый глаз
            self.canvas.create_oval(
                x + 8, head_y - 15, x + 22, head_y + 5,
                fill=self.colors["eyes"], outline=self.colors["body_dark"], width=2
            )
            self.canvas.create_oval(
                x + 12, head_y - 8, x + 18, head_y + 2,
                fill=self.colors["pupils"], outline=""
            )
        elif eye_state == "happy":
            # Счастливые глаза (дуги)
            self.canvas.create_arc(
                x - 22, head_y - 15, x - 8, head_y + 5,
                start=0, extent=180, style="arc",
                outline=self.colors["pupils"], width=3
            )
            self.canvas.create_arc(
                x + 8, head_y - 15, x + 22, head_y + 5,
                start=0, extent=180, style="arc",
                outline=self.colors["pupils"], width=3
            )
        elif eye_state == "thinking":
            # Задумчивые глаза (смотрят вверх)
            self.canvas.create_oval(
                x - 22, head_y - 15, x - 8, head_y + 5,
                fill=self.colors["eyes"], outline=self.colors["body_dark"], width=2
            )
            self.canvas.create_oval(
                x - 18, head_y - 12, x - 12, head_y - 2,
                fill=self.colors["pupils"], outline=""
            )
            
            self.canvas.create_oval(
                x + 8, head_y - 15, x + 22, head_y + 5,
                fill=self.colors["eyes"], outline=self.colors["body_dark"], width=2
            )
            self.canvas.create_oval(
                x + 12, head_y - 12, x + 18, head_y - 2,
                fill=self.colors["pupils"], outline=""
            )
            
        # Рот
        if self.state == "happy":
            # Улыбка
            self.canvas.create_arc(
                x - 12, head_y + 8, x + 12, head_y + 22,
                start=0, extent=-180, style="arc",
                outline=self.colors["mouth"], width=3
            )
        elif self.state == "error":
            # Грустный рот
            self.canvas.create_arc(
                x - 12, head_y + 15, x + 12, head_y + 25,
                start=0, extent=180, style="arc",
                outline=self.colors["mouth"], width=3
            )
        else:
            # Нейтральный рот
            self.canvas.create_line(
                x - 8, head_y + 15, x + 8, head_y + 15,
                fill=self.colors["mouth"], width=3
            )
            
        return x, head_y
        
    def _draw_hands(self, x: int, y: int, left_angle: int = 0, right_angle: int = 0):
        """Руки робота"""
        # Левая рука
        left_hand_x = x - 50 + math.cos(math.radians(left_angle)) * 20
        left_hand_y = y - 10 + math.sin(math.radians(left_angle)) * 20
        
        self.canvas.create_line(
            x - 40, y - 10, left_hand_x, left_hand_y,
            fill=self.colors["hands"], width=8, capstyle="round"
        )
        self.canvas.create_oval(
            left_hand_x - 8, left_hand_y - 8, left_hand_x + 8, left_hand_y + 8,
            fill=self.colors["hands"], outline=self.colors["body_dark"], width=2
        )
        
        # Правая рука
        right_hand_x = x + 50 + math.cos(math.radians(right_angle)) * 20
        right_hand_y = y - 10 + math.sin(math.radians(right_angle)) * 20
        
        self.canvas.create_line(
            x + 40, y - 10, right_hand_x, right_hand_y,
            fill=self.colors["hands"], width=8, capstyle="round"
        )
        self.canvas.create_oval(
            right_hand_x - 8, right_hand_y - 8, right_hand_x + 8, right_hand_y + 8,
            fill=self.colors["hands"], outline=self.colors["body_dark"], width=2
        )
        
    def _draw_speech_bubble(self, text: str):
        """Нарисовать спич-баллон"""
        x, y = 100, 30
        
        # Размеры баллона
        text_width = len(text) * 7 + 20
        bubble_width = max(100, text_width)
        bubble_height = 40
        
        # Фон баллона
        self.canvas.create_rounded_rectangle(
            x - bubble_width//2, y - bubble_height//2,
            x + bubble_width//2, y + bubble_height//2,
            radius=15, fill="#FFFFFF", outline="#333333", width=2
        )
        
        # Хвостик баллона
        self.canvas.create_polygon(
            x - 10, y + bubble_height//2,
            x, y + bubble_height//2 + 15,
            x + 10, y + bubble_height//2,
            fill="#FFFFFF", outline="#333333", width=2
        )
        
        # Текст
        self.canvas.create_text(
            x, y, text=text,
            fill="#333333", font=("Segoe UI", 10, "bold"),
            width=bubble_width - 20
        )
        
    def _animate_idle(self):
        """Анимация покоя"""
        x, y = 100, 150
        
        # Лёгкое покачивание
        body_offset = math.sin(self.frame * 0.05) * 3
        head_offset = math.sin(self.frame * 0.07) * 2
        
        self._draw_robot_base(x, y, body_offset)
        self._draw_head(x, y, head_offset, "open")
        self._draw_hands(x, y, -20, 20)
        
    def _animate_recording(self):
        """Анимация записи"""
        x, y = 100, 150
        
        # Более активное покачивание
        body_offset = math.sin(self.frame * 0.1) * 5
        head_offset = math.sin(self.frame * 0.15) * 3
        
        self._draw_robot_base(x, y, body_offset)
        self._draw_head(x, y, head_offset, "open")
        
        # Руки двигаются
        left_angle = math.sin(self.frame * 0.2) * 30
        right_angle = math.sin(self.frame * 0.2 + math.pi) * 30
        self._draw_hands(x, y, left_angle, right_angle)
        
        # Пульсирующий индикатор
        glow_size = 5 + math.sin(self.frame * 0.3) * 3
        self.canvas.create_oval(
            x - glow_size, y + 5 - glow_size,
            x + glow_size, y + 5 + glow_size,
            fill="#00FF88", outline=""
        )
        
    def _animate_thinking(self):
        """Анимация размышления"""
        x, y = 100, 150
        
        # Покачивание головой
        head_offset = math.sin(self.frame * 0.08) * 4
        
        self._draw_robot_base(x, y, 0)
        self._draw_head(x, y, head_offset, "thinking")
        
        # Рука у "подбородка"
        self._draw_hands(x, y, -60, 10)
        
        # Пузырьки мыслей
        for i in range(3):
            bubble_x = x + 40 + i * 15
            bubble_y = y - 80 - i * 20 + math.sin(self.frame * 0.1 + i) * 5
            size = 5 - i * 1
            self.canvas.create_oval(
                bubble_x - size, bubble_y - size,
                bubble_x + size, bubble_y + size,
                fill="#FFFFFF", outline="#CCCCCC"
            )
            
    def _animate_happy(self):
        """Анимация радости"""
        x, y = 100, 150
        
        # Подпрыгивание
        body_offset = abs(math.sin(self.frame * 0.15)) * -10
        head_offset = abs(math.sin(self.frame * 0.15)) * -8
        
        self._draw_robot_base(x, y, body_offset)
        self._draw_head(x, y, head_offset, "happy")
        
        # Руки вверх
        left_angle = -60 + math.sin(self.frame * 0.2) * 20
        right_angle = -120 + math.sin(self.frame * 0.2) * 20
        self._draw_hands(x, y, left_angle, right_angle)
        
        # Звёздочки
        for i in range(5):
            star_x = x + math.cos(self.frame * 0.1 + i * 1.2) * 60
            star_y = y - 40 + math.sin(self.frame * 0.1 + i * 1.2) * 30
            self._draw_star(star_x, star_y, 5, "#FFD700")
            
    def _animate_error(self):
        """Анимация ошибки"""
        x, y = 100, 150
        
        # Тряска
        shake = math.sin(self.frame * 0.5) * 5
        
        self._draw_robot_base(x + shake, y, 0)
        self._draw_head(x + shake, y, 0, "open")
        self._draw_hands(x + shake, y, -30, -30)
        
        # Красный индикатор
        self.canvas.create_oval(
            x - 8, y + 5, x + 8, y + 20,
            fill="#FF4444", outline=""
        )
        
    def _animate_speaking(self):
        """Анимация говорения"""
        x, y = 100, 150
        
        # Покачивание при разговоре
        body_offset = math.sin(self.frame * 0.12) * 3
        head_offset = math.sin(self.frame * 0.15) * 4
        
        self._draw_robot_base(x, y, body_offset)
        
        # Рот открывается и закрывается
        mouth_open = abs(math.sin(self.frame * 0.3)) * 5
        
        head_y = y - 60 + head_offset
        self.canvas.create_rounded_rectangle(
            x - 35, head_y - 30, x + 35, head_y + 30,
            radius=15, fill=self.colors["body"], outline=self.colors["body_dark"], width=3
        )
        
        # Глаза
        self.canvas.create_oval(
            x - 22, head_y - 15, x - 8, head_y + 5,
            fill=self.colors["eyes"], outline=self.colors["body_dark"], width=2
        )
        self.canvas.create_oval(
            x - 18, head_y - 8, x - 12, head_y + 2,
            fill=self.colors["pupils"], outline=""
        )
        self.canvas.create_oval(
            x + 8, head_y - 15, x + 22, head_y + 5,
            fill=self.colors["eyes"], outline=self.colors["body_dark"], width=2
        )
        self.canvas.create_oval(
            x + 12, head_y - 8, x + 18, head_y + 2,
            fill=self.colors["pupils"], outline=""
        )
        
        # Рот
        self.canvas.create_oval(
            x - 10, head_y + 10 - mouth_open,
            x + 10, head_y + 20 + mouth_open,
            fill=self.colors["mouth"], outline=""
        )
        
        self._draw_hands(x, y, -20, 20)
        
    def _draw_star(self, x: int, y: int, size: int, color: str):
        """Нарисовать звёздочку"""
        points = []
        for i in range(5):
            angle = math.radians(i * 72 - 90)
            points.extend([
                x + math.cos(angle) * size,
                y + math.sin(angle) * size
            ])
            angle = math.radians(i * 72 - 90 + 36)
            points.extend([
                x + math.cos(angle) * size * 0.4,
                y + math.sin(angle) * size * 0.4
            ])
            
        self.canvas.create_polygon(
            points, fill=color, outline=""
        )
        
    def destroy(self):
        """Уничтожить виджет"""
        if self.animation_id:
            self.canvas.after_cancel(self.animation_id)
        if self.canvas:
            self.canvas.destroy()


# Добавляем метод для Canvas (rounded rectangle)
def _create_rounded_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
    """Создать прямоугольник со скруглёнными углами"""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1, x2, y1 + radius,
        x2, y2 - radius,
        x2, y2, x2 - radius, y2,
        x1 + radius, y2,
        x1, y2, x1, y2 - radius,
        x1, y1 + radius,
        x1, y1, x1 + radius, y1
    ]
    return self.create_polygon(points, smooth=True, **kwargs)

tk.Canvas.create_rounded_rectangle = _create_rounded_rectangle