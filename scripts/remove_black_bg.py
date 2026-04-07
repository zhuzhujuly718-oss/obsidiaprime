"""Remove near-black / page-bg-colored background from logo PNG; tight trim; output RGBA."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image


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

    # Distance from pure black
    dist_b = np.sqrt(np.sum(rgb * rgb, axis=2))

    # Match site background --black: #0a0a0a and common export blacks
    targets = (
        np.array([0.0, 0.0, 0.0]),
        np.array([10.0, 10.0, 10.0]),
        np.array([8.0, 8.0, 8.0]),
        np.array([15.0, 15.0, 15.0]),
    )
    dist_near = np.min(
        [np.sqrt(np.sum((rgb - t) ** 2, axis=2)) for t in targets],
        axis=0,
    )

    # Softer transition but aggressive fringe removal
    t1, t2 = 26.0, 82.0
    t = np.clip((dist_b - t1) / (t2 - t1), 0.0, 1.0)
    new_a = t * 255.0 * (old_a / 255.0)

    # Kill pixels that are still visually "background grey" (low chroma, dark)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    chroma = mx - mn
    low_chroma_dark = (mx < 95.0) & (chroma < 28.0) & (dist_b < 100.0)
    new_a = np.where(low_chroma_dark, np.minimum(new_a, dist_near * 2.5), new_a)
    new_a = np.where(low_chroma_dark & (dist_b < 55.0), 0.0, new_a)

    # Hard-remove fringe alpha (stops "lighter rectangle" halo)
    new_a = np.where(new_a < 24.0, 0.0, new_a)

    arr[:, :, 3] = np.clip(new_a, 0, 255)

    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    bbox = out.getchannel("A").getbbox()
    if bbox:
        out = out.crop(bbox)

    out.save(dst, optimize=True)
    print(f"Wrote {dst} size={out.size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
