import math
import random
import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG_DARK, COLOR_MENU_TITLE, COLOR_MENU_SUBTITLE,
    COLOR_BUTTON_NORMAL, COLOR_TEXT_NORMAL, COLOR_WHITE
)
from sprites import ROSTER, get_character

ULTI_NAMES = {
    "Gian": "HUJAN GIAN",
    "Mega": "BANTENG NGAMUK",
    "Puba": "PETIR SAHAM",
    "Subi": "MISIL SAWIT",
    "Wowi": "GEDUNG JATUH",
}


class CharacterSelect:
    def __init__(self):
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Impact", 56) or pygame.font.SysFont("Arial", 56, bold=True)
        self.font_name = pygame.font.SysFont("Verdana", 20, bold=True)
        self.font_small = pygame.font.SysFont("Verdana", 16)
        self.index = 0
        self.anim_counter = 0
        self.preview = None
        self.preview_for = None

    def reset(self):
        self.anim_counter = 0

    def selected(self):
        return ROSTER[self.index]

    def random_opponent(self):
        return random.choice([c for c in ROSTER if c != self.selected()])

    def update(self):
        self.anim_counter += 1
        if self.preview_for != self.selected():
            self.preview_for = self.selected()
            self.preview = get_character(self.selected()).new_animator()
            self.preview.play("idle")
        self.preview.update()

    def handle_key_input(self, key):
        if key in (pygame.K_LEFT, pygame.K_a):
            self.index = (self.index - 1) % len(ROSTER)
            return "NAVIGATE"
        if key in (pygame.K_RIGHT, pygame.K_d):
            self.index = (self.index + 1) % len(ROSTER)
            return "NAVIGATE"
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            return "CONFIRM"
        if key == pygame.K_ESCAPE:
            return "BACK"
        return None

    def card_rects(self):
        card_w, card_h, gap = 150, 170, 22
        total = len(ROSTER) * card_w + (len(ROSTER) - 1) * gap
        x0 = SCREEN_WIDTH // 2 - total // 2
        return [pygame.Rect(x0 + i * (card_w + gap), 330, card_w, card_h) for i in range(len(ROSTER))]

    def handle_click(self, pos):
        for i, rect in enumerate(self.card_rects()):
            if rect.collidepoint(pos):
                if i == self.index:
                    return "CONFIRM"
                self.index = i
                return "NAVIGATE"
        return None

    def draw(self, surface):
        surface.fill(COLOR_BG_DARK)
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, (25, 30, 50), (x, 0), (x, SCREEN_HEIGHT))

        title = self.font_title.render("SELECT YOUR FIGHTER", True, COLOR_MENU_TITLE)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))

        # Big animated preview of the highlighted fighter
        name = self.selected()
        assets = get_character(name)
        floor_y = 290
        pygame.draw.ellipse(surface, (10, 10, 18), (SCREEN_WIDTH // 2 - 70, floor_y - 10, 140, 20))
        if self.preview:
            frame_surface = pygame.Surface((assets.frame_w, assets.frame_w), pygame.SRCALPHA)
            self.preview.draw(frame_surface, (assets.anchor[0], assets.anchor[1]), 1)
            big = pygame.transform.scale(frame_surface, (int(assets.frame_w * 1.8), int(assets.frame_w * 1.8)))
            surface.blit(big, (SCREEN_WIDTH // 2 - int(assets.anchor[0] * 1.8), floor_y - int(assets.anchor[1] * 1.8)))
        ulti = self.font_small.render(f"ULTI: {ULTI_NAMES.get(name, '')}", True, COLOR_MENU_SUBTITLE)
        surface.blit(ulti, (SCREEN_WIDTH // 2 - ulti.get_width() // 2, floor_y + 12))

        # Portrait cards
        for i, (rect, char) in enumerate(zip(self.card_rects(), ROSTER)):
            char_assets = get_character(char)
            selected = i == self.index
            lift = int(4 * math.sin(self.anim_counter * 0.12)) if selected else 0
            r = rect.move(0, -lift)
            pygame.draw.rect(surface, (40, 46, 72) if selected else COLOR_BUTTON_NORMAL, r, border_radius=10)
            pygame.draw.rect(surface, char_assets.color if selected else (60, 70, 100), r,
                             width=3 if selected else 1, border_radius=10)
            portrait = pygame.transform.scale(char_assets.portrait, (108, 120))
            surface.blit(portrait, (r.centerx - 54, r.top + 10))
            label = self.font_name.render(char.upper(), True, COLOR_WHITE if selected else COLOR_TEXT_NORMAL)
            surface.blit(label, (r.centerx - label.get_width() // 2, r.bottom - 34))

        hint = self.font_small.render("A/D or ARROWS to choose  -  ENTER to fight  -  ESC back", True, COLOR_TEXT_NORMAL)
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 40))
