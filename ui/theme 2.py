from __future__ import annotations

from pathlib import Path


def stylesheet_path(theme: str) -> Path:
    base = Path(__file__).resolve().parent
    mapping = {
        "dark": base / "styles.qss",
        "light": base / "styles_light.qss",
    }
    return mapping.get(theme, mapping["dark"])


def load_stylesheet(theme: str) -> str:
    path = stylesheet_path(theme)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
