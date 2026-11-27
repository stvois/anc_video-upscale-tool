"""Run with precision/Scripts/python.exe after CUDA setup."""
import unittest
import torch
from gpu_clean import clean


@unittest.skipUnless(torch.cuda.is_available(), 'NVIDIA CUDA required')
class GPUCleanupTests(unittest.TestCase):
    def test_original_retention_and_bright_neutral_protection(self):
        torch.manual_seed(7)
        image = torch.rand((1, 3, 64, 64), device='cuda') * .02 + .1
        image[:, :, :, 40:] = .7
        self.assertTrue(torch.equal(clean(image, 'balanced', 100), image))
        result = clean(image, 'balanced', 0)
        self.assertTrue(torch.equal(image[:, :, :, 48:], result[:, :, :, 48:]))
        self.assertLess(result[:, :, :, :24].var().item(), image[:, :, :, :24].var().item())
        self.assertEqual(result.dtype, torch.float32)
        self.assertTrue(torch.isfinite(result).all().item())


if __name__ == '__main__':
    unittest.main()
