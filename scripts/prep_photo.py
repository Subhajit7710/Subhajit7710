#!/usr/bin/env python3
"""
Prepare a portrait photo for clean ASCII conversion (run locally, once per photo).

  1. isolate the subject: rembg if it is installed, otherwise a flood fill from
     the image border that treats near-white pixels as background (works well
     for studio shots on a plain white backdrop, like source-photo.jpg)
  2. CLAHE (adaptive histogram equalisation) for local contrast, so eyes,
     brows and beard survive the drop to ~100 columns of characters
  3. tone-stretch over the subject only
  4. composite onto pure white (white -> blank glyph) and crop square

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.

    python scripts/prep_photo.py [input] [output]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "source-prepped.png")

BG_TOLERANCE = 18   # how far from pure white still counts as backdrop (flood fill)
CROP = 0.74         # keep this fraction of the subject's height, from the top
                    # (head + shoulders; more face detail per character)


def subject_mask(rgb):
    """Return a 0..255 alpha mask, 255 = subject."""
    try:
        from rembg import remove  # optional, heavier but handles busy backgrounds
        cut = remove(Image.fromarray(rgb).convert("RGBA"))
        return np.array(cut.split()[-1])
    except ImportError:
        pass
    h, w = rgb.shape[:2]
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    mask = np.zeros((h + 2, w + 2), np.uint8)
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE | (255 << 8)
    tol = (BG_TOLERANCE,) * 3
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0)]:
        if bgr[seed[1], seed[0]].min() > 200:
            cv2.floodFill(bgr.copy(), mask, seed, 0, tol, tol, flags)
    bg = mask[1:-1, 1:-1] > 0
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return alpha


rgb = np.array(Image.open(INP).convert("RGB"))
alpha = subject_mask(rgb)
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# local contrast
clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
eq = clahe.apply(gray)
eq = cv2.bilateralFilter(eq, 7, 30, 7)  # calm fabric/skin texture, keep edges

# tone stretch over the subject only
lo, hi = np.percentile(eq[alpha > 128], [2, 97])
tone = np.clip((eq.astype(np.float32) - lo) / max(hi - lo, 1), 0, 1) * 255

# composite onto white with a slightly feathered edge (no halo)
m = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
out = tone * m + 255.0 * (1.0 - m)

# square crop around the subject
ys, xs = np.where(alpha > 20)
top = ys.min()
side = int((ys.max() - top) * CROP) + 20
# centre horizontally on the head (the widest rows are shoulders, not face)
head = xs[ys < top + side * 0.35]
cx = (head.min() + head.max()) // 2
cy = top - 10 + side // 2
canvas = np.full((side, side), 255, np.uint8)
x0, y0 = cx - side // 2, cy - side // 2
sx0, sy0 = max(x0, 0), max(y0, 0)
sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)

Image.fromarray(canvas, mode="L").save(OUT)
print("wrote", OUT, canvas.shape)
