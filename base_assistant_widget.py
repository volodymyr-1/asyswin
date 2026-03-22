"""
Базовый класс для виджетов-ассистентов AsysWin
Содержит общую логику: UI, драг, статус, callbacks
"""

import customtkinter as ctk
import threading
from datetime import datetime
from typing import Callable, Optional
from robot_widget import EilikRobot


class BaseAssistantWidget:
    """
    Базовый класс для всех виджетов-ассистентов
    """

    def __init__(
        self, width: int = 320, height: int = 450, title: str = "AsysWin Assistant"
    ):
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.width = width
        self.height = height
        self.title = title

        self.root: Optional[ctk.CTk] = None
        self.is_visible = False
        self.is_minimized = False
        self.is_ui_ready = False
        self.robot: Optional[EilikRobot] = None

        self.on_toggle_recording: Optional[Callable] = None
        self.on_analyze: Optional[Callable] = None
        self.on_show_predictions: Optional[Callable] = None
        self.on_open_scripts_folder: Optional[Callable] = None
        self.on_open_settings: Optional[Callable] = None

        self.current_status = "ready"
        self.status_label = None
        self.status_indicator = None
        self.record_btn = None
        self.analyze_btn = None
        self.drag_data = {"x": 0, "y": 0}

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        self.root = ctk.CTk()
        self.root.title(self.title)
        self.root.geometry(f"{self.width}x{self.height}")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        try:
            self.root.attributes("-alpha", 0.95)
        except:
            pass

        self.root.overrideredirect(True)
        self._position_window()
        self._create_ui()
        self._setup_drag()

        self.is_visible = True
        self.root.mainloop()

    def _position_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width - self.width - 20
        y = screen_height - self.height - 60
        self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def _create_ui(self):
        main_frame = ctk.CTkFrame(
            self.root,
            corner_radius=15,
            fg_color=("gray95", "gray15"),
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        self._create_header(main_frame)
        self._create_robot(main_frame)
        self._create_status_area(main_frame)
        self._create_action_buttons(main_frame)
        self._create_extra_ui(main_frame)

        self.is_ui_ready = True

    def _create_robot(self, parent):
        """Создать робота - может быть переопределён"""
        self.robot = EilikRobot(parent)
        self.robot.create(200, 200)

    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)

        self._add_header_content(header_frame)

        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.pack(side="right", fill="y")

        settings_btn = ctk.CTkButton(
            controls_frame,
            text="⚙️",
            width=30,
            height=30,
            corner_radius=8,
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"),
            font=ctk.CTkFont(size=14),
            command=self._on_settings_click,
        )
        settings_btn.pack(side="left", padx=2)

        minimize_btn = ctk.CTkButton(
            controls_frame,
            text="─",
            width=30,
            height=30,
            corner_radius=8,
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"),
            font=ctk.CTkFont(size=14),
            command=self._toggle_minimize,
        )
        minimize_btn.pack(side="left", padx=2)

        close_btn = ctk.CTkButton(
            controls_frame,
            text="✕",
            width=30,
            height=30,
            corner_radius=8,
            fg_color=("gray85", "gray25"),
            hover_color=("#ff5555", "#ff5555"),
            font=ctk.CTkFont(size=14),
            command=self.hide,
        )
        close_btn.pack(side="left", padx=2)

    def _add_header_content(self, parent):
        """Добавить контент в заголовок - переопределяется"""
        icon_label = ctk.CTkLabel(parent, text="🤖", font=ctk.CTkFont(size=24))
        icon_label.pack(side="left", padx=(0, 8))

        title_label = ctk.CTkLabel(
            parent, text=self.title, font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(side="left")

    def _create_status_area(self, parent):
        status_frame = ctk.CTkFrame(
            parent, corner_radius=10, fg_color=("gray90", "gray20"), height=60
        )
        status_frame.pack(fill="x", padx=10, pady=5)
        status_frame.pack_propagate(False)

        self.status_indicator = ctk.CTkLabel(
            status_frame, text="●", font=ctk.CTkFont(size=20), text_color="#00ff00"
        )
        self.status_indicator.pack(side="left", padx=(15, 5))

        self.status_label = ctk.CTkLabel(
            status_frame, text="Готов к работе", font=ctk.CTkFont(size=13), anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=5)

    def _create_action_buttons(self, parent):
        buttons_frame = ctk.CTkFrame(parent, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=(5, 10))

        button_style = {
            "corner_radius": 10,
            "height": 40,
            "font": ctk.CTkFont(size=12),
            "border_spacing": 5,
        }

        row1 = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row1.pack(fill="x", pady=2)

        self.record_btn = ctk.CTkButton(
            row1,
            text="🔴 Запись",
            fg_color=("#0078D4", "#0078D4"),
            hover_color=("#106EBE", "#106EBE"),
            command=self._on_record_click,
            **button_style,
        )
        self.record_btn.pack(side="left", fill="x", expand=True, padx=2)

        self.analyze_btn = ctk.CTkButton(
            row1,
            text="📊 Анализ",
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            command=self._on_analyze_click,
            **button_style,
        )
        self.analyze_btn.pack(side="left", fill="x", expand=True, padx=2)

        row2 = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        row2.pack(fill="x", pady=2)

        predictions_btn = ctk.CTkButton(
            row2,
            text="🔮 Сценарии",
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            command=self._on_predictions_click,
            **button_style,
        )
        predictions_btn.pack(side="left", fill="x", expand=True, padx=2)

        folder_btn = ctk.CTkButton(
            row2,
            text="📁 Папка",
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray40"),
            command=self._on_folder_click,
            **button_style,
        )
        folder_btn.pack(side="left", fill="x", expand=True, padx=2)

    def _create_extra_ui(self, parent):
        """Дополнительный UI - переопределяется в наследниках"""
        pass

    def _setup_drag(self):
        self.root.bind("<Button-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._on_drag)

    def _start_drag(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def _on_drag(self, event):
        x = self.root.winfo_x() + (event.x - self.drag_data["x"])
        y = self.root.winfo_y() + (event.y - self.drag_data["y"])
        self.root.geometry(f"+{x}+{y}")

    def _toggle_minimize(self):
        if self.is_minimized:
            self.root.geometry(f"{self.width}x{self.height}")
            self.is_minimized = False
        else:
            self.root.geometry(f"{self.width}x50")
            self.is_minimized = True

    def _update_status(self, status: str, text: str, color: str = "#00ff00"):
        self.current_status = status
        if self.status_label:
            self.status_label.configure(text=text)
        if self.status_indicator:
            self.status_indicator.configure(text_color=color)

    def _on_record_click(self):
        if self.on_toggle_recording:
            self.on_toggle_recording()

    def _on_analyze_click(self):
        if self.on_analyze:
            self.on_analyze()

    def _on_predictions_click(self):
        if self.on_show_predictions:
            self.on_show_predictions()

    def _on_folder_click(self):
        if self.on_open_scripts_folder:
            self.on_open_scripts_folder()

    def _on_settings_click(self):
        if self.on_open_settings:
            self.on_open_settings()

    def set_recording(self, is_recording: bool):
        if not self.is_ui_ready:
            return

        if is_recording:
            self._update_status("recording", "🔴 Запись идёт...", "#ff4444")
            if self.record_btn:
                self.record_btn.configure(
                    text="⏹ Стоп",
                    fg_color=("#ff4444", "#ff4444"),
                    hover_color=("#cc0000", "#cc0000"),
                )
            if self.robot:
                self.robot.set_state("recording", "Записываю действия...")
        else:
            self._update_status("ready", "Готов к работе", "#00ff00")
            if self.record_btn:
                self.record_btn.configure(
                    text="🔴 Запись",
                    fg_color=("#0078D4", "#0078D4"),
                    hover_color=("#106EBE", "#106EBE"),
                )
            if self.robot:
                self.robot.set_state("idle", "Готов к работе!")

    def set_analyzing(self, is_analyzing: bool):
        if not self.is_ui_ready:
            return

        if is_analyzing:
            self._update_status("analyzing", "🔄 Анализ...", "#ffaa00")
            if self.analyze_btn:
                self.analyze_btn.configure(state="disabled")
            if self.robot:
                self.robot.set_state("thinking", "Анализирую действия...")
        else:
            self._update_status("ready", "Готов к работе", "#00ff00")
            if self.analyze_btn:
                self.analyze_btn.configure(state="normal")

    def notify_analysis_complete(self, scripts_count: int):
        if not self.is_ui_ready:
            return

        self._update_status("ready", "Готов к работе", "#00ff00")
        if self.analyze_btn:
            self.analyze_btn.configure(state="normal")
        if self.robot:
            self.robot.set_state("happy", f"Готово! Создал {scripts_count} скриптов!")

    def notify_predictions_ready(self, count: int):
        if not self.is_ui_ready:
            return

        if self.robot:
            self.robot.set_state("happy", f"Нашёл {count} сценариев!")

    def notify_error(self, message: str):
        if not self.is_ui_ready:
            return

        if self.robot:
            self.robot.set_state("error", "Произошла ошибка!")

    def robot_say(self, message: str):
        if not self.is_ui_ready:
            return

        if self.robot:
            self.robot.set_state("speaking", message)

    def show(self):
        if self.root:
            try:
                self.root.deiconify()
                self.is_visible = True
            except:
                pass

    def hide(self):
        if self.root:
            try:
                self.root.withdraw()
                self.is_visible = False
            except:
                pass

    def destroy(self):
        if self.root:
            try:
                self.root.destroy()
            except:
                pass
