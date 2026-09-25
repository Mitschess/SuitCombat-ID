"""Built-in 5x7 bitmap font + retro UI drawing helpers (panels, bars) shared by every screen."""
import pygame

GLYPHS = {
    "A": ".###." "#...#" "#...#" "#####" "#...#" "#...#" "#...#", "B": "####.#...##...#####.#...##...#####.",
    "C": ".###.#...##....#....#....#...#.###.", "D": "####.#...##...##...##...##...#####.",
    "E": "######....#....####.#....#....#####", "F": "######....#....####.#....#....#....",
    "G": ".###.#...##....#.####...##...#.####", "H": "#...##...##...#######...##...##...#",
    "I": ".###...#....#....#....#....#...###.", "J": "..###...#....#....#.#..#.#..#..##..",
    "K": "#...##..#.#.#..##...#.#..#..#.#...#", "L": "#....#....#....#....#....#....#####",
    "M": "#...###.###.#.##.#.##...##...##...#", "N": "#...###..##.#.##..###...##...##...#",
    "O": ".###.#...##...##...##...##...#.###.", "P": "####.#...##...#####.#....#....#....",
    "Q": ".###.#...##...##...##.#.##..#..##.#", "R": "####.#...##...#####.#.#..#..#.#...#",
    "S": ".#####....#.....###.....#....#####.", "T": "#####..#....#....#....#....#....#..",
    "U": "#...##...##...##...##...##...#.###.", "V": "#...##...##...##...##...#.#.#...#..",
    "W": "#...#" "#...#" "#...#" "#.#.#" "#.#.#" "#.#.#" ".#.#.", "X": "#...##...#.#.#...#...#.#.#...##...#",
    "Y": "#...##...#.#.#...#....#....#....#..", "Z": "#####....#...#...#...#...#....#####",
    "0": ".###.#...##..###.#.###..##...#.###.", "1": "..#...##....#....#....#....#...###.",
    "2": ".###.#...#....#...#...#...#...#####", "3": "####.....#....#.###.....#....#####.",
    "4": "...#...##..#.#.#..#.#####...#....#.", "5": "######....####.....#....##...#.###.",
    "6": ".###.#....#....####.#...##...#.###.", "7": "#####....#...#...#...#....#....#...",
    "8": ".###.#...##...#.###.#...##...#.###.", "9": ".###.#...##...#.####....#....#.###.",
    " ": "." * 35, "!": "..#....#....#....#....#.........#..",
    "?": ".###.#...#....#...#...#.........#..", ".": "." * 32 + "#..",
    ",": "." * 27 + "#...#...", ":": "....." "..#.." "....." "....." "....." "..#.." ".....",
    "-": "....." "....." "....." ".###." "....." "....." ".....", "+": ".......#....#..#####..#....#.......",
    "/": "....#....#...#...#...#...#....#....", "'": "..#.." "..#.." + "." * 25,
    "(": "...#...#...#....#....#.....#.....#.", ")": ".#.....#.....#....#....#...#...#...",
    "[": ".###..#....#....#....#....#....###.", "]": ".###....#....#....#....#....#..###.",
    "<": "...#...#...#...#.....#.....#.....#.", ">": ".#.....#.....#.....#...#...#...#...",
    "%": "##..###..#...#...#...#...#..###..##", "=": "..........#####.....#####..........",
    "_": "." * 30 + "#####", "*": ".....#.#.#.###.#####.###.#.#.#.....",
    "#": ".#.#.#####.#.#..#.#..#.#.#####.#.#.", "&": ".##..#..#.#.#...#...#.#.##..#..##.#",
}

# Retro arcade palette
GOLD = (240, 190, 60)
GOLD_DARK = (150, 96, 20)
CREAM = (250, 240, 214)
RED = (214, 40, 46)
RED_DARK = (110, 14, 22)
INK = (10, 8, 16)
PANEL = (20, 16, 34)
GREY = (140, 136, 160)
GREEN = (80, 220, 90)

_cache = {}


