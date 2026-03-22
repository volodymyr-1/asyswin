"""
Settings window for AsysWin
"""

import customtkinter as ctk


class SettingsWindow:
    def __init__(self):
        self.on_save = None
        self.window = None
        self.settings = {
            "mouse_threshold": 50,
            "key_debounce": 100,
            "auto_record": True,
            "cpu_limit": 50,
        }

    def show(self):
        """Show settings window"""
        self.window = ctk.CTkToplevel()
        self.window.title("AsysWin Settings")
        self.window.geometry("400x300")

        frame = ctk.CTkFrame(self.window)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Mouse threshold:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.mouse_entry = ctk.CTkEntry(frame, width=100)
        self.mouse_entry.insert(0, str(self.settings["mouse_threshold"]))
        self.mouse_entry.grid(row=0, column=1, pady=5)

        ctk.CTkLabel(frame, text="Key debounce (ms):").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.key_entry = ctk.CTkEntry(frame, width=100)
        self.key_entry.insert(0, str(self.settings["key_debounce"]))
        self.key_entry.grid(row=1, column=1, pady=5)

        self.auto_var = ctk.BooleanVar(value=self.settings["auto_record"])
        self.auto_check = ctk.CTkCheckBox(
            frame, text="Auto record on activity", variable=self.auto_var
        )
        self.auto_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=10)

        ctk.CTkButton(frame, text="Save", command=self._save).grid(
            row=3, column=0, pady=20
        )
        ctk.CTkButton(frame, text="Cancel", command=self.window.destroy).grid(
            row=3, column=1, pady=20
        )

    def _save(self):
        try:
            self.settings["mouse_threshold"] = int(self.mouse_entry.get())
            self.settings["key_debounce"] = int(self.key_entry.get())
            self.settings["auto_record"] = self.auto_var.get()

            if self.on_save:
                self.on_save(self.settings)

            self.window.destroy()
        except ValueError:
            pass
