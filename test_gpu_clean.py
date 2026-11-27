"""Run with precision/Scripts/python.exe after CUDA setup."""
import unittest
import torch
from gpu_clean import clean


@unittest.skipUnless(torch.cuda.is_available(), 'NVIDIA CUDA required')
class GPUCleanupTests(unittest.TestCase):
    def test_cyan_stripes_smoothed_while_thin_white_edge_is_retained(self):
        image = torch.zeros((1, 3, 128, 128), device='cuda')
        image[:, 0] = .2
        image[:, 1] = .6
        image[:, 2] = .8
        stripe = torch.sin(torch.arange(128, device='cuda') * .45) * .025
        image += stripe.view(1, 1, 1, -1)
        image[:, :, :, 64] = 1
        result = clean(image, 'balanced', 0)
        self.assertLess(result[:, :, :, 10:50].var(dim=-1).mean().item(),
                        image[:, :, :, 10:50].var(dim=-1).mean().item())
        self.assertTrue(torch.equal(result[:, :, :, 64], image[:, :, :, 64]))

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
