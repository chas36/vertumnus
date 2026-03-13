from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.file_item import FileItem
from models.media_stream import MediaStream


def format_duration(seconds: float) -> str:
    total_seconds = int(seconds or 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes or 0)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return "0 B"


class FileItemWidget(QWidget):
    action_requested = Signal(str, str)

    STATUS_TEXT = {
        "pending": "В очереди",
        "converting": "Конвертация",
        "done": "Готово",
        "error": "Ошибка",
        "cancelled": "Отменено",
    }

    def __init__(self, item: FileItem) -> None:
        super().__init__()
        self._path = item.path

        self.name_label = QLabel(item.display_name)
        self.name_label.setObjectName("fileName")

        self.output_label = QLabel()
        self.output_label.setObjectName("fileMeta")

        self.meta_label = QLabel()
        self.meta_label.setObjectName("fileMeta")

        self.selection_label = QLabel()
        self.selection_label.setObjectName("fileMeta")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.status_label.setObjectName("fileStatus")
        self.status_label.setMinimumHeight(28)

        self.open_result_button = QPushButton("Результат")
        self.open_result_button.setObjectName("secondaryButton")
        self.open_result_button.clicked.connect(lambda: self._emit_action("open_result"))

        self.details_button = QPushButton("Детали")
        self.details_button.setObjectName("secondaryButton")
        self.details_button.clicked.connect(lambda: self._emit_action("show_details"))

        self.error_button = QPushButton("Ошибка")
        self.error_button.setObjectName("secondaryButton")
        self.error_button.clicked.connect(lambda: self._emit_action("show_error"))

        self.retry_button = QPushButton("Повторить")
        self.retry_button.setObjectName("secondaryButton")
        self.retry_button.clicked.connect(lambda: self._emit_action("retry"))

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(self.name_label, stretch=1)
        header.addWidget(self.status_label)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.addWidget(self.output_label, stretch=1)
        actions.addWidget(self.retry_button)
        actions.addWidget(self.error_button)
        actions.addWidget(self.details_button)
        actions.addWidget(self.open_result_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        layout.addLayout(header)
        layout.addWidget(self.meta_label)
        layout.addWidget(self.selection_label)
        layout.addWidget(self.progress_bar)
        layout.addLayout(actions)

        self.update_item(item)

    @property
    def path(self) -> Path:
        return self._path

    def _emit_action(self, action: str) -> None:
        self.action_requested.emit(str(self._path), action)

    def update_item(self, item: FileItem) -> None:
        self.name_label.setText(item.display_name)
        meta_parts = [format_size(item.size_bytes)]
        if item.duration > 0:
            meta_parts.append(format_duration(item.duration))
        if item.resolution:
            meta_parts.append(item.resolution)
        codecs = " / ".join(part for part in [item.video_codec, item.audio_codec] if part)
        if codecs:
            meta_parts.append(codecs)
        self.meta_label.setText(" • ".join(part for part in meta_parts if part))
        self.selection_label.setText(self._build_selection_text(item))
        self.selection_label.setVisible(bool(self.selection_label.text()))
        self.progress_bar.setValue(item.progress)
        self.status_label.setText(self.STATUS_TEXT.get(item.status, item.status))
        self.output_label.setText(str(item.output_path.name) if item.output_path else "")
        self.output_label.setVisible(bool(item.output_path))
        self.open_result_button.setVisible(bool(item.output_path))
        self.open_result_button.setEnabled(bool(item.output_path))
        self.retry_button.setVisible(item.status in {"error", "cancelled"})
        self.error_button.setVisible(item.status == "error" and bool(item.error_message))
        self.details_button.setVisible(True)
        self.setToolTip(item.error_message or str(item.path))

    def _build_selection_text(self, item: FileItem) -> str:
        audio_label = self._stream_label(item.audio_streams, item.selected_audio_stream_index)
        subtitle_label = self._stream_label(item.subtitle_streams, item.selected_subtitle_stream_index)
        parts: list[str] = []
        if audio_label:
            parts.append(f"Аудио: {audio_label}")
        if item.subtitle_enabled and subtitle_label:
            suffix = " (вкл.)" if item.subtitle_default else ""
            parts.append(f"Субтитры: {subtitle_label}{suffix}")
        return " • ".join(parts)

    def _stream_label(self, streams: list[MediaStream], selected_index: int | None) -> str:
        if selected_index is None:
            return ""
        stream = next((stream for stream in streams if stream.index == selected_index), None)
        if stream is None:
            return ""
        return stream.label
