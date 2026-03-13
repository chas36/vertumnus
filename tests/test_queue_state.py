from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.queue_state import item_from_dict, item_to_dict
from models import FileItem, MediaStream


class QueueStateTests(unittest.TestCase):
    def test_item_roundtrip_preserves_stream_selection(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "movie.mkv"
            output = Path(tmp) / "movie.mp4"
            source.touch()
            output.touch()

            item = FileItem(
                path=source,
                status="done",
                progress=100,
                duration=120.0,
                size_bytes=1024,
                video_codec="h264",
                audio_codec="aac",
                resolution="1280x720",
                output_path=output,
                audio_streams=[MediaStream(index=1, stream_type="audio", codec="aac", language="rus")],
                subtitle_streams=[MediaStream(index=3, stream_type="subtitle", codec="subrip", language="eng")],
                selected_audio_stream_index=1,
                selected_subtitle_stream_index=3,
                subtitle_enabled=True,
                subtitle_default=True,
            )

            restored = item_from_dict(item_to_dict(item))
            self.assertIsNotNone(restored)
            assert restored is not None
            self.assertEqual(restored.path, source)
            self.assertEqual(restored.output_path, output)
            self.assertEqual(restored.selected_audio_stream_index, 1)
            self.assertEqual(restored.selected_subtitle_stream_index, 3)
            self.assertTrue(restored.subtitle_enabled)
            self.assertTrue(restored.subtitle_default)
            self.assertEqual(restored.audio_streams[0].language, "rus")

    def test_restore_converting_item_resets_to_pending(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "clip.mov"
            source.touch()
            payload = {
                "path": str(source),
                "status": "converting",
                "progress": 55,
                "audio_streams": [],
                "subtitle_streams": [],
            }
            restored = item_from_dict(payload)
            self.assertIsNotNone(restored)
            assert restored is not None
            self.assertEqual(restored.status, "pending")
            self.assertEqual(restored.progress, 0)


if __name__ == "__main__":
    unittest.main()
