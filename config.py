import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
DEFAULTS = {"master": 0.8, "music": 0.6, "sfx": 0.9, "fullscreen": False}


def load_config():
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH) as f:
            saved = json.load(f)
        for key in DEFAULTS:
            if key in saved and type(saved[key]) is type(DEFAULTS[key]):
                cfg[key] = saved[key]
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    except OSError as e:
        print(f"Could not save settings: {e}")
