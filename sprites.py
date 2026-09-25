import os
import json
import pygame

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
ROSTER = ["Gian", "Mega", "Puba", "Subi", "Wowi"]

# Accent colour per character (projectile trail, hit sparks, UI highlights)
CHARACTER_COLORS = {
    "Gian": (230, 40, 50),
    "Mega": (246, 110, 50),
    "Puba": (60, 150, 250),
    "Subi": (230, 160, 30),
    "Wowi": (220, 220, 235),
}

SOUND_KEYS = ("select", "punch", "kick", "special", "block", "hit", "ko", "victory", "ulti")

_image_cache = {}
_character_cache = {}


def load_image(path):
    if path not in _image_cache:
        _image_cache[path] = pygame.image.load(path).convert_alpha()
    return _image_cache[path]


def load_strip(path, frame_w, scale=1.0):
    """Cuts a horizontal sprite strip into frames."""
    sheet = load_image(path)
    frame_h = sheet.get_height()
    frames = []
    for i in range(sheet.get_width() // frame_w):
        frame = sheet.subsurface(pygame.Rect(i * frame_w, 0, frame_w, frame_h)).copy()
        if scale != 1.0:
            frame = pygame.transform.scale(frame, (int(frame_w * scale), int(frame_h * scale)))
        frames.append(frame)
    return frames


class Animation:
    def __init__(self, frames, fps, loop):
        self.frames = frames
        self.flipped = [pygame.transform.flip(f, True, False) for f in frames]
        self.fps = fps
        self.loop = loop


class Animator:
    """Plays one of a character's animations; frames face right and are flipped for facing left."""

    def __init__(self, animations, anchor, frame_w):
        self.animations = animations
        self.anchor = anchor
        self.frame_w = frame_w
        self.current = "idle"
        self.time = 0.0

    def play(self, name):
        if name not in self.animations:
            name = "idle"
        if name != self.current:
            self.current = name
            self.time = 0.0

    def update(self, dt=1 / 60):
        self.time += dt

    def frame_index(self):
        anim = self.animations[self.current]
        i = int(self.time * anim.fps)
        return i % len(anim.frames) if anim.loop else min(i, len(anim.frames) - 1)

    def draw(self, surface, midbottom, facing):
        anim = self.animations[self.current]
        i = self.frame_index()
        img = anim.frames[i] if facing == 1 else anim.flipped[i]
        ax = self.anchor[0] if facing == 1 else self.frame_w - self.anchor[0]
        surface.blit(img, (midbottom[0] - ax, midbottom[1] - self.anchor[1]))


class CharacterAssets:
    """Everything generate_sprites.py / generate_ulti.py produced for one character."""

    def __init__(self, name):
        self.name = name
        self.base = os.path.join(ASSETS_DIR, "characters", name)
        with open(os.path.join(self.base, f"{name}_sheet.json")) as f:
            meta = json.load(f)

        sheet = load_image(os.path.join(self.base, f"{name}_sheet.png"))
        fw, fh = meta["frame_width"], meta["frame_height"]
        self.frame_w = fw
        self.anchor = tuple(meta["anchor"])
        self.animations = {}
        for anim, info in meta["animations"].items():
            frames = [sheet.subsurface(pygame.Rect(i * fw, info["row"] * fh, fw, fh)).copy()
                      for i in range(info["frames"])]
            self.animations[anim] = Animation(frames, info["fps"], info["loop"])

        self.portrait = load_image(os.path.join(self.base, f"{name}_portrait.png"))
        proj = meta["projectile"]
        self.projectile_frames = load_strip(os.path.join(self.base, proj["file"]), proj["frame_width"])
        self.color = CHARACTER_COLORS.get(name, (255, 255, 255))

        self.ulti_dir = os.path.join(self.base, "ulti")
        with open(os.path.join(self.ulti_dir, "ulti.json")) as f:
            self.ulti = json.load(f)

        self.sounds = {}
        sounds_dir = os.path.join(self.base, "sounds")
        for key in SOUND_KEYS:
            for ext in (".wav", ".ogg", ".mp3"):
                path = os.path.join(sounds_dir, key + ext)
                if os.path.exists(path):
                    try:
                        self.sounds[key] = pygame.mixer.Sound(path)
                    except Exception as e:
                        print(f"Could not load sound {path}: {e}")
                    break

    def new_animator(self):
        return Animator(self.animations, self.anchor, self.frame_w)

    def ulti_frames(self, key, scale=1.0):
        spec = self.ulti["sprites"][key]
        return load_strip(os.path.join(self.ulti_dir, spec["file"]), spec["frame_width"], scale)


def get_character(name):
    if name not in _character_cache:
        _character_cache[name] = CharacterAssets(name)
    return _character_cache[name]


def pick_animation(f):
    """Chooses the animation that matches a fighter's current state."""
    if f.is_dead:
        return "ko"
    if f.is_victorious:
        return "victory"
    if f.ulti_cast_timer > 0:
        return "ulti"
    if f.is_blocking:
        return "block"
    if f.hit_flash_timer > 0:
        return "hit"
    if f.melee_anim_timer > 0:
        return f.melee_anim
    if f.cast_timer > 0:
        return "cast"
    if not f.is_grounded:
        return "jump"
    if f.is_crouching:
        return "crouch"
    if abs(f.vx) > 0.1:
        return "walk" if (f.vx > 0) == (f.facing_direction == 1) else "walk_back"
    return "idle"
