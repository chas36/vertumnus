from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.file_item import FileItem
from models.media_stream import MediaStream


def queue_state_path() -> Path:
    directory = Path.home() / ".mp4_converter"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "queue.json"


def _stream_to_dict(stream: MediaStream) -> dict[str, Any]:
    return {
        "index": stream.index,
        "stream_type": stream.stream_type,
        "codec": stream.codec,
        "language": stream.language,
        "title": stream.title,
        "channels": stream.channels,
    }


def _stream_from_dict(payload: dict[str, Any]) -> MediaStream:
    return MediaStream(
        index=int(payload.get("index") or 0),
        stream_type=str(payload.get("stream_type") or ""),
        codec=str(payload.get("codec") or ""),
        language=str(payload.get("language") or ""),
        title=str(payload.get("title") or ""),
        channels=int(payload.get("channels") or 0),
    )


def item_to_dict(item: FileItem) -> dict[str, Any]:
    return {
        "path": str(item.path),
        "status": item.status,
        "progress": item.progress,
        "duration": item.duration,
        "error_message": item.error_message,
        "size_bytes": item.size_bytes,
        "video_codec": item.video_codec,
        "audio_codec": item.audio_codec,
        "resolution": item.resolution,
        "output_path": str(item.output_path) if item.output_path else "",
        "audio_streams": [_stream_to_dict(stream) for stream in item.audio_streams],
        "subtitle_streams": [_stream_to_dict(stream) for stream in item.subtitle_streams],
        "selected_audio_stream_index": item.selected_audio_stream_index,
        "selected_subtitle_stream_index": item.selected_subtitle_stream_index,
        "subtitle_enabled": item.subtitle_enabled,
        "subtitle_default": item.subtitle_default,
    }


def item_from_dict(payload: dict[str, Any]) -> FileItem | None:
    path = Path(str(payload.get("path") or "")).expanduser()
    if not path.exists() or not path.is_file():
        return None

    output_raw = str(payload.get("output_path") or "")
    output_path = Path(output_raw).expanduser() if output_raw else None

    item = FileItem(
        path=path,
        status=str(payload.get("status") or "pending"),
        progress=int(payload.get("progress") or 0),
        duration=float(payload.get("duration") or 0.0),
        error_message=str(payload.get("error_message") or ""),
        size_bytes=int(payload.get("size_bytes") or 0),
        video_codec=str(payload.get("video_codec") or ""),
        audio_codec=str(payload.get("audio_codec") or ""),
        resolution=str(payload.get("resolution") or ""),
        output_path=output_path if output_path and output_path.exists() else None,
        audio_streams=[_stream_from_dict(stream) for stream in payload.get("audio_streams", [])],
        subtitle_streams=[_stream_from_dict(stream) for stream in payload.get("subtitle_streams", [])],
        selected_audio_stream_index=payload.get("selected_audio_stream_index"),
        selected_subtitle_stream_index=payload.get("selected_subtitle_stream_index"),
        subtitle_enabled=bool(payload.get("subtitle_enabled", False)),
        subtitle_default=bool(payload.get("subtitle_default", False)),
    )

    if item.status == "converting":
        item.status = "pending"
        item.progress = 0
    return item


def save_queue_state(items: list[FileItem]) -> None:
    payload = [item_to_dict(item) for item in items]
    queue_state_path().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_queue_state() -> list[FileItem]:
    path = queue_state_path()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    items: list[FileItem] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        item = item_from_dict(entry)
        if item is not None:
            items.append(item)
    return items


def clear_queue_state() -> None:
    queue_state_path().write_text("[]", encoding="utf-8")
