# -*- coding: utf-8 -*-
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from video_upscaler_core import UpscaleSettings, VideoUpscalePipeline, _parse_ffmpeg_time, format_duration


class VideoUpscalerCoreTests(unittest.TestCase):
    def test_duration_format(self) -> None:
        self.assertEqual(format_duration(3661.9), "01:01:01")

    def test_ffmpeg_time_parser(self) -> None:
        self.assertAlmostEqual(_parse_ffmpeg_time("01:02:03.500000"), 3723.5)

    def test_cache_key_changes_with_settings(self) -> None:
        with TemporaryDirectory() as temp:
            source = Path(temp) / "source.mp4"
            source.write_bytes(b"not-a-real-video")
            first = UpscaleSettings(str(source), str(Path(temp) / "a.mp4"), scale=2)
            second = UpscaleSettings(str(source), str(Path(temp) / "a.mp4"), scale=4)
            self.assertNotEqual(VideoUpscalePipeline(first).cache_dir, VideoUpscalePipeline(second).cache_dir)


if __name__ == "__main__":
    unittest.main()
