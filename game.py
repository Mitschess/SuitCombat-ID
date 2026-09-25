import pygame
import sys
import random
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    STATE_MENU, STATE_HOW_TO_PLAY, STATE_PLAYING, STATE_CHAR_SELECT, STATE_STAGE_SELECT, STATE_SETTINGS,
    STATE_PAUSED, STATE_VICTORY, STATE_DEFEAT, DIFFICULTIES,
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
from ui import UIManager, PAUSE_OPTIONS
from character_select import CharacterSelect, ULTI_NAMES
from ulti import UltiManager
from stage_select import StageSelect
from settings_screen import SettingsScreen
from sprites import get_character
from audio import SoundManager
from pickups import PickupManager
from config import load_config, save_config

MENU_MUSIC_STATES = (STATE_MENU, STATE_HOW_TO_PLAY, STATE_CHAR_SELECT, STATE_STAGE_SELECT)
FIGHT_BANNER_FIGHT_AT = 45   # frames into the round when "FIGHT!" replaces "READY?"


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)

        self.config = load_config()
        flags = pygame.SCALED | (pygame.FULLSCREEN if self.config["fullscreen"] else 0)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        self.clock = pygame.time.Clock()
        self.running = True

        self.state = STATE_MENU
        self.settings_return = STATE_MENU

        # Modules
        self.sound = SoundManager(self.config)
        self.menu = MainMenu()
        self.char_select = CharacterSelect()
        self.stage_select = StageSelect(self.menu.stages)
        self.settings = SettingsScreen(self.config)
        self.ui = UIManager()
        self.combat = CombatManager()
        self.ai = EnemyAI()
        self.ulti = UltiManager()
        self.pickups = PickupManager()

        # Entities
        self.player = None
        self.enemy = None
        self.projectiles = []
        self.player_char = None
        self.enemy_char = None
        self.ko_timer = 0
        self.round_frames = 0

        # Menu option selections for Pause / Game Over overlays
        self.pause_option_index = 0
        self.endgame_option_index = 0

        # Background visual elements
        self.bg_pillars = [(120, 200, 80, 280), (350, 160, 100, 320), (700, 180, 90, 300), (900, 220, 70, 260)]
        self.bg_image = None
        self.difficulty = "MEDIUM"

    # ------------------------------------------------------------------ flow
    def start_new_game(self):
        """Initializes a new battle match between Player and Enemy."""
        self.sound.stop_preview()
        self.player = Player(x=PLAYER_START_X, y=PLAYER_START_Y, character=self.player_char)
        self.enemy = Enemy(x=ENEMY_START_X, y=ENEMY_START_Y, character=self.enemy_char)
        diff = DIFFICULTIES[self.difficulty]
        self.enemy.speed_factor = diff["speed"]
        self.enemy.damage_mult = diff["damage"]
        self.enemy.melee_damage = 10 * diff["damage"]
        self.enemy.ulti_dodge_chance = diff["ulti_dodge"]
        self.ai.set_difficulty(self.difficulty)
        self.ui.difficulty = self.difficulty
        stage = self.stage_select.selected_stage()
        self.bg_image = stage.image if stage else None
        self.projectiles.clear()
        self.ulti.reset()
        self.pickups.reset(diff["pickup_greed"])
        self.ui.reset()
        self.ko_timer = 0
        self.round_frames = 0
        self.pause_option_index = 0
        self.endgame_option_index = 0
        self.state = STATE_PLAYING
        self.sound.play("ready")

    def open_character_select(self):
        self.char_select.reset()
        self.state = STATE_CHAR_SELECT
        self.preview_highlighted_ulti()

    def preview_highlighted_ulti(self):
        """Plays the highlighted fighter's ulti sound once (switching fighters cuts it and plays the new one)."""
        name = self.char_select.highlighted()
        self.sound.play_preview(get_character(name).sounds.get("ulti") if name else None)

    def confirm_character(self):
        self.player_char = self.char_select.selected()
        self.enemy_char = self.char_select.opponent()
        self.sound.stop_preview()
        self.sound.play("select")
        self.state = STATE_STAGE_SELECT

    def confirm_stage(self):
        self.sound.play("select")
        self.difficulty = self.stage_select.difficulty()
        self.start_new_game()

    def open_settings(self, return_state):
        self.settings_return = return_state
        self.state = STATE_SETTINGS

    def set_fullscreen(self, on):
        self.config["fullscreen"] = on
        is_full = bool(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
        if is_full != on:
            try:
                pygame.display.toggle_fullscreen()
            except pygame.error:
                try:
                    flags = pygame.SCALED | (pygame.FULLSCREEN if on else 0)
                    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
                except pygame.error as e:
                    print(f"Fullscreen not available: {e}")
                    self.config["fullscreen"] = is_full
        save_config(self.config)

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
        self.sound.play_fighter(caster, "ulti", "ulti_cast")
        self.ui.show_ulti_banner(f"{caster.name}: {ULTI_NAMES.get(caster.assets.name, 'ULTI')}!", caster.accent_color)
        self.combat.screen_shake = max(self.combat.screen_shake, 6)
        return True

    def select_pause_option(self, index):
        option = PAUSE_OPTIONS[index]
        self.sound.play("select")
        if option == "RESUME":
            self.state = STATE_PLAYING
        elif option == "RESTART":
            self.start_new_game()
        elif option == "SETTINGS":
            self.open_settings(STATE_PAUSED)
        elif option == "MAIN MENU":
            self.state = STATE_MENU

    def select_menu_option(self, option):
        self.sound.play("select")
        if option == "PLAY":
            self.open_character_select()
        elif option == "HOW TO PLAY":
            self.state = STATE_HOW_TO_PLAY
        elif option == "SETTINGS":
            self.open_settings(STATE_MENU)
        elif option == "QUIT":
            self.running = False

    # ------------------------------------------------------------------ events
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.set_fullscreen(not self.config["fullscreen"])
                continue

            # --- MAIN MENU STATE EVENTS ---
            if self.state == STATE_MENU:
                if event.type == pygame.KEYDOWN:
                    action = self.menu.handle_key_input(event.key)
                    if action == "NAVIGATE":
                        self.sound.play("move")
                    elif action:
                        self.select_menu_option(action)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for rect, opt in self.menu.draw(self.screen):
                        if rect.collidepoint(event.pos):
                            self.select_menu_option(opt)

            # --- CHARACTER + OPPONENT SELECT EVENTS ---
            elif self.state == STATE_CHAR_SELECT:
                action = None
                if event.type == pygame.KEYDOWN:
                    action = self.char_select.handle_key_input(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = self.char_select.handle_click(event.pos)
                if action == "NAVIGATE":
                    self.sound.play("move")
                    self.preview_highlighted_ulti()
                elif action == "PLAYER_CHOSEN":
                    self.sound.play("select")
                    self.preview_highlighted_ulti()
                elif action == "CONFIRM":
                    self.confirm_character()
                elif action == "BACK":
                    self.sound.stop_preview()
                    self.sound.play("back")
                    self.state = STATE_MENU

            # --- STAGE + DIFFICULTY SELECT EVENTS ---
            elif self.state == STATE_STAGE_SELECT:
                action = None
                if event.type == pygame.KEYDOWN:
                    action = self.stage_select.handle_key_input(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = self.stage_select.handle_click(event.pos)
                if action == "NAVIGATE":
                    self.sound.play("move")
                elif action == "CONFIRM":
                    self.confirm_stage()
                elif action == "BACK":
                    self.sound.play("back")
                    self.state = STATE_CHAR_SELECT
                    self.preview_highlighted_ulti()

            # --- SETTINGS EVENTS ---
            elif self.state == STATE_SETTINGS:
                action = None
                if event.type == pygame.KEYDOWN:
                    action = self.settings.handle_key_input(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = self.settings.handle_click(event.pos)
                if action == "NAVIGATE":
                    self.sound.play("move")
                elif action == "CHANGED":
                    self.sound.apply_volumes()
                    self.sound.play("move")
                    save_config(self.config)
                elif action == "TOGGLE_FULLSCREEN":
                    self.sound.play("select")
                    self.set_fullscreen(not self.config["fullscreen"])
                elif action == "BACK":
                    self.sound.play("back")
                    save_config(self.config)
                    self.state = self.settings_return

            # --- HOW TO PLAY STATE EVENTS ---
            elif self.state == STATE_HOW_TO_PLAY:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        self.sound.play("back")
                        self.state = STATE_MENU
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    b_rect = self.menu.draw_how_to_play(self.screen)
                    if b_rect.collidepoint(event.pos):
                        self.sound.play("back")
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
                            self.sound.play_fighter(self.player, self.player.melee_anim)

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
                        self.pause_option_index = (self.pause_option_index - 1) % len(PAUSE_OPTIONS)
                        self.sound.play("move")
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.pause_option_index = (self.pause_option_index + 1) % len(PAUSE_OPTIONS)
                        self.sound.play("move")
                    elif event.key == pygame.K_RETURN:
                        self.select_pause_option(self.pause_option_index)
                    elif event.key == pygame.K_ESCAPE:
                        self.sound.play("back")
                        self.state = STATE_PLAYING

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, b_rect in enumerate(self.ui.draw_pause_overlay(self.screen, self.pause_option_index)):
                        if b_rect.collidepoint(event.pos):
                            self.select_pause_option(i)

            # --- VICTORY / DEFEAT END GAME EVENTS ---
            elif self.state in (STATE_VICTORY, STATE_DEFEAT):
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s):
                        self.endgame_option_index = (self.endgame_option_index + 1) % 2
                        self.sound.play("move")
                    elif event.key == pygame.K_RETURN:
                        self.sound.play("select")
                        if self.endgame_option_index == 0:  # PLAY AGAIN
                            self.start_new_game()
                        else:  # MAIN MENU
                            self.state = STATE_MENU

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    is_vic = (self.state == STATE_VICTORY)
                    button_rects = self.ui.draw_end_game_overlay(self.screen, is_vic, self.endgame_option_index, self.winner())
                    for i, b_rect in enumerate(button_rects):
                        if b_rect.collidepoint(event.pos):
                            self.sound.play("select")
                            if i == 0:
                                self.start_new_game()
                            else:
                                self.state = STATE_MENU

    # ------------------------------------------------------------------ update
    def music_for_state(self):
        if self.state in MENU_MUSIC_STATES or (self.state == STATE_SETTINGS and self.settings_return == STATE_MENU):
            return "menu"
        if self.state in (STATE_PLAYING, STATE_PAUSED, STATE_SETTINGS):
            return "battle"
        return None   # victory / defeat jingles play alone

    def update(self):
        self.sound.play_music(self.music_for_state())

        if self.state in (STATE_MENU, STATE_HOW_TO_PLAY):
            self.menu.update()

        elif self.state == STATE_CHAR_SELECT:
            self.char_select.update()
            self.menu.update()

        elif self.state == STATE_STAGE_SELECT:
            self.stage_select.update()

        elif self.state == STATE_SETTINGS:
            self.settings.update()
            if self.settings_return == STATE_MENU:
                self.menu.update()

        elif self.state == STATE_PLAYING:
            self.update_fight()

    def update_fight(self):
        player_hp, enemy_hp = self.player.health, self.enemy.health
        self.round_frames += 1
        if self.round_frames == FIGHT_BANNER_FIGHT_AT:
            self.sound.play("fight")

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
            if self.enemy.ulti_meter >= ULTI_MAX and random.random() < DIFFICULTIES[self.difficulty]["ulti_use"]:
                self.try_cast_ulti(self.enemy, self.player)
            ai_proj = self.ai.update(self.enemy, self.player, self.projectiles, self.ulti, self.pickups)
            if ai_proj:
                self.fire_projectile(self.enemy, ai_proj)
            elif self.enemy.melee_anim_timer == 16:
                self.sound.play_fighter(self.enemy, self.enemy.melee_anim)
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
        self.pickups.update((self.player, self.enemy), self.combat, self.sound,
                            active=self.ko_timer == 0 and self.round_frames > FIGHT_BANNER_FIGHT_AT)
        self.combat.update()

        # 7. ULTI meters: fill by dealing / taking damage, plus a slow passive gain
        dealt_to_enemy = max(0.0, enemy_hp - self.enemy.health)
        dealt_to_player = max(0.0, player_hp - self.player.health)
        for fighter, dealt, taken in ((self.player, dealt_to_enemy, dealt_to_player),
                                      (self.enemy, dealt_to_player, dealt_to_enemy)):
            if not self.ulti.is_active(fighter):
                was_full = fighter.ulti_meter >= ULTI_MAX
                gain = dealt * ULTI_GAIN_DEAL + taken * ULTI_GAIN_TAKE + ULTI_GAIN_PASSIVE
                if fighter is self.enemy:
                    gain *= DIFFICULTIES[self.difficulty]["meter_gain"]
                fighter.ulti_meter = min(ULTI_MAX, fighter.ulti_meter + gain)
                if fighter is self.player and not was_full and fighter.ulti_meter >= ULTI_MAX:
                    self.sound.play("ulti_ready")

        # 8. Check Game Over (let the KO / victory animations play first)
        if self.ko_timer == 0 and (self.enemy.is_dead or self.player.is_dead):
            self.ko_timer = KO_DELAY_FRAMES
            loser = self.enemy if self.enemy.is_dead else self.player
            winner = self.player if loser is self.enemy else self.enemy
            winner.is_victorious = not winner.is_dead
            self.sound.play("ko")
            self.sound.play_fighter(loser, "ko", fallback=None)
        elif self.ko_timer > 0:
            self.ko_timer -= 1
            if self.ko_timer == 0:
                player_won = self.enemy.is_dead and not self.player.is_dead
                self.sound.play("victory" if player_won else "defeat")
                winner = self.winner()
                if winner:
                    self.sound.play_fighter(winner, "victory", fallback=None)
                self.state = STATE_VICTORY if self.enemy.is_dead else STATE_DEFEAT

    def winner(self):
        if self.enemy is None or self.player is None:
            return None
        if self.enemy.is_dead:
            return None if self.player.is_dead else self.player
        return self.enemy if self.player.is_dead else None

    # ------------------------------------------------------------------ render
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

    def draw_battle(self, surface):
        # Draw Arena Environment
        self.draw_arena_background(surface)

        # Ulti ground warnings
        self.ulti.draw_back(surface)

        # Health trays
        self.pickups.draw(surface)

        # Draw Projectiles
        for proj in self.projectiles:
            proj.draw(surface)

        # Draw Player & Enemy
        self.player.draw(surface)
        self.enemy.draw(surface)

        # Ulti hazards (clones, missile, building, bull, lightning)
        self.ulti.draw_front(surface)

        # Draw Combat Particle FX & Hit Floating Texts
        self.combat.draw(surface, self.ui.font_medium)

        # Draw HUD
        self.ui.draw_hud(surface, self.player, self.enemy)
        if self.state == STATE_PLAYING:
            self.ui.draw_ko(surface, self.ko_timer)

    def menu_backdrop(self):
        stages = self.menu.stages
        return stages[self.menu.stage_index].image if stages else None

    def render(self):
        # Create surface for screen shake
        render_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        if self.state in (STATE_PLAYING, STATE_PAUSED, STATE_VICTORY, STATE_DEFEAT):
            self.draw_battle(render_surface)

            # Overlays
            if self.state == STATE_PAUSED:
                self.ui.draw_pause_overlay(render_surface, self.pause_option_index)
            elif self.state == STATE_VICTORY:
                self.ui.draw_end_game_overlay(render_surface, True, self.endgame_option_index, self.winner())
            elif self.state == STATE_DEFEAT:
                self.ui.draw_end_game_overlay(render_surface, False, self.endgame_option_index, self.winner())

        elif self.state == STATE_MENU:
            self.menu.draw(render_surface)

        elif self.state == STATE_CHAR_SELECT:
            self.char_select.draw(render_surface, self.menu_backdrop())

        elif self.state == STATE_STAGE_SELECT:
            self.stage_select.draw(render_surface)

        elif self.state == STATE_SETTINGS:
            if self.settings_return == STATE_PAUSED:
                self.draw_battle(render_surface)
                self.settings.draw(render_surface)
            else:
                self.settings.draw(render_surface, self.menu_backdrop())

        elif self.state == STATE_HOW_TO_PLAY:
            self.menu.draw_how_to_play(render_surface)

        # Blit with Screen Shake offset
        ox = self.combat.shake_offset_x if self.state == STATE_PLAYING else 0
        oy = self.combat.shake_offset_y if self.state == STATE_PLAYING else 0
        self.screen.fill((0, 0, 0))
        self.screen.blit(render_surface, (ox, oy))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        save_config(self.config)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
