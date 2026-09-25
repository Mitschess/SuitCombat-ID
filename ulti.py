import os
import math
import random
import pygame
from settings import SCREEN_WIDTH, GROUND_Y
from sprites import ASSETS_DIR, load_strip

EFFECTS_DIR = os.path.join(ASSETS_DIR, "effects")


def warning_frames():
    return load_strip(os.path.join(EFFECTS_DIR, "ulti_warning.png"), 80)


def crash_frames(scale=1.0):
    return load_strip(os.path.join(EFFECTS_DIR, "ulti_crash.png"), 144, scale)


class OneShot:
    """A non-looping animation drawn once (crash dust, explosion)."""

    def __init__(self, frames, center, fps=16):
        self.frames = frames
        self.center = center
        self.fps = fps
        self.t = 0
        self.alive = True

    def update(self):
        self.t += 1
        if int(self.t * self.fps / 60) >= len(self.frames):
            self.alive = False

    def draw(self, surface):
        if self.alive:
            img = self.frames[min(int(self.t * self.fps / 60), len(self.frames) - 1)]
            surface.blit(img, img.get_rect(center=self.center))


def draw_warning(surface, frames, x, t):
    img = frames[(t // 8) % len(frames)]
    surface.blit(img, img.get_rect(midbottom=(int(x), GROUND_Y + 10)))


class UltiEffect:
    """Base class: an ultimate cast by `owner` that can only damage `target` (unblockable)."""

    def __init__(self, owner, target):
        self.owner = owner
        self.target = target
        self.alive = True
        self.t = 0
        self.fx = []
        self.ai_will_dodge = random.random() < 0.65   # CPU reaction roll, decided once per ulti

    def hit(self, combat, sound, damage, x, y):
        if self.target.is_dead:
            return
        knock = 1 if self.target.rect.centerx >= x else -1
        self.target.take_damage(damage, knockback_dir=knock)
        combat.add_hit_effect(x, y, damage, is_crit=True, color=self.owner.accent_color)
        sound.play_fighter(self.target, "hit")

    def step_fx(self):
        for f in self.fx:
            f.update()
        self.fx = [f for f in self.fx if f.alive]

    def update(self, combat, sound):
        self.t += 1

    def draw_back(self, surface):
        pass

    def draw_front(self, surface):
        for f in self.fx:
            f.draw(surface)

    def ai_hint(self, fighter):
        return None


def away_from(fighter, x):
    return "left" if x > fighter.rect.centerx else "right"


# ---------------------------------------------------------------------------
class GianCloneRain(UltiEffect):
    """10 Gian clones fall around the opponent; dodge by moving left/right."""

    WARN = 30

    def __init__(self, owner, target, assets):
        super().__init__(owner, target)
        s = assets.ulti["suggested"]
        self.frames = assets.ulti_frames("falling", s.get("draw_scale", 0.8))
        self.warn_frames = warning_frames()
        self.crash = crash_frames(0.8)
        self.count = s.get("count", 10)
        self.interval = s.get("spawn_interval_frames", 8)
        self.damage = s.get("damage_per_hit", 4)
        self.spawned = 0
        self.clones = []

    def update(self, combat, sound):
        super().update(combat, sound)
        if self.spawned < self.count and self.t % self.interval == 1:
            x = self.target.rect.centerx + random.gauss(0, 60)
            self.clones.append({"x": max(30, min(SCREEN_WIDTH - 30, x)), "warn": self.WARN,
                                "bottom": -20.0, "vy": 6.0, "facing": random.choice((1, -1))})
            self.spawned += 1
        for c in self.clones:
            if c["warn"] > 0:
                c["warn"] -= 1
                continue
            c["vy"] += 0.6
            c["bottom"] += c["vy"]
            rect = pygame.Rect(0, 0, 40, 70)
            rect.midbottom = (int(c["x"]), int(c["bottom"]))
            if rect.colliderect(self.target.get_rect()):
                self.hit(combat, sound, self.damage, c["x"], rect.centery)
                c["done"] = True
            elif c["bottom"] >= GROUND_Y:
                combat.screen_shake = max(combat.screen_shake, 3)
                c["done"] = True
            if c.get("done"):
                self.fx.append(OneShot(self.crash, (int(c["x"]), GROUND_Y - 25)))
        self.clones = [c for c in self.clones if not c.get("done")]
        self.step_fx()
        self.alive = self.spawned < self.count or bool(self.clones) or bool(self.fx)

    def draw_back(self, surface):
        for c in self.clones:
            draw_warning(surface, self.warn_frames, c["x"], self.t)

    def draw_front(self, surface):
        for c in self.clones:
            if c["warn"] == 0:
                img = self.frames[(self.t // 8) % len(self.frames)]
                if c["facing"] == -1:
                    img = pygame.transform.flip(img, True, False)
                surface.blit(img, img.get_rect(midbottom=(int(c["x"]), int(c["bottom"]) + 10)))
        super().draw_front(surface)

    def ai_hint(self, fighter):
        for c in self.clones:
            if abs(c["x"] - fighter.rect.centerx) < 50:
                return away_from(fighter, c["x"])
        return None


# ---------------------------------------------------------------------------
class SubiMissile(UltiEffect):
    """Palm-oil missile flies in a parabola onto the opponent's position; dodge left/right."""

    def __init__(self, owner, target, assets):
        super().__init__(owner, target)
        s = assets.ulti["suggested"]
        self.frames = assets.ulti_frames("missile")
        self.boom = assets.ulti_frames("explosion", 1.4)
        self.warn_frames = warning_frames()
        self.flight = s.get("flight_frames", 70)
        self.apex = s.get("apex_height_px", 300)
        self.radius = s.get("explosion_radius_px", 60)
        self.damage = s.get("damage", 22)
        self.x0, self.y0 = owner.rect.centerx, owner.rect.top + 20
        self.x1, self.y1 = target.rect.centerx, GROUND_Y - 10
        self.flying = True

    def pos(self, u):
        return (self.x0 + (self.x1 - self.x0) * u,
                self.y0 + (self.y1 - self.y0) * u - 4 * self.apex * u * (1 - u))

    def explode(self, combat, x, y):
        self.flying = False
        self.fx.append(OneShot(self.boom, (int(x), int(y) - 20), fps=14))
        combat.screen_shake = max(combat.screen_shake, 12)
        target = self.target.get_rect()
        if abs(target.centerx - x) < self.radius + target.width / 2 and target.bottom > GROUND_Y - 130:
            return True
        return False

    def update(self, combat, sound):
        super().update(combat, sound)
        if self.flying:
            u = min(1.0, self.t / self.flight)
            x, y = self.pos(u)
            hit_mid_air = pygame.Rect(int(x) - 18, int(y) - 18, 36, 36).colliderect(self.target.get_rect())
            if hit_mid_air or u >= 1.0:
                if self.explode(combat, x, max(y, GROUND_Y - 30) if not hit_mid_air else y):
                    self.hit(combat, sound, self.damage, self.target.rect.centerx, self.target.rect.centery)
        self.step_fx()
        self.alive = self.flying or bool(self.fx)

    def draw_back(self, surface):
        if self.flying:
            draw_warning(surface, self.warn_frames, self.x1, self.t)

    def draw_front(self, surface):
        if self.flying:
            u = min(1.0, self.t / self.flight)
            x, y = self.pos(u)
            dx = self.x1 - self.x0
            dy = (self.y1 - self.y0) - 4 * self.apex * (1 - 2 * u)
            angle = -math.degrees(math.atan2(dy, dx))
            img = pygame.transform.rotate(self.frames[(self.t // 4) % len(self.frames)], angle)
            surface.blit(img, img.get_rect(center=(int(x), int(y))))
        super().draw_front(surface)

    def ai_hint(self, fighter):
        if self.flying and abs(self.x1 - fighter.rect.centerx) < self.radius + 30:
            return away_from(fighter, self.x1)
        return None


# ---------------------------------------------------------------------------
class WowiBuilding(UltiEffect):
    """A building drops on the opponent; dodge left/right during the warning."""

    TRACK = 25   # frames the drop point follows the target before locking

    def __init__(self, owner, target, assets):
        super().__init__(owner, target)
        s = assets.ulti["suggested"]
        self.image = assets.ulti_frames("building")[0]
        self.warn_frames = warning_frames()
        self.crash = crash_frames(1.6)
        self.warn = s.get("warning_frames", 50)
        self.inset = s.get("hitbox_inset_px", 30)
        self.damage = s.get("damage", 25)
        self.x = target.rect.centerx
        self.bottom = 0.0
        self.vy = 12.0
        self.landed = 0
        self.has_hit = False

    def hitbox(self):
        w = self.image.get_width() - self.inset * 2
        rect = pygame.Rect(0, 0, w, self.image.get_height() - 10)
        rect.midbottom = (int(self.x), int(self.bottom))
        return rect

    def update(self, combat, sound):
        super().update(combat, sound)
        if self.t < self.TRACK:
            self.x = self.target.rect.centerx
        if self.t > self.warn and not self.landed:
            self.vy += 1.0
            self.bottom = min(GROUND_Y, self.bottom + self.vy)
            if not self.has_hit and self.hitbox().colliderect(self.target.get_rect()):
                self.has_hit = True
                self.hit(combat, sound, self.damage, self.target.rect.centerx, self.target.rect.centery)
            if self.bottom >= GROUND_Y:
                self.landed = 1
                combat.screen_shake = max(combat.screen_shake, 16)
                self.fx.append(OneShot(self.crash, (int(self.x), GROUND_Y - 30)))
        elif self.landed:
            self.landed += 1
        self.step_fx()
        self.alive = not self.landed or self.landed < 40 or bool(self.fx)

    def draw_back(self, surface):
        if self.t <= self.warn:
            draw_warning(surface, self.warn_frames, self.x, self.t)

    def draw_front(self, surface):
        if self.t > self.warn and self.landed < 40:
            img = self.image
            if self.landed > 20:
                img = img.copy()
                img.set_alpha(int(255 * (40 - self.landed) / 20))
            surface.blit(img, img.get_rect(midbottom=(int(self.x), int(self.bottom))))
        super().draw_front(surface)

    def ai_hint(self, fighter):
        if not self.landed and abs(self.x - fighter.rect.centerx) < self.hitbox().width / 2 + 40:
            return away_from(fighter, self.x)
        return None


# ---------------------------------------------------------------------------
class MegaBull(UltiEffect):
    """A bull charges from Mega's side of the screen; dodge by jumping."""

    WARN = 35

    def __init__(self, owner, target, assets):
        super().__init__(owner, target)
        s = assets.ulti["suggested"]
        self.frames = assets.ulti_frames("run")
        self.flipped = [pygame.transform.flip(f, True, False) for f in self.frames]
        self.warn_frames = warning_frames()
        self.speed = s.get("speed", 11.0)
        self.damage = s.get("damage", 20)
        self.hit_h = s.get("hitbox_height_px", 70)
        self.dir = 1 if owner.rect.centerx < target.rect.centerx else -1
        self.x = -100.0 if self.dir == 1 else SCREEN_WIDTH + 100.0
        self.has_hit = False

    def hitbox(self):
        rect = pygame.Rect(0, 0, 110, self.hit_h)
        rect.midbottom = (int(self.x), GROUND_Y)
        return rect

    def update(self, combat, sound):
        super().update(combat, sound)
        if self.t > self.WARN:
            self.x += self.dir * self.speed
            if self.t % 6 == 0:
                combat.screen_shake = max(combat.screen_shake, 2)
            if not self.has_hit and self.hitbox().colliderect(self.target.get_rect()):
                self.has_hit = True
                self.hit(combat, sound, self.damage, self.target.rect.centerx, self.target.rect.centery)
        self.alive = -200 < self.x < SCREEN_WIDTH + 200

    def draw_back(self, surface):
        if self.t <= self.WARN:
            edge = 50 if self.dir == 1 else SCREEN_WIDTH - 50
            draw_warning(surface, self.warn_frames, edge, self.t)

    def draw_front(self, surface):
        if self.t > self.WARN:
            frames = self.frames if self.dir == 1 else self.flipped
            img = frames[(self.t // 5) % len(frames)]
            surface.blit(img, img.get_rect(midbottom=(int(self.x), GROUND_Y + 6)))

    def ai_hint(self, fighter):
        ahead = (fighter.rect.centerx - self.x) * self.dir
        if not self.has_hit and self.t > self.WARN - 10 and 0 < ahead < 200:
            return "jump"
        return None


# ---------------------------------------------------------------------------
class PubaLightning(UltiEffect):
    """Stock-crash cloud appears over the opponent, then lightning strikes; dodge left/right."""

    def __init__(self, owner, target, assets):
        super().__init__(owner, target)
        s = assets.ulti["suggested"]
        self.cloud = assets.ulti_frames("cloud")
        self.bolt = assets.ulti_frames("bolt")
        self.warn_frames = warning_frames()
        self.strikes = s.get("strikes", 3)
        self.warn = s.get("warning_frames", 45)
        self.bolt_len = s.get("bolt_frames", 18)
        self.width = s.get("hitbox_width_px", 50)
        self.damage = s.get("damage", 12)
        self.cloud_y = s.get("cloud_y_px", 40)
        self.strike = 0
        self.phase_t = 0
        self.x = target.rect.centerx
        self.has_hit = False

    def striking(self):
        return self.phase_t >= self.warn

    def update(self, combat, sound):
        super().update(combat, sound)
        self.phase_t += 1
        if self.striking():
            if self.phase_t == self.warn:
                combat.screen_shake = max(combat.screen_shake, 8)
            hitbox = pygame.Rect(int(self.x) - self.width // 2, 0, self.width, GROUND_Y)
            if not self.has_hit and hitbox.colliderect(self.target.get_rect()):
                self.has_hit = True
                self.hit(combat, sound, self.damage, self.target.rect.centerx, self.target.rect.centery)
            if self.phase_t >= self.warn + self.bolt_len:
                self.strike += 1
                self.phase_t = 0
                self.has_hit = False
                self.x = self.target.rect.centerx
        self.alive = self.strike < self.strikes

    def draw_back(self, surface):
        if not self.striking():
            draw_warning(surface, self.warn_frames, self.x, self.t)

    def draw_front(self, surface):
        cloud = self.cloud[1 if self.striking() else (self.t // 10) % 2]
        cloud_rect = cloud.get_rect(midtop=(int(self.x), self.cloud_y))
        if self.striking():
            bolt = self.bolt[(self.t // 3) % len(self.bolt)]
            surface.blit(bolt, bolt.get_rect(midbottom=(int(self.x), GROUND_Y + 4)))
        surface.blit(cloud, cloud_rect)

    def ai_hint(self, fighter):
        if not self.striking() and abs(self.x - fighter.rect.centerx) < self.width / 2 + 45:
            return away_from(fighter, self.x)
        return None


ULTI_TYPES = {
    "clone_rain": GianCloneRain,
    "parabolic_missile": SubiMissile,
    "falling_object": WowiBuilding,
    "charge": MegaBull,
    "lightning": PubaLightning,
}


class UltiManager:
    def __init__(self):
        self.effects = []

    def reset(self):
        self.effects.clear()

    def is_active(self, owner):
        return any(e.owner is owner for e in self.effects)

    def cast(self, owner, target):
        cls = ULTI_TYPES.get(owner.assets.ulti["type"])
        if cls:
            self.effects.append(cls(owner, target, owner.assets))

    def update(self, combat, sound):
        for e in self.effects:
            e.update(combat, sound)
        self.effects = [e for e in self.effects if e.alive]

    def threat_hint(self, fighter):
        """Dodge suggestion for the CPU: 'left', 'right', 'jump' or None."""
        for e in self.effects:
            if e.target is fighter and e.ai_will_dodge:
                hint = e.ai_hint(fighter)
                if hint:
                    return hint
        return None

    def draw_back(self, surface):
        for e in self.effects:
            e.draw_back(surface)

    def draw_front(self, surface):
        for e in self.effects:
            e.draw_front(surface)
