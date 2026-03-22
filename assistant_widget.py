"""
Виджет-ассистент в стиле Windows 11
Базовый виджет с роботом и уведомлениями
"""

from base_assistant_widget import BaseAssistantWidget


class AssistantWidget(BaseAssistantWidget):
    """Базовый виджет-ассистент"""

    def __init__(self):
        super().__init__(width=320, height=450, title="AsysWin Assistant")

        self.message_frame = None
        self.message_labels = []

    def _create_ui(self):
        from customtkinter import CTkFrame, CTkScrollableFrame

        main_frame = CTkFrame(
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
        self._create_message_area(main_frame)
        self._create_action_buttons(main_frame)

        self.is_ui_ready = True

    def _create_message_area(self, parent):
        from customtkinter import CTkScrollableFrame, CTkFrame, CTkLabel, CTkFont
        from datetime import datetime

        self.message_frame = CTkScrollableFrame(
            parent, corner_radius=10, fg_color=("gray92", "gray18"), height=120
        )
        self.message_frame.pack(fill="x", padx=10, pady=5)

    def _add_message(self, icon: str, title: str, text: str):
        if not self.message_frame:
            return

        from customtkinter import CTkFrame, CTkLabel, CTkFont
        from datetime import datetime

        msg_frame = CTkFrame(
            self.message_frame,
            corner_radius=8,
            fg_color=("gray88", "gray22"),
            height=50,
        )
        msg_frame.pack(fill="x", pady=3, padx=5)
        msg_frame.pack_propagate(False)

        icon_label = CTkLabel(msg_frame, text=icon, font=CTkFont(size=18), width=30)
        icon_label.pack(side="left", padx=(10, 5))

        text_frame = CTkFrame(msg_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        title_label = CTkLabel(
            text_frame, text=title, font=CTkFont(size=11, weight="bold"), anchor="w"
        )
        title_label.pack(fill="x")

        desc_label = CTkLabel(
            text_frame,
            text=text,
            font=CTkFont(size=10),
            anchor="w",
            text_color=("gray50", "gray60"),
        )
        desc_label.pack(fill="x")

        time_label = CTkLabel(
            msg_frame,
            text=datetime.now().strftime("%H:%M"),
            font=CTkFont(size=9),
            text_color=("gray50", "gray60"),
            width=40,
        )
        time_label.pack(side="right", padx=5)

        self.message_labels.append(msg_frame)
        if len(self.message_labels) > 10:
            self.message_labels[0].destroy()
            self.message_labels.pop(0)

    def set_recording(self, is_recording: bool):
        super().set_recording(is_recording)
        if is_recording:
            self._add_message("🔴", "Запись начата", "Выполняйте нужные действия")
        else:
            self._add_message("⏹", "Запись остановлена", "Нажмите F10 для анализа")

    def set_analyzing(self, is_analyzing: bool):
        super().set_analyzing(is_analyzing)
        if is_analyzing:
            self._add_message("🔄", "Анализ начат", "Отправлено в LM Studio")

    def notify_analysis_complete(self, scripts_count: int):
        super().notify_analysis_complete(scripts_count)
        self._add_message("✅", "Анализ завершён", f"Создано {scripts_count} скриптов")

    def notify_predictions_ready(self, count: int):
        super().notify_predictions_ready(count)
        self._add_message("🔮", "Сценарии готовы", f"Найдено {count} сценариев")

    def notify_error(self, message: str):
        super().notify_error(message)
        self._add_message("❌", "Ошибка", message)
