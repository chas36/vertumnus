from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from models.conversion_settings import ConversionSettings
from models.file_item import FileItem

ProgressCallback = Callable[[int], None]
CancelCallback = Callable[[], bool]


def _bundled_binary_path(binary_name: str) -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(getattr(sys, "_MEIPASS"))
    else:
        base_dir = Path(__file__).resolve().parent.parent
    return base_dir / "assets" / "ffmpeg" / binary_name


def find_ffmpeg_binary() -> str:
    env_path = os.environ.get("VERTUMNUS_FFMPEG")
    if env_path:
        return env_path

    names = ["ffmpeg.exe", "ffmpeg"] if os.name == "nt" else ["ffmpeg", "ffmpeg.exe"]
    for name in names:
        bundled = _bundled_binary_path(name)
        if bundled.exists():
            return str(bundled)

    for name in names:
        system_binary = shutil.which(name)
        if system_binary:
            return system_binary

    raise FileNotFoundError("Не найден ffmpeg. Добавьте бинарник в assets/ffmpeg или в PATH.")


def ensure_unique_output_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def resolve_output_path(source_path: Path, settings: ConversionSettings) -> Path:
    base_dir = settings.target_dir_for(source_path)
    output_path = base_dir / f"{source_path.stem}.mp4"
    return ensure_unique_output_path(output_path)


def _apply_resolution(command: list[str], resolution: str) -> None:
    if resolution == "original":
        return
    mapping = {
        "1080p": "1920:1080",
        "720p": "1280:720",
        "480p": "854:480",
        "1920x1080": "1920:1080",
        "1280x720": "1280:720",
        "854x480": "854:480",
    }
    target = mapping.get(resolution, "")
    if target:
        command.extend(["-vf", f"scale={target}:force_original_aspect_ratio=decrease"])


def build_ffmpeg_command(
    source_path: Path,
    output_path: Path,
    settings: ConversionSettings,
    file_item: FileItem | None = None,
    ffmpeg_binary: str | None = None,
) -> list[str]:
    binary = ffmpeg_binary or find_ffmpeg_binary()
    audio_map = "0:a:0?"
    if file_item and file_item.selected_audio_stream_index is not None:
        audio_map = f"0:{file_item.selected_audio_stream_index}"
    command = [
        binary,
        "-y",
        "-i",
        str(source_path),
        "-map",
        "0:v:0",
        "-map",
        audio_map,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        settings.preset,
        "-c:a",
        "aac",
        "-profile:a",
        "aac_low",
        "-b:a",
        settings.audio_bitrate,
        "-ac",
        "2",
        "-ar",
        "48000",
        "-movflags",
        "+faststart",
    ]

    if file_item and file_item.subtitle_enabled and file_item.selected_subtitle_stream_index is not None:
        command.extend(
            [
                "-map",
                f"0:{file_item.selected_subtitle_stream_index}",
                "-c:s",
                "mov_text",
                "-disposition:s:0",
                "default" if file_item.subtitle_default else "0",
            ]
        )

    if settings.profile == "projector":
        command.extend(["-profile:v", "baseline", "-level", "3.0"])
    if settings.video_bitrate != "auto":
        command.extend(["-b:v", settings.video_bitrate])
    if settings.fps > 0:
        command.extend(["-r", str(settings.fps)])
    _apply_resolution(command, settings.resolution)

    command.extend(
        [
            "-progress",
            "pipe:1",
            "-nostats",
            str(output_path),
        ]
    )
    return command


def convert_with_progress(
    source_path: Path,
    output_path: Path,
    settings: ConversionSettings,
    duration_seconds: float,
    file_item: FileItem | None = None,
    progress_callback: ProgressCallback | None = None,
    cancel_callback: CancelCallback | None = None,
    ffmpeg_binary: str | None = None,
) -> tuple[bool, str]:
    command = build_ffmpeg_command(source_path, output_path, settings, file_item=file_item, ffmpeg_binary=ffmpeg_binary)
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    last_progress = 0
    stderr_lines: list[str] = []
    try:
        if process.stdout is None:
            raise RuntimeError("Не удалось открыть stdout ffmpeg.")

        for raw_line in process.stdout:
            if cancel_callback and cancel_callback():
                process.kill()
                process.wait(timeout=5)
                if output_path.exists():
                    output_path.unlink(missing_ok=True)
                return False, "Конвертация отменена пользователем."

            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("out_time_ms=") and duration_seconds > 0:
                try:
                    out_time_us = int(line.split("=", 1)[1])
                except ValueError:
                    continue
                progress = min(100, max(0, int(out_time_us / (duration_seconds * 1_000_000) * 100)))
                if progress > last_progress:
                    last_progress = progress
                    if progress_callback:
                        progress_callback(progress)

        if process.stderr is not None:
            stderr_lines = [line.strip() for line in process.stderr.readlines() if line.strip()]
        return_code = process.wait()
    finally:
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()

    if return_code == 0:
        if progress_callback:
            progress_callback(100)
        return True, ""

    if output_path.exists():
        output_path.unlink(missing_ok=True)
    return False, stderr_lines[-1] if stderr_lines else "FFmpeg завершился с ошибкой."
