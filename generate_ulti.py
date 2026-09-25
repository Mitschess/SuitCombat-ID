"""
generate_ulti.py — Ultimate-attack sprites + sounds for the 5 PyFight characters.

Reads the ulti pictures / sounds the user dropped in assets/ (ulti_<name>.jpg / .m4a)
and writes, per character, assets/characters/<Name>/ulti/:

  Gian  clones falling on the opponent  gian_fall.png   (10 Gian clones rain down, dodge left/right)
  Mega  bull charge across the floor     bull_run.png    (runs toward the opponent, dodge by jumping)
  Puba  stock-crash lightning            chart_cloud.png + bolt.png (dodge left/right)
  Subi  palm-oil missile (parabolic)     sawit_missile.png + explosion.png (dodge left/right)
  Wowi  falling building                 building.png    (dodge left/right)

  ulti.json   frame sizes + suggested gameplay values for each ulti

Shared: assets/effects/ulti_warning.png (target marker), ulti_crash.png (dust/debris)
Sounds: assets/ulti_<name>.wav is copied to assets/characters/<Name>/sounds/ulti.wav
        (if only the .m4a exists it is converted with imageio-ffmpeg; pygame can't play .m4a).

Run after generate_sprites.py:  python generate_ulti.py
"""
import os
import json
import math
import random
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from generate_sprites import (
    ASSETS, CHARACTERS, SCALE, Layer, compose, upscale, draw_fighter, load_head, mix, mul,
)

EFFECTS = os.path.join(ASSETS, "effects")


def ulti_dir(name):
    path = os.path.join(ASSETS, "characters", name, "ulti")
    os.makedirs(path, exist_ok=True)
    return path


def save_strip(frames, path, scale=SCALE):
    w, h = frames[0].size
    strip = Image.new("RGBA", (w * scale * len(frames), h * scale), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.paste(upscale(f, scale), (i * w * scale, 0))
    strip.save(path)
    return {"frame_width": w * scale, "frame_height": h * scale, "frames": len(frames)}


def pixelate(img, width, colors=16):
    """RGBA photo cut-out -> small pixel-art RGBA with hard alpha and a reduced palette."""
    h = max(1, round(img.height * width / img.width))
    small = img.resize((width, h), Image.LANCZOS)
    alpha = small.getchannel("A").point(lambda a: 255 if a > 110 else 0)
    rgb = small.convert("RGB").quantize(colors=colors, method=Image.Quantize.MEDIANCUT).convert("RGB")
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def outlined(img, color, pad=1):
    """Add a 1px outline around an RGBA sprite (returns a padded image)."""
    L = Layer(img.width + pad * 2, img.height + pad * 2)
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y][3]:
                L.put(x + pad, y + pad, px[x, y][:3])
    return compose([(L, True)], color, L.w, L.h)


