import os
import pygame

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
GENERIC_SOUNDS = ["move", "select", "back", "punch", "kick", "hit", "block", "shoot", "jump", "ko",
                  "ready", "fight", "ulti_ready", "ulti_cast", "victory", "defeat", "heal"]
SAME = object()   # "fall back to the generic sound with the same key"


class SoundManager:
    """Sound effects, per-character voices, background music and the character-select ulti preview.
    Volumes come from the shared config dict (master / music / sfx, 0.0 - 1.0)."""

    def __init__(self, config):
        self.config = config
        self.sounds = {}
        self.enabled = True
        self.current_music = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.set_num_channels(24)
            pygame.mixer.set_reserved(1)
            self.preview_channel = pygame.mixer.Channel(0)   # character-select ulti preview
        except pygame.error as e:
            print(f"Audio disabled: {e}")
            self.enabled = False
            self.preview_channel = None
        self.load_sounds()

    def load_sounds(self):
        if not self.enabled:
            return
        sounds_dir = os.path.join(ASSETS_DIR, "sounds")
        for key in GENERIC_SOUNDS:
            path = os.path.join(sounds_dir, f"{key}.wav")
            if os.path.exists(path):
                try:
                    self.sounds[key] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"Could not load sound {path}: {e}")

    # ------------------------------------------------------------------ volume
    def sfx_volume(self):
        return self.config["sfx"] * self.config["master"]

    def music_volume(self):
        return self.config["music"] * self.config["master"]

    def apply_volumes(self):
        if not self.enabled:
            return
        pygame.mixer.music.set_volume(self.music_volume())

    # ------------------------------------------------------------------ effects
    def _play(self, sound):
        try:
            sound.set_volume(self.sfx_volume())
            sound.play()
        except Exception:
            pass

    def play(self, key):
        if self.enabled and key in self.sounds:
            self._play(self.sounds[key])

    def play_character(self, assets, key, fallback=SAME):
        """Plays the character's own sound (assets/characters/<Name>/sounds/<key>.wav) if it exists,
        otherwise the generic `fallback` sound (same key by default, None = no fallback)."""
        if not self.enabled:
            return
        if assets and key in assets.sounds:
            self._play(assets.sounds[key])
        elif fallback is not None:
            self.play(key if fallback is SAME else fallback)

    def play_fighter(self, fighter, key, fallback=SAME):
        self.play_character(getattr(fighter, "assets", None), key, fallback)

    def play_preview(self, sound):
        """Plays one sound on the preview channel, cutting off the previous one (no looping)."""
        if not self.enabled or not self.preview_channel:
            return
        self.preview_channel.stop()
        if sound:
            sound.set_volume(self.sfx_volume())
            self.preview_channel.play(sound)

    def stop_preview(self):
        if self.enabled and self.preview_channel:
            self.preview_channel.stop()

    # ------------------------------------------------------------------ music
    def play_music(self, name):
        """Switches the looping background track ('menu', 'battle' or None). Safe to call every frame."""
        if not self.enabled or name == self.current_music:
            return
        self.current_music = name
        if name is None:
            pygame.mixer.music.fadeout(600)
            return
        path = os.path.join(ASSETS_DIR, "music", f"{name}.wav")
        if not os.path.exists(path):
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume())
            pygame.mixer.music.play(-1, fade_ms=500)
        except pygame.error as e:
            print(f"Could not play music {path}: {e}")
