"""Checks actual FFmpeg dark-region mask, not just filter string creation."""
import array
import subprocess
import unittest

from video_upscaler_core import VideoDenoisePipeline, VideoDenoiseSettings, find_ffmpeg


class ShadowFilterTests(unittest.TestCase):
    @unittest.skipUnless(find_ffmpeg(), 'FFmpeg required')
    def test_glow_mask_changes_cyan_but_protects_neutral_and_original(self):
        source = ("nullsrc=size=64x32:rate=1,format=yuv444p10le,"
                  "geq=lum='450+mod(X*13+Y*7,17)':cb='if(lt(X,W/2),650,512)':cr=480")

        def render(graph):
            data = array.array('H')
            data.frombytes(subprocess.check_output([
                find_ffmpeg(), '-v', 'error', '-f', 'lavfi', '-i', source,
                '-vf', graph + ',format=yuv444p10le', '-frames:v', '1',
                '-f', 'rawvideo', '-pix_fmt', 'yuv444p10le', '-',
            ]))
            return data[:64*32]

        original = render('null')
        result = render(VideoDenoisePipeline(VideoDenoiseSettings(
            'unused', 'unused', glow_only=True))._video_filter())
        self.assertGreater(sum(abs(original[i]-result[i]) for i in range(len(original)) if i % 64 < 24), 0)
        self.assertEqual(max(abs(original[i]-result[i]) for i in range(len(original)) if i % 64 >= 40), 0)
        preserved = render(VideoDenoisePipeline(VideoDenoiseSettings(
            'unused', 'unused', glow_only=True, original_keep=100))._video_filter())
        self.assertEqual(original, preserved)

    @unittest.skipUnless(find_ffmpeg(), 'FFmpeg required')
    def test_dark_cleanup_protects_bright_regions_and_original_keep(self):
        source = ("nullsrc=size=64x32:rate=1,format=yuv444p10le,"
                  "geq=lum='if(lt(X,W/2),120,700)+mod(X*13+Y*7,17)':cb=512:cr=512")

        def render(graph):
            command = [find_ffmpeg(), '-v', 'error', '-f', 'lavfi', '-i', source,
                       '-vf', graph + ',format=yuv444p10le', '-frames:v', '1',
                       '-f', 'rawvideo', '-pix_fmt', 'yuv444p10le', '-']
            data = array.array('H')
            data.frombytes(subprocess.check_output(command))
            return data[:64*32]

        original = render('null')
        filtered = render(VideoDenoisePipeline(VideoDenoiseSettings(
            'unused', 'unused', shadow_only=True, strength='strong'))._video_filter())
        dark = [abs(original[i]-filtered[i]) for i in range(len(original)) if i % 64 < 32]
        bright = [abs(original[i]-filtered[i]) for i in range(len(original)) if i % 64 >= 32]
        self.assertGreater(sum(dark), 0)
        self.assertEqual(max(bright), 0)
        preserved = render(VideoDenoisePipeline(VideoDenoiseSettings(
            'unused', 'unused', shadow_only=True, original_keep=100))._video_filter())
        self.assertEqual(original, preserved)


if __name__ == '__main__':
    unittest.main()
