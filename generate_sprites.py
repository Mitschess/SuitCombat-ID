"""
generate_sprites.py — Pixel-art asset generator for PyFight.

Turns the 5 character photos in assets/ (Gian, Mega, Puba, Subi, Wowi) into
"big-head" pixel-art fighters: the head is a pixelated crop of the photo, the
body is drawn procedurally with a costume matching the photo.

Per character (assets/characters/<Name>/):
  <Name>_sheet.png / .json   sprite sheet + animation table (rows = animations)
  <Name>_portrait.png        head portrait for character select / HUD
  <Name>_projectile.png      4-frame projectile strip
  frames/<anim>_<i>.png      every frame as its own PNG
  sounds/                    put the character's own sound effects here

Shared:
  assets/effects/hit_spark.png, block_spark.png, dust.png
  assets/backgrounds/arena_temple.png   1024x576 arena background
  assets/preview/overview.png, fighters.gif

Run:  python generate_sprites.py
"""
import os
import math
import json
import random
from PIL import Image, ImageDraw, ImageEnhance

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")

FRAME = 56          # frame size in base (pixel-art) pixels
SCALE = 2           # export scale, nearest neighbour -> 112x112 frames
OFFSET = (4, 8)     # poses are authored on a 48x48 grid, then shifted into the 56x56 frame
ANCHOR = (24, 55)   # base-pixel point on the floor under the fighter (bottom-center)
HEAD_W, HEAD_H = 16, 18

UPPER_ARM, FOREARM = 6.5, 6.5
THIGH, SHIN = 9.0, 9.0

SUIT_BLACK = (30, 32, 40)
SHIRT_WHITE = (236, 236, 242)
SKIN = (226, 182, 146)

# ---------------------------------------------------------------------------
# Characters: photo + head crop box (x0, y0, x1, y1) + costume colours
# ---------------------------------------------------------------------------
CHARACTERS = {
    "Gian": dict(
        photo="Gian.jpg", crop=(90, 28, 265, 228),
        jacket=SUIT_BLACK, shirt=SHIRT_WHITE, tie=(206, 30, 42), pants=(28, 30, 38),
        shoe=(16, 16, 20), skin=SKIN, build=3.1, jacket_long=True, pin=(220, 40, 40),
        outline=(8, 8, 12), projectile="ice",
        energy=[(255, 255, 255), (255, 190, 190), (230, 40, 50), (130, 10, 20)],
    ),
    "Mega": dict(
        photo="Mega.jpg", crop=(183, 5, 353, 200),
        jacket=(204, 40, 38), pants=(186, 34, 34), shoe=(70, 26, 26), skin=SKIN,
        build=3.6, drape=(246, 128, 58), skirt=(196, 38, 36), glasses=True,
        outline=(30, 6, 8), projectile="fire",
        energy=[(255, 250, 210), (255, 190, 90), (246, 110, 50), (170, 30, 30)],
    ),
    "Puba": dict(
        photo="Puba.jpg", crop=(350, 12, 570, 262),
        jacket=(30, 52, 94), shirt=SHIRT_WHITE, pants=(42, 42, 52), shoe=(24, 24, 30),
        skin=SKIN, build=3.4, jacket_long=True, patch=True, glasses=True,
        outline=(8, 12, 26), projectile="ice",
        energy=[(255, 255, 255), (170, 225, 255), (60, 150, 250), (20, 60, 150)],
    ),
    "Subi": dict(
        photo="Subi.jpeg", crop=(72, 10, 210, 172),
        jacket=(26, 28, 34), shirt=SHIRT_WHITE, tie=(170, 28, 40), pants=(26, 28, 34),
        shoe=(14, 14, 18), skin=SKIN, build=3.9, jacket_long=True, pin=(220, 40, 40),
        outline=(6, 6, 10), projectile="fire",
        energy=[(255, 250, 210), (255, 220, 90), (230, 160, 30), (140, 80, 10)],
    ),
    "Wowi": dict(
        photo="Wowi.jpg", crop=(182, 64, 310, 248),
        jacket=SHIRT_WHITE, pants=(30, 30, 38), shoe=(16, 16, 20), skin=SKIN,
        build=3.0, belt=(20, 20, 24), pin=(220, 40, 40), bg_tol=110,
        outline=(24, 24, 34), projectile="acid",
        energy=[(255, 255, 255), (235, 235, 245), (200, 60, 60), (120, 20, 30)],
    ),
}

SOUND_README = """Put {name}'s own sound effects in this folder (.wav or .ogg).
Suggested file names:

  select.wav    voice line when {name} is picked in character select
  punch.wav     melee attack (J)
  kick.wav      kick attack
  special.wav   ranged / projectile attack (K)
  block.wav     blocking a hit (L)
  hit.wav       {name} gets hit
  ko.wav        {name} is knocked out
  victory.wav   {name} wins the round
"""


# ---------------------------------------------------------------------------
# Small vector / colour helpers
# ---------------------------------------------------------------------------
def mul(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def add(p, q, k=1.0):
    return (p[0] + q[0] * k, p[1] + q[1] * k)


def sub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def norm(v):
    length = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / length, v[1] / length)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


