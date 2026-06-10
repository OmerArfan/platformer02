import pygame
import cleobo.data.manage_data as manage_data

"""
The purpose of this levels submodule is to store the mechanics altering features in one place.
It is pretty much just buttons for now, as you need to activate them by touching them so that you can do things you normally cannot do!
"""

def handle_buttons(screen, buttons, player, current_state, defined_state):
    # Draw only if the state isn't already active
    if current_state != defined_state: 
        for button in buttons:
            # Draw using camera-relative coordinates so buttons appear on screen
            bx = button.get('x', 0) - player.camera_x
            by = button.get('y', 0) - player.camera_y
            screen.blit(manage_data.assets[defined_state], (bx, by))
            # Button collision
            button_rect = pygame.FRect(button['x'], button['y'], 80, 80)
            if player.rect.colliderect(button_rect): # Have to hard code this for now.
                if not manage_data.is_mute:
                    manage_data.sounds['collect'].play()
                return defined_state
    return current_state

def handle_light_blocks(screen, lights, player):
  if lights:
    for lights in lights:    
        if not player.lights_on:
            light_mask = pygame.Surface((manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT), pygame.SRCALPHA)
            light_mask.fill((0, 0, 0, 255)) 
            spotlight_center = (player.rect.x + player.rect.width // 2 - player.camera_x, player.rect.y + player.rect.width // 2 - player.camera_y)
            radius = 320 
            pygame.draw.circle(light_mask, (0, 0, 0, 0), spotlight_center, radius)
            screen.blit(light_mask, (0, 0))

        else:

            pygame.draw.rect(screen, (104, 102, 204), (lights['block'].x - player.camera_x, lights['block'].y - player.camera_y, lights['block'].width, lights['block'].height))
            # Draw using camera-relative coordinates so buttons appear on screen
            bx = lights['button'].x - player.camera_x
            by = lights['button'].y - player.camera_y
            screen.blit(manage_data.assets['light'], (bx, by))

            if player.rect.colliderect(lights['button']):
                if not manage_data.is_mute and player.lights_on:
                    manage_data.sounds['collect'].play()
                    player.lights_on = False
            
            if player.rect.colliderect(lights['block']):
                # Falling onto a block
                if player.velocity_y > 0 and player.rect.y + player.rect.width - player.velocity_y <= lights['block'].y:
                    player.rect.y = lights['block'].x - player.rect.height
                    player.velocity_y = 0
                    player.on_ground = True

                # Horizontal collision (left or right side of the block)
                elif player.rect.x + player.rect.width > lights['block'].x and player.rect.x < lights['block'].x + lights['block'].width:
                    if player.rect.x < lights['block'].x:  # Colliding with the left side of the block
                        player.rect.x = lights['block'].x - player.rect.width
                    elif player.rect.x + player.rect.width > lights['block'].x + lights['block'].width:  # Colliding with the right side
                        player.rect.x = lights['block'].x + lights['block'].width

  return player