def _glyph(ch, color, scale):
    key = (ch, color, scale)
    if key not in _cache:
        bits = GLYPHS.get(ch) or GLYPHS["?"]
        bits = bits.ljust(35, ".")
        surf = pygame.Surface((5 * scale, 7 * scale), pygame.SRCALPHA)
        for i, b in enumerate(bits[:35]):
            if b == "#":
                surf.fill(color, ((i % 5) * scale, (i // 5) * scale, scale, scale))
        _cache[key] = surf
    return _cache[key]


def render(text, scale, color):
    text = str(text).upper().replace("—", "-")
    surf = pygame.Surface((max(1, len(text) * 6 * scale - scale), 7 * scale), pygame.SRCALPHA)
    for i, ch in enumerate(text):
        surf.blit(_glyph(ch, tuple(color[:3]), scale), (i * 6 * scale, 0))
    return surf


def text_size(text, scale):
    return max(1, len(str(text)) * 6 * scale - scale), 7 * scale


def draw_text(surface, text, pos, scale=2, color=CREAM, align="left", outline=INK, shadow=True):
    """Draws pixel text with a 1-pixel outline and drop shadow. pos is the anchor for `align`."""
    main = render(text, scale, color)
    w, h = main.get_size()
    x, y = pos
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w
    if outline or shadow:
        edge = render(text, scale, outline or INK)
        if shadow:
            surface.blit(edge, (x + scale, y + scale * 2))
        if outline:
            for dx, dy in ((-scale, 0), (scale, 0), (0, -scale), (0, scale)):
                surface.blit(edge, (x + dx, y + dy))
    surface.blit(main, (x, y))
    return pygame.Rect(x, y, w, h)


def draw_title(surface, text, center_x, y, scale, top=GOLD, bottom=(230, 110, 30)):
    """Big two-tone arcade title (gold fading to orange) with a thick outline."""
    w, h = text_size(text, scale)
    x = center_x - w // 2
    edge = render(text, scale, INK)
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2, 3, 4):
            surface.blit(edge, (x + dx * scale // 2, y + dy * scale // 2))
    upper = render(text, scale, top)
    lower = render(text, scale, bottom)
    surface.blit(upper, (x, y))
    surface.blit(lower, (x, y + h // 2), pygame.Rect(0, h // 2, w, h - h // 2))
    return pygame.Rect(x, y, w, h)


def draw_panel(surface, rect, border=GOLD, fill=PANEL, alpha=235, thick=3):
    """Pixel panel with notched corners, gold border and an inner dark line."""
    rect = pygame.Rect(rect)
    body = pygame.Surface(rect.size, pygame.SRCALPHA)
    body.fill((*fill, alpha))
    c = thick * 2
    for (cx, cy) in ((0, 0), (rect.w - c, 0), (0, rect.h - c), (rect.w - c, rect.h - c)):
        body.fill((0, 0, 0, 0), (cx, cy, c, c))
    surface.blit(body, rect.topleft)
    x, y, w, h = rect
    pygame.draw.rect(surface, INK, (x + c, y - 1, w - 2 * c, thick + 2))
    pygame.draw.rect(surface, INK, (x + c, y + h - thick - 1, w - 2 * c, thick + 2))
    pygame.draw.rect(surface, INK, (x - 1, y + c, thick + 2, h - 2 * c))
    pygame.draw.rect(surface, INK, (x + w - thick - 1, y + c, thick + 2, h - 2 * c))
    pygame.draw.rect(surface, border, (x + c, y, w - 2 * c, thick))
    pygame.draw.rect(surface, border, (x + c, y + h - thick, w - 2 * c, thick))
    pygame.draw.rect(surface, border, (x, y + c, thick, h - 2 * c))
    pygame.draw.rect(surface, border, (x + w - thick, y + c, thick, h - 2 * c))
    for (cx, cy) in ((x + thick, y + thick), (x + w - c, y + thick), (x + thick, y + h - c), (x + w - c, y + h - c)):
        pygame.draw.rect(surface, border, (cx, cy, thick, thick))
    return rect


def draw_bar(surface, rect, ratio, color, back=(46, 10, 16), trail_ratio=None, trail_color=(255, 150, 40),
             right_to_left=False):
    """Beveled pixel bar (health / meter)."""
    x, y, w, h = rect
    pygame.draw.rect(surface, INK, (x - 3, y - 3, w + 6, h + 6))
    pygame.draw.rect(surface, GOLD_DARK, (x - 2, y - 2, w + 4, h + 4))
    pygame.draw.rect(surface, back, (x, y, w, h))

    def fill(r, col):
        fw = int(w * max(0.0, min(1.0, r)))
        if fw <= 0:
            return
        fx = x + w - fw if right_to_left else x
        pygame.draw.rect(surface, col, (fx, y, fw, h))
        light = tuple(min(255, c + 70) for c in col)
        dark = tuple(int(c * 0.6) for c in col)
        pygame.draw.rect(surface, light, (fx, y, fw, max(2, h // 5)))
        pygame.draw.rect(surface, dark, (fx, y + h - max(2, h // 5), fw, max(2, h // 5)))

    if trail_ratio is not None:
        fill(trail_ratio, trail_color)
    fill(ratio, color)
    for sx in range(x + 12, x + w, 12):   # segment ticks
        pygame.draw.line(surface, (0, 0, 0), (sx, y + h - 3), (sx, y + h - 1))


def dim(surface, alpha=150, color=(6, 4, 12)):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((*color, alpha))
    surface.blit(overlay, (0, 0))


class PixelFont:
    """Drop-in for pygame.font.Font.render() so older code (floating damage text) uses the pixel font."""

    def __init__(self, scale):
        self.scale = scale

    def render(self, text, antialias=False, color=CREAM, background=None):
        return render(text, self.scale, color)
