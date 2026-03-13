from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from models.media_stream import MediaStream


@dataclass(slots=True)
class ProbeResult:
    duration: float = 0.0
    size_bytes: int = 0
    video_codec: str = ""
    audio_codec: str = ""
    width: int = 0
    height: int = 0
    audio_streams: list[MediaStream] | None = None
    subtitle_streams: list[MediaStream] | None = None

    @property
    def resolution(self) -> str:
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return ""


def _bundled_binary_path(binary_name: str) -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(getattr(sys, "_MEIPASS"))
    else:
        base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "assets" / "ffmpeg" / binary_name


def find_ffprobe_binary() -> str:
    env_path = os.environ.get("VERTUMNUS_FFPROBE")
    if env_path:
        return env_path

    names = ["ffprobe.exe", "ffprobe"] if os.name == "nt" else ["ffprobe", "ffprobe.exe"]
    for name in names:
        bundled = _bundled_binary_path(name)
        if bundled.exists():
            return str(bundled)

    for name in names:
        system_binary = shutil.which(name)
        if system_binary:
            return system_binary

    raise FileNotFoundError("Не найден ffprobe. Добавьте бинарник в assets/ffmpeg или в PATH.")


def parse_probe_payload(payload: dict) -> ProbeResult:
    streams = payload.get("streams", [])
    fmt = payload.get("format", {})

    video_stream = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), {})
    audio_streams = [_parse_stream(item) for item in streams if item.get("codec_type") == "audio"]
    subtitle_streams = [_parse_stream(item) for item in streams if item.get("codec_type") == "subtitle"]

    try:
        duration = float(fmt.get("duration") or 0.0)
    except (TypeError, ValueError):
        duration = 0.0

    try:
        size_bytes = int(fmt.get("size") or 0)
    except (TypeError, ValueError):
        size_bytes = 0

    return ProbeResult(
        duration=duration,
        size_bytes=size_bytes,
        video_codec=str(video_stream.get("codec_name") or ""),
        audio_codec=str(audio_stream.get("codec_name") or ""),
        width=int(video_stream.get("width") or 0),
        height=int(video_stream.get("height") or 0),
        audio_streams=audio_streams,
        subtitle_streams=subtitle_streams,
    )


def _parse_stream(stream: dict) -> MediaStream:
    tags = stream.get("tags", {})
    return MediaStream(
        index=int(stream.get("index") or 0),
        stream_type=str(stream.get("codec_type") or ""),
        codec=str(stream.get("codec_name") or ""),
        language=str(tags.get("language") or ""),
        title=str(tags.get("title") or ""),
        channels=int(stream.get("channels") or 0),
    )


def probe_media(path: Path, ffprobe_binary: str | None = None) -> ProbeResult:
    binary = ffprobe_binary or find_ffprobe_binary()
    command = [
        binary,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "ffprobe завершился с ошибкой."
        raise RuntimeError(stderr)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Не удалось разобрать ответ ffprobe.") from exc

    return parse_probe_payload(payload)
