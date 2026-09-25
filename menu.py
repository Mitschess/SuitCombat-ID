import random
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG_DARK
from pixelfont import draw_text, draw_title, draw_panel, dim, text_size, GOLD, CREAM, GREY, RED
from sprites import ROSTER, get_character
from stages import load_stages
from character_select import ULTI_NAMES

BG_SWITCH_FRAMES = 360


class MainMenu:
    """Title screen + HOW TO PLAY screen."""

    def __init__(self):
        self.selected_index = 0
        self.options = ["PLAY", "HOW TO PLAY", "SETTINGS", "QUIT"]
        self.anim_counter = 0
        self.stages = load_stages()
        self.stage_index = 0
        self.fighters = []
        self.pick_fighters()

    def pick_fighters(self):
        left, right = random.sample(ROSTER, 2)
        self.fighters = []
        for name, facing in ((left, 1), (right, -1)):
            anim = get_character(name).new_animator()
            anim.play("idle")
            self.fighters.append((name, anim, facing))

    def update(self):
        self.anim_counter += 1
        for _, anim, _ in self.fighters:
            anim.update()
        if self.anim_counter % BG_SWITCH_FRAMES == 0:
            if self.stages:
                self.stage_index = (self.stage_index + 1) % len(self.stages)
            self.pick_fighters()

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

    def draw_backdrop(self, surface, darkness=150):
        if self.stages:
            surface.blit(self.stages[self.stage_index].image, (0, 0))
        else:
            surface.fill(COLOR_BG_DARK)
        dim(surface, darkness)

    def draw_fighter(self, surface, name, anim, facing, x, ground, scale=2):
        assets = get_character(name)
        frame = pygame.Surface((assets.frame_w, assets.frame_w), pygame.SRCALPHA)
        anim.draw(frame, (assets.anchor[0] if facing == 1 else assets.frame_w - assets.anchor[0], assets.anchor[1]), facing)
        big = pygame.transform.scale(frame, (assets.frame_w * scale, assets.frame_w * scale))
        surface.blit(big, (x - big.get_width() // 2, ground - big.get_height()))

    def draw(self, surface):
        self.draw_backdrop(surface, 120)

        # fighters flanking the menu
        ground = SCREEN_HEIGHT - 30
        for (name, anim, facing), x in zip(self.fighters, (170, SCREEN_WIDTH - 170)):
            self.draw_fighter(surface, name, anim, facing, x, ground)
            draw_text(surface, name, (x, ground + 4), 2, GOLD, align="center")

        # title
        bob = 3 if (self.anim_counter // 30) % 2 else 0
        # "SUIT COMBAT" with a smaller red "ID" beside it, bottom-aligned, centred as one logo
        title_w, title_h = text_size("SUIT COMBAT", 10)
        id_w, id_h = text_size("ID", 6)
        gap = 18
        x0 = SCREEN_WIDTH // 2 - (title_w + gap + id_w) // 2
        y0 = 44 + bob
        draw_title(surface, "SUIT COMBAT", x0 + title_w // 2, y0, 10)
        draw_title(surface, "ID", x0 + title_w + gap + id_w // 2, y0 + title_h - id_h, 6, top=(255, 90, 60), bottom=RED)

        # options
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 190, 200, 380, 286)
        draw_panel(surface, panel)
        button_rects = []
        for i, opt in enumerate(self.options):
            y = panel.top + 30 + i * 62
            rect = pygame.Rect(panel.left + 20, y - 10, panel.width - 40, 48)
            button_rects.append((rect, opt))
            selected = i == self.selected_index
            if selected:
                pygame.draw.rect(surface, (70, 20, 30), rect)
                pygame.draw.rect(surface, RED, rect, 2)
                if (self.anim_counter // 15) % 2 == 0:
                    draw_text(surface, ">", (rect.left + 14, y), 4, GOLD)
                    draw_text(surface, "<", (rect.right - 14, y), 4, GOLD, align="right")
            draw_text(surface, opt, (rect.centerx, y), 4, GOLD if selected else GREY, align="center")

        draw_text(surface, "W/S : PILIH     ENTER : OK", (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 26), 2, CREAM, align="center")
        return button_rects

    def draw_how_to_play(self, surface):
        self.draw_backdrop(surface, 190)
        panel = pygame.Rect(60, 24, SCREEN_WIDTH - 120, SCREEN_HEIGHT - 48)
        draw_panel(surface, panel)
        draw_title(surface, "HOW TO PLAY", SCREEN_WIDTH // 2, panel.top + 18, 6)

        controls = [
            ("A / D", "MAJU / MUNDUR"),
            ("W", "LOMPAT"),
            ("S", "JONGKOK"),
            ("J", "PUKUL / TENDANG"),
            ("K", "TEMBAK PROYEKTIL"),
            ("L", "TANGKIS (-75% DMG)"),
            ("U", "ULTI (METER PENUH)"),
            ("ESC", "PAUSE"),
        ]
        x0, y0 = panel.left + 40, panel.top + 90
        draw_text(surface, "KONTROL", (x0, y0), 3, RED)
        for i, (key, desc) in enumerate(controls):
            y = y0 + 40 + i * 34
            draw_text(surface, key, (x0, y), 2, GOLD)
            draw_text(surface, desc, (x0 + 90, y), 2, CREAM)

        x1 = panel.centerx + 20
        draw_text(surface, "ULTI", (x1, y0), 3, RED)
        dodge = {"Mega": "LOMPAT!"}
        for i, name in enumerate(ROSTER):
            y = y0 + 40 + i * 58
            surface.blit(pygame.transform.scale(get_character(name).portrait, (40, 45)), (x1, y - 6))
            draw_text(surface, f"{name}: {ULTI_NAMES[name]}", (x1 + 52, y), 2, GOLD)
            draw_text(surface, f"HINDARI: {dodge.get(name, 'GESER KIRI/KANAN')}", (x1 + 52, y + 20), 2, GREY)

        back = pygame.Rect(SCREEN_WIDTH // 2 - 130, panel.bottom - 56, 260, 40)
        pygame.draw.rect(surface, (70, 20, 30), back)
        pygame.draw.rect(surface, RED, back, 2)
        draw_text(surface, "ESC : KEMBALI", (back.centerx, back.top + 12), 2, GOLD, align="center")
        return back
