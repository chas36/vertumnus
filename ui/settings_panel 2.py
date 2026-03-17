from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models.conversion_settings import ConversionSettings
from models.file_item import FileItem
from models.media_stream import MediaStream


class SettingsPanel(QWidget):
    settings_changed = Signal()
    theme_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.qt_settings = QSettings("Vertumnus", "MP4Converter")
        self._current_item: FileItem | None = None
        self._loading_stream_controls = False

        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Для проектора", "projector")
        self.profile_combo.addItem("Кастомный", "custom")

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("/Users/you/Videos/Converted")
        self.output_button = QPushButton("Выбрать")
        self.near_source_checkbox = QCheckBox("Сохранять рядом с оригиналом")

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItem("Оригинал", "original")
        self.resolution_combo.addItem("Высокое 1080p", "1080p")
        self.resolution_combo.addItem("Среднее 720p", "720p")
        self.resolution_combo.addItem("Компактное 480p", "480p")

        self.fps_combo = QComboBox()
        self.fps_combo.addItem("Как в оригинале", "0")
        self.fps_combo.addItem("30 FPS", "30")
        self.fps_combo.addItem("25 FPS", "25")
        self.fps_combo.addItem("24 FPS", "24")

        self.video_bitrate_combo = QComboBox()
        self.video_bitrate_combo.addItem("Авто", "auto")
        self.video_bitrate_combo.addItem("8 Mbps", "8M")
        self.video_bitrate_combo.addItem("4 Mbps", "4M")
        self.video_bitrate_combo.addItem("2 Mbps", "2M")
        self.video_bitrate_combo.addItem("1 Mbps", "1M")

        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItem("128 kbps", "128k")
        self.audio_bitrate_combo.addItem("192 kbps", "192k")
        self.audio_bitrate_combo.addItem("256 kbps", "256k")
        self.audio_bitrate_combo.addItem("320 kbps", "320k")

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Очень быстро", "ultrafast")
        self.preset_combo.addItem("Быстро", "fast")
        self.preset_combo.addItem("Сбалансировано", "medium")
        self.preset_combo.addItem("Лучше качество", "slow")
        self.preset_combo.setCurrentIndex(2)

        self.audio_track_combo = QComboBox()
        self.subtitle_track_combo = QComboBox()
        self.subtitle_enabled_checkbox = QCheckBox("Сохранять выбранные субтитры")
        self.subtitle_default_checkbox = QCheckBox("Включать субтитры по умолчанию")
        self.stream_target_label = QLabel("Выберите файл, чтобы настроить дорожки.")
        self.stream_target_label.setWordWrap(True)
        self.stream_hint_label = QLabel("")
        self.stream_hint_label.setWordWrap(True)

        self.advanced_toggle = QCheckBox("Расширенный режим")
        self.theme_toggle = QCheckBox("Светлая тема")
        self.advanced_toggle.setObjectName("subtleToggle")
        self.theme_toggle.setObjectName("subtleToggle")

        self._build_ui()
        self._connect_signals()
        self.load()
        self._sync_ui_state()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.viewport().setObjectName("settingsViewport")

        content = QWidget()
        content.setObjectName("settingsContent")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(14)

        self.profile_card = QGroupBox("Профиль")
        profile_layout = QVBoxLayout(self.profile_card)
        profile_layout.setSpacing(8)
        profile_layout.addWidget(self._field_block("Режим конвертации", self.profile_combo))

        self.profile_hint_label = QLabel(
            "Для проектора: совместимый MP4 с безопасными настройками. "
            "Кастомный: откройте расширенный режим для дополнительных параметров."
        )
        self.profile_hint_label.setWordWrap(True)
        profile_layout.addWidget(self.profile_hint_label)

        self.quality_card = QGroupBox("Качество и кодирование")
        quality_layout = QVBoxLayout(self.quality_card)
        quality_layout.setSpacing(8)
        quality_layout.addWidget(self._field_block("Качество видео", self.resolution_combo))
        quality_layout.addWidget(self._field_block("FPS", self.fps_combo))
        quality_layout.addWidget(self._field_block("Видео битрейт", self.video_bitrate_combo))
        quality_layout.addWidget(self._field_block("Аудио битрейт", self.audio_bitrate_combo))
        quality_layout.addWidget(self._field_block("Скорость кодирования", self.preset_combo))

        self.output_card = QGroupBox("Сохранение")
        output_layout = QVBoxLayout(self.output_card)
        output_layout.setSpacing(8)
        output_layout.addWidget(self._field_block("Папка вывода", self.output_edit))
        output_buttons = QHBoxLayout()
        output_buttons.setContentsMargins(0, 0, 0, 0)
        output_buttons.addWidget(self.output_button)
        output_buttons.addStretch(1)
        output_layout.addLayout(output_buttons)
        output_layout.addWidget(self.near_source_checkbox)

        self.streams_card = QGroupBox("Дорожки выбранного файла")
        streams_layout = QVBoxLayout(self.streams_card)
        streams_layout.setSpacing(8)
        streams_layout.addWidget(self.stream_target_label)
        streams_layout.addWidget(self._field_block("Оставить аудио дорожку", self.audio_track_combo))
        streams_layout.addWidget(self._field_block("Оставить субтитры", self.subtitle_track_combo))
        streams_layout.addWidget(self.subtitle_enabled_checkbox)
        streams_layout.addWidget(self.subtitle_default_checkbox)
        streams_layout.addWidget(self.stream_hint_label)

        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 6, 0, 0)
        footer_layout.setSpacing(18)
        footer_layout.addWidget(self.advanced_toggle)
        footer_layout.addStretch(1)
        footer_layout.addWidget(self.theme_toggle)

        self.content_layout.addWidget(self.profile_card)
        self.content_layout.addWidget(self.quality_card)
        self.content_layout.addWidget(self.output_card)
        self.content_layout.addWidget(self.streams_card)
        self.content_layout.addStretch(1)
        self.content_layout.addWidget(footer)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.setMinimumWidth(420)

    def _field_block(self, title: str, widget: QWidget) -> QWidget:
        container = QWidget()
        block_layout = QVBoxLayout(container)
        block_layout.setContentsMargins(0, 0, 0, 0)
        block_layout.setSpacing(6)

        label = QLabel(title)
        label.setProperty("fieldLabel", True)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        block_layout.addWidget(label)
        block_layout.addWidget(widget)
        return container

    def _connect_signals(self) -> None:
        controls = [
            self.profile_combo,
            self.output_edit,
            self.near_source_checkbox,
            self.resolution_combo,
            self.fps_combo,
            self.video_bitrate_combo,
            self.audio_bitrate_combo,
            self.preset_combo,
            self.advanced_toggle,
            self.theme_toggle,
        ]
        for control in controls:
            if hasattr(control, "currentIndexChanged"):
                control.currentIndexChanged.connect(self._on_global_control_changed)
            if hasattr(control, "textChanged"):
                control.textChanged.connect(self._on_global_control_changed)
            if hasattr(control, "toggled"):
                control.toggled.connect(self._on_global_control_changed)

        self.audio_track_combo.currentIndexChanged.connect(self._on_stream_control_changed)
        self.subtitle_track_combo.currentIndexChanged.connect(self._on_stream_control_changed)
        self.subtitle_enabled_checkbox.toggled.connect(self._on_stream_control_changed)
        self.subtitle_default_checkbox.toggled.connect(self._on_stream_control_changed)
        self.output_button.clicked.connect(self.choose_output_dir)

    def _on_global_control_changed(self) -> None:
        self._sync_ui_state()
        self.save()
        self.theme_changed.emit(self.current_theme())
        self.settings_changed.emit()

    def _on_stream_control_changed(self) -> None:
        if self._loading_stream_controls or self._current_item is None:
            return

        audio_index = self.audio_track_combo.currentData()
        subtitle_index = self.subtitle_track_combo.currentData()
        self._current_item.selected_audio_stream_index = int(audio_index) if audio_index is not None else None
        self._current_item.selected_subtitle_stream_index = int(subtitle_index) if subtitle_index is not None else None
        self._current_item.subtitle_enabled = self.subtitle_enabled_checkbox.isChecked() and subtitle_index is not None
        self._current_item.subtitle_default = self.subtitle_default_checkbox.isChecked() and self._current_item.subtitle_enabled
        self.settings_changed.emit()
        self._sync_ui_state()

    def _sync_ui_state(self) -> None:
        advanced = self.advanced_toggle.isChecked()
        custom_profile = self.profile_combo.currentData() == "custom"

        self.quality_card.setVisible(advanced)
        self.output_card.setVisible(advanced)
        self.streams_card.setVisible(advanced)

        self.fps_combo.setEnabled(advanced and custom_profile)
        self.video_bitrate_combo.setEnabled(advanced and custom_profile)
        self.output_edit.setEnabled(advanced and not self.near_source_checkbox.isChecked())
        self.output_button.setEnabled(advanced and not self.near_source_checkbox.isChecked())

        subtitle_selected = self.subtitle_track_combo.currentData() is not None
        has_stream_item = self._current_item is not None
        self.audio_track_combo.setEnabled(advanced and has_stream_item and self.audio_track_combo.count() > 0)
        self.subtitle_track_combo.setEnabled(advanced and has_stream_item and self.subtitle_track_combo.count() > 0)
        self.subtitle_enabled_checkbox.setEnabled(advanced and has_stream_item and subtitle_selected)
        self.subtitle_default_checkbox.setEnabled(
            advanced and has_stream_item and subtitle_selected and self.subtitle_enabled_checkbox.isChecked()
        )

        if not advanced:
            self.profile_hint_label.setText(
                "Базовый режим: выберите профиль и запускайте конвертацию. "
                "Расширенный режим откроет качество, папку вывода и дорожки."
            )
        elif custom_profile:
            self.profile_hint_label.setText(
                "Кастомный профиль активен: можно менять качество, FPS, битрейт и дорожки для выбранного файла."
            )
        else:
            self.profile_hint_label.setText(
                "Профиль проектора остаётся совместимым, но в расширенном режиме можно выбрать качество и нужные дорожки."
            )

    def choose_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку вывода")
        if directory:
            self.output_edit.setText(directory)

    def to_settings(self) -> ConversionSettings:
        output_dir = Path(self.output_edit.text()).expanduser() if self.output_edit.text().strip() else None
        return ConversionSettings(
            output_dir=output_dir,
            resolution=str(self.resolution_combo.currentData()),
            fps=int(self.fps_combo.currentData()),
            video_bitrate=str(self.video_bitrate_combo.currentData()),
            audio_bitrate=str(self.audio_bitrate_combo.currentData()),
            preset=str(self.preset_combo.currentData()),
            profile=str(self.profile_combo.currentData()),
            save_next_to_source=self.near_source_checkbox.isChecked(),
        )

    def set_current_item(self, item: FileItem | None) -> None:
        self._current_item = item
        self._loading_stream_controls = True
        self.audio_track_combo.clear()
        self.subtitle_track_combo.clear()

        if item is None:
            self.stream_target_label.setText("Выберите файл, чтобы настроить дорожки.")
            self.stream_hint_label.setText("")
            self.subtitle_enabled_checkbox.setChecked(False)
            self.subtitle_default_checkbox.setChecked(False)
        else:
            self.stream_target_label.setText(item.display_name)
            for stream in item.audio_streams:
                self.audio_track_combo.addItem(stream.label, stream.index)
            supported_subtitles = [stream for stream in item.subtitle_streams if stream.supports_mp4_subtitle]
            self.subtitle_track_combo.addItem("Не сохранять субтитры", None)
            for stream in supported_subtitles:
                self.subtitle_track_combo.addItem(stream.label, stream.index)

            unsupported_count = len(item.subtitle_streams) - len(supported_subtitles)
            self.stream_hint_label.setText(
                "Только текстовые субтитры сохраняются в MP4."
                if unsupported_count > 0
                else ""
            )

            self._select_combo_data(
                self.audio_track_combo,
                item.selected_audio_stream_index if item.selected_audio_stream_index is not None else self._default_audio(item),
            )
            self._select_combo_data(self.subtitle_track_combo, item.selected_subtitle_stream_index)
            self.subtitle_enabled_checkbox.setChecked(item.subtitle_enabled and item.selected_subtitle_stream_index is not None)
            self.subtitle_default_checkbox.setChecked(item.subtitle_default and self.subtitle_enabled_checkbox.isChecked())

        self._loading_stream_controls = False
        self._sync_ui_state()

    def _default_audio(self, item: FileItem) -> int | None:
        return item.audio_streams[0].index if item.audio_streams else None

    def _select_combo_data(self, combo: QComboBox, value: int | None) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)
        elif combo.count() > 0:
            combo.setCurrentIndex(0)

    def load(self) -> None:
        self.advanced_toggle.setChecked(self.qt_settings.value("advanced_mode", False, bool))
        self.theme_toggle.setChecked(self.qt_settings.value("theme", "dark") == "light")

        profile = self.qt_settings.value("profile", "projector")
        index = self.profile_combo.findData(profile)
        self.profile_combo.setCurrentIndex(max(index, 0))
        self.output_edit.setText(str(self.qt_settings.value("output_dir", "")))
        self.near_source_checkbox.setChecked(self.qt_settings.value("save_next_to_source", True, bool))
        self._set_combo_data(self.resolution_combo, str(self.qt_settings.value("resolution", "original")))
        self._set_combo_data(self.fps_combo, str(self.qt_settings.value("fps", "0")))
        self._set_combo_data(self.video_bitrate_combo, str(self.qt_settings.value("video_bitrate", "auto")))
        self._set_combo_data(self.audio_bitrate_combo, str(self.qt_settings.value("audio_bitrate", "128k")))
        self._set_combo_data(self.preset_combo, str(self.qt_settings.value("preset", "medium")))

    def _set_combo_data(self, combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def save(self) -> None:
        settings = self.to_settings()
        self.qt_settings.setValue("advanced_mode", self.advanced_toggle.isChecked())
        self.qt_settings.setValue("theme", self.current_theme())
        self.qt_settings.setValue("profile", settings.profile)
        self.qt_settings.setValue("output_dir", str(settings.output_dir or ""))
        self.qt_settings.setValue("save_next_to_source", settings.save_next_to_source)
        self.qt_settings.setValue("resolution", settings.resolution)
        self.qt_settings.setValue("fps", str(settings.fps))
        self.qt_settings.setValue("video_bitrate", settings.video_bitrate)
        self.qt_settings.setValue("audio_bitrate", settings.audio_bitrate)
        self.qt_settings.setValue("preset", settings.preset)

    def current_theme(self) -> str:
        return "light" if self.theme_toggle.isChecked() else "dark"
