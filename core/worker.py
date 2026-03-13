from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.converter import convert_with_progress, resolve_output_path
from core.history import append_history
from core.probe import ProbeResult, probe_media
from models.conversion_settings import ConversionSettings
from models.file_item import FileItem


class ConversionWorker(QThread):
    progress_updated = Signal(str, int)
    status_updated = Signal(str, str)
    file_probed = Signal(str, float, int, str, str, str)
    file_done = Signal(str, bool, str, str)
    all_done = Signal()

    def __init__(self, items: list[FileItem], settings: ConversionSettings) -> None:
        super().__init__()
        self._items = items
        self._settings = settings
        self._cancel_requested = False

    def cancel(self) -> None:
        self._cancel_requested = True

    def _should_cancel(self) -> bool:
        return self._cancel_requested

    def _probe_if_needed(self, item: FileItem) -> ProbeResult:
        if item.duration > 0 or item.size_bytes > 0:
            return ProbeResult(
                duration=item.duration,
                size_bytes=item.size_bytes,
                video_codec=item.video_codec,
                audio_codec=item.audio_codec,
                width=int(item.resolution.split("x")[0]) if "x" in item.resolution else 0,
                height=int(item.resolution.split("x")[1]) if "x" in item.resolution else 0,
            )
        return probe_media(item.path)

    def run(self) -> None:
        try:
            for item in self._items:
                if self._cancel_requested:
                    self.status_updated.emit(str(item.path), "cancelled")
                    continue

                self.status_updated.emit(str(item.path), "converting")
                try:
                    probe_result = self._probe_if_needed(item)
                except Exception as exc:  # noqa: BLE001
                    message = str(exc)
                    self.status_updated.emit(str(item.path), "error")
                    self.file_done.emit(str(item.path), False, message, "")
                    append_history(
                        {
                            "source": str(item.path),
                            "status": "error",
                            "message": message,
                        }
                    )
                    continue

                self.file_probed.emit(
                    str(item.path),
                    probe_result.duration,
                    probe_result.size_bytes,
                    probe_result.video_codec,
                    probe_result.audio_codec,
                    probe_result.resolution,
                )

                output_path = resolve_output_path(item.path, self._settings)
                success, message = convert_with_progress(
                    item.path,
                    output_path,
                    self._settings,
                    duration_seconds=probe_result.duration,
                    file_item=item,
                    progress_callback=lambda percent, path=str(item.path): self.progress_updated.emit(path, percent),
                    cancel_callback=self._should_cancel,
                )

                final_status = "done" if success else "cancelled" if self._cancel_requested else "error"
                if not success and output_path.exists():
                    Path(output_path).unlink(missing_ok=True)

                self.status_updated.emit(str(item.path), final_status)
                self.file_done.emit(str(item.path), success, message, str(output_path) if success else "")
                append_history(
                    {
                        "source": str(item.path),
                        "output": str(output_path) if success else "",
                        "status": final_status,
                        "message": message,
                    }
                )

                if self._cancel_requested:
                    break
        finally:
            self.all_done.emit()