# ---------------------------------------------------------------------------
# Pixel layer: rasterises capsules, auto-shades, and outlines its silhouette
# ---------------------------------------------------------------------------
class Layer:
    def __init__(self, w=FRAME, h=FRAME):
        self.w, self.h = w, h
        self.px = {}

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[(x, y)] = c

    def capsule(self, a, b, r, c):
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy
        for y in range(int(math.floor(min(ay, by) - r)), int(math.ceil(max(ay, by) + r)) + 1):
            for x in range(int(math.floor(min(ax, bx) - r)), int(math.ceil(max(ax, bx) + r)) + 1):
                t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / l2))
                qx, qy = ax + t * dx - x, ay + t * dy - y
                if qx * qx + qy * qy <= r * r:
                    self.put(x, y, c)

    def circle(self, p, r, c):
        self.capsule(p, p, r, c)

    def shade(self):
        """Light from above: highlight top edges, darken bottom/back edges."""
        out = {}
        for (x, y), c in self.px.items():
            if (x, y - 1) not in self.px:
                out[(x, y)] = mix(c, (255, 255, 255), 0.22)
            elif (x, y + 1) not in self.px or (x - 1, y) not in self.px:
                out[(x, y)] = mul(c, 0.72)
            else:
                out[(x, y)] = c
        self.px = out

    def outline(self, color):
        edge = {}
        for (x, y) in self.px:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in self.px and 0 <= nx < self.w and 0 <= ny < self.h:
                    edge[(nx, ny)] = color
        return edge


def compose(layers, outline_color, w=FRAME, h=FRAME):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pix = img.load()
    for layer, outlined in layers:
        if outlined:
            for (x, y), c in layer.outline(outline_color).items():
                pix[x, y] = (*c, 255)
        for (x, y), c in layer.px.items():
            pix[x, y] = c if len(c) == 4 else (*c, 255)
    return img


