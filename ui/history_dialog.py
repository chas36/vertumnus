from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.history import clear_history, load_history


class HistoryDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("История конвертаций")
        self.resize(900, 420)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Дата", "Файл", "Результат", "Статус", "Сообщение"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.refresh_button = QPushButton("Обновить")
        self.clear_button = QPushButton("Очистить")
        self.close_button = QPushButton("Закрыть")

        controls = QHBoxLayout()
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.clear_button)
        controls.addStretch(1)
        controls.addWidget(self.close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addLayout(controls)

        self.refresh_button.clicked.connect(self.reload)
        self.clear_button.clicked.connect(self.clear)
        self.close_button.clicked.connect(self.accept)

        self.reload()

    def reload(self) -> None:
        history = list(reversed(load_history()))
        self.table.setRowCount(len(history))

        for row, entry in enumerate(history):
            timestamp = str(entry.get("timestamp", ""))
            try:
                formatted_timestamp = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                formatted_timestamp = timestamp

            values = [
                formatted_timestamp,
                str(entry.get("source", "")),
                str(entry.get("output", "")),
                str(entry.get("status", "")),
                str(entry.get("message", "")),
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()

    def clear(self) -> None:
        clear_history()
        self.reload()
