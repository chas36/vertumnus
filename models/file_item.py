from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from models.media_stream import MediaStream

FileStatus = Literal["pending", "converting", "done", "error", "cancelled"]


@dataclass(slots=True)
class FileItem:
    path: Path
    status: FileStatus = "pending"
    progress: int = 0
    duration: float = 0.0
    error_message: str = ""
    size_bytes: int = 0
    video_codec: str = ""
    audio_codec: str = ""
    resolution: str = ""
    output_path: Path | None = None
    audio_streams: list[MediaStream] = field(default_factory=list)
    subtitle_streams: list[MediaStream] = field(default_factory=list)
    selected_audio_stream_index: int | None = None
    selected_subtitle_stream_index: int | None = None
    subtitle_enabled: bool = False
    subtitle_default: bool = False
    history_notes: dict[str, str] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        return self.path.name
