"""CUDA SDR selective cleanup; decode/encode stay in FFmpeg subprocesses."""
import json
import subprocess
import sys
import tempfile
import time

import numpy as np
import torch
import torch.nn.functional as F


def box(image, radius):
    size = radius * 2 + 1
    image = F.pad(image, (radius, radius, 0, 0), mode='replicate')
    image = F.avg_pool2d(image, (1, size), stride=1)
    image = F.pad(image, (0, 0, radius, radius), mode='replicate')
    return F.avg_pool2d(image, (size, 1), stride=1)


def guided(image, radius, epsilon):
    mean = box(image, radius)
    variance = (box(image * image, radius) - mean * mean).clamp_min(0)
    a = variance / (variance + epsilon)
    b = mean * (1 - a)
    return box(a, radius) * image + box(b, radius)


def clean(image, strength, keep, banding=False):
    radius, epsilon = {'light': (6, 0.00015), 'balanced': (12, 0.0004),
                       'strong': (20, 0.001)}[strength]
    y = image[:, 0:1] * .2126 + image[:, 1:2] * .7152 + image[:, 2:3] * .0722
    shadow = ((.34 - y) / .28).clamp(0, 1)
    blue = ((image[:, 2:3] - image[:, 0:1] - .015) / .16).clamp(0, 1)
    cyan = ((image[:, 1:2] - image[:, 0:1] + .015) / .16).clamp(0, 1)
    glow = blue * cyan * ((y - .09) / .16).clamp(0, 1)
    dx = F.pad((y[:, :, :, 1:] - y[:, :, :, :-1]).abs(), (0, 1, 0, 0))
    dy = F.pad((y[:, :, 1:, :] - y[:, :, :-1, :]).abs(), (0, 0, 0, 1))
    edge = (1 - F.max_pool2d(dx + dy, 3, stride=1, padding=1) / .06).clamp(0, 1)
    glow = box(glow, 2) * edge
    mask = torch.maximum(shadow * .7, glow * .7) * (1 - keep / 100)
    filtered = guided(image, radius, epsilon)
    if banding:
        filtered = filtered * .8 + guided(filtered, 4, .0001) * .2
    return (image + (filtered - image) * mask).clamp(0, 1)


def main():
    with open(sys.argv[1], encoding='utf-8') as handle:
        job = json.load(handle)
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable. Run precision engine setup and check NVIDIA driver.')
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    print('CUDA combined cleanup: ' + torch.cuda.get_device_name(0), flush=True)
    width, height = job['width'], job['height']
    count = width * height * 3 * 2
    decoder = encoder = None
    with tempfile.TemporaryFile() as errors:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        try:
            decoder = subprocess.Popen(job['decode'], stdout=subprocess.PIPE, stderr=errors, creationflags=flags)
            encoder = subprocess.Popen(job['encode'], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                       stderr=errors, creationflags=flags)
            frame = 0
            started = time.perf_counter()
            with torch.inference_mode():
                while True:
                    data = bytearray()
                    while len(data) < count:
                        chunk = decoder.stdout.read(count - len(data))
                        if not chunk:
                            break
                        data.extend(chunk)
                    if not data:
                        break
                    if len(data) != count:
                        raise RuntimeError('Incomplete decoded frame')
                    array = np.frombuffer(data, dtype='<u2').reshape(height, width, 3)
                    image = torch.from_numpy(array.astype(np.float32).transpose(2, 0, 1).copy())
                    image = image.unsqueeze(0).to('cuda') / 65535
                    result = clean(image, job['strength'], job['keep'], job['banding'])
                    array = (result[0].permute(1, 2, 0) * 65535).round().cpu().numpy().astype('<u2')
                    encoder.stdin.write(array.tobytes())
                    frame += 1
                    print(f'frame_gpu={frame}', flush=True)
            encoder.stdin.close()
            if decoder.wait() or encoder.wait():
                raise RuntimeError('FFmpeg decode/encode failed')
            if not frame:
                raise RuntimeError('No video frames decoded')
            print(f'CUDA filter completed: {frame} frames, {time.perf_counter()-started:.2f}s', flush=True)
        except Exception as exc:
            errors.seek(0)
            details = errors.read().decode('utf-8', errors='replace')[-4000:]
            raise RuntimeError(f'{exc}\n{details}') from exc
        finally:
            for process in (decoder, encoder):
                if process and process.poll() is None:
                    process.terminate()
                    process.wait()


if __name__ == '__main__':
    main()
