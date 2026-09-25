import pygame
import math
import random
from settings import (
    COLOR_PROJECTILE_PLAYER, COLOR_PROJECTILE_ENEMY,
    COLOR_WHITE, PROJECTILE_SIZE, SCREEN_WIDTH
)

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, is_player_owner, damage, speed, frames=None, color=None):
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.direction = direction  # 1 for Right, -1 for Left
        self.is_player_owner = is_player_owner
        self.damage = damage
        self.speed = speed
        
        self.size = PROJECTILE_SIZE
        self.rect = pygame.Rect(int(self.x), int(self.y), self.size, self.size)
        self.alive = True
        self.lifetime = 180  # frames (3 seconds max)
        self.particles = []
        self.color = color or (COLOR_PROJECTILE_PLAYER if is_player_owner else COLOR_PROJECTILE_ENEMY)
        # Character projectile sprite (frames face right)
        self.frames = frames if direction == 1 or not frames else [pygame.transform.flip(f, True, False) for f in frames]
        self.age = 0

    def update(self, delta_time=1.0):
        # Move projectile
        self.x += self.direction * self.speed * delta_time
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
        self.lifetime -= 1
        self.age += 1
        if self.lifetime <= 0 or self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.alive = False

        # Add tail particles
        if random.random() < 0.6:
            self.particles.append({
                'x': self.x + self.size / 2 + random.uniform(-4, 4),
                'y': self.y + self.size / 2 + random.uniform(-4, 4),
                'vx': -self.direction * random.uniform(1.0, 3.0),
                'vy': random.uniform(-1.0, 1.0),
                'radius': random.uniform(3, 6),
                'alpha': 255,
                'decay': random.uniform(15, 25)
            })

        # Update existing tail particles
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['alpha'] -= p['decay']
            p['radius'] = max(0, p['radius'] - 0.2)
            
        self.particles = [p for p in self.particles if p['alpha'] > 0 and p['radius'] > 0]

    def draw(self, surface):
        # Draw particle trails
        for p in self.particles:
            particle_surface = pygame.Surface((int(p['radius'] * 2), int(p['radius'] * 2)), pygame.SRCALPHA)
            color_with_alpha = (self.color[0], self.color[1], self.color[2], int(max(0, p['alpha'])))
            pygame.draw.circle(particle_surface, color_with_alpha, (int(p['radius']), int(p['radius'])), int(p['radius']))
            surface.blit(particle_surface, (int(p['x'] - p['radius']), int(p['y'] - p['radius'])))

        center_x = self.rect.centerx
        center_y = self.rect.centery

        # Character projectile sprite
        if self.frames:
            img = self.frames[(self.age // 5) % len(self.frames)]
            surface.blit(img, img.get_rect(center=(center_x, center_y)))
            return

        # Draw main glowing orb
        
        # Outer glow
        glow_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        glow_color = (self.color[0], self.color[1], self.color[2], 100)
        pygame.draw.circle(glow_surf, glow_color, (self.size, self.size), self.size)
        surface.blit(glow_surf, (center_x - self.size, center_y - self.size))
        
        # Inner core
        pygame.draw.circle(surface, self.color, (center_x, center_y), self.size // 2)
        pygame.draw.circle(surface, COLOR_WHITE, (center_x, center_y), self.size // 4)
