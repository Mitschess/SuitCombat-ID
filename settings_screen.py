import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from pixelfont import draw_text, draw_title, draw_panel, dim, GOLD, CREAM, GREY, RED, INK, GREEN

VOLUME_KEYS = [("MASTER VOLUME", "master"), ("MUSIK", "music"), ("EFEK SUARA", "sfx")]
OPTIONS = [label for label, _ in VOLUME_KEYS] + ["FULLSCREEN", "KEMBALI"]


class SettingsScreen:
    """Volume sliders + fullscreen toggle. Changes are applied and saved by the Game."""

    def __init__(self, config):
        self.config = config
        self.index = 0
        self.anim_counter = 0

    def update(self):
        self.anim_counter += 1

    def adjust(self, step):
        label = OPTIONS[self.index]
        for name, key in VOLUME_KEYS:
            if name == label:
                self.config[key] = round(max(0.0, min(1.0, self.config[key] + step * 0.1)), 1)
                return "CHANGED"
        if label == "FULLSCREEN":
            return "TOGGLE_FULLSCREEN"
        return None

    def handle_key_input(self, key):
        if key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(OPTIONS)
            return "NAVIGATE"
        if key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(OPTIONS)
            return "NAVIGATE"
        if key in (pygame.K_LEFT, pygame.K_a):
            return self.adjust(-1)
        if key in (pygame.K_RIGHT, pygame.K_d):
            return self.adjust(1)
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            if OPTIONS[self.index] == "KEMBALI":
                return "BACK"
            if OPTIONS[self.index] == "FULLSCREEN":
                return "TOGGLE_FULLSCREEN"
            return None
        if key == pygame.K_ESCAPE:
            return "BACK"
        return None

    def row_rects(self):
        return [pygame.Rect(SCREEN_WIDTH // 2 - 330, 150 + i * 70, 660, 54) for i in range(len(OPTIONS))]

    def handle_click(self, pos):
        for i, rect in enumerate(self.row_rects()):
            if rect.collidepoint(pos):
                self.index = i
                label = OPTIONS[i]
                if label == "KEMBALI":
                    return "BACK"
                if label == "FULLSCREEN":
                    return "TOGGLE_FULLSCREEN"
                # click on the right half raises the volume, left half lowers it
                return self.adjust(1 if pos[0] > rect.left + 420 else -1)
        return None

    def draw(self, surface, backdrop=None):
        if backdrop:
            surface.blit(backdrop, (0, 0))
        dim(surface, 190)
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 370, 40, 740, 500)
        draw_panel(surface, panel)
        draw_title(surface, "SETTINGS", SCREEN_WIDTH // 2, panel.top + 22, 7)

        blink = (self.anim_counter // 15) % 2 == 0
        for i, (rect, label) in enumerate(zip(self.row_rects(), OPTIONS)):
            selected = i == self.index
            pygame.draw.rect(surface, (70, 20, 30) if selected else (26, 20, 40), rect)
            pygame.draw.rect(surface, RED if selected else (70, 64, 96), rect, 2)
            color = GOLD if selected else GREY
            if label == "KEMBALI":
                draw_text(surface, label, (rect.centerx, rect.top + 17), 3, color, align="center")
                continue
            draw_text(surface, label, (rect.left + 20, rect.top + 17), 3, color)

            if label == "FULLSCREEN":
                on = self.config["fullscreen"]
                draw_text(surface, "ON" if on else "OFF", (rect.right - 70, rect.top + 17), 3, GREEN if on else RED,
                          align="center")
                continue

            key = dict(VOLUME_KEYS)[label]
            value = self.config[key]
            bx = rect.left + 330
            for s in range(10):
                seg = pygame.Rect(bx + s * 22, rect.top + 16, 18, 22)
                pygame.draw.rect(surface, INK, seg.inflate(2, 2))
                filled = s < round(value * 10)
                pygame.draw.rect(surface, (GOLD if selected else CREAM) if filled else (40, 34, 56), seg)
            draw_text(surface, f"{int(round(value * 100))}%", (rect.right - 16, rect.top + 17), 2, CREAM, align="right")
            if selected and blink:
                draw_text(surface, "<", (bx - 26, rect.top + 17), 3, GOLD)
                draw_text(surface, ">", (bx + 224, rect.top + 17), 3, GOLD)

        draw_text(surface, "W/S: PILIH   A/D: UBAH   ENTER: OK   ESC: KEMBALI   F11: FULLSCREEN",
                  (SCREEN_WIDTH // 2, panel.bottom - 30), 2, GREY, align="center")
