import pygame
import os
import sys
import random
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    STATE_MENU, STATE_HOW_TO_PLAY, STATE_PLAYING, STATE_CHAR_SELECT,
    STATE_PAUSED, STATE_VICTORY, STATE_DEFEAT,
    COLOR_BG_DARK, COLOR_GROUND, COLOR_GROUND_LINE, GROUND_Y,
    PLAYER_START_X, PLAYER_START_Y, ENEMY_START_X, ENEMY_START_Y,
    ULTI_MAX, ULTI_GAIN_DEAL, ULTI_GAIN_TAKE, ULTI_GAIN_PASSIVE, ULTI_CAST_FRAMES, KO_DELAY_FRAMES
)
from player import Player
from enemy import Enemy
from ai import EnemyAI
from projectile import Projectile
from combat import CombatManager
from menu import MainMenu
from ui import UIManager
from character_select import CharacterSelect, ULTI_NAMES
from ulti import UltiManager
from sprites import load_image, get_character

class SoundManager:
    def __init__(self):
        pygame.mixer.init()
        self.sounds = {}
        self.enabled = True
        self.load_sounds()

    def load_sounds(self):
        sounds_dir = os.path.join(os.path.dirname(__file__), "assets", "sounds")
        sound_files = {
            "punch": "punch.wav",
            "shoot": "shoot.wav",
            "hit": "hit.wav",
            "jump": "jump.wav",
            "select": "select.wav",
            "victory": "victory.wav",
            "defeat": "defeat.wav"
        }
        for key, filename in sound_files.items():
            path = os.path.join(sounds_dir, filename)
            if os.path.exists(path):
                try:
                    self.sounds[key] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"Could not load sound {filename}: {e}")

    def play(self, key):
        if self.enabled and key in self.sounds:
            try:
                self.sounds[key].play()
            except Exception:
                pass

    def play_fighter(self, fighter, key, fallback=None):
        self.play_character(getattr(fighter, "assets", None), key, fallback)

    def play_character(self, assets, key, fallback=None):
        """Plays the character's own sound (assets/characters/<Name>/sounds/<key>.wav) if it exists,
        otherwise the generic `fallback` sound."""
        if self.enabled and assets and key in assets.sounds:
            try:
                assets.sounds[key].play()
                return
            except Exception:
                pass
        self.play(fallback or key)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.state = STATE_MENU

        # Modules
        self.sound = SoundManager()
        self.menu = MainMenu()
        self.char_select = CharacterSelect()
        self.ui = UIManager()
        self.combat = CombatManager()
        self.ai = EnemyAI()
        self.ulti = UltiManager()

        # Entities
        self.player = None
        self.enemy = None
        self.projectiles = []
        self.player_char = None
        self.enemy_char = None
        self.ko_timer = 0

        # Menu option selections for Pause / Game Over overlays
        self.pause_option_index = 0
        self.endgame_option_index = 0

        # Background visual elements
        self.bg_pillars = [(120, 200, 80, 280), (350, 160, 100, 320), (700, 180, 90, 300), (900, 220, 70, 260)]
        bg_path = os.path.join(os.path.dirname(__file__), "assets", "backgrounds", "arena_temple.png")
        self.bg_image = load_image(bg_path) if os.path.exists(bg_path) else None

    def start_new_game(self):
        """Initializes a new battle match between Player and Enemy."""
        self.player = Player(x=PLAYER_START_X, y=PLAYER_START_Y, character=self.player_char)
        self.enemy = Enemy(x=ENEMY_START_X, y=ENEMY_START_Y, character=self.enemy_char)
        self.projectiles.clear()
        self.ulti.reset()
        self.ui.reset()
        self.ko_timer = 0
        self.pause_option_index = 0
        self.endgame_option_index = 0
        self.state = STATE_PLAYING

    def open_character_select(self):
        self.char_select.reset()
        self.state = STATE_CHAR_SELECT

    def confirm_character(self):
        self.player_char = self.char_select.selected()
        self.enemy_char = self.char_select.random_opponent()
        self.sound.play_character(get_character(self.player_char), "select")
        self.start_new_game()

    def fire_projectile(self, fighter, spec):
        if fighter.assets:
            spec["frames"] = fighter.assets.projectile_frames
            spec["color"] = fighter.assets.color
        self.projectiles.append(Projectile(**spec))
        self.sound.play_fighter(fighter, "special", "shoot")

    def try_cast_ulti(self, caster, target):
        if (caster.assets is None or caster.is_dead or target.is_dead or caster.ulti_meter < ULTI_MAX
                or caster.ulti_cast_timer > 0 or self.ulti.is_active(caster)):
            return False
        caster.ulti_meter = 0.0
        caster.ulti_cast_timer = ULTI_CAST_FRAMES
        caster.vx = 0.0
        caster.is_blocking = caster.is_crouching = False
        self.ulti.cast(caster, target)
        self.sound.play_fighter(caster, "ulti", "shoot")
        self.ui.show_ulti_banner(f"{caster.name}: {ULTI_NAMES.get(caster.assets.name, 'ULTI')}!", caster.accent_color)
        self.combat.screen_shake = max(self.combat.screen_shake, 6)
        return True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # --- MAIN MENU STATE EVENTS ---
            if self.state == STATE_MENU:
                if event.type == pygame.KEYDOWN:
                    action = self.menu.handle_key_input(event.key)
                    if action == "NAVIGATE":
                        self.sound.play("select")
                    elif action == "PLAY":
                        self.sound.play("select")
                        self.open_character_select()
                    elif action == "HOW TO PLAY":
                        self.sound.play("select")
                        self.state = STATE_HOW_TO_PLAY
                    elif action == "QUIT":
                        self.running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    m_pos = event.pos
                    button_rects = self.menu.draw(self.screen)
                    for rect, opt in button_rects:
                        if rect.collidepoint(m_pos):
                            self.sound.play("select")
                            if opt == "PLAY":
                                self.open_character_select()
                            elif opt == "HOW TO PLAY":
                                self.state = STATE_HOW_TO_PLAY
                            elif opt == "QUIT":
                                self.running = False

            # --- CHARACTER SELECT STATE EVENTS ---
            elif self.state == STATE_CHAR_SELECT:
                action = None
                if event.type == pygame.KEYDOWN:
                    action = self.char_select.handle_key_input(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = self.char_select.handle_click(event.pos)
                if action == "NAVIGATE":
                    self.sound.play("select")
                elif action == "CONFIRM":
                    self.confirm_character()
                elif action == "BACK":
                    self.sound.play("select")
                    self.state = STATE_MENU

            # --- HOW TO PLAY STATE EVENTS ---
            elif self.state == STATE_HOW_TO_PLAY:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        self.sound.play("select")
                        self.state = STATE_MENU
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    b_rect = self.menu.draw_how_to_play(self.screen)
                    if b_rect.collidepoint(event.pos):
                        self.sound.play("select")
                        self.state = STATE_MENU

            # --- PLAYING STATE EVENTS ---
            elif self.state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.sound.play("select")
                        self.pause_option_index = 0
                        self.state = STATE_PAUSED

                    elif self.ko_timer > 0:
                        pass  # round is over, just let the KO / victory animation play

                    elif event.key == pygame.K_j:
                        # Melee attack
                        if self.player.attack_melee():
                            self.sound.play_fighter(self.player, self.player.melee_anim, "punch")

                    elif event.key == pygame.K_k:
                        # Ranged attack
                        proj_spec = self.player.attack_ranged()
                        if proj_spec:
                            self.fire_projectile(self.player, proj_spec)

                    elif event.key == pygame.K_u:
                        # Ultimate
                        self.try_cast_ulti(self.player, self.enemy)

            # --- PAUSED STATE EVENTS ---
            elif self.state == STATE_PAUSED:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.pause_option_index = (self.pause_option_index - 1) % 3
                        self.sound.play("select")
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.pause_option_index = (self.pause_option_index + 1) % 3
                        self.sound.play("select")
                    elif event.key == pygame.K_RETURN:
                        self.sound.play("select")
                        if self.pause_option_index == 0:  # RESUME
                            self.state = STATE_PLAYING
                        elif self.pause_option_index == 1:  # RESTART
                            self.start_new_game()
                        elif self.pause_option_index == 2:  # MAIN MENU
                            self.state = STATE_MENU
                    elif event.key == pygame.K_ESCAPE:
                        self.state = STATE_PLAYING

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    m_pos = event.pos
                    button_rects = self.ui.draw_pause_overlay(self.screen, self.pause_option_index)
                    for i, b_rect in enumerate(button_rects):
                        if b_rect.collidepoint(m_pos):
                            self.sound.play("select")
                            if i == 0:
                                self.state = STATE_PLAYING
                            elif i == 1:
                                self.start_new_game()
                            elif i == 2:
                                self.state = STATE_MENU

            # --- VICTORY / DEFEAT END GAME EVENTS ---
            elif self.state in (STATE_VICTORY, STATE_DEFEAT):
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN or event.key == pygame.K_w or event.key == pygame.K_s:
                        self.endgame_option_index = (self.endgame_option_index + 1) % 2
                        self.sound.play("select")
                    elif event.key == pygame.K_RETURN:
                        self.sound.play("select")
                        if self.endgame_option_index == 0:  # PLAY AGAIN
                            self.start_new_game()
                        else:  # MAIN MENU
                            self.state = STATE_MENU

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    m_pos = event.pos
                    is_vic = (self.state == STATE_VICTORY)
                    button_rects = self.ui.draw_end_game_overlay(self.screen, is_vic, self.endgame_option_index)
                    for i, b_rect in enumerate(button_rects):
                        if b_rect.collidepoint(m_pos):
                            self.sound.play("select")
                            if i == 0:
                                self.start_new_game()
                            else:
                                self.state = STATE_MENU

    def update(self):
        if self.state == STATE_MENU:
            self.menu.update()

        elif self.state == STATE_CHAR_SELECT:
            self.char_select.update()

        elif self.state == STATE_PLAYING:
            player_hp, enemy_hp = self.player.health, self.enemy.health

            # Fighters always face each other
            if not self.player.is_dead:
                self.player.facing_direction = 1 if self.enemy.rect.centerx >= self.player.rect.centerx else -1

            # 1. Player Key Input
            keys = pygame.key.get_pressed()

            # Sound for jump
            was_grounded = self.player.is_grounded
            self.player.handle_input(keys)
            if was_grounded and not self.player.is_grounded and self.player.vy < 0:
                self.sound.play("jump")

            # 2. Update Player
            self.player.update()

            # 3. Update AI Computer
            if self.ko_timer == 0:
                if self.enemy.ulti_meter >= ULTI_MAX and random.random() < 0.01:
                    self.try_cast_ulti(self.enemy, self.player)
                ai_proj = self.ai.update(self.enemy, self.player, self.projectiles, self.ulti)
                if ai_proj:
                    self.fire_projectile(self.enemy, ai_proj)
                elif self.enemy.melee_anim_timer == 16:
                    self.sound.play_fighter(self.enemy, self.enemy.melee_anim, "punch")
            else:
                self.enemy.stop_moving()

            # 4. Update Enemy
            self.enemy.update()

            # 5. Update Projectiles
            for proj in self.projectiles:
                proj.update()
            self.projectiles = [p for p in self.projectiles if p.alive]

            # 6. Process Combat Collisions
            self.combat.process_melee_hit(self.player, self.enemy, self.sound)
            self.combat.process_melee_hit(self.enemy, self.player, self.sound)
            self.combat.process_projectiles(self.projectiles, self.player, self.enemy, self.sound)
            self.ulti.update(self.combat, self.sound)
            self.combat.update()

            # 7. ULTI meters: fill by dealing / taking damage, plus a slow passive gain
            dealt_to_enemy = max(0.0, enemy_hp - self.enemy.health)
            dealt_to_player = max(0.0, player_hp - self.player.health)
            for fighter, dealt, taken in ((self.player, dealt_to_enemy, dealt_to_player),
                                          (self.enemy, dealt_to_player, dealt_to_enemy)):
                if not self.ulti.is_active(fighter):
                    fighter.ulti_meter = min(ULTI_MAX, fighter.ulti_meter + dealt * ULTI_GAIN_DEAL
                                             + taken * ULTI_GAIN_TAKE + ULTI_GAIN_PASSIVE)

            # 8. Check Game Over (let the KO / victory animations play first)
            if self.ko_timer == 0 and (self.enemy.is_dead or self.player.is_dead):
                self.ko_timer = KO_DELAY_FRAMES
                loser = self.enemy if self.enemy.is_dead else self.player
                winner = self.player if loser is self.enemy else self.enemy
                winner.is_victorious = not winner.is_dead
                self.sound.play_fighter(loser, "ko", "hit")
            elif self.ko_timer > 0:
                self.ko_timer -= 1
                if self.ko_timer == 0:
                    if self.enemy.is_dead:
                        self.sound.play_fighter(self.player, "victory")
                        self.state = STATE_VICTORY
                    else:
                        self.sound.play_fighter(self.enemy, "victory", "defeat")
                        self.state = STATE_DEFEAT

    def draw_arena_background(self, target_surface):
        if self.bg_image:
            target_surface.blit(self.bg_image, (0, 0))
            return

        target_surface.fill(COLOR_BG_DARK)

        # Background Pillars & Arena Architecture
        for px, py, pw, ph in self.bg_pillars:
            pygame.draw.rect(target_surface, (22, 26, 42), (px, py, pw, ph), border_radius=4)
            pygame.draw.rect(target_surface, (35, 42, 68), (px, py, pw, ph), width=1, border_radius=4)

        # Neon Ground Floor
        floor_rect = pygame.Rect(0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y)
        pygame.draw.rect(target_surface, COLOR_GROUND, floor_rect)
        pygame.draw.line(target_surface, COLOR_GROUND_LINE, (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 3)

        # Ground Grid Lines
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(target_surface, (28, 35, 60), (x, GROUND_Y), (x - 20, SCREEN_HEIGHT))

    def render(self):
        # Create surface for screen shake
        render_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        if self.state in (STATE_PLAYING, STATE_PAUSED, STATE_VICTORY, STATE_DEFEAT):
            # Draw Arena Environment
            self.draw_arena_background(render_surface)

            # Ulti ground warnings
            self.ulti.draw_back(render_surface)

            # Draw Projectiles
            for proj in self.projectiles:
                proj.draw(render_surface)

            # Draw Player & Enemy
            self.player.draw(render_surface)
            self.enemy.draw(render_surface)

            # Ulti hazards (clones, missile, building, bull, lightning)
            self.ulti.draw_front(render_surface)

            # Draw Combat Particle FX & Hit Floating Texts
            self.combat.draw(render_surface, self.ui.font_medium)

            # Draw HUD
            self.ui.draw_hud(render_surface, self.player, self.enemy)

            # Overlays
            if self.state == STATE_PAUSED:
                self.ui.draw_pause_overlay(render_surface, self.pause_option_index)
            elif self.state == STATE_VICTORY:
                self.ui.draw_end_game_overlay(render_surface, True, self.endgame_option_index)
            elif self.state == STATE_DEFEAT:
                self.ui.draw_end_game_overlay(render_surface, False, self.endgame_option_index)

        elif self.state == STATE_MENU:
            self.menu.draw(render_surface)

        elif self.state == STATE_CHAR_SELECT:
            self.char_select.draw(render_surface)

        elif self.state == STATE_HOW_TO_PLAY:
            self.menu.draw_how_to_play(render_surface)

        # Blit with Screen Shake offset
        ox = self.combat.shake_offset_x if self.state == STATE_PLAYING else 0
        oy = self.combat.shake_offset_y if self.state == STATE_PLAYING else 0
        self.screen.blit(render_surface, (ox, oy))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