def remove_background(img, is_bg):
    """Flood-fill from the border, clearing every connected pixel where is_bg(rgb) is true."""
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    seen = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        if not is_bg(px[x, y][:3]):
            continue
        px[x, y] = (0, 0, 0, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return img.crop(img.getbbox())


# ---------------------------------------------------------------------------
# Gian — clones falling from the sky
# ---------------------------------------------------------------------------
def build_gian():
    pal = CHARACTERS["Gian"]
    head = load_head(pal)
    poses = [
        dict(hip=(20, 27), neck=(21, 15), hf=(31, 8), hb=(12, 9), ef=(1, 0), eb=(-1, 0),
             ff=(26, 39), fb=(15, 41), toe_f=(2, 2), toe_b=(2, 2)),
        dict(hip=(20, 27), neck=(21, 15), hf=(32, 10), hb=(11, 7), ef=(1, 0), eb=(-1, 0),
             ff=(25, 41), fb=(16, 39), toe_f=(2, 2), toe_b=(2, 2)),
    ]
    frames = [draw_fighter(p, pal, head) for p in poses]
    info = save_strip(frames, os.path.join(ulti_dir("Gian"), "gian_fall.png"))
    return {
        "type": "clone_rain",
        "description": "10 Gian clones fall from the sky onto the opponent; dodge by moving left/right.",
        "dodge": "move",
        "sprites": {"falling": dict(info, file="gian_fall.png", fps=8, loop=True),
                    "impact": {"file": "../../../effects/ulti_crash.png", "fps": 16}},
        "suggested": {"count": 10, "spawn_interval_frames": 8, "spread_px": 140,
                      "fall_speed": 9.0, "damage_per_hit": 4, "draw_scale": 0.8},
    }


# ---------------------------------------------------------------------------
# Mega — red bull charging along the floor
# ---------------------------------------------------------------------------
def build_mega():
    src = Image.open(os.path.join(ASSETS, "ulti_mega.jpg")).convert("RGB")
    src = ImageEnhance.Color(src).enhance(1.2)
    bull = remove_background(src, lambda c: min(c) > 215)
    frames = []
    for bob, tilt in ((0, 0), (-3, -4), (-1, -1), (-2, 3)):
        img = bull.rotate(tilt, resample=Image.BICUBIC, expand=True)
        small = outlined(pixelate(img, 72, 18), (40, 6, 8))
        canvas = Image.new("RGBA", (92, 80), (0, 0, 0, 0))
        canvas.alpha_composite(small, (16, 80 - small.height - 3 + bob))
        frames.append(canvas)
    # dust kicked up behind the hooves
    for i, f in enumerate(frames):
        d = Layer(92, 80)
        for k in range(3):
            r = 2.5 + ((i + k) % 3) * 0.9
            d.circle((12 - k * 5 + (i % 2), 74 - k * 1.5), r, (176, 160, 146) if k % 2 else (140, 126, 116))
        f.alpha_composite(compose([(d, False)], (0, 0, 0), 92, 80))
    info = save_strip(frames, os.path.join(ulti_dir("Mega"), "bull_run.png"))
    return {
        "type": "charge",
        "description": "A bull runs along the floor from Mega's side of the screen toward the opponent; "
                       "dodge by jumping. Sprite faces right - flip it when running right-to-left.",
        "dodge": "jump",
        "sprites": {"run": dict(info, file="bull_run.png", fps=12, loop=True, facing="right")},
        "suggested": {"speed": 11.0, "damage": 20, "hitbox_height_px": 70},
    }


# ---------------------------------------------------------------------------
# Puba — red stock-crash cloud + lightning bolt
# ---------------------------------------------------------------------------
def build_puba():
    out = ulti_dir("Puba")
    chart = Image.open(os.path.join(ASSETS, "ulti_puba.jpg")).convert("RGB")
    chart = ImageEnhance.Contrast(chart).enhance(1.4)

    # cloud: the crash chart pixelated and masked to a cloud silhouette
    W, H = 72, 30
    tex = chart.resize((W, H), Image.LANCZOS).quantize(colors=12).convert("RGBA")
    mask = Layer(W, H)
    for cx, cy, r in ((14, 19, 10), (28, 13, 12), (44, 12, 13), (58, 18, 11), (36, 21, 11), (22, 22, 8), (50, 22, 8)):
        mask.circle((cx, cy), r, (1, 1, 1))
    clouds = []
    for flash in (0.0, 0.35):
        L = Layer(W, H)
        tpx = tex.load()
        for (x, y) in mask.px:
            c = mul(mix(tpx[x, y][:3], (150, 36, 46), 0.3), 1.35)
            L.put(x, y, mix(c, (255, 80, 80), flash) if flash else c)
        clouds.append(compose([(L, True)], (90, 10, 16), W, H))
    cloud_info = save_strip(clouds, os.path.join(out, "chart_cloud.png"))

    # bolt: a jagged "falling chart" line from cloud to floor
    BW, BH = 40, 208
    bolts = []
    for seed in range(4):
        rng = random.Random(seed * 17 + 3)
        pts, x, y = [(BW // 2, 0)], BW // 2, 0
        while y < BH - 6:
            y += rng.randint(8, 18)
            x = max(8, min(BW - 8, x + rng.choice((-1, 1)) * rng.randint(3, 9)))
            pts.append((x, min(y, BH - 2)))
        L = Layer(BW, BH)
        for r, col in ((4.2, (120, 10, 20)), (2.8, (230, 40, 50)), (1.4, (255, 150, 150)), (0.6, (255, 255, 255))):
            for a, b in zip(pts, pts[1:]):
                L.capsule(a, b, r, col)
        for _ in range(6):   # candlesticks shaken loose from the chart
            cx, cy = rng.randint(3, BW - 4), rng.randint(10, BH - 20)
            L.capsule((cx, cy - 4), (cx, cy + 4), 0.4, (255, 120, 120))
            for yy in range(cy - 2, cy + 3):
                L.put(cx, yy, (230, 30, 40))
                L.put(cx + 1, yy, (200, 20, 30))
        bolts.append(compose([(L, False)], (0, 0, 0), BW, BH))
    bolt_info = save_strip(bolts, os.path.join(out, "bolt.png"))
    return {
        "type": "lightning",
        "description": "A red stock-crash cloud appears above the opponent, then a lightning bolt strikes "
                       "that spot; dodge by moving left/right during the warning.",
        "dodge": "move",
        "sprites": {"cloud": dict(cloud_info, file="chart_cloud.png", fps=6, loop=True),
                    "bolt": dict(bolt_info, file="bolt.png", fps=20, loop=True),
                    "warning": {"file": "../../../effects/ulti_warning.png", "fps": 6}},
        "suggested": {"strikes": 3, "warning_frames": 45, "bolt_frames": 18,
                      "hitbox_width_px": 50, "damage": 12, "cloud_y_px": 40},
    }


# ---------------------------------------------------------------------------
# Subi — palm-oil tree missile + explosion
# ---------------------------------------------------------------------------
def build_subi():
    out = ulti_dir("Subi")
    frond = [(72, 142, 52), (104, 172, 62), (52, 112, 42)]
    bark_a, bark_b = (118, 98, 68), (84, 70, 48)
    fruit = [(150, 40, 30), (200, 70, 40), (60, 22, 20)]

    W, H = 60, 26
    frames = []
    for i in range(4):
        L = Layer(W, H)
        cy = H // 2
        # fronds as tail fins
        for k, (dy, length) in enumerate(((-9, 13), (-5, 15), (0, 16), (5, 15), (9, 13))):
            sway = math.sin(i * 1.6 + k) * 1.2
            col = frond[k % 3]
            L.capsule((18, cy), (18 - length, cy + dy + sway), 1.1, col)
            for t in range(3, length, 3):
                q = (18 - t, cy + (dy + sway) * t / length)
                L.put(round(q[0]), round(q[1]) - 1, mul(col, 0.8))
                L.put(round(q[0]), round(q[1]) + 1, mul(col, 0.8))
        # trunk with diamond bark pattern
        for x in range(16, 44):
            for y in range(cy - 3, cy + 4):
                L.put(x, y, bark_a if (x + abs(y - cy)) % 4 < 2 else bark_b)
        # fruit bunch warhead
        L.circle((47, cy), 6.2, fruit[2])
        rng = random.Random(9)
        for _ in range(26):
            a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 5.2)
            L.circle((47 + math.cos(a) * r, cy + math.sin(a) * r), 1.1, fruit[rng.randint(0, 1)])
        L.shade()
        # flame exhaust
        fx = Layer(W, H)
        flick = [0, 2, 1, 3][i]
        for r, col, n in ((3.5, (230, 90, 30), 7 + flick), (2.2, (255, 190, 60), 5 + flick), (1.0, (255, 250, 200), 3)):
            fx.capsule((16, cy), (16 - n, cy + (i % 2) - 0.5), r, col)
        frames.append(compose([(L, True), (fx, False)], (26, 18, 10), W, H))
    missile_info = save_strip(frames, os.path.join(out, "sawit_missile.png"))

    # explosion
    E = 56
    boom = []
    for i in range(6):
        L = Layer(E, E)
        c = (E // 2, E // 2 + 6)
        radius = [6, 12, 17, 20, 21, 21][i]
        cols = [(90, 80, 80), (200, 60, 30), (255, 150, 50), (255, 240, 170)]
        if i >= 4:
            cols = [(70, 64, 64), (110, 100, 100), (150, 140, 136)]
        for j, col in enumerate(cols):
            rr = radius - j * (radius / (len(cols) + 0.5))
            if rr > 0.5:
                for k in range(7):
                    a = k * 2 * math.pi / 7 + i
                    L.circle((c[0] + math.cos(a) * rr * 0.35, c[1] + math.sin(a) * rr * 0.3 - j), rr * 0.7, col)
        if i >= 1:   # flying palm fruit
            rng = random.Random(i)
            for _ in range(8):
                a = rng.uniform(0, 2 * math.pi)
                d = radius + 3 + i * 1.5
                L.circle((c[0] + math.cos(a) * d, c[1] + math.sin(a) * d * 0.8), 1.2, fruit[rng.randint(0, 1)])
        if i == 5:
            L.px = {k: v for k, v in L.px.items() if (k[0] + k[1]) % 2 == 0}
        boom.append(compose([(L, False)], (0, 0, 0), E, E))
    boom_info = save_strip(boom, os.path.join(out, "explosion.png"))
    return {
        "type": "parabolic_missile",
        "description": "A palm-oil tree missile launches from Subi, arcs upward and comes down on the "
                       "opponent's position; dodge by moving left/right. Rotate the sprite to its velocity "
                       "angle (it points right at 0 degrees).",
        "dodge": "move",
        "sprites": {"missile": dict(missile_info, file="sawit_missile.png", fps=14, loop=True, facing="right"),
                    "explosion": dict(boom_info, file="explosion.png", fps=14, loop=False)},
        "suggested": {"flight_frames": 70, "apex_height_px": 300, "explosion_radius_px": 60, "damage": 22},
    }


# ---------------------------------------------------------------------------
# Wowi — the building falls on the opponent
# ---------------------------------------------------------------------------
def build_wowi():
    src = Image.open(os.path.join(ASSETS, "ulti_wowi.jpg")).convert("RGB").crop((50, 28, 592, 170))
    src = ImageEnhance.Contrast(src).enhance(1.3)
    top = remove_background(src, lambda c: sum(c) / 3 > 150 and max(c) - min(c) < 70)
    top.putalpha(top.getchannel("A").filter(ImageFilter.MaxFilter(7)))   # keep the thin blades
    top = pixelate(top, 88, 14)

    W = top.width + 8
    base_h = 20
    L = Layer(W, top.height + base_h)
    tp = top.load()
    for y in range(top.height):
        for x in range(top.width):
            if tp[x, y][3]:
                L.put(x + 4, y, tp[x, y][:3])
    # white colonnade base with the golden emblem, drawn as pixel art
    y0 = top.height
    for y in range(y0, y0 + base_h):
        for x in range(0, W):
            dy = y - y0
            if dy < 3:
                col = (236, 236, 240) if dy else (255, 255, 255)
            elif dy < 16:
                col = (236, 236, 240) if x % 6 in (1, 2) else (150, 152, 164)
            else:
                col = (200, 200, 210) if dy < 18 else (120, 120, 132)
            L.put(x, y, col)
    for y in range(y0 - 6, y0 + 1):   # flag pole + emblem
        L.put(W // 2, y, (230, 230, 230))
    L.put(W // 2 - 1, y0 + 3, (220, 170, 40))
    L.put(W // 2, y0 + 3, (240, 190, 60))
    L.put(W // 2 + 1, y0 + 3, (220, 170, 40))
    L.put(W // 2, y0 + 4, (200, 150, 30))
    building = compose([(L, True)], (18, 22, 30), W, L.h)
    out = ulti_dir("Wowi")
    info = save_strip([building], os.path.join(out, "building.png"))
    return {
        "type": "falling_object",
        "description": "The building drops from the top of the screen onto the opponent's position; "
                       "dodge by moving left/right during the warning.",
        "dodge": "move",
        "sprites": {"building": dict(info, file="building.png", fps=1, loop=False),
                    "warning": {"file": "../../../effects/ulti_warning.png", "fps": 6},
                    "impact": {"file": "../../../effects/ulti_crash.png", "fps": 16}},
        "suggested": {"warning_frames": 50, "fall_speed": 16.0, "damage": 25, "hitbox_inset_px": 30},
    }


# ---------------------------------------------------------------------------
# Shared effects
# ---------------------------------------------------------------------------
def build_shared():
    os.makedirs(EFFECTS, exist_ok=True)
    warn = []
    for i in range(2):
        L = Layer(40, 14)
        col = (255, 60, 60) if i == 0 else (255, 200, 80)
        for a in range(0, 360, 4):
            t = math.radians(a)
            L.put(round(20 + math.cos(t) * 17), round(9 + math.sin(t) * 4), col)
        for dy in range(0, 7):     # down arrow
            for dx in range(-(6 - dy) // 2, (6 - dy) // 2 + 1):
                L.put(20 + dx, dy, col)
        warn.append(compose([(L, True)], (40, 0, 0), 40, 14))
    save_strip(warn, os.path.join(EFFECTS, "ulti_warning.png"))

    crash = []
    for i in range(6):
        L = Layer(72, 40)
        rng = random.Random(3)
        spread = 6 + i * 5
        for k in range(9):
            side = -1 if k % 2 else 1
            x = 36 + side * rng.uniform(0, spread)
            y = 34 - rng.uniform(0, 4 + i * 2)
            r = max(0.0, rng.uniform(2.5, 5.0) - i * 0.4)
            if r > 0.5:
                L.circle((x, y), r, mix((170, 158, 146), (110, 100, 96), k / 9))
        for k in range(8):   # debris
            a = math.pi + k * math.pi / 7
            d = 4 + i * 5
            L.put(round(36 + math.cos(a) * d * 1.4), round(34 + math.sin(a) * d * 0.9 + i * i * 0.3), (90, 82, 76))
        if i >= 4:
            L.px = {k: v for k, v in L.px.items() if (k[0] + k[1] + i) % 3 != 0}
        crash.append(compose([(L, False)], (0, 0, 0), 72, 40))
    save_strip(crash, os.path.join(EFFECTS, "ulti_crash.png"))


# ---------------------------------------------------------------------------
# Sounds: m4a -> wav (pygame can't decode AAC)
# ---------------------------------------------------------------------------
def convert_sounds():
    """Copy assets/ulti_<name>.wav into the character's sounds/ folder.
    Falls back to converting ulti_<name>.m4a with imageio-ffmpeg (pygame can't decode .m4a)."""
    for name in CHARACTERS:
        dst = os.path.join(ASSETS, "characters", name, "sounds", "ulti.wav")
        wav = os.path.join(ASSETS, f"ulti_{name.lower()}.wav")
        m4a = os.path.join(ASSETS, f"ulti_{name.lower()}.m4a")
        if os.path.exists(wav):
            shutil.copyfile(wav, dst)
        elif os.path.exists(m4a):
            try:
                import imageio_ffmpeg
            except ImportError:
                print(f"{name}: only .m4a found and imageio-ffmpeg is missing; convert it to .wav manually")
                continue
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", m4a,
                            "-ac", "2", "-ar", "44100", dst], check=True)
        else:
            print(f"no ulti sound for {name}")


def build_preview(results):
    prev = os.path.join(ASSETS, "preview")
    os.makedirs(prev, exist_ok=True)
    rows = []
    for name, spec in results.items():
        base = ulti_dir(name)
        for key, s in spec["sprites"].items():
            path = os.path.normpath(os.path.join(base, s["file"]))
            rows.append((f"{name} / {key}", Image.open(path)))
    W = max(im.width for _, im in rows) + 170
    H = sum(min(im.height, 420) + 16 for _, im in rows)
    sheet = Image.new("RGBA", (W, H), (26, 26, 38, 255))
    d = ImageDraw.Draw(sheet)
    y = 0
    for label, im in rows:
        d.text((10, y + 10), label, fill=(255, 220, 120, 255))
        sheet.alpha_composite(im.crop((0, 0, im.width, min(im.height, 420))), (160, y + 8))
        y += min(im.height, 420) + 16
    sheet.save(os.path.join(prev, "ulti_overview.png"))


def main():
    build_shared()
    results = {"Gian": build_gian(), "Mega": build_mega(), "Puba": build_puba(),
               "Subi": build_subi(), "Wowi": build_wowi()}
    for name, spec in results.items():
        spec["sound"] = "../sounds/ulti.wav"
        spec["caster_animation"] = "ulti"
        with open(os.path.join(ulti_dir(name), "ulti.json"), "w") as f:
            json.dump(spec, f, indent=2)
    convert_sounds()
    build_preview(results)
    print("Ulti sprites + sounds generated for", ", ".join(results))


if __name__ == "__main__":
    main()
