# -*- coding: utf-8 -*-
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from video_upscaler_core import (
    ImageUpscalePipeline,
    ImageUpscaleSettings,
    UpscaleSettings,
    VideoUpscalePipeline,
    _parse_ffmpeg_time,
    format_duration,
)


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

    def test_image_folder_targets_keep_same_stem_files_distinct(self) -> None:
        with TemporaryDirectory() as temp:
            source = Path(temp) / "images"
            output = Path(temp) / "results"
            source.mkdir()
            (source / "sample.jpg").write_bytes(b"jpg")
            (source / "sample.png").write_bytes(b"png")
            settings = ImageUpscaleSettings(
                input_path=str(source),
                output_path=str(output),
                scale=4,
                backend="lanczos",
                output_format="webp",
            )
            pipeline = ImageUpscalePipeline(settings)
            inputs = pipeline._collect_inputs()
            targets = pipeline._targets(inputs)
            self.assertEqual(len(inputs), 2)
            self.assertEqual(len(set(targets)), 2)
            self.assertTrue(all(path.name.endswith("_upscaled_4x.webp") for path in targets))

    def test_image_folder_ignores_previous_results(self) -> None:
        with TemporaryDirectory() as temp:
            source = Path(temp)
            (source / "original.png").write_bytes(b"png")
            (source / "original_upscaled_2x.png").write_bytes(b"png")
            settings = ImageUpscaleSettings(str(source), str(source / "out"), backend="lanczos")
            inputs = ImageUpscalePipeline(settings)._collect_inputs()
            self.assertEqual([path.name for path in inputs], ["original.png"])


if __name__ == "__main__":
    unittest.main()
