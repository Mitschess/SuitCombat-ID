import pygame
import math
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_WHITE, COLOR_BLACK,
    COLOR_HEALTH_PLAYER, COLOR_HEALTH_ENEMY, COLOR_HEALTH_BG,
    COLOR_HEALTH_BORDER, COLOR_MENU_TITLE, COLOR_MENU_SUBTITLE,
    COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER, COLOR_BUTTON_BORDER,
    COLOR_TEXT_NORMAL, COLOR_TEXT_SELECTED, ULTI_MAX
)

class UIManager:
    def __init__(self):
        pygame.font.init()
        # Initialize fonts
        self.font_large = pygame.font.SysFont("Impact", 54) or pygame.font.SysFont("Arial", 54, bold=True)
        self.font_medium = pygame.font.SysFont("Verdana", 28, bold=True)
        self.font_small = pygame.font.SysFont("Verdana", 18)
        self.font_title = pygame.font.SysFont("Impact", 68) or pygame.font.SysFont("Arial", 68, bold=True)

        # Smooth HP Bar Interpolation Values
        self.player_hp_display = 100.0
        self.enemy_hp_display = 100.0
        
        # Round Timer / Announcement
        self.fight_banner_timer = 90  # "FIGHT!" banner frames at start
        self.ulti_banner = None       # (text, color, frames left)
        self.anim_counter = 0

    def reset(self):
        self.player_hp_display = 100.0
        self.enemy_hp_display = 100.0
        self.fight_banner_timer = 90
        self.ulti_banner = None

    def show_ulti_banner(self, text, color):
        self.ulti_banner = (text, color, 70)

    def draw_fighter_badge(self, surface, fighter, x, y, align_right):
        """Portrait + ULTI meter under the health bar."""
        size = (48, 54)
        px = x - size[0] if align_right else x
        if fighter.assets:
            surface.blit(pygame.transform.scale(fighter.assets.portrait, size), (px, y))
        meter_w, meter_h = 170, 12
        mx = px - 10 - meter_w if align_right else px + size[0] + 10
        my = y + 8
        ratio = max(0.0, min(1.0, fighter.ulti_meter / ULTI_MAX))
        pygame.draw.rect(surface, COLOR_HEALTH_BG, (mx, my, meter_w, meter_h), border_radius=4)
        fill_w = int(meter_w * ratio)
        full = ratio >= 1.0
        color = (255, 220, 60) if not full or (self.anim_counter // 8) % 2 else (255, 255, 200)
        if fill_w > 0:
            fx = mx + meter_w - fill_w if align_right else mx
            pygame.draw.rect(surface, color, (fx, my, fill_w, meter_h), border_radius=4)
        pygame.draw.rect(surface, COLOR_HEALTH_BORDER, (mx, my, meter_w, meter_h), width=1, border_radius=4)
        label = "ULTI READY! [U]" if full and not align_right else ("ULTI READY!" if full else "ULTI")
        txt = self.font_small.render(label, True, (255, 220, 60) if full else COLOR_TEXT_NORMAL)
        tx = mx + meter_w - txt.get_width() if align_right else mx
        surface.blit(txt, (tx, my + meter_h + 2))

    def draw_hud(self, surface, player, enemy):
        # Smooth HP interpolation
        self.player_hp_display += (player.health - self.player_hp_display) * 0.1
        self.enemy_hp_display += (enemy.health - self.enemy_hp_display) * 0.1

        bar_width = 380
        bar_height = 24
        bar_top = 34

        # ------------------- PLAYER HUD (LEFT) -------------------
        p_x = 40
        # Label & Avatar Badge
        p_name = self.font_medium.render(player.name, True, COLOR_WHITE)
        surface.blit(p_name, (p_x, bar_top - 25))

        # Health Bar Outer Border
        p_bg_rect = pygame.Rect(p_x, bar_top, bar_width, bar_height)
        pygame.draw.rect(surface, COLOR_HEALTH_BG, p_bg_rect, border_radius=6)
        
        # Red damage trail bar
        p_trail_w = int((max(0, self.player_hp_display) / player.max_health) * bar_width)
        if p_trail_w > 0:
            pygame.draw.rect(surface, (255, 140, 0), pygame.Rect(p_x, bar_top, p_trail_w, bar_height), border_radius=6)

        # Main green HP bar
        p_hp_w = int((max(0, player.health) / player.max_health) * bar_width)
        if p_hp_w > 0:
            pygame.draw.rect(surface, COLOR_HEALTH_PLAYER, pygame.Rect(p_x, bar_top, p_hp_w, bar_height), border_radius=6)
            
        pygame.draw.rect(surface, COLOR_HEALTH_BORDER, p_bg_rect, width=2, border_radius=6)
        
        # HP Text
        hp_str_p = f"{int(player.health)} / {int(player.max_health)}"
        p_hp_txt = self.font_small.render(hp_str_p, True, COLOR_WHITE)
        surface.blit(p_hp_txt, (p_x + 10, bar_top + 2))

        # ------------------- ENEMY HUD (RIGHT) -------------------
        e_x = SCREEN_WIDTH - 40 - bar_width
        e_name = self.font_medium.render(enemy.name, True, COLOR_WHITE)
        surface.blit(e_name, (SCREEN_WIDTH - 40 - e_name.get_width(), bar_top - 25))

        # Health Bar Outer Border
        e_bg_rect = pygame.Rect(e_x, bar_top, bar_width, bar_height)
        pygame.draw.rect(surface, COLOR_HEALTH_BG, e_bg_rect, border_radius=6)

        # Red damage trail bar (right aligned)
        e_trail_w = int((max(0, self.enemy_hp_display) / enemy.max_health) * bar_width)
        if e_trail_w > 0:
            trail_x = e_x + (bar_width - e_trail_w)
            pygame.draw.rect(surface, (255, 140, 0), pygame.Rect(trail_x, bar_top, e_trail_w, bar_height), border_radius=6)

        # Main red HP bar
        e_hp_w = int((max(0, enemy.health) / enemy.max_health) * bar_width)
        if e_hp_w > 0:
            hp_x = e_x + (bar_width - e_hp_w)
            pygame.draw.rect(surface, COLOR_HEALTH_ENEMY, pygame.Rect(hp_x, bar_top, e_hp_w, bar_height), border_radius=6)

        pygame.draw.rect(surface, COLOR_HEALTH_BORDER, e_bg_rect, width=2, border_radius=6)

        # HP Text
        hp_str_e = f"{int(enemy.health)} / {int(enemy.max_health)}"
        e_hp_txt = self.font_small.render(hp_str_e, True, COLOR_WHITE)
        surface.blit(e_hp_txt, (SCREEN_WIDTH - 40 - e_hp_txt.get_width() - 10, bar_top + 2))

        # ------------------- PORTRAITS + ULTI METERS -------------------
        self.anim_counter += 1
        self.draw_fighter_badge(surface, player, p_x, bar_top + bar_height + 6, False)
        self.draw_fighter_badge(surface, enemy, SCREEN_WIDTH - 40, bar_top + bar_height + 6, True)

        # ------------------- ULTI BANNER -------------------
        if self.ulti_banner:
            text, color, frames = self.ulti_banner
            rendered = self.font_large.render(text, True, color)
            shadow = self.font_large.render(text, True, (0, 0, 0))
            bx = SCREEN_WIDTH // 2 - rendered.get_width() // 2
            by = 110 - max(0, frames - 60) * 4
            surface.blit(shadow, (bx + 3, by + 3))
            surface.blit(rendered, (bx, by))
            self.ulti_banner = (text, color, frames - 1) if frames > 1 else None

        # ------------------- VS BADGE -------------------
        vs_txt = self.font_large.render("VS", True, COLOR_MENU_SUBTITLE)
        surface.blit(vs_txt, (SCREEN_WIDTH // 2 - vs_txt.get_width() // 2, bar_top - 12))

        # ------------------- START FIGHT ANNOUNCEMENT -------------------
        if self.fight_banner_timer > 0:
            self.fight_banner_timer -= 1
            banner_text = "READY..." if self.fight_banner_timer > 45 else "FIGHT!"
            banner_color = COLOR_MENU_SUBTITLE if self.fight_banner_timer > 45 else (255, 50, 50)
            rendered = self.font_title.render(banner_text, True, banner_color)
            
            # Pulse scale
            pulse = 1.0 + 0.1 * math.sin(self.fight_banner_timer * 0.2)
            w = int(rendered.get_width() * pulse)
            h = int(rendered.get_height() * pulse)
            scaled = pygame.transform.smoothscale(rendered, (w, h))
            
            surface.blit(scaled, (SCREEN_WIDTH // 2 - w // 2, SCREEN_HEIGHT // 3 - h // 2))

    def draw_pause_overlay(self, surface, selected_index=0):
        # Semi-transparent dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 20, 200))
        surface.blit(overlay, (0, 0))

        # Pause Card
        card_w, card_h = 400, 320
        card_x = SCREEN_WIDTH // 2 - card_w // 2
        card_y = SCREEN_HEIGHT // 2 - card_h // 2

        pygame.draw.rect(surface, (25, 30, 48), (card_x, card_y, card_w, card_h), border_radius=12)
        pygame.draw.rect(surface, COLOR_BUTTON_BORDER, (card_x, card_y, card_w, card_h), width=2, border_radius=12)

        # Title
        title = self.font_large.render("PAUSED", True, COLOR_MENU_TITLE)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, card_y + 25))

        # Options
        options = ["RESUME", "RESTART", "MAIN MENU"]
        button_rects = []
        
        for i, opt in enumerate(options):
            btn_w, btn_h = 280, 48
            btn_x = SCREEN_WIDTH // 2 - btn_w // 2
            btn_y = card_y + 110 + i * 60
            b_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            button_rects.append(b_rect)

            is_sel = (i == selected_index)
            bg_col = COLOR_BUTTON_HOVER if is_sel else COLOR_BUTTON_NORMAL
            border_col = COLOR_MENU_TITLE if is_sel else (70, 80, 110)
            txt_col = COLOR_TEXT_SELECTED if is_sel else COLOR_TEXT_NORMAL

            pygame.draw.rect(surface, bg_col, b_rect, border_radius=8)
            pygame.draw.rect(surface, border_col, b_rect, width=2 if is_sel else 1, border_radius=8)

            txt = self.font_medium.render(opt, True, txt_col)
            surface.blit(txt, (b_rect.centerx - txt.get_width() // 2, b_rect.centery - txt.get_height() // 2))

        return button_rects

    def draw_end_game_overlay(self, surface, is_victory, selected_index=0):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 20, 210))
        surface.blit(overlay, (0, 0))

        card_w, card_h = 440, 340
        card_x = SCREEN_WIDTH // 2 - card_w // 2
        card_y = SCREEN_HEIGHT // 2 - card_h // 2

        pygame.draw.rect(surface, (25, 30, 48), (card_x, card_y, card_w, card_h), border_radius=12)
        accent_color = COLOR_HEALTH_PLAYER if is_victory else COLOR_HEALTH_ENEMY
        pygame.draw.rect(surface, accent_color, (card_x, card_y, card_w, card_h), width=3, border_radius=12)

        # Header Title (VICTORY! / DEFEAT)
        main_title_str = "VICTORY!" if is_victory else "DEFEAT"
        sub_title_str = "YOU WIN!" if is_victory else "YOU LOSE!"
        
        main_title = self.font_title.render(main_title_str, True, accent_color)
        sub_title = self.font_medium.render(sub_title_str, True, COLOR_WHITE)

        surface.blit(main_title, (SCREEN_WIDTH // 2 - main_title.get_width() // 2, card_y + 20))
        surface.blit(sub_title, (SCREEN_WIDTH // 2 - sub_title.get_width() // 2, card_y + 90))

        # Options
        options = ["PLAY AGAIN", "MAIN MENU"]
        button_rects = []
        
        for i, opt in enumerate(options):
            btn_w, btn_h = 280, 50
            btn_x = SCREEN_WIDTH // 2 - btn_w // 2
            btn_y = card_y + 160 + i * 65
            b_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            button_rects.append(b_rect)

            is_sel = (i == selected_index)
            bg_col = COLOR_BUTTON_HOVER if is_sel else COLOR_BUTTON_NORMAL
            border_col = accent_color if is_sel else (70, 80, 110)
            txt_col = COLOR_TEXT_SELECTED if is_sel else COLOR_TEXT_NORMAL

            pygame.draw.rect(surface, bg_col, b_rect, border_radius=8)
            pygame.draw.rect(surface, border_col, b_rect, width=2 if is_sel else 1, border_radius=8)

            txt = self.font_medium.render(opt, True, txt_col)
            surface.blit(txt, (b_rect.centerx - txt.get_width() // 2, b_rect.centery - txt.get_height() // 2))

        return button_rects
