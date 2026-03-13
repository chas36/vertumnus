from __future__ import annotations

from dataclasses import dataclass


TEXT_SUBTITLE_CODECS = {"subrip", "srt", "ass", "ssa", "mov_text", "webvtt", "text"}


@dataclass(slots=True)
class MediaStream:
    index: int
    stream_type: str
    codec: str = ""
    language: str = ""
    title: str = ""
    channels: int = 0

    @property
    def supports_mp4_subtitle(self) -> bool:
        return self.stream_type != "subtitle" or self.codec in TEXT_SUBTITLE_CODECS

    @property
    def label(self) -> str:
        parts = [f"#{self.index}"]
        if self.language:
            parts.append(self.language)
        if self.title:
            parts.append(self.title)
        if self.codec:
            parts.append(self.codec)
        if self.channels:
            parts.append(f"{self.channels} ch")
        return " • ".join(parts)
