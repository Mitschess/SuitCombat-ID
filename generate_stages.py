"""
generate_stages.py — Turns the stage photos in assets/ (latar_*.jpg) into pixel-art
arena backgrounds (1024x576, drawn at 512x288 and scaled 2x like the fighters).

Output: assets/backgrounds/stage_<id>.png + assets/backgrounds/stages.json
Run:    python generate_stages.py
"""
import os
import json
from PIL import Image, ImageEnhance, ImageOps

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ASSETS, "backgrounds")

W, H = 512, 288          # base resolution (exported 2x)
GROUND = 238             # = GROUND_Y 476 / 2

# id, display name, photo, crop box (x0, y0, x1, y1), extra processing
STAGES = [
    ("ikn", "IKN", "latar_ikn.jpg", (25, 0, 738, 401), None),
    ("istana", "ISTANA", "latar_isatana.jpg", (0, 30, 660, 401), "mirror"),
    ("kopdes", "KOPDES", "latar_kopdes.jpeg", (0, 80, 1200, 755), None),
    ("mbg", "DAPUR MBG", "latar_mbg.jpg", (0, 50, 678, 431), None),
    ("sawit", "KEBUN SAWIT", "latar_sawit.jpg", (0, 165, 638, 480), "sky"),
]
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def mirror_left_half(im, center):
    """Rebuild a symmetric building from its left half (also hides corner watermarks)."""
    left = im.crop((0, 0, center, im.height))
    out = Image.new("RGB", (center * 2, im.height))
    out.paste(left, (0, 0))
    out.paste(ImageOps.mirror(left), (center, 0))
    return out


def sky_canvas(photo):
    """Photo without usable sky: put it on a pixel sky gradient."""
    canvas = Image.new("RGB", (W, H))
    top, bottom = (70, 140, 215), (190, 225, 245)
    px = canvas.load()
    for y in range(H):
        for x in range(W):
            t = y / (H * 0.45)
            band = min(1.0, t + (BAYER[y % 4][x % 4] - 7.5) / 64)
            px[x, y] = tuple(int(top[i] + (bottom[i] - top[i]) * band) for i in range(3))
    scaled = photo.resize((W, int(photo.height * W / photo.width)), Image.LANCZOS)
    canvas.paste(scaled, (0, H - scaled.height))
    return canvas


def pixelate(im):
    im = ImageEnhance.Color(im).enhance(1.2)
    im = ImageEnhance.Contrast(im).enhance(1.1)
    im = im.quantize(colors=40, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    return im


def add_arena_floor(im):
    """Darken the ground band under the fighters and add a lit edge so they read as standing on it."""
    px = im.load()
    for y in range(GROUND, H):
        depth = (y - GROUND) / (H - GROUND)
        for x in range(W):
            r, g, b = px[x, y]
            k = 0.62 - 0.22 * depth
            if (x + y) % 2 and depth > 0.6:
                k -= 0.05
            px[x, y] = (int(r * k), int(g * k), int(b * k))
    for x in range(W):
        r, g, b = px[x, GROUND]
        px[x, GROUND] = (min(255, r + 90), min(255, g + 80), min(255, b + 70))
        r, g, b = px[x, GROUND + 1]
        px[x, GROUND + 1] = (r // 2, g // 2, b // 2)
    # soft vignette + slight overall dim so the fighters pop
    for y in range(H):
        for x in range(W):
            e = max(abs(x - W / 2) / (W / 2), abs(y - H / 2) / (H / 2))
            k = 0.9 if e < 0.8 else 0.9 - (e - 0.8) * 1.2
            if e >= 0.8 and BAYER[y % 4][x % 4] / 16 < (e - 0.8) * 3:
                k -= 0.08
            r, g, b = px[x, y]
            px[x, y] = (int(r * k), int(g * k), int(b * k))
    return im


def build_stage(stage_id, name, photo, crop, extra):
    im = Image.open(os.path.join(ASSETS, photo)).convert("RGB")
    if extra == "mirror":
        im = mirror_left_half(im, 330)
    im = im.crop(crop)
    im = sky_canvas(im) if extra == "sky" else ImageOps.fit(im, (W, H), Image.LANCZOS)
    im = add_arena_floor(pixelate(im))
    path = os.path.join(OUT, f"stage_{stage_id}.png")
    im.resize((W * 2, H * 2), Image.NEAREST).save(path)
    return {"id": stage_id, "name": name, "file": f"stage_{stage_id}.png"}


def main():
    os.makedirs(OUT, exist_ok=True)
    stages = []
    for stage in STAGES:
        if os.path.exists(os.path.join(ASSETS, stage[2])):
            stages.append(build_stage(*stage))
        else:
            print("missing photo:", stage[2])
    if os.path.exists(os.path.join(OUT, "arena_temple.png")):
        stages.append({"id": "temple", "name": "ARENA KUIL", "file": "arena_temple.png"})
    with open(os.path.join(OUT, "stages.json"), "w") as f:
        json.dump(stages, f, indent=2)
    print("Stages:", ", ".join(s["name"] for s in stages))


if __name__ == "__main__":
    main()
