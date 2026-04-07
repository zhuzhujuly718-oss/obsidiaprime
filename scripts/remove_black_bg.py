"""Remove near-black background from logo PNG; output RGBA with transparency."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
import numpy as np


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if not src or not dst:
        print("Usage: remove_black_bg.py <input.png> <output.png>")
        return 1

    img = Image.open(src).convert("RGBA")
    arr = np.asarray(img, dtype=np.float32)
    rgb = arr[:, :, :3]
    old_a = arr[:, :, 3]

    # Euclidean distance from black; background is ~0, logo content is brighter
    dist = np.sqrt(np.sum(rgb * rgb, axis=2))

    # Tune: low = fully transparent, high = fully opaque (smooth anti-alias band)
    t1, t2 = 42.0, 95.0
    t = np.clip((dist - t1) / (t2 - t1), 0.0, 1.0)
    new_a = t * 255.0 * (old_a / 255.0)
    arr[:, :, 3] = np.clip(new_a, 0, 255)

    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    out.save(dst, optimize=True)
    print(f"Wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
