"""
Enhanced settings window with AI provider selection
"""

import customtkinter as ctk
from config_manager import get_config


class SettingsWindow:
    def __init__(self):
        self.on_save = None
        self.on_provider_change = None
        self.window = None
        self.config = get_config()

        self.provider_var = None
        self.lmstudio_url_entry = None
        self.gemini_key_entry = None
        self.openai_key_entry = None
        self.groq_key_entry = None
        self.mouse_entry = None
        self.key_entry = None
        self.auto_var = None
        self.cpu_entry = None
        self.idle_entry = None
        self.provider_frames = {}

    def show(self):
        self.window = ctk.CTkToplevel()
        self.window.title("AsysWin Settings")
        self.window.geometry("600x700")

        main_scroll = ctk.CTkScrollableFrame(self.window)
        main_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self._create_provider_section(main_scroll)

        ctk.CTkFrame(main_scroll, height=2, fg_color=("gray70", "gray30")).pack(
            fill="x", pady=15
        )

        self._create_recording_section(main_scroll)

        ctk.CTkFrame(main_scroll, height=2, fg_color=("gray70", "gray30")).pack(
            fill="x", pady=15
        )

        self._create_automation_section(main_scroll)

        self._create_buttons(main_scroll)

    def _create_provider_section(self, parent):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=5)

        ctk.CTkLabel(
            section, text="AI Provider", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        provider_frame = ctk.CTkFrame(section, fg_color="transparent")
        provider_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(provider_frame, text="Provider:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.provider_var = ctk.StringVar(value=self.config.get_active_provider())

        provider_menu = ctk.CTkOptionMenu(
            provider_frame,
            variable=self.provider_var,
            values=["lmstudio", "gemini", "openai", "groq"],
            command=self._on_provider_selected,
            width=200,
        )
        provider_menu.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        self.provider_status_label = ctk.CTkLabel(
            provider_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
        )
        self.provider_status_label.grid(row=0, column=2, sticky="w", padx=10)

        self.provider_frames["lmstudio"] = self._create_lmstudio_settings(section)
        self.provider_frames["gemini"] = self._create_gemini_settings(section)
        self.provider_frames["openai"] = self._create_openai_settings(section)
        self.provider_frames["groq"] = self._create_groq_settings(section)

        self._on_provider_selected(self.provider_var.get())

    def _create_lmstudio_settings(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"), corner_radius=10)
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            frame, text="LM Studio (Local)", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        url_frame = ctk.CTkFrame(frame, fg_color="transparent")
        url_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(url_frame, text="Server URL:", width=120).grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.lmstudio_url_entry = ctk.CTkEntry(url_frame, width=300)
        self.lmstudio_url_entry.insert(0, self.config.get("lmstudio_url"))
        self.lmstudio_url_entry.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        test_btn = ctk.CTkButton(
            url_frame, text="Test", width=80, command=self._test_lmstudio
        )
        test_btn.grid(row=0, column=2, padx=5)

        ctk.CTkLabel(
            frame,
            text="Start LM Studio -> Developer -> Start Server",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
        ).pack(anchor="w", padx=15, pady=(0, 10))

        return frame

    def _create_gemini_settings(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"), corner_radius=10)
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            frame, text="Google Gemini", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        key_frame = ctk.CTkFrame(frame, fg_color="transparent")
        key_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(key_frame, text="API Key:", width=120).grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.gemini_key_entry = ctk.CTkEntry(key_frame, width=300, show="*")
        self.gemini_key_entry.insert(0, self.config.get("gemini_api_key"))
        self.gemini_key_entry.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        self.gemini_show_btn = ctk.CTkButton(
            key_frame,
            text="Show",
            width=60,
            command=lambda: self._toggle_password(
                self.gemini_key_entry, self.gemini_show_btn
            ),
        )
        self.gemini_show_btn.grid(row=0, column=2, padx=5)

        ctk.CTkLabel(
            frame,
            text="Get key: https://aistudio.google.com/apikey",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
        ).pack(anchor="w", padx=15, pady=(0, 10))

        return frame

    def _create_openai_settings(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"), corner_radius=10)
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            frame, text="OpenAI (GPT-4)", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        key_frame = ctk.CTkFrame(frame, fg_color="transparent")
        key_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(key_frame, text="API Key:", width=120).grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.openai_key_entry = ctk.CTkEntry(key_frame, width=300, show="*")
        self.openai_key_entry.insert(0, self.config.get("openai_api_key"))
        self.openai_key_entry.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        self.openai_show_btn = ctk.CTkButton(
            key_frame,
            text="Show",
            width=60,
            command=lambda: self._toggle_password(
                self.openai_key_entry, self.openai_show_btn
            ),
        )
        self.openai_show_btn.grid(row=0, column=2, padx=5)

        ctk.CTkLabel(
            frame,
            text="Get key: https://platform.openai.com/api-keys",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
        ).pack(anchor="w", padx=15, pady=(0, 10))

        return frame

    def _create_groq_settings(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"), corner_radius=10)
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            frame, text="Groq (Free, Fast)", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        key_frame = ctk.CTkFrame(frame, fg_color="transparent")
        key_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(key_frame, text="API Key:", width=120).grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.groq_key_entry = ctk.CTkEntry(key_frame, width=300, show="*")
        self.groq_key_entry.insert(0, self.config.get("groq_api_key"))
        self.groq_key_entry.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        self.groq_show_btn = ctk.CTkButton(
            key_frame,
            text="Show",
            width=60,
            command=lambda: self._toggle_password(
                self.groq_key_entry, self.groq_show_btn
            ),
        )
        self.groq_show_btn.grid(row=0, column=2, padx=5)

        ctk.CTkLabel(
            frame,
            text="Get key: https://console.groq.com/keys",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
        ).pack(anchor="w", padx=15, pady=(0, 10))

        return frame

    def _create_recording_section(self, parent):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=5)

        ctk.CTkLabel(
            section, text="Recording", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x")

        ctk.CTkLabel(grid, text="Mouse threshold (px):").grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.mouse_entry = ctk.CTkEntry(grid, width=100)
        self.mouse_entry.insert(0, str(self.config.get("mouse_threshold")))
        self.mouse_entry.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(grid, text="Key debounce (ms):").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.key_entry = ctk.CTkEntry(grid, width=100)
        self.key_entry.insert(0, str(self.config.get("key_debounce")))
        self.key_entry.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        self.auto_var = ctk.BooleanVar(value=self.config.get("auto_record"))
        ctk.CTkCheckBox(
            section, text="Auto record on activity", variable=self.auto_var
        ).pack(anchor="w", pady=10)

    def _create_automation_section(self, parent):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", pady=5)

        ctk.CTkLabel(
            section, text="Automation", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x")

        ctk.CTkLabel(grid, text="CPU limit (%):").grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.cpu_entry = ctk.CTkEntry(grid, width=100)
        self.cpu_entry.insert(0, str(self.config.get("cpu_limit")))
        self.cpu_entry.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(grid, text="Idle threshold (sec):").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.idle_entry = ctk.CTkEntry(grid, width=100)
        self.idle_entry.insert(0, str(self.config.get("idle_threshold")))
        self.idle_entry.grid(row=1, column=1, sticky="w", padx=10, pady=5)

    def _create_buttons(self, parent):
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)

        ctk.CTkButton(
            button_frame,
            text="Save",
            command=self._save,
            fg_color=("#0078D4", "#0078D4"),
            hover_color=("#106EBE", "#106EBE"),
            width=150,
            height=40,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            width=150,
            height=40,
        ).pack(side="left", padx=5)

    def _on_provider_selected(self, provider: str):
        for frame in self.provider_frames.values():
            frame.pack_forget()
        if provider in self.provider_frames:
            self.provider_frames[provider].pack(fill="x", pady=5)
        self._update_provider_status(provider)

    def _update_provider_status(self, provider: str):
        from llm_analyzer import create_provider

        try:
            if provider == "lmstudio":
                url = self.lmstudio_url_entry.get()
                p = create_provider("lmstudio", api_url=url)
            elif provider == "gemini":
                key = self.gemini_key_entry.get()
                p = create_provider("gemini", api_key=key) if key else None
            elif provider == "openai":
                key = self.openai_key_entry.get()
                p = create_provider("openai", api_key=key) if key else None
            elif provider == "groq":
                key = self.groq_key_entry.get()
                p = create_provider("groq", api_key=key) if key else None
            else:
                p = None

            if p and p.is_ready():
                self.provider_status_label.configure(
                    text="OK", text_color=("green", "lightgreen")
                )
            else:
                self.provider_status_label.configure(
                    text="Not available", text_color=("red", "lightcoral")
                )
        except Exception as e:
            self.provider_status_label.configure(
                text="Error", text_color=("red", "lightcoral")
            )

    def _test_lmstudio(self):
        from llm_analyzer import create_provider

        url = self.lmstudio_url_entry.get()
        try:
            provider = create_provider("lmstudio", api_url=url)
            if provider.is_ready():
                self.provider_status_label.configure(
                    text="Connected!", text_color=("green", "lightgreen")
                )
            else:
                self.provider_status_label.configure(
                    text="No response", text_color=("red", "lightcoral")
                )
        except Exception as e:
            self.provider_status_label.configure(
                text="Error", text_color=("red", "lightcoral")
            )

    def _toggle_password(self, entry, button):
        if entry.cget("show") == "*":
            entry.configure(show="")
            button.configure(text="Hide")
        else:
            entry.configure(show="*")
            button.configure(text="Show")

    def _save(self):
        try:
            old_provider = self.config.get_active_provider()
            new_provider = self.provider_var.get()

            self.config.set("ai_provider", new_provider)
            self.config.set("lmstudio_url", self.lmstudio_url_entry.get())
            self.config.set("gemini_api_key", self.gemini_key_entry.get())
            self.config.set("openai_api_key", self.openai_key_entry.get())
            self.config.set("groq_api_key", self.groq_key_entry.get())
            self.config.set("mouse_threshold", int(self.mouse_entry.get()))
            self.config.set("key_debounce", int(self.key_entry.get()))
            self.config.set("auto_record", self.auto_var.get())
            self.config.set("cpu_limit", int(self.cpu_entry.get()))
            self.config.set("idle_threshold", int(self.idle_entry.get()))

            self.config.save_config()

            if self.on_save:
                self.on_save(self.config.get_all())

            if new_provider != old_provider and self.on_provider_change:
                self.on_provider_change(new_provider)

            self.window.destroy()
        except ValueError:
            pass
