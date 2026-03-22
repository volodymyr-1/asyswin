"""
Assistant widget with script recommendations (auto mode)
Shows 3 most likely scripts to run
Recording and analysis happen automatically
"""

import threading
from typing import TYPE_CHECKING

from base_assistant_widget_auto import BaseAssistantWidget

if TYPE_CHECKING:
    from script_manager import ScriptManager, ScriptInfo


class AssistantWidgetAuto(BaseAssistantWidget):
    """Widget with script recommendations (auto mode)"""

    def __init__(self):
        super().__init__(width=360, height=480, title="AsysWin Auto")

        self.script_manager = None
        self.recommended_scripts = []

        from config_manager import get_config

        config = get_config()
        provider = config.get_active_provider()

        provider_names = {
            "lmstudio": "LM Studio (Local)",
            "gemini": "Gemini Pro",
            "openai": "GPT-4",
            "groq": "Groq (Fast)",
        }

        self.active_provider = provider_names.get(provider, provider)
        self.provider_label = None
        self.rec_container = None

    def update_provider_display(self, provider: str):
        """Update displayed provider name"""
        provider_names = {
            "lmstudio": "LM Studio (Local)",
            "gemini": "Gemini Pro",
            "openai": "GPT-4",
            "groq": "Groq (Fast)",
        }

        self.active_provider = provider_names.get(provider, provider)

        if self.provider_label:
            self.provider_label.configure(text=f"🤖 {self.active_provider}")

        print(f"[WIDGET] Provider updated: {self.active_provider}")

    def _create_extra_ui(self, parent):
        self._create_recommendations_area(parent)

    def _add_header_content(self, parent):
        from customtkinter import CTkLabel, CTkFont

        icon_label = CTkLabel(parent, text="🤖", font=CTkFont(size=24))
        icon_label.pack(side="left", padx=(0, 8))

        title_label = CTkLabel(
            parent, text="AsysWin", font=CTkFont(size=14, weight="bold")
        )
        title_label.pack(side="left")

        auto_badge = CTkLabel(
            parent,
            text="AUTO",
            font=CTkFont(size=9, weight="bold"),
            text_color=("#00ff00", "#00ff00"),
            fg_color=("gray80", "gray30"),
            corner_radius=4,
            width=45,
            height=18,
        )
        auto_badge.pack(side="left", padx=5)

        self.provider_label = CTkLabel(
            parent,
            text=f"🤖 {self.active_provider}",
            font=CTkFont(size=10),
            text_color=("gray50", "gray60"),
        )
        self.provider_label.pack(side="left", padx=5)

    def _create_recommendations_area(self, parent):
        from customtkinter import (
            CTkFrame,
            CTkLabel,
            CTkButton,
            CTkScrollableFrame,
            CTkFont,
        )

        rec_frame = CTkFrame(
            parent, corner_radius=10, fg_color=("gray92", "gray18"), height=200
        )
        rec_frame.pack(fill="x", padx=10, pady=5)
        rec_frame.pack_propagate(False)

        header_frame = CTkFrame(rec_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_label = CTkLabel(
            header_frame,
            text="📋 Recommended Scripts",
            font=CTkFont(size=12, weight="bold"),
        )
        title_label.pack(side="left")

        refresh_btn = CTkButton(
            header_frame,
            text="🔄",
            width=30,
            height=25,
            corner_radius=6,
            fg_color=("gray85", "gray25"),
            hover_color=("gray75", "gray35"),
            font=CTkFont(size=12),
            command=self._update_recommendations,
        )
        refresh_btn.pack(side="right")

        self.rec_container = CTkScrollableFrame(
            rec_frame, fg_color="transparent", height=140
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
            self.rec_container, fg_color=("gray88", "gray22"), height=120
        )
        no_rec_frame.pack(fill="x", pady=5)
        no_rec_frame.pack_propagate(False)

        msg_label = CTkLabel(
            no_rec_frame,
            text="No scripts available\nJust start working - system records automatically",
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
            corner_radius=8,
            fg_color=("gray88", "gray22"),
            height=80,
        )
        card_frame.pack(fill="x", pady=5)
        card_frame.pack_propagate(False)

        info_frame = CTkFrame(card_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        header_frame = CTkFrame(info_frame, fg_color="transparent")
        header_frame.pack(fill="x")

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
            wraplength=200,
        )
        desc_label.pack(fill="x", pady=(5, 0))

        stats_frame = CTkFrame(info_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(5, 0))

        success_rate = script.success_rate
        success_color = (
            "#00ff00"
            if success_rate >= 80
            else "#ffaa00"
            if success_rate >= 50
            else "#ff4444"
        )

        stats_label = CTkLabel(
            stats_frame,
            text=f"⚡ {success_rate:.0f}% success | {script.run_count} runs",
            font=CTkFont(size=9),
            text_color=success_color,
        )
        stats_label.pack(side="left", anchor="w")

        action_frame = CTkFrame(card_frame, fg_color="transparent")
        action_frame.pack(side="right", fill="y", padx=10, pady=10)

        run_btn = CTkButton(
            action_frame,
            text="▶ Run",
            width=80,
            height=30,
            corner_radius=6,
            fg_color=("#0078D4", "#0078D4"),
            hover_color=("#106EBE", "#106EBE"),
            font=CTkFont(size=10),
            command=lambda s=script: self._on_script_run(s),
        )
        run_btn.pack(fill="y", expand=True)

    def _get_script_type_icon(self, script_type: str) -> str:
        icons = {"python": "🐍", "powershell": "⚡", "batch": "📁"}
        return icons.get(script_type, "📄")

    def _on_script_run(self, script):
        if not self.is_ui_ready:
            return

        self._update_status("running", f"Running: {script.name}", "#00ff00")
        self.robot_say(f"Running script: {script.name}")

        thread = threading.Thread(
            target=self._execute_script_thread, args=(script,), daemon=True
        )
        thread.start()

    def _execute_script_thread(self, script):
        try:
            result = self.script_manager.execute_script(script.path, timeout=300)

            if result.success:
                self._update_status("ready", "Ready", "#00ff00")
                self.robot_say("Script completed successfully!")
            else:
                self._update_status("error", "Execution error", "#ff4444")
                self.robot_say("Error running script")

        except Exception as e:
            self._update_status("error", "Launch error", "#ff4444")
            self.robot_say("Error launching script")

    def notify_analysis_complete(self, scripts_count: int):
        super().notify_analysis_complete(scripts_count)
        self._update_recommendations()

    def notify_predictions_ready(self, count: int):
        super().notify_predictions_ready(count)
        self._update_recommendations()
