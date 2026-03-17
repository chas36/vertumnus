from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)

from core.probe import probe_media
from core.queue_state import clear_queue_state, load_queue_state, save_queue_state
from core.worker import ConversionWorker
from models.file_item import FileItem
from ui.details_dialog import FileDetailsDialog
from ui.error_dialog import ErrorDialog
from ui.file_list_widget import FileListWidget
from ui.history_dialog import HistoryDialog
from ui.settings_panel import SettingsPanel
from ui.theme import load_stylesheet
from ui.waiting_gallery import WaitingGalleryWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MP4 Converter")
        self.resize(1180, 720)
        self.setAcceptDrops(True)

        self.file_list = FileListWidget()
        self.waiting_gallery = WaitingGalleryWidget()
        self.settings_panel = SettingsPanel()
        self.worker: ConversionWorker | None = None
        self._items_by_path: dict[str, FileItem] = {}

        self.add_button = QPushButton("+ Добавить файлы")
        self.remove_button = QPushButton("Удалить выбранные")
        self.history_button = QPushButton("История")
        self.open_result_button = QPushButton("Открыть результат")
        self.details_button = QPushButton("Детали")
        self.retry_failed_button = QPushButton("Повторить ошибки")
        self.start_button = QPushButton("Конвертировать")
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setEnabled(False)
        self.open_result_button.setEnabled(False)
        self.details_button.setEnabled(False)
        self.retry_failed_button.setEnabled(False)
        self.remove_button.setObjectName("secondaryButton")
        self.history_button.setObjectName("secondaryButton")
        self.open_result_button.setObjectName("secondaryButton")
        self.details_button.setObjectName("secondaryButton")
        self.retry_failed_button.setObjectName("secondaryButton")
        self.cancel_button.setObjectName("secondaryButton")

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("Все файлы", "all")
        self.filter_combo.addItem("В очереди", "pending")
        self.filter_combo.addItem("В работе", "converting")
        self.filter_combo.addItem("Готовые", "done")
        self.filter_combo.addItem("С ошибкой", "error")
        self.filter_combo.addItem("Отменённые", "cancelled")
        self.filter_combo.setMinimumWidth(180)

        self.summary_label = QLabel("Файлы не добавлены")
        self.queue_label = QLabel("")
        self.total_progress = QProgressBar()
        self.total_progress.setRange(0, 100)

        self._build_ui()
        self._connect_signals()
        self._build_menu()
        self._restore_queue()
        self.sync_waiting_gallery_from_settings()
        self._refresh_summary()

    def _build_ui(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(14)

        toolbar_card = QWidget()
        toolbar_card.setProperty("actionBar", True)
        toolbar_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        toolbar_layout = QVBoxLayout(toolbar_card)
        toolbar_layout.setContentsMargins(14, 12, 14, 12)
        toolbar_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        top_row.addWidget(self.add_button)
        top_row.addWidget(self.remove_button)
        top_row.addWidget(self.history_button)
        top_row.addWidget(self.retry_failed_button)
        top_row.addStretch(1)
        filter_label = QLabel("Показать")
        filter_label.setProperty("toolbarCaption", True)
        top_row.addWidget(filter_label)
        top_row.addWidget(self.filter_combo)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)
        bottom_row.addWidget(self.open_result_button)
        bottom_row.addWidget(self.details_button)
        bottom_row.addStretch(1)
        bottom_row.addWidget(self.cancel_button)
        bottom_row.addWidget(self.start_button)

        toolbar_layout.addLayout(top_row)
        toolbar_layout.addLayout(bottom_row)
        toolbar_card.setMaximumHeight(128)

        splitter = QSplitter()
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self.settings_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([860, 460])

        outer.addWidget(toolbar_card)
        outer.addWidget(splitter)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

    def _build_left_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self.waiting_gallery)
        layout.addWidget(self.file_list, stretch=1)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.queue_label)
        layout.addWidget(self.total_progress)
        return widget

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Файл")
        add_action = QAction("Добавить файлы", self)
        add_action.triggered.connect(self.choose_files)
        file_menu.addAction(add_action)

        clear_action = QAction("Очистить список", self)
        clear_action.triggered.connect(self.clear_files)
        file_menu.addAction(clear_action)

        history_action = QAction("Открыть историю", self)
        history_action.triggered.connect(self.show_history)
        file_menu.addAction(history_action)

    def _connect_signals(self) -> None:
        self.add_button.clicked.connect(self.choose_files)
        self.remove_button.clicked.connect(self.remove_selected)
        self.history_button.clicked.connect(self.show_history)
        self.open_result_button.clicked.connect(self.open_current_result)
        self.details_button.clicked.connect(self.show_selected_details)
        self.retry_failed_button.clicked.connect(self.retry_failed_items)
        self.start_button.clicked.connect(self.start_conversion)
        self.cancel_button.clicked.connect(self.cancel_conversion)
        self.file_list.itemDoubleClicked.connect(self.open_selected_result)
        self.file_list.itemSelectionChanged.connect(self.update_selection_actions)
        self.file_list.item_action_requested.connect(self.handle_item_action)
        self.file_list.customContextMenuRequested.connect(self.show_item_context_menu)
        self.filter_combo.currentIndexChanged.connect(self.apply_filter)
        self.settings_panel.theme_changed.connect(self.apply_theme)
        self.settings_panel.settings_changed.connect(self.persist_queue_state)
        self.settings_panel.settings_changed.connect(self.sync_waiting_gallery_from_settings)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        paths = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_file():
                paths.append(path)
        self.add_files(paths)
        event.acceptProposedAction()

    def choose_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите видеофайлы",
            "",
            "Видео (*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.mpeg *.mpg *.webm *.m4v);;Все файлы (*.*)",
        )
        self.add_files(Path(path) for path in files)

    def add_files(self, paths) -> None:
        added = 0
        first_added_key: str | None = None
        for path in paths:
            resolved = Path(path).expanduser().resolve()
            if not resolved.exists() or not resolved.is_file():
                continue
            key = str(resolved)
            if key in self._items_by_path:
                continue

            item = FileItem(path=resolved, size_bytes=resolved.stat().st_size)
            try:
                probe_result = probe_media(resolved)
                item.duration = probe_result.duration
                item.video_codec = probe_result.video_codec
                item.audio_codec = probe_result.audio_codec
                item.resolution = probe_result.resolution
                item.size_bytes = probe_result.size_bytes or item.size_bytes
                item.audio_streams = probe_result.audio_streams or []
                item.subtitle_streams = probe_result.subtitle_streams or []
                if item.audio_streams:
                    item.selected_audio_stream_index = item.audio_streams[0].index
            except Exception:
                pass

            self._items_by_path[key] = item
            self.file_list.add_file_item(item)
            added += 1
            if first_added_key is None:
                first_added_key = key

        if added:
            self.statusBar().showMessage(f"Добавлено файлов: {added}", 3000)
            self._refresh_summary()
            if first_added_key and self.file_list.count() == added:
                self.file_list.setCurrentRow(0)
            self.update_selection_actions()
            self.persist_queue_state()

    def remove_selected(self) -> None:
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Конвертация активна", "Нельзя удалять файлы во время конвертации.")
            return

        removed = self.file_list.remove_selected_files()
        for path in removed:
            self._items_by_path.pop(str(path.resolve()), None)
        self._refresh_summary()
        self.update_selection_actions()
        self.persist_queue_state()

    def clear_files(self) -> None:
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Конвертация активна", "Сначала остановите текущую задачу.")
            return
        self.file_list.clear_all()
        self._items_by_path.clear()
        self._refresh_summary()
        self.update_selection_actions()
        clear_queue_state()

    def start_conversion(self) -> None:
        self.start_conversion_for_items(self.items_ready_for_start())

    def start_conversion_for_items(self, items: list[FileItem]) -> None:
        if self.worker and self.worker.isRunning():
            return

        if not items:
            QMessageBox.information(self, "Нет файлов", "Нет файлов, подходящих для запуска конвертации.")
            return

        settings = self.settings_panel.to_settings()
        if not settings.save_next_to_source and settings.output_dir is None:
            QMessageBox.warning(self, "Папка вывода", "Выберите папку вывода или включите сохранение рядом с оригиналом.")
            return

        for item in items:
            item.status = "pending"
            item.progress = 0
            item.error_message = ""
            self.file_list.update_item(item)

        self.worker = ConversionWorker(items, settings)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.status_updated.connect(self.on_status_updated)
        self.worker.file_probed.connect(self.on_file_probed)
        self.worker.file_done.connect(self.on_file_done)
        self.worker.all_done.connect(self.on_all_done)
        self.worker.start()

        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.waiting_gallery.set_active(True)
        self.statusBar().showMessage("Конвертация запущена")
        self.apply_filter()
        self.persist_queue_state()

    def items_ready_for_start(self) -> list[FileItem]:
        return [
            item
            for item in self._items_by_path.values()
            if item.status in {"pending", "error", "cancelled"}
        ]

    def retry_failed_items(self) -> None:
        items = [item for item in self._items_by_path.values() if item.status in {"error", "cancelled"}]
        self.start_conversion_for_items(items)

    def cancel_conversion(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.statusBar().showMessage("Останавливаю текущую конвертацию...")

    def on_file_probed(
        self,
        path: str,
        duration: float,
        size_bytes: int,
        video_codec: str,
        audio_codec: str,
        resolution: str,
    ) -> None:
        item = self._items_by_path.get(path)
        if item is None:
            return
        item.duration = duration
        item.size_bytes = size_bytes or item.size_bytes
        item.video_codec = video_codec
        item.audio_codec = audio_codec
        item.resolution = resolution
        self.file_list.update_item(item)
        if self.current_selected_item() is item:
            self.settings_panel.set_current_item(item)
        self.persist_queue_state()

    def on_status_updated(self, path: str, status: str) -> None:
        item = self._items_by_path.get(path)
        if item is None:
            return
        item.status = status
        if status in {"pending", "cancelled", "error"} and item.progress == 0:
            item.progress = 0
        self.file_list.update_item(item)
        self._refresh_summary()
        self.apply_filter()
        self.persist_queue_state()

    def on_progress_updated(self, path: str, progress: int) -> None:
        item = self._items_by_path.get(path)
        if item is None:
            return
        item.progress = progress
        self.file_list.update_item(item)
        self._refresh_summary()
        self.apply_filter()
        self.persist_queue_state()

    def on_file_done(self, path: str, success: bool, message: str, output_path: str) -> None:
        item = self._items_by_path.get(path)
        if item is None:
            return

        item.output_path = Path(output_path) if output_path else None
        item.error_message = message
        if success:
            item.progress = 100
        self.file_list.update_item(item)
        self._refresh_summary()
        self.apply_filter()
        self.persist_queue_state()

    def on_all_done(self) -> None:
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.waiting_gallery.set_active(False)
        self._refresh_summary()

        completed = sum(1 for item in self._items_by_path.values() if item.status == "done")
        total = len(self._items_by_path)
        self.statusBar().showMessage(f"Завершено файлов: {completed}/{total}", 5000)
        self.update_selection_actions()

    def _refresh_summary(self) -> None:
        total = len(self._items_by_path)
        if total == 0:
            self.summary_label.setText("Файлы не добавлены")
            self.queue_label.setText("")
            self.total_progress.setValue(0)
            self.update_selection_actions()
            return

        done = sum(1 for item in self._items_by_path.values() if item.status == "done")
        failed = sum(1 for item in self._items_by_path.values() if item.status == "error")
        pending = sum(1 for item in self._items_by_path.values() if item.status == "pending")
        converting = sum(1 for item in self._items_by_path.values() if item.status == "converting")
        cancelled = sum(1 for item in self._items_by_path.values() if item.status == "cancelled")
        average_progress = int(sum(item.progress for item in self._items_by_path.values()) / total)
        self.summary_label.setText(f"Готово: {done}/{total} • Ошибок: {failed}")
        self.queue_label.setText(
            f"Очередь: ожидание {pending} • в работе {converting} • отменено {cancelled} • фильтр {self.filter_combo.currentText()}"
        )
        self.total_progress.setValue(average_progress)
        self.retry_failed_button.setEnabled(failed > 0 or cancelled > 0)
        self.apply_filter()

    def open_output_folder(self, item: FileItem) -> None:
        if not item.output_path:
            return
        QDesktopServices.openUrl(item.output_path.parent.as_uri())

    def open_source_file(self, item: FileItem) -> None:
        QDesktopServices.openUrl(item.path.as_uri())

    def open_selected_result(self, list_item) -> None:
        item = self.file_list.item_from_list_item(list_item)
        if item is None:
            return
        if item.output_path and item.output_path.exists():
            self.open_output_folder(item)
            return
        if item.status == "error" and item.error_message:
            self.show_error_dialog(item)

    def show_history(self) -> None:
        dialog = HistoryDialog(self)
        dialog.exec()

    def current_selected_item(self) -> FileItem | None:
        return self.file_list.selected_file_item()

    def update_selection_actions(self) -> None:
        item = self.current_selected_item()
        has_item = item is not None
        can_open_result = bool(item and item.output_path and item.output_path.exists())
        self.details_button.setEnabled(has_item)
        self.open_result_button.setEnabled(can_open_result)
        self.settings_panel.set_current_item(item)

    def apply_filter(self) -> None:
        filter_value = str(self.filter_combo.currentData())
        for item in self._items_by_path.values():
            hidden = filter_value != "all" and item.status != filter_value
            self.file_list.set_item_hidden_by_path(item.path, hidden)

    def open_current_result(self) -> None:
        item = self.current_selected_item()
        if item is None:
            return
        if item.output_path and item.output_path.exists():
            self.open_output_folder(item)

    def show_selected_details(self) -> None:
        item = self.current_selected_item()
        if item is None:
            return
        dialog = FileDetailsDialog(item, self)
        dialog.exec()

    def apply_theme(self, theme: str) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(load_stylesheet(theme))

    def show_error_dialog(self, item: FileItem) -> None:
        dialog = ErrorDialog(item, self)
        dialog.exec()

    def remove_item(self, item: FileItem) -> None:
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Конвертация активна", "Нельзя удалять файлы во время конвертации.")
            return
        self.file_list.clearSelection()
        for index in range(self.file_list.count()):
            list_item = self.file_list.item(index)
            candidate = self.file_list.item_from_list_item(list_item)
            if candidate is None or candidate.path != item.path:
                continue
            list_item.setSelected(True)
            break
        self.remove_selected()

    def handle_item_action(self, path: str, action: str) -> None:
        item = self._items_by_path.get(path)
        if item is None:
            return
        if action == "open_result" and item.output_path and item.output_path.exists():
            self.open_output_folder(item)
            return
        if action == "show_details":
            dialog = FileDetailsDialog(item, self)
            dialog.exec()
            return
        if action == "show_error" and item.error_message:
            self.show_error_dialog(item)
            return
        if action == "retry":
            self.start_conversion_for_items([item])

    def show_item_context_menu(self, position) -> None:
        list_item = self.file_list.itemAt(position)
        if list_item is None:
            return
        item = self.file_list.item_from_list_item(list_item)
        if item is None:
            return

        self.file_list.setCurrentItem(list_item)

        menu = QMenu(self)
        open_source_action = menu.addAction("Открыть исходный файл")
        open_result_action = menu.addAction("Открыть папку результата")
        details_action = menu.addAction("Показать детали")
        error_action = menu.addAction("Показать ошибку FFmpeg")
        retry_action = menu.addAction("Повторить файл")
        menu.addSeparator()
        remove_action = menu.addAction("Удалить из списка")

        open_result_action.setEnabled(bool(item.output_path and item.output_path.exists()))
        error_action.setEnabled(bool(item.error_message))
        retry_action.setEnabled(item.status in {"error", "cancelled", "pending"})

        chosen = menu.exec(self.file_list.mapToGlobal(position))
        if chosen == open_source_action:
            self.open_source_file(item)
        elif chosen == open_result_action:
            self.open_output_folder(item)
        elif chosen == details_action:
            self.show_selected_details()
        elif chosen == error_action:
            self.show_error_dialog(item)
        elif chosen == retry_action:
            self.start_conversion_for_items([item])
        elif chosen == remove_action:
            self.remove_item(item)

    def _restore_queue(self) -> None:
        restored_items = load_queue_state()
        for item in restored_items:
            key = str(item.path.resolve())
            self._items_by_path[key] = item
            self.file_list.add_file_item(item)
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
            self.update_selection_actions()

    def persist_queue_state(self) -> None:
        save_queue_state(list(self._items_by_path.values()))

    def sync_waiting_gallery_from_settings(self) -> None:
        self.waiting_gallery.set_image_directory(self.settings_panel.waiting_photos_dir())
        running = bool(self.worker and self.worker.isRunning())
        self.waiting_gallery.set_active(running)