def upscale(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


# ---------------------------------------------------------------------------
# Two-bone IK: returns (elbow/knee, end effector)
# ---------------------------------------------------------------------------
def ik(root, target, l1, l2, pref):
    d_vec = sub(target, root)
    d = math.hypot(*d_vec)
    u = norm(d_vec) if d > 1e-6 else (0.0, 1.0)
    reach = l1 + l2 - 0.05
    if d >= reach:
        return add(root, u, l1), add(root, u, reach)
    d = max(d, abs(l1 - l2) + 0.05)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    perp = (-u[1], u[0])
    if dot(perp, pref) < 0:
        perp = (-perp[0], -perp[1])
    return add(add(root, u, a), perp, h), target


# ---------------------------------------------------------------------------
# Fighter renderer (all poses face right; flip at runtime to face left)
# ---------------------------------------------------------------------------
STANCE = dict(hip=(20, 29), neck=(21.5, 17), hf=(28, 17), hb=(25, 19), ff=(26, 45), fb=(14, 45))
POINT_KEYS = ("hip", "neck", "hf", "hb", "ff", "fb")


def load_head(pal):
    """Crop the photo to the head, pixelate it and mask it to an oval."""
    im = Image.open(os.path.join(ASSETS, pal["photo"])).convert("RGB").crop(pal["crop"])
    im = ImageEnhance.Contrast(im).enhance(1.3)
    im = ImageEnhance.Color(im).enhance(1.15)
    # background colour = median of the crop's top corners
    corners = [im.getpixel((x, y)) for x in (1, 2, im.width - 3, im.width - 2) for y in (1, 2, 3)]
    bg = tuple(sorted(c[i] for c in corners)[len(corners) // 2] for i in range(3))
    im = im.resize((HEAD_W, HEAD_H), Image.LANCZOS)
    im = im.quantize(colors=14, method=Image.Quantize.MEDIANCUT).convert("RGBA")
    px = im.load()
    cx, cy = (HEAD_W - 1) / 2, (HEAD_H - 1) / 2
    for y in range(HEAD_H):
        for x in range(HEAD_W):
            if ((x - cx) / (HEAD_W / 2)) ** 2 + ((y - cy) / (HEAD_H / 2)) ** 2 > 1.0:
                px[x, y] = (0, 0, 0, 0)
    # flood-fill background-coloured pixels inward from the transparent border
    tol = pal.get("bg_tol", 55)
    stack = [(x, y) for y in range(HEAD_H) for x in range(HEAD_W) if px[x, y][3] == 0]
    while stack:
        x, y = stack.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < HEAD_W and 0 <= ny < HEAD_H and px[nx, ny][3] and ny < HEAD_H * 0.8:
                if sum(abs(px[nx, ny][i] - bg[i]) for i in range(3)) < tol:
                    px[nx, ny] = (0, 0, 0, 0)
                    stack.append((nx, ny))
    if pal.get("glasses"):
        ey = int(HEAD_H * 0.45)
        for x0 in (3, 9):
            for x in range(x0, x0 + 4):
                px[x, ey - 1] = (40, 36, 40, 255)
            px[x0, ey] = px[x0 + 3, ey] = (40, 36, 40, 255)
    return im


def draw_arm(layer, sh, el, hand, pal, k):
    layer.capsule(sh, el, 1.9, mul(pal["jacket"], k))
    layer.capsule(el, hand, 1.6, mul(pal["jacket"], k))
    if pal.get("shirt"):
        layer.circle(add(hand, norm(sub(el, hand)), 1.6), 1.4, mul(pal["shirt"], k))  # shirt cuff
    layer.circle(hand, 1.8, mul(pal["skin"], k))


def draw_leg(layer, hp, kn, ank, toe_dir, pal, k):
    layer.capsule(hp, kn, 2.4, mul(pal["pants"], k))
    layer.capsule(kn, ank, 2.1, mul(pal["pants"], k))
    layer.capsule(ank, add(ank, toe_dir), 1.6, mul(pal["shoe"], k))


def draw_fx(layer, fx, pal):
    energy = pal["energy"]
    for item in fx:
        if item[0] == "orb":
            _, p, r = item
            for i, col in enumerate(reversed(energy)):
                if r - i * 1.1 > 0.4:
                    layer.circle(p, r - i * 1.1, col)
        elif item[0] == "whoosh":
            _, x0, x1, y = item
            for dy, alpha in ((-1.5, 150), (0, 200), (1.5, 150)):
                layer.capsule((x0 + abs(dy), y + dy), (x1, y + dy), 0.45, (255, 255, 255, alpha))


def line(layer, a, b, c, width=(0,)):
    steps = max(1, int(math.ceil(max(abs(b[0] - a[0]), abs(b[1] - a[1])))))
    for i in range(steps + 1):
        q = add(a, sub(b, a), i / steps)
        for w in width:
            layer.put(round(q[0]) + w, round(q[1]), c)


def shifted(pose):
    """Move a pose authored on the 48x48 grid into the frame."""
    ox, oy = OFFSET
    out = dict(pose)
    for key in POINT_KEYS:
        out[key] = (pose[key][0] + ox, pose[key][1] + oy)
    fx = []
    for item in pose.get("fx", []):
        if item[0] == "orb":
            fx.append(("orb", (item[1][0] + ox, item[1][1] + oy), item[2]))
        else:
            fx.append(("whoosh", item[1] + ox, item[2] + ox, item[3] + oy))
    out["fx"] = fx
    return out


def draw_fighter(pose, pal, head_img):
    P = dict(STANCE)
    P.update(pose)
    P = shifted(P)
    hip, neck = P["hip"], P["neck"]
    down = norm(sub(hip, neck))       # torso axis, neck -> hip
    fwd = (down[1], -down[0])         # facing direction, perpendicular to torso
    build = pal["build"]

    sh_n = add(neck, down, 1.5)
    sh_f = add(sh_n, fwd, -1.0)
    hip_n = add(hip, fwd, 1.0)
    hip_f = add(hip, fwd, -1.0)

    el_n, hand_n = ik(sh_n, P["hf"], UPPER_ARM, FOREARM, P.get("ef", (0, 1)))
    el_f, hand_f = ik(sh_f, P["hb"], UPPER_ARM, FOREARM, P.get("eb", (0, 1)))
    kn_n, ank_n = ik(hip_n, P["ff"], THIGH, SHIN, P.get("kf", (1, 0)))
    kn_f, ank_f = ik(hip_f, P["fb"], THIGH, SHIN, P.get("kb", (1, 0)))

    far_k = 0.72
    far_leg, far_arm, near_leg, near_arm = Layer(), Layer(), Layer(), Layer()
    draw_leg(far_leg, hip_f, kn_f, ank_f, P.get("toe_b", (3, 0.6)), pal, far_k)
    draw_arm(far_arm, sh_f, el_f, hand_f, pal, far_k)
    draw_leg(near_leg, hip_n, kn_n, ank_n, P.get("toe_f", (3, 0.6)), pal, 1.0)
    draw_arm(near_arm, sh_n, el_n, hand_n, pal, 1.0)
    for layer in (far_leg, far_arm, near_leg, near_arm):
        layer.shade()
    if pal.get("patch"):   # red-white flag patch on the sleeve
        mx, my = (round(v) for v in add(sh_n, sub(el_n, sh_n), 0.5))
        for dx in (0, 1):
            near_arm.put(mx + dx, my - 1, (220, 30, 40))
            near_arm.put(mx + dx, my, (250, 250, 250))

    # --- torso --------------------------------------------------------------
    t = Layer()
    if pal.get("drape"):   # hijab falling behind the shoulders
        t.capsule(add(neck, fwd, -2.0), add(add(neck, down, 7.0), fwd, -3.5), 2.2, pal["drape"])
    bottom = add(hip, down, 2.5) if pal.get("jacket_long") else hip
    t.capsule(neck, bottom, build, pal["jacket"])
    chest_top = add(neck, down, 2.5)
    t.capsule(add(chest_top, fwd, 0.6), add(hip, down, -4.5), build + 0.8, pal["jacket"])
    front = build + 0.4
    if pal.get("shirt"):
        t.capsule(add(neck, fwd, front - 0.6), add(add(neck, down, 6.0), fwd, front + 0.2), 1.1, pal["shirt"])
    if pal.get("belt"):
        b = add(hip, down, -0.5)
        t.capsule(add(b, fwd, -build), add(b, fwd, build), 0.7, pal["belt"])
    t.shade()
    if pal.get("tie"):
        line(t, add(add(neck, down, 1.0), fwd, front + 0.3), add(add(neck, down, 7.5), fwd, front + 0.6), pal["tie"])
    if pal.get("drape"):
        line(t, add(add(neck, down, 0.5), fwd, 2.0), add(add(neck, down, 6.0), fwd, 3.5), pal["drape"], (0, -1))
    if pal.get("pin"):
        pp = add(add(neck, down, 4.0), fwd, 1.0)
        t.put(round(pp[0]), round(pp[1]), pal["pin"])

    # --- head from the photo (tilts with the torso) -----------------------
    head = Layer()
    angle = math.degrees(math.atan2(down[0], down[1]))
    img = head_img.rotate(angle, resample=Image.NEAREST, expand=True) if abs(angle) > 18 else head_img
    centre = add(add(neck, down, -8.3), fwd, 0.5)
    ox, oy = round(centre[0] - img.width / 2), round(centre[1] - img.height / 2)
    hpx = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if hpx[x, y][3] > 0:
                head.put(ox + x, oy + y, hpx[x, y][:3])

    skirt = Layer()
    if pal.get("skirt"):
        skirt.capsule(add(hip, down, -1.0), add(hip, down, 7.0), 4.4, pal["skirt"])
        skirt.shade()

    fx = Layer()
    draw_fx(fx, P.get("fx", []), pal)

    return compose([(far_leg, True), (far_arm, True), (t, True), (head, True),
                    (near_leg, True), (skirt, True), (near_arm, True), (fx, False)], pal["outline"])


# ---------------------------------------------------------------------------
# Animation poses (authored on a 48x48 grid, facing right, floor at y=45)
# ---------------------------------------------------------------------------
def bobbed(b, **kw):
    p = dict(STANCE)
    for key in ("hip", "neck", "hf", "hb"):
        p[key] = (p[key][0], p[key][1] + b)
    p.update(kw)
    return p


def anim_idle():
    return [bobbed(b) for b in (0, 1, 1, 0)]


def anim_walk():
    frames = []
    for i in range(6):
        ph = 2 * math.pi * i / 6
        s, c = math.sin(ph), math.cos(ph)
        b = 1 if abs(s) > 0.5 else 0
        frames.append(bobbed(
            b,
            ff=(21 + 6 * s, 45 - (2.5 if c > 0.5 else 0)),
            fb=(19 - 6 * s, 45 - (2.5 if c < -0.5 else 0)),
            hf=(28 - s, 17 + b), hb=(25 + s, 19 + b),
        ))
    return frames


def anim_walk_back():
    return list(reversed(anim_walk()))


def anim_crouch():
    return [
        dict(hip=(20, 34), neck=(22, 22.5), hf=(29, 23), hb=(26, 25), ff=(26, 45), fb=(13, 45)),
        dict(hip=(20, 37), neck=(23, 26), hf=(30, 26), hb=(27, 28), ff=(27, 45), fb=(13, 45)),
    ]


def anim_jump():
    air = dict(toe_f=(2, 2), toe_b=(2, 2))
    return [
        dict(hip=(20, 27), neck=(21.5, 15), hf=(27, 12), hb=(24, 14), ff=(24, 38), fb=(15, 42), **air),
        dict(hip=(20, 26), neck=(22, 14.5), hf=(28, 16), hb=(25, 18), ff=(27, 31), fb=(21, 35), **air),
        dict(hip=(20, 27), neck=(21.5, 15), hf=(29, 15), hb=(26, 17), ff=(25, 41), fb=(14, 40), **air),
    ]


def anim_punch():
    lunge = dict(hip=(21, 29), neck=(23.5, 17.5), ff=(28, 45), fb=(13, 45))
    return [
        dict(hip=(19.5, 29), neck=(20.5, 17), hf=(23, 20), hb=(26, 17)),
        dict(lunge, hf=(37, 18.5), hb=(24, 21), fx=[("whoosh", 26, 32, 20)]),
        dict(lunge, hf=(37, 18.5), hb=(24, 21)),
        dict(hip=(20.5, 29), neck=(22, 17), hf=(31, 17), hb=(25, 19)),
    ]


def anim_kick():
    chamber = dict(hip=(19, 29), neck=(19.5, 17), hf=(25, 17), hb=(22, 19),
                   ff=(25, 34), fb=(18, 45), toe_f=(2, 1))
    extend = dict(hip=(19, 28.5), neck=(16.5, 17.5), hf=(22, 19), hb=(13, 24),
                  ff=(38, 25), fb=(18, 45), toe_f=(1, -2), eb=(0, -1))
    return [chamber, dict(extend, fx=[("whoosh", 28, 34, 28)]), dict(extend, hf=(22, 20)), chamber]


def anim_cast():
    gather = dict(hip=(19.5, 29.5), neck=(19.5, 17.5), hf=(17, 26), hb=(16, 25), eb=(-1, 0), ef=(-1, 0))
    push = dict(hip=(21, 29), neck=(23.5, 17.5), hf=(35, 21), hb=(34, 23), ff=(28, 45), fb=(13, 45))
    return [
        dict(gather, fx=[("orb", (15, 25), 2.5)]),
        dict(gather, fx=[("orb", (15, 25), 3.6)]),
        dict(push, fx=[("orb", (39, 22), 4.2)]),
        dict(hip=(20.5, 29), neck=(22, 17), hf=(32, 19), hb=(31, 21)),
    ]


def anim_block():
    guard = dict(hip=(19.5, 29), neck=(20.5, 17.5), hf=(27, 13), hb=(26, 16),
                 ef=(1, 0.3), eb=(1, 0.3), fb=(13, 45))
    return [guard, dict(guard, hip=(19, 29.5), neck=(19.5, 18), hf=(26, 13.5), hb=(25, 16.5))]


def anim_hit():
    h0 = dict(hip=(19, 29), neck=(17, 17.5), hf=(22, 24), hb=(15, 24), ff=(25, 45), fb=(13, 45))
    h1 = dict(hip=(18, 29.5), neck=(14.5, 18.5), hf=(23, 21), hb=(10, 21), ff=(25, 45), fb=(12, 45))
    return [h0, h1, h0]


def anim_ko():
    up = (0, -1)
    lying = dict(hip=(27, 43), neck=(15, 42.5), hf=(20, 37), hb=(11, 45),
                 ff=(43, 43), fb=(40, 44.5), toe_f=(0.5, -2.5), toe_b=(0.5, -2.5), kf=up, kb=up)
    return [
        dict(hip=(18, 29.5), neck=(14.5, 18.5), hf=(23, 21), hb=(10, 21), ff=(25, 45), fb=(12, 45)),
        dict(hip=(19, 34), neck=(12, 25), hf=(17, 21), hb=(7, 28), ff=(29, 39), fb=(26, 41), toe_f=(2, -1)),
        dict(hip=(25, 41), neck=(14, 38), hf=(18, 33), hb=(11, 44), ff=(37, 33), fb=(33, 36),
             kf=up, kb=up, toe_f=(1, -2), toe_b=(1, -2)),
        lying,
        lying,
    ]


def anim_victory():
    base = dict(hb=(19, 28), eb=(-1, 0), ef=(0, 1), ff=(25, 45), fb=(15, 45))
    return [
        bobbed(0, hf=(36, 12), **base),
        bobbed(-1, hf=(38, 8), **base),
        bobbed(-1, hf=(38, 7), **base),
        bobbed(0, hf=(37, 10), **base),
    ]


def anim_ulti():
    charge = dict(hip=(20, 29.5), neck=(21, 17.5), hf=(34, 7), hb=(32, 8), ef=(0, 1), eb=(0, 1),
                  ff=(27, 45), fb=(13, 45))
    return [
        dict(charge, fx=[("orb", (37, 2), 2.5)]),
        dict(charge, fx=[("orb", (37, 2), 3.5)]),
        dict(charge, hf=(34, 6), hb=(32, 7), fx=[("orb", (37, 1), 4.5)]),
        dict(charge, hf=(34, 6), hb=(32, 7), fx=[("orb", (37, 1), 4.0)]),
    ]


# name, pose builder, fps, loop
ANIMATIONS = [
    ("idle", anim_idle, 6, True),
    ("walk", anim_walk, 10, True),
    ("walk_back", anim_walk_back, 9, True),
    ("crouch", anim_crouch, 14, False),
    ("jump", anim_jump, 8, False),
    ("punch", anim_punch, 16, False),
    ("kick", anim_kick, 14, False),
    ("cast", anim_cast, 12, False),
    ("block", anim_block, 10, False),
    ("hit", anim_hit, 12, False),
    ("ko", anim_ko, 8, False),
    ("victory", anim_victory, 6, True),
    ("ulti", anim_ulti, 8, False),
]


# ---------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------
def projectile_frame(style, energy, i):
    L = Layer(24, 16)
    rng = random.Random(i * 31 + len(style))
    head = (16, 8)
    if style == "fire":
        for layer_i, col in enumerate(reversed(energy)):
            shrink = layer_i * 1.2
            for t in range(0, 12):
                r = 5.2 - t * 0.42 - shrink
                if r > 0.4:
                    y = 8 + math.sin(t * 0.8 + i * 1.6) * 1.3 * (t / 11)
                    L.circle((16 - t, y), r, col)
    elif style == "acid":
        for k in range(4):
            x = 11 - k * 2.6 - (i % 2)
            L.circle((x, 8 + k * 0.9 + (i % 2) * 0.5), 1.8 - k * 0.3, energy[2 if k % 2 else 1])
        L.circle(head, 5.0, energy[3])
        L.circle(head, 4.0, energy[2])
        L.circle((16.5, 7.5 + (i % 2) * 0.5), 2.6, energy[1])
        L.put(17, 5, energy[0])
        L.put(18 - i % 2, 6, energy[0])
    else:  # ice
        for k in range(6):
            L.put(12 - k * 2 - i % 2, 8 + rng.randint(-3, 3), energy[1 + k % 2])
        L.circle(head, 5.2, energy[3])
        L.circle(head, 4.2, energy[2])
        L.circle(head, 2.8, energy[1])
        L.circle(head, 1.3, energy[0])
        arms = [(1, 0), (0, 1)] if i % 2 == 0 else [(1, 1), (1, -1)]
        for dx, dy in arms:
            for s in (5, 6, -5, -6):
                L.put(16 + dx * s, 8 + dy * s, energy[0])
    return compose([(L, False)], (0, 0, 0), 24, 16)


def hit_spark_frame(i):
    L = Layer(32, 32)
    c = (16, 16)
    starts = [0, 2, 5, 8, 11]
    ends = [5, 9, 12, 13, 14]
    for k in range(8):
        ang = k * math.pi / 4 + 0.2
        length = ends[i] * (1.0 if k % 2 == 0 else 0.65)
        d = (math.cos(ang), math.sin(ang))
        t = starts[i] * (1.0 if k % 2 == 0 else 0.65)
        while t <= length:
            col = (255, 255, 255) if t < length * 0.4 else (255, 226, 110) if t < length * 0.75 else (255, 140, 50)
            if i < 4 or int(t) % 2 == 0:
                L.put(round(c[0] + d[0] * t), round(c[1] + d[1] * t), col)
            t += 0.5
    core = [3.5, 4.5, 3.2, 1.5, 0][i]
    if core:
        L.circle(c, core, (255, 226, 110))
        L.circle(c, core - 1.2, (255, 255, 255))
    return compose([(L, False)], (0, 0, 0), 32, 32)


def block_spark_frame(i):
    L = Layer(24, 24)
    radius = [4, 7, 9, 11][i]
    cols = [(230, 250, 255), (140, 210, 255), (80, 160, 240)]
    for step in range(-30, 31):
        a = math.radians(step * 2)
        for w, col in enumerate(cols):
            r = radius - w
            if r <= 0 or (i >= 2 and (step + w) % 3 == 0):
                continue
            L.put(round(6 + math.cos(a) * r), round(12 + math.sin(a) * r * 1.3), col)
    return compose([(L, False)], (0, 0, 0), 24, 24)


def dust_frame(i):
    L = Layer(32, 16)
    spread = [3, 6, 9, 11][i]
    radius = [2.2, 3.0, 3.2, 2.6][i]
    for side in (-1, 1):
        for j, col in enumerate([(150, 140, 135), (190, 182, 172)]):
            L.circle((16 + side * spread, 12 - i * 0.6 - j * 0.8), radius - j * 0.9, col)
    if i >= 2:
        L.px = {k: v for k, v in L.px.items() if (k[0] + k[1] + i) % (4 - i // 3 * 2) != 0}
    return compose([(L, False)], (0, 0, 0), 32, 16)


def save_strip(frames, path, scale=SCALE):
    w, h = frames[0].size
    strip = Image.new("RGBA", (w * scale * len(frames), h * scale), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        strip.paste(upscale(f, scale), (i * w * scale, 0))
    strip.save(path)
    return strip


def build_effects():
    fx_dir = os.path.join(ASSETS, "effects")
    os.makedirs(fx_dir, exist_ok=True)
    save_strip([hit_spark_frame(i) for i in range(5)], os.path.join(fx_dir, "hit_spark.png"))
    save_strip([block_spark_frame(i) for i in range(4)], os.path.join(fx_dir, "block_spark.png"))
    save_strip([dust_frame(i) for i in range(4)], os.path.join(fx_dir, "dust.png"))
    meta = {
        "hit_spark": {"frame_width": 64, "frame_height": 64, "frames": 5, "fps": 24, "loop": False},
        "block_spark": {"frame_width": 48, "frame_height": 48, "frames": 4, "fps": 20, "loop": False},
        "dust": {"frame_width": 64, "frame_height": 32, "frames": 4, "fps": 14, "loop": False},
    }
    with open(os.path.join(fx_dir, "effects.json"), "w") as f:
        json.dump(meta, f, indent=2)


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------
def build_character(name, pal):
    out_dir = os.path.join(ASSETS, "characters", name)
    frames_dir = os.path.join(out_dir, "frames")
    sounds_dir = os.path.join(out_dir, "sounds")
    for d in (frames_dir, sounds_dir):
        os.makedirs(d, exist_ok=True)
    readme = os.path.join(sounds_dir, "README.txt")
    if not os.path.exists(readme):
        with open(readme, "w") as f:
            f.write(SOUND_README.format(name=name))

    head_img = load_head(pal)
    rendered = [(anim, [draw_fighter(p, pal, head_img) for p in builder()], fps, loop)
                for anim, builder, fps, loop in ANIMATIONS]

    cols = max(len(frames) for _, frames, _, _ in rendered)
    fw = fh = FRAME * SCALE
    sheet = Image.new("RGBA", (cols * fw, len(rendered) * fh), (0, 0, 0, 0))
    meta = {
        "name": name,
        "frame_width": fw,
        "frame_height": fh,
        "anchor": [ANCHOR[0] * SCALE, ANCHOR[1] * SCALE + SCALE],
        "facing": "right",
        "projectile": {"file": f"{name}_projectile.png", "frame_width": 48, "frame_height": 32,
                       "frames": 4, "fps": 12},
        "animations": {},
    }
    for row, (anim, frames, fps, loop) in enumerate(rendered):
        for col, img in enumerate(frames):
            big = upscale(img, SCALE)
            sheet.paste(big, (col * fw, row * fh))
            big.save(os.path.join(frames_dir, f"{anim}_{col}.png"))
        meta["animations"][anim] = {"row": row, "frames": len(frames), "fps": fps, "loop": loop}

    sheet.save(os.path.join(out_dir, f"{name}_sheet.png"))
    with open(os.path.join(out_dir, f"{name}_sheet.json"), "w") as f:
        json.dump(meta, f, indent=2)

    portrait = Layer(HEAD_W + 2, HEAD_H + 2)
    hp = head_img.load()
    for y in range(HEAD_H):
        for x in range(HEAD_W):
            if hp[x, y][3]:
                portrait.put(x + 1, y + 1, hp[x, y][:3])
    upscale(compose([(portrait, True)], pal["outline"], HEAD_W + 2, HEAD_H + 2), 8).save(
        os.path.join(out_dir, f"{name}_portrait.png"))

    save_strip([projectile_frame(pal["projectile"], pal["energy"], i) for i in range(4)],
               os.path.join(out_dir, f"{name}_projectile.png"))
    return name, rendered


# ---------------------------------------------------------------------------
# Background (256x144 base, exported 4x -> 1024x576). Ground line at y=119 (=476 px)
# ---------------------------------------------------------------------------
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither(x, y):
    return (BAYER[y % 4][x % 4] + 0.5) / 16.0


def build_background():
    W, H, GY = 256, 144, 119
    rng = random.Random(7)
    img = Image.new("RGB", (W, H))
    px = img.load()

    sky = [(16, 9, 32), (28, 13, 46), (44, 19, 60), (64, 27, 70), (90, 37, 76), (118, 50, 78)]
    for y in range(H):
        for x in range(W):
            band = y / GY * (len(sky) - 1)
            lo = min(int(band), len(sky) - 1)
            hi = min(lo + 1, len(sky) - 1)
            px[x, y] = sky[hi] if band - lo > dither(x, y) else sky[lo]

    for _ in range(70):
        x, y = rng.randrange(W), rng.randrange(70)
        px[x, y] = rng.choice([(210, 200, 235), (150, 140, 190), (255, 240, 220)])

    # moon with dithered halo
    mc, mr = (128, 40), 16
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - mc[0], y - mc[1])
            if d <= mr:
                px[x, y] = (242, 226, 196)
            elif d <= mr + 7 and (d - mr) / 7 < dither(x, y):
                px[x, y] = mix(px[x, y], (160, 90, 110), 0.5)
    for cx, cy, cr in ((122, 34, 3.5), (134, 46, 2.5), (131, 33, 1.5), (120, 45, 2)):
        for y in range(int(cy - cr), int(cy + cr) + 1):
            for x in range(int(cx - cr), int(cx + cr) + 1):
                if math.hypot(x - cx, y - cy) <= cr:
                    px[x, y] = (220, 200, 172)

    # mountains
    for base, amp, col, rim, seed in ((80, 10, (46, 22, 60), (70, 34, 76), 1.0),
                                      (92, 7, (32, 16, 44), (58, 28, 66), 2.3)):
        for x in range(W):
            h = int(base - amp * (0.6 * math.sin(x * 0.045 + seed) + 0.4 * math.sin(x * 0.13 + seed * 2)))
            for y in range(h, GY):
                px[x, y] = col
            px[x, h] = rim

    # back wall with bricks
    wall_top = 96
    for y in range(wall_top, GY):
        row = (y - wall_top) // 4
        for x in range(W):
            if (y - wall_top) % 4 == 3 or (x + (row % 2) * 6) % 12 == 0:
                px[x, y] = (38, 32, 50)
            else:
                v = ((x + (row % 2) * 6) // 12 * 7 + row * 13) % 11 - 5
                c = (72 + v, 62 + v, 84 + v)
                px[x, y] = mix(c, (255, 255, 255), 0.12) if (y - wall_top) % 4 == 0 else c
    for y in range(wall_top - 3, wall_top):
        for x in range(W):
            px[x, y] = (100, 90, 112) if y == wall_top - 3 else (80, 72, 94)

    def pillar(x0, w):
        for y in range(8, GY):
            for x in range(x0, x0 + w):
                c = mix((118, 106, 128), (48, 40, 58), (x - x0) / (w - 1))
                if (x - x0) % 5 == 2 and 18 < y < GY - 8:
                    c = mul(c, 0.8)
                px[x, y] = c
        for y0, y1 in ((8, 15), (GY - 7, GY)):
            for y in range(y0, y1):
                for x in range(x0 - 3, x0 + w + 3):
                    if 0 <= x < W:
                        px[x, y] = (126, 114, 138) if y == y0 else (86, 76, 98)

    def banner(x0, w):
        for y in range(18, 62):
            for x in range(x0, x0 + w):
                notch = y > 56 and abs(x - (x0 + w / 2 - 0.5)) < (y - 56) * 0.9
                if not notch:
                    px[x, y] = (156, 28, 38) if x not in (x0, x0 + w - 1) else (110, 18, 28)
        cx, cy = x0 + w // 2, 36
        for y in range(cy - 5, cy + 6):
            for x in range(cx - 5, cx + 6):
                d = abs(x - cx) + abs(y - cy)
                if d == 5 or d == 2:
                    px[x, y] = (240, 190, 70)

    for x0, w in ((6, 22), (48, 16), (228, 22), (192, 16)):
        pillar(x0, w)
    banner(50, 12)
    banner(194, 12)

    # roof beam
    for y in range(0, 9):
        for x in range(W):
            px[x, y] = (54, 30, 32) if y < 7 else (86, 50, 44)
            if x % 32 == 0 and y < 7:
                px[x, y] = (36, 20, 22)

    # braziers with warm light
    flame_cols = [(150, 40, 30), (230, 90, 30), (255, 180, 60), (255, 240, 160)]
    for bx in (96, 160):
        for y in range(GY - 22, GY):
            px[bx, y] = (60, 48, 50)
            px[bx + 1, y] = (44, 34, 38)
        for y in range(GY - 28, GY - 22):
            half = 6 - (y - (GY - 28)) // 2
            for x in range(bx - half, bx + half + 2):
                px[x, y] = (120, 92, 60) if y == GY - 28 else (86, 64, 44)
        for i, col in enumerate(flame_cols):
            for y in range(GY - 44 + i * 3, GY - 28):
                t = (y - (GY - 44)) / 16
                half = max(0.0, 5.5 * math.sin(t * math.pi * 0.9) - i * 1.2)
                sway = math.sin(y * 0.6) * (1 - t)
                for x in range(int(bx - half + sway), int(bx + half + 2 + sway)):
                    px[x, y] = col
        for y in range(8, GY):
            for x in range(max(0, bx - 44), min(W, bx + 46)):
                d = math.hypot(x - bx, (y - (GY - 34)) * 1.2)
                if d < 44 and (1 - d / 44) * 0.55 > dither(x, y) * 0.9:
                    px[x, y] = mix(px[x, y], (255, 150, 70), 0.18)

    # stone floor with perspective tiles
    for y in range(GY, H):
        depth = (y - GY) / (H - GY)
        tile_w = 16 + 14 * depth
        row = int(math.sqrt(depth) * 5)
        row_line = int(math.sqrt(max(0.0, (y + 1 - GY) / (H - GY))) * 5) != row
        for x in range(W):
            col = int(math.floor((x - 128) / tile_w))
            fx = (x - 128) / tile_w - col
            base = (64, 56, 74) if (row + col) % 2 == 0 else (56, 48, 66)
            base = mix(base, (0, 0, 0), depth * 0.25)
            if y == GY:
                base = (120, 106, 132)
            elif row_line or fx < 1 / tile_w:
                base = (38, 32, 48)
            for bx in (96, 160):
                d = abs(x - bx) / 60 + depth * 0.6
                if d < 1 and (1 - d) * 0.5 > dither(x, y):
                    base = mix(base, (255, 150, 70), 0.15)
            px[x, y] = base

    # soft vignette
    for y in range(H):
        for x in range(W):
            e = max(abs(x - 128) / 128, abs(y - 72) / 72)
            if e > 0.85 and (e - 0.85) * 5 > dither(x, y):
                px[x, y] = mul(px[x, y], 0.75)

    bg_dir = os.path.join(ASSETS, "backgrounds")
    os.makedirs(bg_dir, exist_ok=True)
    img.resize((W * 4, H * 4), Image.NEAREST).save(os.path.join(bg_dir, "arena_temple.png"))
    return img


# ---------------------------------------------------------------------------
# Previews
# ---------------------------------------------------------------------------
PREVIEW_FRAME = {"walk": 1, "walk_back": 4, "crouch": 1, "jump": 1, "punch": 1, "kick": 1,
                 "cast": 2, "hit": 1, "ko": 3, "victory": 1}


def build_previews(characters, bg_base):
    prev_dir = os.path.join(ASSETS, "preview")
    os.makedirs(prev_dir, exist_ok=True)
    fw = FRAME * SCALE

    # overview: one row per character, one column per animation
    label_w, head_h = 70, 24
    ov = Image.new("RGBA", (label_w + fw * len(ANIMATIONS), head_h + fw * len(characters)), (22, 22, 32, 255))
    d = ImageDraw.Draw(ov)
    for a, (anim, *_r) in enumerate(ANIMATIONS):
        d.text((label_w + a * fw + 6, 6), anim.upper(), fill=(200, 200, 220, 255))
    for r, (name, rendered) in enumerate(characters):
        if r % 2:
            d.rectangle((0, head_h + r * fw, ov.width, head_h + (r + 1) * fw - 1), fill=(30, 30, 44, 255))
        d.text((8, head_h + r * fw + fw // 2 - 6), name.upper(), fill=(255, 220, 120, 255))
        for a, (anim, frames, _fps, _loop) in enumerate(rendered):
            f = frames[min(PREVIEW_FRAME.get(anim, 0), len(frames) - 1)]
            ov.alpha_composite(upscale(f, SCALE), (label_w + a * fw, head_h + r * fw))
    ov.save(os.path.join(prev_dir, "overview.png"))

    # animated GIF: all fighters on the arena, cycling every animation
    bg = bg_base.resize((bg_base.width * 3, bg_base.height * 3), Image.NEAREST)
    ground = 119 * 3
    gif_frames, durations = [], []
    for a_idx, (anim, _b, fps, loop) in enumerate(ANIMATIONS):
        n = len(characters[0][1][a_idx][1])
        steps = n * (3 if loop else 1) + (0 if loop else 5)
        for s in range(steps):
            f = bg.copy().convert("RGBA")
            for c_idx, (_name, rendered) in enumerate(characters):
                frame = rendered[a_idx][1][s % n if loop else min(s, n - 1)]
                x = 105 + c_idx * 140 - ANCHOR[0] * SCALE
                f.alpha_composite(upscale(frame, SCALE), (x, ground - fw + SCALE * 2))
            dd = ImageDraw.Draw(f)
            dd.rectangle((0, bg.height - 26, bg.width, bg.height), fill=(0, 0, 0, 180))
            dd.text((10, bg.height - 20), f"{anim.upper()}  ({n} frames @ {fps} fps)", fill=(255, 230, 140, 255))
            gif_frames.append(f.convert("RGB"))
            durations.append(int(1000 / fps))
    gif_frames[0].save(os.path.join(prev_dir, "fighters.gif"), save_all=True,
                       append_images=gif_frames[1:], duration=durations, loop=0)


def main():
    characters = [build_character(name, pal) for name, pal in CHARACTERS.items()]
    build_effects()
    bg = build_background()
    build_previews(characters, bg)
    print("Generated", ", ".join(CHARACTERS), "+ effects, background and previews in assets/")


if __name__ == "__main__":
    main()
