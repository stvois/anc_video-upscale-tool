"""Actual encoder output must meet the requested average video bitrate."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from video_upscaler_core import (VideoDenoisePipeline, VideoDenoiseSettings,
                                 UpscaleSettings, VideoUpscalePipeline,
                                 find_ffmpeg, find_ffprobe, nvenc_available)


class BitrateTests(unittest.TestCase):
    @unittest.skipUnless(find_ffmpeg(), 'FFmpeg required')
    def test_upscale_bitrate_policy_mp4_mkv_and_bit_depth(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source.mp4'
            subprocess.run([find_ffmpeg(), '-v', 'error', '-f', 'lavfi', '-i',
                            'testsrc2=size=128x96:rate=12:duration=2', '-y', str(source)], check=True)
            for codec, suffix, pixel in [('h264', 'mp4', 'yuv420p'), ('h265', 'mp4', 'yuv420p'),
                                          ('h265_10', 'mp4', 'yuv420p10le'), ('h265_10', 'mkv', 'yuv420p10le')]:
                with self.subTest(codec=codec, suffix=suffix):
                    output = root / f'{codec}.{suffix}'
                    VideoUpscalePipeline(UpscaleSettings(
                        str(source), str(output), backend='lanczos', denoise='none', codec=codec,
                        preserve_bitrate=True, minimum_mbps=2, hardware_encode=False,
                        keep_cache=False)).run()
                    stream = json.loads(subprocess.check_output([
                        find_ffprobe(), '-v', 'error', '-select_streams', 'v:0',
                        '-show_entries', 'stream=pix_fmt,width,height', '-of', 'json', str(output),
                    ]))['streams'][0]
                    self.assertEqual(stream['pix_fmt'], pixel)
                    self.assertEqual((stream['width'], stream['height']), (256, 192))

    @unittest.skipUnless(find_ffmpeg(), 'FFmpeg required')
    def test_minimum_bitrate_cpu_and_available_nvenc(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'source.mp4'
            subprocess.run([find_ffmpeg(), '-v', 'error', '-f', 'lavfi', '-i',
                            'testsrc2=size=256x144:rate=24:duration=2', '-y', str(source)], check=True)
            for hardware in ([False, True] if nvenc_available() else [False]):
                with self.subTest(hardware=hardware):
                    output = root / f'clean{hardware}.mp4'
                    VideoDenoisePipeline(VideoDenoiseSettings(
                        str(source), str(output), preserve_bitrate=True,
                        minimum_mbps=15, hardware_encode=hardware)).run()
                    stream = json.loads(subprocess.check_output([
                        find_ffprobe(), '-v', 'error', '-select_streams', 'v:0',
                        '-show_entries', 'stream=bit_rate,pix_fmt', '-of', 'json', str(output),
                    ]))['streams'][0]
                    self.assertGreaterEqual(int(stream['bit_rate']), 15_000_000)
                    self.assertEqual(stream['pix_fmt'], 'yuv420p10le')


if __name__ == '__main__':
    unittest.main()
