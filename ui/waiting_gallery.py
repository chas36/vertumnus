from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class WaitingGalleryWidget(QWidget):
    SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("waitingGalleryCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(220)

        self._image_paths: list[Path] = []
        self._directory: Path | None = None
        self._current_index = 0
        self._active = False
        self._current_pixmap: QPixmap | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(4500)
        self._timer.timeout.connect(self._show_next_image)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.title_label = QLabel("Медвежий режим ожидания")
        self.title_label.setObjectName("waitingGalleryTitle")

        self.image_label = QLabel()
        self.image_label.setObjectName("waitingGalleryImage")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(150)

        self.caption_label = QLabel("")
        self.caption_label.setObjectName("waitingGalleryHint")
        self.caption_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label)
        layout.addWidget(self.caption_label)

        self._render_state()
        self.hide()

    def set_image_directory(self, directory: Path | None) -> None:
        self._directory = directory
        self._image_paths = []
        self._current_index = 0

        if directory and directory.exists():
            self._image_paths = sorted(
                path
                for path in directory.iterdir()
                if path.is_file() and path.suffix.lower() in self.SUPPORTED_SUFFIXES
            )

        self._render_state()
        self._sync_visibility()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._sync_timer()
        self._render_state()
        self._sync_visibility()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._update_pixmap()

    def _sync_visibility(self) -> None:
        should_show = self._active and self._directory is not None
        self.setVisible(should_show)

    def _sync_timer(self) -> None:
        if self._active and len(self._image_paths) > 1:
            self._timer.start()
            return
        self._timer.stop()

    def _show_next_image(self) -> None:
        if not self._image_paths:
            return
        self._current_index = (self._current_index + 1) % len(self._image_paths)
        self._render_state()

    def _render_state(self) -> None:
        if not self._directory:
            self._current_pixmap = None
            self.image_label.clear()
            self.image_label.setText("")
            self.caption_label.setText("")
            return

        if not self._image_paths:
            self._current_pixmap = None
            self.image_label.clear()
            self.image_label.setText("В выбранной папке пока нет JPG, PNG, WEBP или BMP.")
            self.caption_label.setText("Скопируй фотографии с iPhone в папку на компьютере и выбери её в настройках.")
            return

        current_path = self._image_paths[self._current_index]
        pixmap = QPixmap(str(current_path))
        if pixmap.isNull():
            self._current_pixmap = None
            self.image_label.clear()
            self.image_label.setText("Эту фотографию не удалось открыть.")
            self.caption_label.setText(current_path.name)
            return

        self._current_pixmap = pixmap
        self._update_pixmap()
        self.caption_label.setText(f"{current_path.name} • {self._current_index + 1}/{len(self._image_paths)}")

    def _update_pixmap(self) -> None:
        if self._current_pixmap is None:
            return

        scaled = self._current_pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

