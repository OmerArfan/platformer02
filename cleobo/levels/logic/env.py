import pygame
import math
import cleobo.data.manage_data as manage_data

"""
The purpose of this levels submodule is to store different functions of the game where the situation of the game may be affected the most.
"""

def draw_portal(screen, img, portal, player):
    bobbing_offset = math.sin(pygame.time.get_ticks() * 0.005) * 5
    screen.blit(img, (portal.x - player.camera_x, portal.y + bobbing_offset - player.camera_y))

def handle_teleports(screen, teleporters, player):
    for teleporter in teleporters:
        # Draw the entry rectangle
        draw_portal(screen, manage_data.assets['teleport'], teleporter['entry'], player)
        # Draw the exit rectangle
        draw_portal(screen, manage_data.assets['teleport_exit'], teleporter['exit'], player)

        # Check if the player collides with the entry rectangle
        if player.rect.colliderect(teleporter["entry"]):
            # Teleport the player to the exit rectangle
            if not manage_data.is_mute:
                manage_data.sounds['warp'].play()
            player.rect.x, player.rect.y = teleporter['exit'].x, teleporter['exit'].y
    
    return player