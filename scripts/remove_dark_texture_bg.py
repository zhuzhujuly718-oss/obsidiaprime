"""
Remove dark textured background (e.g. leather) from logo: flood-fill from image edges.
Keeps bright metallic / silver logo; stops at high-L or high-chroma pixels.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: remove_dark_texture_bg.py <input.png> <output.png>")
        return 1
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])

    im = Image.open(src).convert("RGB")
    rgb = np.asarray(im, dtype=np.float32)
    h, w = rgb.shape[:2]

    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    L = 0.299 * r + 0.587 * g + 0.114 * b
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    chroma = mx - mn

    # 背景：暗、偏中性（皮革颗粒）；logo 金属更亮或略带色散
    bg_candidate = (L < 88.0) & (chroma < 44.0)

    mask = np.zeros((h, w), dtype=bool)
    mask[0, :] = bg_candidate[0, :]
    mask[-1, :] = bg_candidate[-1, :]
    mask[:, 0] = bg_candidate[:, 0]
    mask[:, -1] = bg_candidate[:, -1]
    mask &= bg_candidate

    def dilate4(m: np.ndarray) -> np.ndarray:
        o = np.zeros_like(m)
        o[1:, :] |= m[:-1, :]
        o[:-1, :] |= m[1:, :]
        o[:, 1:] |= m[:, :-1]
        o[:, :-1] |= m[:, 1:]
        return o

    for _ in range(h + w + 100):
        n = mask | (dilate4(mask) & bg_candidate)
        if np.array_equal(n, mask):
            break
        mask = n

    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = rgb.astype(np.uint8)
    rgba[:, :, 3] = np.where(mask, 0, 255)

    out = Image.fromarray(rgba, "RGBA")
    bbox = out.getchannel("A").getbbox()
    if bbox:
        out = out.crop(bbox)

    out.save(dst, optimize=True)
    print(f"Wrote {dst} size={out.size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
