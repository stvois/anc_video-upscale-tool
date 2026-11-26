"""External float32 / uint16 SDR inference worker; no 8-bit conversion."""
import argparse
from pathlib import Path
import cv2
import numpy as np
import torch
from spandrel import ModelLoader


def main():
    parser = argparse.ArgumentParser()
    for name in ('input', 'output', 'model'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--scale', type=int, default=2)
    parser.add_argument('--preserve', type=int, default=70)
    args = parser.parse_args()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    torch.set_num_threads(4)
    model = ModelLoader().load_from_file(args.model).to(device).float().eval()
    print(f'Device: {device}; inference=float32; frames=uint16', flush=True)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    files = sorted(Path(args.input).glob('*.png'))
    for index, path in enumerate(files, 1):
        target = output / path.name
        if target.exists():
            continue
        image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if image is None or image.dtype != np.uint16 or image.ndim != 3:
            raise ValueError(f'Expected uint16 RGB input: {path}')
        rgb = image[:, :, :3][:, :, ::-1].astype(np.float32) / 65535.0
        height, width = rgb.shape[:2]
        native = np.empty((height * model.scale, width * model.scale, 3), np.float32)
        # Padded tiles bound VRAM while avoiding hard tile edges.
        tile, pad = 128, 24
        with torch.inference_mode():
            for y in range(0, height, tile):
                for x in range(0, width, tile):
                    y1, x1 = max(0, y-pad), max(0, x-pad)
                    y2, x2 = min(height, y+tile+pad), min(width, x+tile+pad)
                    patch = np.ascontiguousarray(rgb[y1:y2, x1:x2].transpose(2, 0, 1))
                    tensor = torch.from_numpy(patch).unsqueeze(0).to(device)
                    result = model(tensor).clamp(0, 1)[0].cpu().numpy().transpose(1, 2, 0)
                    s = model.scale
                    h, w = min(tile, height-y), min(tile, width-x)
                    native[y*s:(y+h)*s, x*s:(x+w)*s] = result[(y-y1)*s:(y-y1+h)*s, (x-x1)*s:(x-x1+w)*s]
        size = (width * args.scale, height * args.scale)
        enhanced = cv2.resize(native, size, interpolation=cv2.INTER_LANCZOS4)
        original = cv2.resize(rgb, size, interpolation=cv2.INTER_LANCZOS4)
        mixed = enhanced * (1-args.preserve/100) + original * (args.preserve/100)
        encoded = np.round(np.clip(mixed, 0, 1) * 65535).astype(np.uint16)[:, :, ::-1]
        ok, data = cv2.imencode('.png', encoded)
        if not ok:
            raise RuntimeError('PNG encode failed')
        temp = target.with_suffix('.tmp')
        data.tofile(temp)
        temp.replace(target)
        print(f'FRAME={index}/{len(files)}', flush=True)


if __name__ == '__main__':
    main()
