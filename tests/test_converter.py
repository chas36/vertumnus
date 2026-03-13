from pathlib import Path
import json
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from core.converter import (
    build_ffmpeg_command,
    convert_with_progress,
    ensure_unique_output_path,
    resolve_output_path,
)
from core.probe import probe_media
from models import FileItem, MediaStream
from models.conversion_settings import ConversionSettings


class ConverterTests(unittest.TestCase):
    def test_build_ffmpeg_command_for_projector_profile(self) -> None:
        settings = ConversionSettings(profile="projector")
        command = build_ffmpeg_command(
            Path("input.avi"),
            Path("output.mp4"),
            settings,
            ffmpeg_binary="ffmpeg",
        )
        joined = " ".join(command)
        self.assertIn("-profile:v baseline", joined)
        self.assertIn("-map 0:v:0", joined)
        self.assertIn("-map 0:a:0?", joined)
        self.assertIn("-profile:a aac_low", joined)
        self.assertIn("-ac 2", joined)
        self.assertIn("-ar 48000", joined)
        self.assertIn("-movflags +faststart", joined)
        self.assertIn("output.mp4", joined)

    def test_build_ffmpeg_command_applies_resolution_for_projector(self) -> None:
        settings = ConversionSettings(profile="projector", resolution="720p")
        command = build_ffmpeg_command(
            Path("input.avi"),
            Path("output.mp4"),
            settings,
            ffmpeg_binary="ffmpeg",
        )
        joined = " ".join(command)
        self.assertIn("scale=1280:720:force_original_aspect_ratio=decrease", joined)

    def test_build_ffmpeg_command_uses_selected_streams(self) -> None:
        settings = ConversionSettings(profile="custom")
        item = FileItem(
            path=Path("input.mkv"),
            audio_streams=[MediaStream(index=2, stream_type="audio", codec="aac", language="eng")],
            subtitle_streams=[MediaStream(index=4, stream_type="subtitle", codec="subrip", language="eng")],
            selected_audio_stream_index=2,
            selected_subtitle_stream_index=4,
            subtitle_enabled=True,
            subtitle_default=True,
        )
        command = build_ffmpeg_command(
            Path("input.mkv"),
            Path("output.mp4"),
            settings,
            file_item=item,
            ffmpeg_binary="ffmpeg",
        )
        joined = " ".join(command)
        self.assertIn("-map 0:2", joined)
        self.assertIn("-map 0:4", joined)
        self.assertIn("-c:s mov_text", joined)
        self.assertIn("-disposition:s:0 default", joined)

    def test_resolve_output_path_renames_existing_file(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "video.avi"
            source.touch()
            existing = Path(tmp) / "video.mp4"
            existing.touch()
            settings = ConversionSettings(output_dir=Path(tmp), save_next_to_source=False)

            output = resolve_output_path(source, settings)
            self.assertEqual(output.name, "video_1.mp4")

    def test_unique_output_path_returns_same_when_free(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "free.mp4"
            self.assertEqual(ensure_unique_output_path(target), target)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe not available")
    def test_convert_with_progress_keeps_audio_stream(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "sample_input.mp4"
            output = tmp_path / "sample_output.mp4"

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc=size=640x360:rate=25",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=1000:sample_rate=48000",
                    "-t",
                    "2",
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    str(source),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            source_probe = probe_media(source, ffprobe_binary="ffprobe")
            settings = ConversionSettings(profile="projector")
            success, message = convert_with_progress(
                source,
                output,
                settings,
                duration_seconds=source_probe.duration,
                ffmpeg_binary="ffmpeg",
            )

            self.assertTrue(success, msg=message)
            result_probe = probe_media(output, ffprobe_binary="ffprobe")
            self.assertEqual(result_probe.audio_codec, "aac")
            self.assertEqual(result_probe.video_codec, "h264")

            audio_probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_entries",
                    "stream=codec_name,sample_rate,channels",
                    "-select_streams",
                    "a:0",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(audio_probe.stdout)
            stream = payload["streams"][0]
            self.assertEqual(stream["codec_name"], "aac")
            self.assertEqual(int(stream["channels"]), 2)
            self.assertEqual(stream["sample_rate"], "48000")


if __name__ == "__main__":
    unittest.main()
