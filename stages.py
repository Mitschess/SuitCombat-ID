import os
import json
import pygame
from sprites import ASSETS_DIR, load_image

BG_DIR = os.path.join(ASSETS_DIR, "backgrounds")


class Stage:
    def __init__(self, stage_id, name, file):
        self.id = stage_id
        self.name = name
        self.path = os.path.join(BG_DIR, file)
        self._thumbs = {}

    @property
    def image(self):
        return load_image(self.path)

    def thumbnail(self, size):
        if size not in self._thumbs:
            self._thumbs[size] = pygame.transform.scale(self.image, size)
        return self._thumbs[size]


def load_stages():
    """Stages listed in assets/backgrounds/stages.json (made by generate_stages.py)."""
    stages = []
    index = os.path.join(BG_DIR, "stages.json")
    if os.path.exists(index):
        with open(index) as f:
            for s in json.load(f):
                if os.path.exists(os.path.join(BG_DIR, s["file"])):
                    stages.append(Stage(s["id"], s["name"], s["file"]))
    if not stages and os.path.exists(os.path.join(BG_DIR, "arena_temple.png")):
        stages.append(Stage("temple", "ARENA KUIL", "arena_temple.png"))
    return stages
