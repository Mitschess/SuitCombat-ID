import pygame
import random
import math
from settings import (
    COLOR_WHITE, COLOR_HEALTH_ENEMY, COLOR_HEALTH_PLAYER,
    COLOR_MENU_SUBTITLE, BLOCK_DAMAGE_REDUCTION
)

class FloatingText:
    def __init__(self, x, y, text, color=(255, 255, 255), is_crit=False):
        self.x = float(x)
        self.y = float(y)
        self.text = text
        self.color = color
        self.is_crit = is_crit
        self.vy = -2.5
        self.alpha = 255
        self.lifetime = 45  # frames (~0.75s)
        self.scale = 1.3 if is_crit else 1.0

    def update(self):
        self.y += self.vy
        self.vy *= 0.92  # decelerate
        self.lifetime -= 1
        self.alpha = max(0, int((self.lifetime / 45.0) * 255))

    def draw(self, surface, font):
        if self.alpha <= 0:
            return
        rendered = font.render(str(self.text), True, self.color)
        if self.scale != 1.0:
            w, h = rendered.get_size()
            rendered = pygame.transform.smoothscale(rendered, (int(w * self.scale), int(h * self.scale)))
            
        rendered.set_alpha(self.alpha)
        # Draw shadow
        shadow = font.render(str(self.text), True, (0, 0, 0))
        shadow.set_alpha(int(self.alpha * 0.7))
        surface.blit(shadow, (int(self.x) + 2, int(self.y) + 2))
        surface.blit(rendered, (int(self.x), int(self.y)))


class SparkParticle:
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(3.0, 9.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.lifetime = random.randint(12, 25)
        self.max_lifetime = self.lifetime
        self.radius = random.uniform(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.92
        self.vy *= 0.92
        self.lifetime -= 1

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        alpha_ratio = self.lifetime / self.max_lifetime
        r = int(self.radius * alpha_ratio)
        if r > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)


class CombatManager:
    def __init__(self):
        self.floating_texts = []
        self.sparks = []
        self.screen_shake = 0  # shake duration / magnitude in frames
        self.shake_offset_x = 0
        self.shake_offset_y = 0

    def add_hit_effect(self, x, y, damage, is_blocked=False, is_crit=False, color=(255, 255, 255)):
        text = "BLOCKED" if is_blocked else f"-{int(damage)}"
        textColor = (180, 180, 200) if is_blocked else color
        self.floating_texts.append(FloatingText(x, y - 20, text, textColor, is_crit=is_crit))
        
        # Add spark particles
        spark_count = 8 if is_blocked else (20 if is_crit else 12)
        spark_color = (200, 220, 255) if is_blocked else ((255, 230, 80) if is_crit else color)
        for _ in range(spark_count):
            self.sparks.append(SparkParticle(x, y, spark_color))
            
        # Trigger screen shake
        shake_intensity = 4 if is_blocked else (12 if is_crit else 8)
        self.screen_shake = max(self.screen_shake, shake_intensity)

    def process_melee_hit(self, attacker, defender, sound_manager=None):
        """Processes melee collision and damage calculation between attacker and defender."""
        if not attacker.is_attacking_melee or attacker.melee_hit_processed:
            return False

        hitbox = attacker.get_melee_hitbox()
        if hitbox and hitbox.colliderect(defender.get_rect()):
            attacker.melee_hit_processed = True
            
            # Check if defender is blocking
            is_blocked = defender.is_blocking and defender.facing_direction != attacker.facing_direction
            damage = attacker.melee_damage * (1.0 - BLOCK_DAMAGE_REDUCTION if is_blocked else 1.0)
            
            # Apply damage to defender
            defender.take_damage(damage, knockback_dir=attacker.facing_direction)
            
            # Play sound effect
            if sound_manager:
                sound_manager.play("hit" if not is_blocked else "block")
                
            hit_x = defender.rect.centerx
            hit_y = defender.rect.centery
            self.add_hit_effect(hit_x, hit_y, damage, is_blocked=is_blocked, color=attacker.accent_color)
            return True

        return False

    def process_projectiles(self, projectiles, player, enemy, sound_manager=None):
        """Processes collision between active projectiles and fighters."""
        for p in projectiles:
            if not p.alive:
                continue
            
            target = enemy if p.is_player_owner else player
            if p.rect.colliderect(target.get_rect()):
                p.alive = False
                
                # Check block
                is_blocked = target.is_blocking and target.facing_direction != p.direction
                damage = p.damage * (1.0 - BLOCK_DAMAGE_REDUCTION if is_blocked else 1.0)
                
                target.take_damage(damage, knockback_dir=p.direction)
                
                if sound_manager:
                    sound_manager.play("hit" if not is_blocked else "block")
                    
                self.add_hit_effect(p.rect.centerx, p.rect.centery, damage, is_blocked=is_blocked, color=p.color)

    def update(self):
        # Update floating text
        for t in self.floating_texts:
            t.update()
        self.floating_texts = [t for t in self.floating_texts if t.lifetime > 0]

        # Update sparks
        for s in self.sparks:
            s.update()
        self.sparks = [s for s in self.sparks if s.lifetime > 0]

        # Update screen shake
        if self.screen_shake > 0:
            self.shake_offset_x = random.randint(-self.screen_shake, self.screen_shake)
            self.shake_offset_y = random.randint(-self.screen_shake, self.screen_shake)
            self.screen_shake -= 1
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0

    def draw(self, surface, font):
        for s in self.sparks:
            s.draw(surface)
        for t in self.floating_texts:
            t.draw(surface, font)
