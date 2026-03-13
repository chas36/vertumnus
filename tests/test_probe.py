import unittest

from core.probe import parse_probe_payload
from models.media_stream import MediaStream


class ProbeTests(unittest.TestCase):
    def test_parse_probe_payload(self) -> None:
        payload = {
            "format": {"duration": "125.42", "size": "1048576"},
            "streams": [
                {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080},
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "channels": 2,
                    "tags": {"language": "rus", "title": "Dub"},
                },
                {
                    "index": 2,
                    "codec_type": "subtitle",
                    "codec_name": "subrip",
                    "tags": {"language": "eng", "title": "Full"},
                },
            ],
        }

        result = parse_probe_payload(payload)
        self.assertAlmostEqual(result.duration, 125.42)
        self.assertEqual(result.size_bytes, 1048576)
        self.assertEqual(result.video_codec, "h264")
        self.assertEqual(result.audio_codec, "aac")
        self.assertEqual(result.resolution, "1920x1080")
        self.assertEqual(result.audio_streams, [MediaStream(index=1, stream_type="audio", codec="aac", language="rus", title="Dub", channels=2)])
        self.assertEqual(result.subtitle_streams, [MediaStream(index=2, stream_type="subtitle", codec="subrip", language="eng", title="Full", channels=0)])


if __name__ == "__main__":
    unittest.main()
