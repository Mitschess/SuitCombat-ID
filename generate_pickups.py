"""
generate_pickups.py — Health power-up sprite from assets/health.jpeg (the MBG food tray).

Output: assets/effects/health_pickup.png  (4-frame strip: bob + sparkle, 2x pixel scale)
Run:    python generate_pickups.py
"""
import os
import math
from PIL import Image, ImageEnhance

from generate_sprites import ASSETS, SCALE, Layer, compose, upscale
from generate_ulti import remove_background, pixelate, outlined

OUT = os.path.join(ASSETS, "effects", "health_pickup.png")


def is_table(c):
    """Warm beige wood around the tray (the tray itself is grey metal)."""
    r, g, b = c
    return r - b > 22 and r > 120


def build():
    src = Image.open(os.path.join(ASSETS, "health.jpeg")).convert("RGB")
    src = ImageEnhance.Color(src).enhance(1.25)
    src = ImageEnhance.Contrast(src).enhance(1.15)
    tray = remove_background(src.crop((140, 10, 890, 490)), is_table)
    sprite = outlined(pixelate(tray, 46, 20), (20, 24, 34))

    W, H = sprite.width + 12, sprite.height + 14
    frames = []
    for i in range(4):
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bob = [0, -1, -2, -1][i]
        # soft green glow under the tray
        glow = Layer(W, H)
        for x in range(W):
            for y in range(H - 5, H):
                d = abs(x - W / 2) / (W / 2)
                if d < 0.85 - (y - (H - 5)) * 0.1 and (x + y + i) % 2 == 0:
                    glow.put(x, y, (90, 230, 110))
        canvas.alpha_composite(compose([(glow, False)], (0, 0, 0), W, H))
        canvas.alpha_composite(sprite, (6, 5 + bob))
        # sparkles + a small green cross badge
        fx = Layer(W, H)
        for k, (sx, sy) in enumerate(((4, 6), (W - 6, 4), (W // 2, 2), (W - 10, H - 12))):
            if (i + k) % 2 == 0:
                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    fx.put(sx + dx, sy + dy, (255, 255, 220) if (dx, dy) == (0, 0) else (200, 255, 190))
        cx, cy = 5, H - 12 + bob
        for dx in range(-2, 3):
            fx.put(cx + dx, cy, (60, 220, 80))
            fx.put(cx, cy + dx, (60, 220, 80))
        canvas.alpha_composite(compose([(fx, True)], (10, 40, 16), W, H))
        frames.append(canvas)

    strip = Image.new("RGBA", (W * SCALE * 4, H * SCALE), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.paste(upscale(f, SCALE), (i * W * SCALE, 0))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    strip.save(OUT)
    print(f"health_pickup.png: 4 frames of {W * SCALE}x{H * SCALE}")


if __name__ == "__main__":
    build()
