import pygame

# Screen Settings
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
FPS = 60
TITLE = "Suit Combat ID"

# Colors (Vibrant Cyber/Fighting Palette)
COLOR_BG_DARK = (15, 17, 26)
COLOR_BG_GRADIENT_TOP = (25, 20, 45)
COLOR_BG_GRADIENT_BOTTOM = (10, 10, 20)

COLOR_GROUND = (35, 39, 58)
COLOR_GROUND_LINE = (0, 229, 255)  # Cyan neon accent
COLOR_GROUND_GRID = (30, 45, 75)

COLOR_WHITE = (245, 245, 250)
COLOR_BLACK = (10, 10, 15)
COLOR_GRAY = (120, 125, 140)
COLOR_DARK_GRAY = (40, 44, 52)

# Fighter Colors (Default Mockup Colors)
COLOR_PLAYER = (0, 180, 255)       # Cyber Blue
COLOR_PLAYER_ACCENT = (100, 220, 255)
COLOR_ENEMY = (255, 50, 80)         # Cyber Red/Crimson
COLOR_ENEMY_ACCENT = (255, 120, 140)

# FX Colors
COLOR_PROJECTILE_PLAYER = (0, 240, 255)
COLOR_PROJECTILE_ENEMY = (255, 80, 50)
COLOR_HEALTH_PLAYER = (0, 230, 118)
COLOR_HEALTH_ENEMY = (255, 61, 0)
COLOR_HEALTH_BG = (40, 40, 50)
COLOR_HEALTH_BORDER = (200, 200, 220)

# Menu Colors
COLOR_MENU_TITLE = (0, 229, 255)
COLOR_MENU_SUBTITLE = (255, 179, 0)
COLOR_BUTTON_NORMAL = (30, 35, 55)
COLOR_BUTTON_HOVER = (60, 70, 110)
COLOR_BUTTON_BORDER = (0, 229, 255)
COLOR_TEXT_SELECTED = (255, 255, 255)
COLOR_TEXT_NORMAL = (170, 180, 200)

# Arena & Physics
GROUND_Y = SCREEN_HEIGHT - 100
GRAVITY = 0.8

# Fighter Attributes
PLAYER_START_X = 200
PLAYER_START_Y = GROUND_Y - 90
ENEMY_START_X = SCREEN_WIDTH - 200 - 60
ENEMY_START_Y = GROUND_Y - 90

FIGHTER_WIDTH = 60
FIGHTER_HEIGHT = 90
FIGHTER_CROUCH_HEIGHT = 55
FIGHTER_SPEED = 6.0
JUMP_FORCE = -15.0

# Combat Values
MAX_HEALTH = 100
MELEE_DAMAGE = 10
MELEE_RANGE = 75
MELEE_COOLDOWN = 25  # frames (~0.4s)
MELEE_DURATION = 10  # frames attack hitbox stays active

RANGED_DAMAGE = 15
RANGED_SPEED = 11.0
RANGED_COOLDOWN = 40  # frames (~0.65s)
PROJECTILE_SIZE = 16

BLOCK_DAMAGE_REDUCTION = 0.75  # 75% damage blocked

# Game States
STATE_MENU = "MENU"
STATE_HOW_TO_PLAY = "HOW_TO_PLAY"
STATE_PLAYING = "PLAYING"
STATE_PAUSED = "PAUSED"
STATE_VICTORY = "VICTORY"
STATE_DEFEAT = "DEFEAT"

# Ultimate (ULTI) meter
ULTI_MAX = 100.0
ULTI_GAIN_DEAL = 1.2      # meter gained per point of damage dealt
ULTI_GAIN_TAKE = 0.8      # meter gained per point of damage taken
ULTI_GAIN_PASSIVE = 0.02  # meter gained every frame
ULTI_CAST_FRAMES = 40     # caster is locked in the ulti pose this long
KO_DELAY_FRAMES = 120     # KO / victory animation time before the result screen

STATE_CHAR_SELECT = "CHAR_SELECT"
STATE_STAGE_SELECT = "STAGE_SELECT"

# CPU difficulty presets
DIFFICULTY_ORDER = ["EASY", "MEDIUM", "HARD"]
DIFFICULTIES = {
    "EASY": dict(speed=0.7, damage=0.75, attack_chance=0.04, melee_block=0.15, proj_block=0.2, proj_jump=0.15,
                 ranged_far=0.015, ranged_mid=0.008, ulti_use=0.004, ulti_dodge=0.3, meter_gain=0.7,
                 pickup_greed=0.3, color=(80, 220, 90), desc="CPU LAMBAT & JARANG MENANGKIS"),
    "MEDIUM": dict(speed=0.9, damage=1.0, attack_chance=0.2, melee_block=0.4, proj_block=0.5, proj_jump=0.3,
                   ranged_far=0.04, ranged_mid=0.02, ulti_use=0.01, ulti_dodge=0.65, meter_gain=1.0,
                   pickup_greed=0.6, color=(240, 190, 60), desc="LAWAN SEIMBANG"),
    "HARD": dict(speed=1.05, damage=1.25, attack_chance=1.0, melee_block=0.65, proj_block=0.6, proj_jump=0.35,
                 ranged_far=0.06, ranged_mid=0.035, ulti_use=0.025, ulti_dodge=0.9, meter_gain=1.3,
                 pickup_greed=0.9, color=(230, 50, 50), desc="CPU CEPAT, KUAT & PINTAR MENGHINDAR"),
}
STATE_SETTINGS = "SETTINGS"

# Health power-up (MBG food tray)
HEAL_AMOUNT = MAX_HEALTH / 3   # a tray restores 1/3 of the health bar
PICKUP_SPAWN_MIN = 480      # frames between spawns (8 - 13 s)
PICKUP_SPAWN_MAX = 780
PICKUP_LIFETIME = 540       # frames it stays on the floor before vanishing
