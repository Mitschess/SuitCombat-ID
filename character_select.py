import math
import random
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from pixelfont import draw_text, draw_title, draw_panel, dim, GOLD, CREAM, GREY, RED, INK
from sprites import ROSTER, get_character

ULTI_NAMES = {
    "Gian": "HUJAN GIAN",
    "Mega": "BANTENG NGAMUK",
    "Puba": "PETIR SAHAM",
    "Subi": "MISIL SAWIT",
    "Wowi": "GEDUNG JATUH",
}

RANDOM = "ACAK"
PHASE_PLAYER, PHASE_CPU = 0, 1
CPU_COLOR = (90, 170, 255)


class CharacterSelect:
    """Two steps: pick your fighter (P1), then the CPU opponent (any fighter or ACAK/random)."""

    def __init__(self):
        self.index = 0
        self.cpu_index = len(ROSTER)   # ACAK by default
        self.phase = PHASE_PLAYER
        self.anim_counter = 0
        self.previews = {}

    def reset(self):
        self.anim_counter = 0
        self.phase = PHASE_PLAYER

    def selected(self):
        return ROSTER[self.index]

    def highlighted(self):
        """Fighter currently under the cursor (None when the CPU cursor is on ACAK)."""
        if self.phase == PHASE_PLAYER:
            return self.selected()
        choice = self.cpu_options()[self.cpu_index]
        return None if choice == RANDOM else choice

    def cpu_options(self):
        return ROSTER + [RANDOM]

    def opponent(self):
        """The CPU fighter; ACAK picks a random fighter other than the player's."""
        choice = self.cpu_options()[self.cpu_index]
        if choice == RANDOM:
            return random.choice([c for c in ROSTER if c != self.selected()])
        return choice

    def preview(self, name):
        if name not in self.previews:
            anim = get_character(name).new_animator()
            anim.play("idle")
            self.previews[name] = anim
        return self.previews[name]

    def update(self):
        self.anim_counter += 1
        for anim in self.previews.values():
            anim.update()

    def handle_key_input(self, key):
        options = ROSTER if self.phase == PHASE_PLAYER else self.cpu_options()
        step = -1 if key in (pygame.K_LEFT, pygame.K_a) else 1 if key in (pygame.K_RIGHT, pygame.K_d) else 0
        if step:
            if self.phase == PHASE_PLAYER:
                self.index = (self.index + step) % len(options)
            else:
                self.cpu_index = (self.cpu_index + step) % len(options)
            return "NAVIGATE"
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            return self.confirm()
        if key == pygame.K_ESCAPE:
            if self.phase == PHASE_CPU:
                self.phase = PHASE_PLAYER
                return "NAVIGATE"
            return "BACK"
        return None

    def confirm(self):
        if self.phase == PHASE_PLAYER:
            self.phase = PHASE_CPU
            return "PLAYER_CHOSEN"
        return "CONFIRM"

    def card_rects(self):
        count = len(ROSTER) if self.phase == PHASE_PLAYER else len(self.cpu_options())
        card_w, card_h, gap = 130, 150, 16
        total = count * card_w + (count - 1) * gap
        x0 = SCREEN_WIDTH // 2 - total // 2
        return [pygame.Rect(x0 + i * (card_w + gap), 392, card_w, card_h) for i in range(count)]

    def handle_click(self, pos):
        for i, rect in enumerate(self.card_rects()):
            if rect.collidepoint(pos):
                current = self.index if self.phase == PHASE_PLAYER else self.cpu_index
                if i == current:
                    return self.confirm()
                if self.phase == PHASE_PLAYER:
                    self.index = i
                else:
                    self.cpu_index = i
                return "NAVIGATE"
        return None

    def draw_fighter_panel(self, surface, rect, name, facing, label, color):
        draw_panel(surface, rect, border=color)
        draw_text(surface, label, (rect.left + 16 if facing == 1 else rect.right - 16, rect.top + 14), 2, color,
                  align="left" if facing == 1 else "right")
        floor = rect.bottom - 40
        pygame.draw.ellipse(surface, INK, (rect.centerx - 60, floor - 7, 120, 14))
        if name == RANDOM:
            if (self.anim_counter // 20) % 2 == 0:
                draw_text(surface, "?", (rect.centerx, rect.centery - 50), 12, GOLD, align="center")
            draw_text(surface, "ACAK", (rect.centerx, rect.bottom - 30), 3, CREAM, align="center")
            return
        assets = get_character(name)
        frame = pygame.Surface((assets.frame_w, assets.frame_w), pygame.SRCALPHA)
        anchor_x = assets.anchor[0] if facing == 1 else assets.frame_w - assets.anchor[0]
        self.preview(name).draw(frame, (anchor_x, assets.anchor[1]), facing)
        big = pygame.transform.scale(frame, (assets.frame_w * 2, assets.frame_w * 2))
        surface.blit(big, (rect.centerx - anchor_x * 2, floor - assets.anchor[1] * 2))
        draw_text(surface, name, (rect.centerx, rect.bottom - 30), 3, CREAM, align="center")
        draw_text(surface, ULTI_NAMES[name], (rect.centerx, rect.top + 40), 2, GOLD, align="center")

    def draw(self, surface, backdrop=None):
        if backdrop:
            surface.blit(backdrop, (0, 0))
        else:
            surface.fill((12, 10, 22))
        dim(surface, 170)
        title = "PILIH JAGOAN" if self.phase == PHASE_PLAYER else "PILIH LAWAN"
        draw_title(surface, title, SCREEN_WIDTH // 2, 18, 7)

        # P1 (left) vs CPU (right)
        player_rect = pygame.Rect(70, 92, 360, 286)
        cpu_rect = pygame.Rect(SCREEN_WIDTH - 70 - 360, 92, 360, 286)
        player = self.selected()
        self.draw_fighter_panel(surface, player_rect, player, 1, "PLAYER 1",
                                get_character(player).color if self.phase == PHASE_PLAYER else GOLD)
        cpu_name = self.cpu_options()[self.cpu_index] if self.phase == PHASE_CPU else RANDOM
        self.draw_fighter_panel(surface, cpu_rect, cpu_name, -1, "CPU",
                                CPU_COLOR if self.phase == PHASE_CPU else (70, 64, 96))
        draw_text(surface, "VS", (SCREEN_WIDTH // 2, 212), 7, RED, align="center")

        # Cards: roster for P1, roster + ACAK for the CPU
        options = ROSTER if self.phase == PHASE_PLAYER else self.cpu_options()
        current = self.index if self.phase == PHASE_PLAYER else self.cpu_index
        accent = GOLD if self.phase == PHASE_PLAYER else CPU_COLOR
        for i, (rect, char) in enumerate(zip(self.card_rects(), options)):
            selected = i == current
            lift = int(5 * abs(math.sin(self.anim_counter * 0.1))) if selected else 0
            r = rect.move(0, -lift)
            border = (get_character(char).color if char != RANDOM else accent) if selected else (70, 64, 96)
            draw_panel(surface, r, border=border, thick=3 if selected else 2)
            if char == RANDOM:
                draw_text(surface, "?", (r.centerx, r.top + 30), 8, GOLD if selected else GREY, align="center")
            else:
                portrait = pygame.transform.scale(get_character(char).portrait, (96, 108))
                if not selected:
                    portrait = portrait.copy()
                    portrait.fill((110, 110, 120), special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(portrait, (r.centerx - 48, r.top + 8))
            draw_text(surface, char, (r.centerx, r.bottom - 26), 2, accent if selected else GREY, align="center")
            if selected and (self.anim_counter // 12) % 2 == 0:
                draw_text(surface, "P1" if self.phase == PHASE_PLAYER else "CPU", (r.left + 8, r.top + 8), 2,
                          RED if self.phase == PHASE_PLAYER else CPU_COLOR)
            if self.phase == PHASE_CPU and char == player:
                draw_text(surface, "P1", (r.right - 8, r.top + 8), 2, RED, align="right")

        hint = "A/D : PILIH    ENTER : OK    ESC : KEMBALI" if self.phase == PHASE_PLAYER else \
            "A/D : PILIH LAWAN    ENTER : OK    ESC : GANTI JAGOAN"
        draw_text(surface, hint, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 24), 2, CREAM, align="center")
