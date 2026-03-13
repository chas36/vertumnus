from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from models.file_item import FileItem
from ui.file_item_widget import FileItemWidget


class FileListWidget(QListWidget):
    item_action_requested = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setSpacing(8)
        self.setAlternatingRowColors(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._items: dict[str, FileItem] = {}

    def has_path(self, path: Path) -> bool:
        return str(path.resolve()) in self._items

    def add_file_item(self, item: FileItem) -> None:
        key = str(item.path.resolve())
        if key in self._items:
            return

        self._items[key] = item
        list_item = QListWidgetItem()
        list_item.setData(Qt.ItemDataRole.UserRole, key)
        list_item.setSizeHint(QSize(0, 108))

        widget = FileItemWidget(item)
        widget.action_requested.connect(self.item_action_requested)
        self.addItem(list_item)
        self.setItemWidget(list_item, widget)

    def remove_selected_files(self) -> list[Path]:
        removed: list[Path] = []
        for list_item in self.selectedItems():
            key = list_item.data(Qt.ItemDataRole.UserRole)
            row = self.row(list_item)
            self.takeItem(row)
            item = self._items.pop(key, None)
            if item:
                removed.append(item.path)
        return removed

    def all_items(self) -> list[FileItem]:
        return list(self._items.values())

    def update_item(self, item: FileItem) -> None:
        key = str(item.path.resolve())
        if key not in self._items:
            return
        self._items[key] = item

        for index in range(self.count()):
            list_item = self.item(index)
            if list_item.data(Qt.ItemDataRole.UserRole) != key:
                continue
            widget = self.itemWidget(list_item)
            if isinstance(widget, FileItemWidget):
                widget.update_item(item)
            break

    def set_item_hidden_by_path(self, path: Path, hidden: bool) -> None:
        key = str(path.resolve())
        for index in range(self.count()):
            list_item = self.item(index)
            if list_item.data(Qt.ItemDataRole.UserRole) != key:
                continue
            list_item.setHidden(hidden)
            break

    def item_from_list_item(self, list_item: QListWidgetItem) -> FileItem | None:
        key = list_item.data(Qt.ItemDataRole.UserRole)
        return self._items.get(key)

    def selected_file_item(self) -> FileItem | None:
        selected = self.selectedItems()
        if not selected:
            return None
        return self.item_from_list_item(selected[0])

    def clear_all(self) -> None:
        super().clear()
        self._items.clear()
