from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTextEdit,
    QVBoxLayout,
)

from models.file_item import FileItem


class ErrorDialog(QDialog):
    def __init__(self, item: FileItem, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Ошибка конвертации: {item.display_name}")
        self.resize(760, 420)

        file_label = QLabel(str(item.path))
        file_label.setWordWrap(True)

        error_view = QTextEdit()
        error_view.setReadOnly(True)
        error_view.setPlainText(item.error_message or "Сообщение об ошибке отсутствует.")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(file_label)
        layout.addWidget(error_view)
        layout.addWidget(buttons)
