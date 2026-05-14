import pygame
import math

"""
The purpose of this levels submodule is to store different functions of the game where the situation of the game may be affected the most.
"""

def draw_portal(screen, img, portal, player):
    bobbing_offset = math.sin(pygame.time.get_ticks() * 0.005) * 5
    screen.blit(img, (portal.x - player.camera_x, portal.y + bobbing_offset - player.camera_y))
