from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

from ui.main_window import MainWindow
from ui.theme import load_stylesheet


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MP4 Converter")
    app.setOrganizationName("Vertumnus")

    settings = QSettings("Vertumnus", "MP4Converter")
    app.setStyleSheet(load_stylesheet(str(settings.value("theme", "dark"))))

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
