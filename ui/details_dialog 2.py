from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)

from models.file_item import FileItem


class FileDetailsDialog(QDialog):
    def __init__(self, item: FileItem, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Детали: {item.display_name}")
        self.resize(720, 420)

        summary = QFormLayout()
        summary.addRow("Файл", QLabel(str(item.path)))
        summary.addRow("Статус", QLabel(item.status))
        summary.addRow("Прогресс", QLabel(f"{item.progress}%"))
        summary.addRow("Видео", QLabel(item.video_codec or "—"))
        summary.addRow("Аудио", QLabel(item.audio_codec or "—"))
        summary.addRow("Разрешение", QLabel(item.resolution or "—"))
        summary.addRow("Результат", QLabel(str(item.output_path) if item.output_path else "—"))

        self.message_edit = QTextEdit()
        self.message_edit.setReadOnly(True)
        self.message_edit.setPlainText(item.error_message or "Ошибок нет.")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addLayout(summary)
        layout.addWidget(self.message_edit)
        layout.addWidget(buttons)
