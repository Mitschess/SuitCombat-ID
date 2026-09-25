import pygame
import os
import math
from sprites import get_character, pick_animation
from settings import (
    SCREEN_WIDTH, GROUND_Y, GRAVITY, FIGHTER_WIDTH, FIGHTER_HEIGHT,
    FIGHTER_CROUCH_HEIGHT, FIGHTER_SPEED, JUMP_FORCE, MAX_HEALTH,
    MELEE_DAMAGE, MELEE_RANGE, MELEE_COOLDOWN, MELEE_DURATION,
    RANGED_DAMAGE, RANGED_SPEED, RANGED_COOLDOWN,
    COLOR_PLAYER, COLOR_PLAYER_ACCENT, COLOR_WHITE, COLOR_GRAY, COLOR_BLACK
)

class Player:
    def __init__(self, x=200, y=GROUND_Y - 90, character=None):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        
        self.width = FIGHTER_WIDTH
        self.height = FIGHTER_HEIGHT
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        
        self.health = float(MAX_HEALTH)
        self.max_health = float(MAX_HEALTH)
        
        self.facing_direction = 1  # 1: Right, -1: Left
        self.is_grounded = True
        self.is_crouching = False
        self.is_blocking = False
        
        # Combat Timers & States
        self.is_attacking_melee = False
        self.melee_timer = 0
        self.melee_cooldown = 0
        self.melee_hit_processed = False
        
        self.ranged_cooldown = 0
        
        self.hit_flash_timer = 0
        self.is_dead = False
        
        # Colors & Visuals
        self.color = COLOR_PLAYER
        self.accent_color = COLOR_PLAYER_ACCENT
        self.name = "PLAYER 1"
        self.melee_damage = MELEE_DAMAGE

        # Photo-sprite character, animation + ulti state
        self.assets = get_character(character) if character else None
        self.animator = self.assets.new_animator() if self.assets else None
        if self.assets:
            self.name = character.upper()
            self.accent_color = self.assets.color
        self.ulti_meter = 0.0
        self.ulti_cast_timer = 0
        self.cast_timer = 0
        self.melee_anim = "punch"
        self.melee_anim_timer = 0
        self.melee_count = 0
        self.is_victorious = False
        
        # Sprite loading support (FR-14)
        self.sprite_sheet = None
        if not self.assets:
            self.load_sprites()

    def load_sprites(self):
        """Attempts to load character sprite image if provided in assets (FR-14 compliance)."""
        sprite_path = os.path.join(os.path.dirname(__file__), "assets", "characters", "player", "player.png")
        if os.path.exists(sprite_path):
            try:
                img = pygame.image.load(sprite_path).convert_alpha()
                self.sprite_sheet = pygame.transform.scale(img, (self.width, self.height))
            except Exception as e:
                print(f"Could not load player sprite: {e}")

    def get_rect(self):
        current_h = FIGHTER_CROUCH_HEIGHT if self.is_crouching else self.height
        return pygame.Rect(int(self.x), int(self.y), self.width, current_h)

    def handle_input(self, keys):
        # Reset horizontal velocity
        self.vx = 0.0
        if self.is_dead or self.is_victorious or self.ulti_cast_timer > 0:
            self.is_crouching = False
            self.is_blocking = False
            return None

        # Crouch state
        if keys[pygame.K_s] and self.is_grounded:
            self.is_crouching = True
            self.is_blocking = False
        else:
            self.is_crouching = False

        # Block state
        if keys[pygame.K_l] and self.is_grounded and not self.is_crouching:
            self.is_blocking = True
        else:
            self.is_blocking = False

        # Movement (disabled while blocking or crouching)
        if not self.is_blocking and not self.is_crouching:
            if keys[pygame.K_a]:
                self.vx = -FIGHTER_SPEED
            if keys[pygame.K_d]:
                self.vx = FIGHTER_SPEED

            # Jump
            if keys[pygame.K_w] and self.is_grounded:
                self.vy = JUMP_FORCE
                self.is_grounded = False

    def attack_melee(self):
        if self.melee_cooldown == 0 and not self.is_blocking and not self.is_dead and self.ulti_cast_timer == 0:
            self.melee_count += 1
            self.melee_anim = "kick" if self.melee_count % 3 == 0 else "punch"
            self.melee_anim_timer = 16
            self.is_attacking_melee = True
            self.melee_timer = MELEE_DURATION
            self.melee_cooldown = MELEE_COOLDOWN
            self.melee_hit_processed = False
            return True
        return False

    def attack_ranged(self):
        if self.ranged_cooldown == 0 and not self.is_blocking and not self.is_dead and self.ulti_cast_timer == 0:
            self.cast_timer = 16
            self.ranged_cooldown = RANGED_COOLDOWN
            # Return projectile spawn specs
            spawn_x = self.x + self.width if self.facing_direction == 1 else self.x - 16
            spawn_y = self.y + 25 if not self.is_crouching else self.y + 15
            return {
                'x': spawn_x,
                'y': spawn_y,
                'direction': self.facing_direction,
                'is_player_owner': True,
                'damage': RANGED_DAMAGE,
                'speed': RANGED_SPEED
            }
        return None

    def get_melee_hitbox(self):
        if not self.is_attacking_melee:
            return None
        
        hitbox_width = MELEE_RANGE
        hitbox_height = 40
        hitbox_y = self.y + 15 if not self.is_crouching else self.y + 10
        
        if self.facing_direction == 1:
            hitbox_x = self.x + self.width
        else:
            hitbox_x = self.x - hitbox_width
            
        return pygame.Rect(int(hitbox_x), int(hitbox_y), hitbox_width, hitbox_height)

    def take_damage(self, amount, knockback_dir=1):
        if self.is_dead:
            return
        
        self.health = max(0.0, self.health - amount)
        self.hit_flash_timer = 10  # flash red frames
        self.vx = knockback_dir * (3.0 if not self.is_blocking else 1.0)
        
        if self.health <= 0:
            self.is_dead = True

    def update(self, delta_time=1.0):
        # Physics update
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time

        # Gravity
        if not self.is_grounded:
            self.vy += GRAVITY * delta_time

        # Ground collision
        current_h = FIGHTER_CROUCH_HEIGHT if self.is_crouching else self.height
        if self.y + current_h >= GROUND_Y:
            self.y = GROUND_Y - current_h
            self.vy = 0.0
            self.is_grounded = True

        # Screen boundaries
        self.x = max(10.0, min(float(SCREEN_WIDTH - self.width - 10), self.x))
        self.rect = self.get_rect()

        # Update timers
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1
        if self.ranged_cooldown > 0:
            self.ranged_cooldown -= 1
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

        if self.ulti_cast_timer > 0:
            self.ulti_cast_timer -= 1
        if self.cast_timer > 0:
            self.cast_timer -= 1
        if self.melee_anim_timer > 0:
            self.melee_anim_timer -= 1
        if self.animator:
            self.animator.play(pick_animation(self))
            self.animator.update()

        if self.is_attacking_melee:
            self.melee_timer -= 1
            if self.melee_timer <= 0:
                self.is_attacking_melee = False

    def draw(self, surface):
        rect = self.get_rect()
        
        # 1. Animated photo-sprite character
        if self.animator:
            shadow_surf = pygame.Surface((70, 12), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 120), (0, 0, 70, 12))
            surface.blit(shadow_surf, (rect.centerx - 35, GROUND_Y - 6))
            self.animator.draw(surface, rect.midbottom, self.facing_direction)
            return

        # 2. If sprite is available, draw sprite (FR-14)
        if self.sprite_sheet:
            img = self.sprite_sheet
            if self.facing_direction == -1:
                img = pygame.transform.flip(img, True, False)
            surface.blit(img, rect.topleft)
            return

        # 3. Draw styled mockup character (Stylized avatar figure)
        draw_color = (255, 60, 60) if self.hit_flash_timer > 0 else self.color
        
        # Main Body Box (Torso / Suit)
        pygame.draw.rect(surface, draw_color, rect, border_radius=8)
        pygame.draw.rect(surface, self.accent_color, rect, width=2, border_radius=8)
        
        # Head Circle
        head_radius = 16
        head_x = rect.centerx
        head_y = rect.top - 10 if not self.is_crouching else rect.top + 8
        pygame.draw.circle(surface, draw_color, (head_x, head_y), head_radius)
        pygame.draw.circle(surface, self.accent_color, (head_x, head_y), head_radius, width=2)
        
        # Eye / Visor (direction indicator)
        eye_x = head_x + (self.facing_direction * 6)
        eye_y = head_y - 2
        pygame.draw.circle(surface, COLOR_WHITE, (eye_x, eye_y), 4)
        
        # Blocking shield overlay
        if self.is_blocking:
            shield_x = rect.right if self.facing_direction == 1 else rect.left - 15
            shield_rect = pygame.Rect(shield_x, rect.top, 15, rect.height)
            pygame.draw.rect(surface, (100, 200, 255), shield_rect, border_radius=4)
            pygame.draw.rect(surface, COLOR_WHITE, shield_rect, width=2, border_radius=4)

        # Melee Attack Visual Arc / Slash
        if self.is_attacking_melee:
            hitbox = self.get_melee_hitbox()
            if hitbox:
                # Slash effect
                slash_surf = pygame.Surface((hitbox.width, hitbox.height), pygame.SRCALPHA)
                slash_color = (255, 230, 100, 180)
                pygame.draw.ellipse(slash_surf, slash_color, (0, 0, hitbox.width, hitbox.height))
                surface.blit(slash_surf, hitbox.topleft)
                pygame.draw.ellipse(surface, COLOR_WHITE, hitbox, width=2)

        # Ground Shadow
        shadow_rect = pygame.Rect(rect.left, GROUND_Y - 4, rect.width, 8)
        shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 120), (0, 0, shadow_rect.width, shadow_rect.height))
        surface.blit(shadow_surf, shadow_rect.topleft)
