import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, ULTI_MAX, DIFFICULTIES
from pixelfont import (
    PixelFont, draw_text, draw_title, draw_panel, draw_bar, dim,
    GOLD, GOLD_DARK, CREAM, GREY, RED, INK, GREEN
)

BAR_W, BAR_H, BAR_TOP = 360, 22, 18
PAUSE_OPTIONS = ["RESUME", "RESTART", "SETTINGS", "MAIN MENU"]
PORTRAIT = (60, 68)


class UIManager:
    def __init__(self):
        # Pixel "fonts" (combat.py renders floating damage numbers with font_medium)
        self.font_large = PixelFont(5)
        self.font_medium = PixelFont(3)
        self.font_small = PixelFont(2)
        self.font_title = PixelFont(8)

        # Smooth HP Bar Interpolation Values
        self.player_hp_display = 100.0
        self.enemy_hp_display = 100.0

        # Round Timer / Announcement
        self.fight_banner_timer = 90  # "READY?" / "FIGHT!" banner frames at start
        self.ulti_banner = None       # (text, color, frames left)
        self.anim_counter = 0
        self.difficulty = "MEDIUM"

    def reset(self):
        self.player_hp_display = 100.0
        self.enemy_hp_display = 100.0
        self.fight_banner_timer = 90
        self.ulti_banner = None

    def show_ulti_banner(self, text, color):
        self.ulti_banner = (text, color, 70)

    # ------------------------------------------------------------------ HUD
    def draw_side(self, surface, fighter, hp_display, right):
        """Portrait, health bar, name and ULTI meter for one fighter (right=True mirrors the layout)."""
        px = SCREEN_WIDTH - 14 - PORTRAIT[0] if right else 14
        frame = pygame.Rect(px, 10, *PORTRAIT)
        pygame.draw.rect(surface, INK, frame.inflate(8, 8))
        pygame.draw.rect(surface, GOLD, frame.inflate(4, 4), 2)
        if fighter.assets:
            portrait = pygame.transform.scale(fighter.assets.portrait, PORTRAIT)
            if right:
                portrait = pygame.transform.flip(portrait, True, False)
            if fighter.hit_flash_timer > 0:
                portrait = portrait.copy()
                portrait.fill((255, 120, 120), special_flags=pygame.BLEND_RGB_MULT)
            surface.blit(portrait, frame.topleft)

        bx = frame.left - 16 - BAR_W if right else frame.right + 16
        ratio = max(0.0, fighter.health / fighter.max_health)
        low = ratio < 0.3
        color = (230, 60, 50) if low and (self.anim_counter // 8) % 2 else (240, 200, 50) if ratio < 0.5 else GREEN
        draw_bar(surface, (bx, BAR_TOP, BAR_W, BAR_H), ratio, color,
                 trail_ratio=max(0.0, hp_display / fighter.max_health), right_to_left=right)

        name_x = bx + BAR_W if right else bx
        draw_text(surface, fighter.name, (name_x, BAR_TOP + BAR_H + 8), 3, CREAM, align="right" if right else "left")

        # ULTI meter: 10 segments
        seg_w, seg_h, gap = 16, 8, 3
        full = fighter.ulti_meter >= ULTI_MAX
        total_w = 10 * seg_w + 9 * gap
        mx = bx if right else bx + BAR_W - total_w
        my = BAR_TOP + BAR_H + 12
        filled = fighter.ulti_meter / ULTI_MAX * 10
        for i in range(10):
            idx = 9 - i if right else i
            sx = mx + idx * (seg_w + gap)
            pygame.draw.rect(surface, INK, (sx - 1, my - 1, seg_w + 2, seg_h + 2))
            amount = max(0.0, min(1.0, filled - i))
            if amount > 0:
                col = (255, 255, 200) if full and (self.anim_counter // 6) % 2 else (90, 170, 255) if not full else GOLD
                w = int(seg_w * amount)
                pygame.draw.rect(surface, col, (sx + (seg_w - w if right else 0), my, w, seg_h))
            else:
                pygame.draw.rect(surface, (30, 26, 44), (sx, my, seg_w, seg_h))
        label = "ULTI READY [U]" if full and not right else "ULTI READY" if full else "ULTI"
        lx = mx + total_w if right else mx
        draw_text(surface, label, (lx, my + seg_h + 6), 2, GOLD if full else GREY, align="right" if right else "left")

    def draw_hud(self, surface, player, enemy):
        self.anim_counter += 1
        self.player_hp_display += (player.health - self.player_hp_display) * 0.06
        self.enemy_hp_display += (enemy.health - self.enemy_hp_display) * 0.06

        self.draw_side(surface, player, self.player_hp_display, False)
        self.draw_side(surface, enemy, self.enemy_hp_display, True)

        # center emblem
        draw_text(surface, "VS", (SCREEN_WIDTH // 2, BAR_TOP - 2), 4, GOLD, align="center")
        diff = DIFFICULTIES.get(self.difficulty)
        if diff:
            draw_text(surface, self.difficulty, (SCREEN_WIDTH // 2, BAR_TOP + 34), 2, diff["color"], align="center")

        # ULTI banner
        if self.ulti_banner:
            text, color, frames = self.ulti_banner
            y = 118 - max(0, frames - 60) * 5
            draw_text(surface, text, (SCREEN_WIDTH // 2, y), 4, color, align="center")
            self.ulti_banner = (text, color, frames - 1) if frames > 1 else None

        # READY? / FIGHT!
        if self.fight_banner_timer > 0:
            self.fight_banner_timer -= 1
            if self.fight_banner_timer > 45:
                draw_title(surface, "READY?", SCREEN_WIDTH // 2, 190, 10, top=CREAM, bottom=GOLD)
            else:
                draw_title(surface, "FIGHT!", SCREEN_WIDTH // 2, 190, 12, top=(255, 90, 60), bottom=RED)

    def draw_ko(self, surface, ko_timer):
        """Big K.O. stamp while the KO / victory animations play."""
        if ko_timer > 0 and (ko_timer > 90 or (ko_timer // 10) % 2 == 0):
            draw_title(surface, "K.O.", SCREEN_WIDTH // 2, 180, 16, top=(255, 90, 60), bottom=RED)

    # ------------------------------------------------------------------ overlays
    def menu_buttons(self, surface, options, selected_index, top, accent=RED):
        rects = []
        for i, opt in enumerate(options):
            rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, top + i * 58, 300, 46)
            rects.append(rect)
            selected = i == selected_index
            pygame.draw.rect(surface, (70, 20, 30) if selected else (26, 20, 40), rect)
            pygame.draw.rect(surface, accent if selected else (70, 64, 96), rect, 2)
            if selected and (self.anim_counter // 15) % 2 == 0:
                draw_text(surface, ">", (rect.left + 14, rect.top + 13), 3, GOLD)
            draw_text(surface, opt, (rect.centerx, rect.top + 13), 3, GOLD if selected else GREY, align="center")
        return rects

    def draw_pause_overlay(self, surface, selected_index=0):
        self.anim_counter += 1
        dim(surface, 170)
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 190, 400, 380)
        draw_panel(surface, panel)
        draw_title(surface, "PAUSE", SCREEN_WIDTH // 2, panel.top + 26, 7)
        return self.menu_buttons(surface, PAUSE_OPTIONS, selected_index, panel.top + 120)

    def draw_end_game_overlay(self, surface, is_victory, selected_index=0, winner=None):
        self.anim_counter += 1
        dim(surface, 170)
        panel = pygame.Rect(SCREEN_WIDTH // 2 - 260, SCREEN_HEIGHT // 2 - 210, 520, 420)
        accent = GREEN if is_victory else RED
        draw_panel(surface, panel, border=accent)
        if is_victory:
            draw_title(surface, "YOU WIN!", SCREEN_WIDTH // 2, panel.top + 24, 8, top=(170, 255, 150), bottom=GREEN)
        else:
            draw_title(surface, "YOU LOSE", SCREEN_WIDTH // 2, panel.top + 24, 8, top=(255, 120, 100), bottom=RED)

        if winner is not None and winner.assets:
            frame = pygame.Rect(SCREEN_WIDTH // 2 - 45, panel.top + 100, 90, 102)
            pygame.draw.rect(surface, INK, frame.inflate(8, 8))
            pygame.draw.rect(surface, GOLD, frame.inflate(4, 4), 2)
            surface.blit(pygame.transform.scale(winner.assets.portrait, frame.size), frame.topleft)
            draw_text(surface, f"{winner.name} MENANG!", (SCREEN_WIDTH // 2, frame.bottom + 16), 3, GOLD, align="center")

        return self.menu_buttons(surface, ["PLAY AGAIN", "MAIN MENU"], selected_index, panel.bottom - 128, accent)
