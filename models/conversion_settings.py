from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ConversionSettings:
    output_dir: Path | None = None
    resolution: str = "original"
    fps: int = 0
    video_bitrate: str = "auto"
    audio_bitrate: str = "128k"
    preset: str = "medium"
    profile: str = "projector"
    save_next_to_source: bool = True

    def target_dir_for(self, source_path: Path) -> Path:
        if self.save_next_to_source or self.output_dir is None:
            return source_path.parent
        return self.output_dir
