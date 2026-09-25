import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, DIFFICULTY_ORDER, DIFFICULTIES
from pixelfont import draw_text, draw_title, draw_panel, dim, GOLD, CREAM, GREY, RED

ROW_STAGE, ROW_DIFFICULTY = 0, 1


class StageSelect:
    """Pick the arena (background) and the CPU difficulty before the fight."""

    def __init__(self, stages):
        self.stages = stages
        self.index = 0
        self.difficulty_index = 1   # MEDIUM
        self.row = ROW_STAGE
        self.anim_counter = 0

    def selected_stage(self):
        return self.stages[self.index] if self.stages else None

    def difficulty(self):
        return DIFFICULTY_ORDER[self.difficulty_index]

    def update(self):
        self.anim_counter += 1

    def handle_key_input(self, key):
        if key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
            self.row = ROW_DIFFICULTY if self.row == ROW_STAGE else ROW_STAGE
            return "NAVIGATE"
        step = -1 if key in (pygame.K_LEFT, pygame.K_a) else 1 if key in (pygame.K_RIGHT, pygame.K_d) else 0
        if step:
            if self.row == ROW_STAGE and self.stages:
                self.index = (self.index + step) % len(self.stages)
            else:
                self.difficulty_index = (self.difficulty_index + step) % len(DIFFICULTY_ORDER)
            return "NAVIGATE"
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            return "CONFIRM"
        if key == pygame.K_ESCAPE:
            return "BACK"
        return None

    # layout
    def preview_rect(self):
        return pygame.Rect(SCREEN_WIDTH // 2 - 224, 84, 448, 252)

    def thumb_rects(self):
        w, h, gap = 128, 72, 14
        n = len(self.stages)
        x0 = SCREEN_WIDTH // 2 - (n * w + (n - 1) * gap) // 2
        return [pygame.Rect(x0 + i * (w + gap), 364, w, h) for i in range(n)]

    def difficulty_rects(self):
        return [pygame.Rect(SCREEN_WIDTH // 2 - 250 + i * 170, 470, 160, 40) for i in range(len(DIFFICULTY_ORDER))]

    def handle_click(self, pos):
        if self.preview_rect().collidepoint(pos):
            return "CONFIRM"
        for i, rect in enumerate(self.thumb_rects()):
            if rect.collidepoint(pos):
                self.index, self.row = i, ROW_STAGE
                return "NAVIGATE"
        for i, rect in enumerate(self.difficulty_rects()):
            if rect.collidepoint(pos):
                self.difficulty_index, self.row = i, ROW_DIFFICULTY
                return "NAVIGATE"
        return None

    def draw(self, surface):
        stage = self.selected_stage()
        if stage:
            surface.blit(stage.image, (0, 0))
        dim(surface, 185)
        draw_title(surface, "PILIH ARENA", SCREEN_WIDTH // 2, 16, 7)

        blink = (self.anim_counter // 15) % 2 == 0
        preview = self.preview_rect()
        draw_panel(surface, preview.inflate(16, 16), border=GOLD if self.row == ROW_STAGE else (90, 80, 110))
        if stage:
            surface.blit(stage.thumbnail(preview.size), preview.topleft)
            draw_text(surface, stage.name, (preview.centerx, preview.bottom - 30), 4, CREAM, align="center")
            if self.row == ROW_STAGE and blink:
                draw_text(surface, "<", (preview.left - 40, preview.centery - 14), 4, GOLD)
                draw_text(surface, ">", (preview.right + 40, preview.centery - 14), 4, GOLD, align="right")

        for i, (rect, s) in enumerate(zip(self.thumb_rects(), self.stages)):
            surface.blit(s.thumbnail(rect.size), rect.topleft)
            if i == self.index:
                pygame.draw.rect(surface, GOLD, rect.inflate(6, 6), 3)
            else:
                shade = pygame.Surface(rect.size, pygame.SRCALPHA)
                shade.fill((0, 0, 0, 120))
                surface.blit(shade, rect.topleft)
                pygame.draw.rect(surface, (70, 64, 96), rect.inflate(4, 4), 2)

        draw_text(surface, "DIFFICULTY", (SCREEN_WIDTH // 2, 450), 2, GOLD if self.row == ROW_DIFFICULTY else GREY,
                  align="center")
        for i, (rect, name) in enumerate(zip(self.difficulty_rects(), DIFFICULTY_ORDER)):
            color = DIFFICULTIES[name]["color"]
            selected = i == self.difficulty_index
            pygame.draw.rect(surface, (40, 12, 20) if selected else (20, 16, 30), rect)
            border = color if selected else (70, 64, 96)
            pygame.draw.rect(surface, border, rect, 3 if selected and (self.row != ROW_DIFFICULTY or blink) else 1)
            draw_text(surface, name, (rect.centerx, rect.top + 12), 3, color if selected else GREY, align="center")
        draw_text(surface, DIFFICULTIES[self.difficulty()]["desc"], (SCREEN_WIDTH // 2, 520), 2, CREAM, align="center")

        draw_text(surface, "A/D: PILIH   W/S: BARIS   ENTER: FIGHT   ESC: KEMBALI",
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20), 2, GREY, align="center")
