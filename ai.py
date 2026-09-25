import random
import pygame
from settings import DIFFICULTIES

class EnemyAI:
    def __init__(self, difficulty="MEDIUM"):
        self.set_difficulty(difficulty)
        self.action_cooldown = 0
        self.reaction_delay = 0

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty if difficulty in DIFFICULTIES else "MEDIUM"
        self.p = DIFFICULTIES[self.difficulty]

    def update(self, enemy, player, projectiles, ulti_manager=None, pickups=None):
        """
        Executes AI decision tree based on PRD Section 12:
        - distance > 300 -> approach / ranged attack
        - 100 < distance <= 300 -> approach player
        - distance <= 100 -> melee attack / block / crouch
        """
        if enemy.is_dead or player.is_dead or enemy.ulti_cast_timer > 0:
            enemy.stop_moving()
            enemy.block(False)
            return None

        # Face towards player
        dist_x = player.x - enemy.x
        abs_dist = abs(dist_x)

        if dist_x > 0:
            enemy.facing_direction = 1
        else:
            enemy.facing_direction = -1

        spawn_proj = None

        # 0. Dodge incoming ultimates (left/right away from the drop point, or jump over the bull)
        hint = ulti_manager.threat_hint(enemy) if ulti_manager else None
        if hint:
            enemy.block(False)
            enemy.crouch(False)
            if hint == "jump":
                enemy.jump()
            elif hint == "left":
                enemy.move_left()
            else:
                enemy.move_right()
            return None

        # 0b. Hurt CPU walks over to grab a health tray
        target_x = pickups.cpu_target(enemy) if pickups else None
        if target_x is not None and abs(target_x - enemy.rect.centerx) > 20:
            enemy.block(False)
            enemy.crouch(False)
            if target_x < enemy.rect.centerx:
                enemy.move_left()
            else:
                enemy.move_right()
            return None

        # 1. Check incoming player ranged attacks to reactively block/jump
        incoming_proj = False
        for p in projectiles:
            if p.is_player_owner and p.alive:
                # If projectile is moving towards enemy
                if (p.direction == 1 and p.rect.x < enemy.rect.x) or (p.direction == -1 and p.rect.x > enemy.rect.x):
                    if abs(p.rect.x - enemy.rect.x) < 220:
                        incoming_proj = True
                        break

        if incoming_proj:
            # block / jump / ignore, depending on difficulty
            r = random.random()
            if r < self.p["proj_block"]:
                enemy.block(True)
                return None
            elif r < self.p["proj_block"] + self.p["proj_jump"]:
                enemy.block(False)
                enemy.jump()

        # Reset block if no threat
        enemy.block(False)

        # 2. Distance-Based AI Logic (PRD Section 12)
        if abs_dist > 300:
            # Very far away -> Approach player or use ranged attack
            if random.random() < self.p["ranged_far"] and enemy.ranged_cooldown == 0:
                spawn_proj = enemy.attack_ranged()
            else:
                if dist_x > 0:
                    enemy.move_right()
                else:
                    enemy.move_left()

        elif 100 < abs_dist <= 300:
            # Medium distance -> Move towards player, occasionally shoot or jump
            if random.random() < self.p["ranged_mid"] and enemy.ranged_cooldown == 0:
                spawn_proj = enemy.attack_ranged()
            else:
                if dist_x > 0:
                    enemy.move_right()
                else:
                    enemy.move_left()
                    
                # Small chance to jump randomly to close gap dynamically
                if random.random() < 0.015 and enemy.is_grounded:
                    enemy.jump()

        else:
            # Close distance (distance <= 100) -> Melee attack!
            enemy.stop_moving()
            
            # If player is actively attacking melee, CPU has chance to block
            if player.is_attacking_melee and random.random() < self.p["melee_block"]:
                enemy.block(True)
            else:
                enemy.block(False)
                # Execute melee attack
                if enemy.melee_cooldown == 0 and random.random() < self.p["attack_chance"]:
                    enemy.attack_melee()
                elif random.random() < 0.05:
                    # Crouch or maneuver
                    enemy.crouch(random.choice([True, False]))

        return spawn_proj
