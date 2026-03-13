from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


def history_path() -> Path:
    directory = Path.home() / ".mp4_converter"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "history.json"


def load_history() -> list[dict[str, Any]]:
    path = history_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def append_history(entry: dict[str, Any]) -> None:
    payload = load_history()
    payload.append({"timestamp": datetime.now(UTC).isoformat(), **entry})
    history_path().write_text(
        json.dumps(payload[-200:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_history() -> None:
    history_path().write_text("[]", encoding="utf-8")
