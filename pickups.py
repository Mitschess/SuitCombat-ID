import os
import random
import pygame
from settings import (
    SCREEN_WIDTH, GROUND_Y, HEAL_AMOUNT, PICKUP_SPAWN_MIN, PICKUP_SPAWN_MAX, PICKUP_LIFETIME
)
from sprites import ASSETS_DIR, load_strip
from combat import FloatingText, SparkParticle

PICKUP_FILE = os.path.join(ASSETS_DIR, "effects", "health_pickup.png")
PICKUP_FRAME_W = 120


class HealthPickup:
    """MBG food tray: drops from the sky, whoever touches it first heals HEAL_AMOUNT."""

    def __init__(self, x, frames, cpu_wants):
        self.x = float(x)
        self.bottom = -10.0
        self.vy = 2.0
        self.frames = frames
        self.landed = False
        self.life = PICKUP_LIFETIME
        self.t = 0
        self.alive = True
        self.cpu_wants = cpu_wants   # CPU decides once whether it goes for this one

    def rect(self):
        r = pygame.Rect(0, 0, 70, 50)
        r.midbottom = (int(self.x), int(self.bottom))
        return r

    def update(self):
        self.t += 1
        if not self.landed:
            self.vy = min(9.0, self.vy + 0.35)
            self.bottom = min(GROUND_Y, self.bottom + self.vy)
            self.landed = self.bottom >= GROUND_Y
        else:
            self.life -= 1
            self.alive = self.life > 0

    def draw(self, surface):
        if self.landed and self.life < 120 and (self.t // 6) % 2:
            return   # blink before vanishing
        img = self.frames[(self.t // 8) % len(self.frames)]
        surface.blit(img, img.get_rect(midbottom=(int(self.x), int(self.bottom) + 8)))


class PickupManager:
    def __init__(self):
        self.frames = None
        self.pickups = []
        self.timer = 0
        self.greed = 0.6

    def reset(self, greed=0.6):
        if self.frames is None and os.path.exists(PICKUP_FILE):
            self.frames = load_strip(PICKUP_FILE, PICKUP_FRAME_W)
        self.pickups.clear()
        self.greed = greed
        self.timer = random.randint(PICKUP_SPAWN_MIN, PICKUP_SPAWN_MAX)

    def update(self, fighters, combat, sound, active=True):
        if not self.frames:
            return
        if active:
            self.timer -= 1
            if self.timer <= 0 and not self.pickups:
                x = random.randint(90, SCREEN_WIDTH - 90)
                self.pickups.append(HealthPickup(x, self.frames, random.random() < self.greed))
                self.timer = random.randint(PICKUP_SPAWN_MIN, PICKUP_SPAWN_MAX)

        for p in self.pickups:
            p.update()
            if not active:
                continue
            for f in fighters:
                if not f.is_dead and f.health < f.max_health and p.rect().colliderect(f.get_rect()):
                    healed = min(HEAL_AMOUNT, f.max_health - f.health)
                    f.health += healed
                    p.alive = False
                    cx, cy = p.rect().center
                    combat.floating_texts.append(FloatingText(cx - 20, cy - 30, f"+{int(healed)}", (90, 240, 110), True))
                    for _ in range(14):
                        combat.sparks.append(SparkParticle(cx, cy, (120, 255, 140)))
                    sound.play("heal")
                    break
        self.pickups = [p for p in self.pickups if p.alive]

    def cpu_target(self, fighter):
        """X position of a tray the CPU wants to grab (only when it is hurt), else None."""
        if fighter.health >= fighter.max_health * 0.75:
            return None
        for p in self.pickups:
            if p.cpu_wants and p.landed:
                return p.x
        return None

    def draw(self, surface):
        for p in self.pickups:
            p.draw(surface)
