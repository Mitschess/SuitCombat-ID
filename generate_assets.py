import os
import pygame

def generate_sprites():
    pygame.init()
    
    # 1. Player Sprite (Cyan / Blue Fighting Avatar)
    p_dir = os.path.join(os.path.dirname(__file__), "assets", "characters", "player")
    os.makedirs(p_dir, exist_ok=True)
    p_surf = pygame.Surface((60, 90), pygame.SRCALPHA)
    
    # Body
    pygame.draw.rect(p_surf, (0, 180, 255), (5, 25, 50, 60), border_radius=8)
    pygame.draw.rect(p_surf, (100, 230, 255), (5, 25, 50, 60), width=2, border_radius=8)
    # Belt / Details
    pygame.draw.rect(p_surf, (255, 200, 0), (10, 52, 40, 6))
    # Head
    pygame.draw.circle(p_surf, (0, 180, 255), (30, 16), 16)
    pygame.draw.circle(p_surf, (100, 230, 255), (30, 16), 16, width=2)
    # Visor
    pygame.draw.circle(p_surf, (255, 255, 255), (36, 14), 4)
    pygame.image.save(p_surf, os.path.join(p_dir, "player.png"))

    # 2. Enemy Sprite (Crimson / Red Cyber Opponent Avatar)
    e_dir = os.path.join(os.path.dirname(__file__), "assets", "characters", "enemy")
    os.makedirs(e_dir, exist_ok=True)
    e_surf = pygame.Surface((60, 90), pygame.SRCALPHA)
    
    # Body
    pygame.draw.rect(e_surf, (255, 50, 80), (5, 25, 50, 60), border_radius=8)
    pygame.draw.rect(e_surf, (255, 140, 160), (5, 25, 50, 60), width=2, border_radius=8)
    # Belt / Details
    pygame.draw.rect(e_surf, (255, 200, 0), (10, 52, 40, 6))
    # Head
    pygame.draw.circle(e_surf, (255, 50, 80), (30, 16), 16)
    pygame.draw.circle(e_surf, (255, 140, 160), (30, 16), 16, width=2)
    # Visor
    pygame.draw.circle(e_surf, (255, 255, 255), (24, 14), 4)
    pygame.image.save(e_surf, os.path.join(e_dir, "enemy.png"))

    # Create empty folders for background, effects, music
    for folder in ["backgrounds", "effects", "music"]:
        os.makedirs(os.path.join(os.path.dirname(__file__), "assets", folder), exist_ok=True)

    print("Sprite assets generated successfully.")

if __name__ == "__main__":
    generate_sprites()
