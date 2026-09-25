import pygame
import math
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG_DARK, COLOR_MENU_TITLE,
    COLOR_MENU_SUBTITLE, COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER,
    COLOR_BUTTON_BORDER, COLOR_TEXT_NORMAL, COLOR_TEXT_SELECTED, COLOR_WHITE,
    COLOR_PLAYER, COLOR_ENEMY
)

class MainMenu:
    def __init__(self):
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Impact", 80) or pygame.font.SysFont("Arial", 80, bold=True)
        self.font_subtitle = pygame.font.SysFont("Verdana", 20)
        self.font_button = pygame.font.SysFont("Verdana", 26, bold=True)
        self.font_controls = pygame.font.SysFont("Consolas", 22) or pygame.font.SysFont("Courier New", 22)
        
        self.selected_index = 0
        self.options = ["PLAY", "HOW TO PLAY", "QUIT"]
        self.anim_counter = 0

    def update(self):
        self.anim_counter += 1

    def handle_key_input(self, key):
        if key == pygame.K_UP or key == pygame.K_w:
            self.selected_index = (self.selected_index - 1) % len(self.options)
            return "NAVIGATE"
        elif key == pygame.K_DOWN or key == pygame.K_s:
            self.selected_index = (self.selected_index + 1) % len(self.options)
            return "NAVIGATE"
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            return self.options[self.selected_index]
        return None

    def draw_background_arena(self, surface):
        """Draws animated background preview for Main Menu."""
        surface.fill(COLOR_BG_DARK)
        
        # Grid lines background
        grid_size = 40
        grid_offset = (self.anim_counter * 0.5) % grid_size
        for x in range(0, SCREEN_WIDTH, grid_size):
            pygame.draw.line(surface, (25, 30, 50), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, grid_size):
            pygame.draw.line(surface, (25, 30, 50), (0, int(y + grid_offset)), (SCREEN_WIDTH, int(y + grid_offset)))

        # Neon Floor line
        ground_y = SCREEN_HEIGHT - 80
        pygame.draw.rect(surface, (20, 24, 40), (0, ground_y, SCREEN_WIDTH, 80))
        pygame.draw.line(surface, COLOR_MENU_TITLE, (0, ground_y), (SCREEN_WIDTH, ground_y), 3)

        # Background silhouette mockup fighters
        p1_rect = pygame.Rect(180, ground_y - 90, 60, 90)
        p2_rect = pygame.Rect(SCREEN_WIDTH - 240, ground_y - 90, 60, 90)
        
        p1_surf = pygame.Surface((60, 90), pygame.SRCALPHA)
        p1_surf.fill((0, 180, 255, 60))
        surface.blit(p1_surf, p1_rect.topleft)

        p2_surf = pygame.Surface((60, 90), pygame.SRCALPHA)
        p2_surf.fill((255, 50, 80, 60))
        surface.blit(p2_surf, p2_rect.topleft)

    def draw(self, surface):
        self.draw_background_arena(surface)

        # Main Title Banner
        title_str = "PYFIGHT"
        title_surf = self.font_title.render(title_str, True, COLOR_MENU_TITLE)
        
        # Title Glow & Pulse effect
        glow_pulse = 2 + math.sin(self.anim_counter * 0.08) * 2
        title_shadow = self.font_title.render(title_str, True, (0, 100, 200))
        surface.blit(title_shadow, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2 + int(glow_pulse), 90 + int(glow_pulse)))
        surface.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 90))

        # Subtitle
        sub_txt = self.font_subtitle.render("2D RETRO FIGHTING GAME — PLAYER VS CPU", True, COLOR_MENU_SUBTITLE)
        surface.blit(sub_txt, (SCREEN_WIDTH // 2 - sub_txt.get_width() // 2, 180))

        # Menu Option Buttons
        button_rects = []
        btn_w, btn_h = 320, 55
        start_y = 250

        for i, opt in enumerate(self.options):
            btn_x = SCREEN_WIDTH // 2 - btn_w // 2
            btn_y = start_y + i * 75
            b_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            button_rects.append((b_rect, opt))

            is_selected = (i == self.selected_index)
            bg_color = COLOR_BUTTON_HOVER if is_selected else COLOR_BUTTON_NORMAL
            border_color = COLOR_MENU_TITLE if is_selected else (60, 70, 100)
            text_color = COLOR_TEXT_SELECTED if is_selected else COLOR_TEXT_NORMAL

            # Draw Button Card
            pygame.draw.rect(surface, bg_color, b_rect, border_radius=10)
            pygame.draw.rect(surface, border_color, b_rect, width=3 if is_selected else 1, border_radius=10)

            # Draw Selection Pointer Indicator
            if is_selected:
                pointer_left = (b_rect.left - 25, b_rect.centery)
                pointer_top = (b_rect.left - 40, b_rect.centery - 10)
                pointer_bot = (b_rect.left - 40, b_rect.centery + 10)
                pygame.draw.polygon(surface, COLOR_MENU_TITLE, [pointer_left, pointer_top, pointer_bot])

            text_surf = self.font_button.render(opt, True, text_color)
            surface.blit(text_surf, (b_rect.centerx - text_surf.get_width() // 2, b_rect.centery - text_surf.get_height() // 2))

        # Footer instructions
        footer = self.font_subtitle.render("Use UP/DOWN Arrows & ENTER or MOUSE to select", True, COLOR_TEXT_NORMAL)
        surface.blit(footer, (SCREEN_WIDTH // 2 - footer.get_width() // 2, SCREEN_HEIGHT - 45))

        return button_rects

    def draw_how_to_play(self, surface):
        self.draw_background_arena(surface)

        card_w, card_h = 680, 480
        card_x = SCREEN_WIDTH // 2 - card_w // 2
        card_y = SCREEN_HEIGHT // 2 - card_h // 2

        pygame.draw.rect(surface, (20, 25, 42), (card_x, card_y, card_w, card_h), border_radius=12)
        pygame.draw.rect(surface, COLOR_MENU_TITLE, (card_x, card_y, card_w, card_h), width=2, border_radius=12)

        title = self.font_title.render("HOW TO PLAY", True, COLOR_MENU_TITLE)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, card_y + 15))

        lines = [
            ("--- MOVEMENT ---", COLOR_MENU_SUBTITLE),
            ("A / D      : Move Left / Right", COLOR_WHITE),
            ("W          : Jump", COLOR_WHITE),
            ("S          : Crouch Stance", COLOR_WHITE),
            ("", COLOR_WHITE),
            ("--- COMBAT ---", COLOR_MENU_SUBTITLE),
            ("J          : Melee Attack (Punch / Slash)", COLOR_WHITE),
            ("K          : Ranged Attack (Energy Projectile)", COLOR_WHITE),
            ("L          : Block (Reduce 75% Damage)", COLOR_WHITE),
            ("U          : ULTI (when the ULTI meter is full)", COLOR_WHITE),
            ("", COLOR_WHITE),
            ("--- SYSTEM ---", COLOR_MENU_SUBTITLE),
            ("ESC        : Pause / Back to Menu", COLOR_WHITE)
        ]

        y_offset = card_y + 90
        for line, col in lines:
            if line:
                txt = self.font_controls.render(line, True, col)
                surface.blit(txt, (card_x + 50, y_offset))
            y_offset += 24

        # Back Button prompt
        btn_w, btn_h = 220, 45
        b_rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_w // 2, card_y + card_h - 60, btn_w, btn_h)
        pygame.draw.rect(surface, COLOR_BUTTON_HOVER, b_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_MENU_TITLE, b_rect, width=2, border_radius=8)

        back_txt = self.font_button.render("BACK (ESC)", True, COLOR_TEXT_SELECTED)
        surface.blit(back_txt, (b_rect.centerx - back_txt.get_width() // 2, b_rect.centery - back_txt.get_height() // 2))

        return b_rect
