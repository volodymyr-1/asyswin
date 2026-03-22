"""
Улучшенный виджет-ассистент с анимированным роботом
Профессиональная графика и анимации
"""

import threading
from typing import TYPE_CHECKING

from base_assistant_widget import BaseAssistantWidget

if TYPE_CHECKING:
    from script_manager import ScriptManager, ScriptInfo


class EnhancedAssistantWidget(BaseAssistantWidget):
    """Улучшенный виджет с EnhancedRobotWidget"""

    def __init__(self):
        super().__init__(width=400, height=600, title="AsysWin Enhanced Assistant")

        self.script_manager = None
        self.recommended_scripts = []
        self.active_provider = "🤖 Gemini Pro"
        self.rec_container = None

        self.theme_colors = {
            "primary": "#3498db",
            "secondary": "#2c3e50",
            "accent": "#e74c3c",
            "success": "#2ecc71",
            "warning": "#f1c40f",
        }

    def _create_robot(self, parent):
        from enhanced_robot_widget import EnhancedRobotWidget

        self.robot = EnhancedRobotWidget(parent)
        self.robot.pack(pady=10)

    def _create_extra_ui(self, parent):
        self._create_recommendations_area(parent)

    def _add_header_content(self, parent):
        from customtkinter import CTkLabel, CTkFont, CTkFrame

        icon_label = CTkLabel(parent, text="🤖", font=CTkFont(size=24))
        icon_label.pack(side="left", padx=(0, 8))

        title_label = CTkLabel(
            parent, text="AsysWin Enhanced", font=CTkFont(size=14, weight="bold")
        )
        title_label.pack(side="left")

        provider_frame = CTkFrame(parent, fg_color="transparent")
        provider_frame.pack(side="left", fill="y")

        provider_label = CTkLabel(
            provider_frame,
            text=self.active_provider,
            font=CTkFont(size=11),
            text_color=("gray50", "gray60"),
        )
        provider_label.pack(side="left", padx=5)

    def _create_recommendations_area(self, parent):
        from customtkinter import (
            CTkFrame,
            CTkLabel,
            CTkButton,
            CTkScrollableFrame,
            CTkFont,
        )

        rec_frame = CTkFrame(
            parent, corner_radius=10, fg_color=("gray92", "gray18"), height=220
        )
        rec_frame.pack(fill="x", padx=10, pady=5)
        rec_frame.pack_propagate(False)

        header_frame = CTkFrame(rec_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_label = CTkLabel(
            header_frame,
            text="🎯 Рекомендуемые скрипты",
            font=CTkFont(size=13, weight="bold"),
        )
        title_label.pack(side="left")

        refresh_btn = CTkButton(
            header_frame,
            text="🔄",
            width=30,
            height=28,
            corner_radius=6,
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"),
            font=CTkFont(size=12),
            command=self._update_recommendations,
        )
        refresh_btn.pack(side="right")

        self.rec_container = CTkScrollableFrame(
            rec_frame, fg_color="transparent", height=160
        )
        self.rec_container.pack(fill="both", expand=True, padx=5, pady=5)

        self._show_no_recommendations()

        self.script_manager = self._get_script_manager()
        self._update_recommendations()

    def _get_script_manager(self):
        from script_manager import ScriptManager

        return ScriptManager()

    def _show_no_recommendations(self):
        from customtkinter import CTkFrame, CTkLabel, CTkFont

        no_rec_frame = CTkFrame(
            self.rec_container, fg_color=("gray88", "gray22"), height=140
        )
        no_rec_frame.pack(fill="x", pady=5)
        no_rec_frame.pack_propagate(False)

        msg_label = CTkLabel(
            no_rec_frame,
            text="💡 Запишите действия и проанализируйте их\nРобот предложит лучшие скрипты",
            font=CTkFont(size=11),
            justify="center",
        )
        msg_label.pack(expand=True)

    def _update_recommendations(self):
        if not self.is_ui_ready or not self.rec_container:
            return

        for widget in self.rec_container.winfo_children():
            widget.destroy()

        if not self.script_manager:
            self._show_no_recommendations()
            return

        self.recommended_scripts = self.script_manager.get_top_scripts(limit=3)

        if not self.recommended_scripts:
            self._show_no_recommendations()
            return

        for i, script in enumerate(self.recommended_scripts):
            self._create_script_card(script, i + 1)

    def _create_script_card(self, script, position: int):
        from customtkinter import CTkFrame, CTkLabel, CTkButton, CTkFont

        card_frame = CTkFrame(
            self.rec_container,
            corner_radius=10,
            fg_color=("gray85", "gray25"),
            height=90,
        )
        card_frame.pack(fill="x", pady=5)
        card_frame.pack_propagate(False)

        info_frame = CTkFrame(card_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        header_frame = CTkFrame(info_frame, fg_color="transparent")
        header_frame.pack(fill="x")

        pos_badge = CTkLabel(
            header_frame,
            text=f"#{position}",
            font=CTkFont(size=10, weight="bold"),
            text_color=self.theme_colors["primary"],
        )
        pos_badge.pack(side="left", padx=(0, 8))

        type_icon = self._get_script_type_icon(script.script_type)
        name_label = CTkLabel(
            header_frame,
            text=f"{type_icon} {script.name}",
            font=CTkFont(size=12, weight="bold"),
        )
        name_label.pack(side="left", anchor="w")

        desc_label = CTkLabel(
            info_frame,
            text=script.description,
            font=CTkFont(size=10),
            text_color=("gray50", "gray60"),
            wraplength=220,
        )
        desc_label.pack(fill="x", pady=(5, 0))

        stats_frame = CTkFrame(info_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(5, 0))

        success_rate = script.success_rate
        success_color = (
            self.theme_colors["success"]
            if success_rate >= 80
            else self.theme_colors["warning"]
            if success_rate >= 50
            else self.theme_colors["accent"]
        )

        stats_label = CTkLabel(
            stats_frame,
            text=f"✅ {success_rate:.0f}% | ⏱ {script.avg_duration:.1f}s | 📊 {script.run_count} запусков",
            font=CTkFont(size=9),
            text_color=success_color,
        )
        stats_label.pack(side="left", anchor="w")

        action_frame = CTkFrame(card_frame, fg_color="transparent")
        action_frame.pack(side="right", fill="y", padx=10, pady=10)

        run_btn = CTkButton(
            action_frame,
            text="▶",
            width=50,
            height=40,
            corner_radius=8,
            fg_color=(self.theme_colors["primary"]),
            hover_color=("#2980b9"),
            font=CTkFont(size=16),
            command=lambda s=script: self._on_script_run(s),
        )
        run_btn.pack(fill="y", expand=True)

    def _get_script_type_icon(self, script_type: str) -> str:
        icons = {"python": "🐍", "powershell": "⚡", "batch": "📁"}
        return icons.get(script_type, "📄")

    def _on_script_run(self, script):
        if not self.is_ui_ready:
            return

        self._update_status("running", f"Запуск: {script.name}", "#00ff00")
        self.robot_say(f"Запускаю: {script.name}")

        thread = threading.Thread(
            target=self._execute_script_thread, args=(script,), daemon=True
        )
        thread.start()

    def _execute_script_thread(self, script):
        try:
            result = self.script_manager.execute_script(script.path, timeout=300)

            if result.success:
                self._update_status("ready", "✅ Выполнено!", "#00ff00")
                self.robot_say("Готово!")
                self.robot.happy()
            else:
                self._update_status("error", "❌ Ошибка", "#ff4444")
                self.robot_say("Ошибка...")
                self.robot.error()

        except Exception as e:
            self._update_status("error", "❌ Сбой", "#ff4444")
            self.robot_say("Ошибка запуска")
            self.robot.error()

    def notify_analysis_complete(self, scripts_count: int):
        super().notify_analysis_complete(scripts_count)
        self._update_recommendations()

    def notify_predictions_ready(self, count: int):
        super().notify_predictions_ready(count)
        self._update_recommendations()
