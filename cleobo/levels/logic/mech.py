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
            bx = button.get('x', 0) - getattr(player, 'camera_x', 0)
            by = button.get('y', 0) - getattr(player, 'camera_y', 0)
            screen.blit(manage_data.assets[defined_state], (bx, by))
            # Button collision
            button_rect = pygame.FRect(button['x'], button['y'], 80, 80)
            if player.rect.colliderect(button_rect): # Have to hard code this for now.
                if not manage_data.is_mute:
                    manage_data.sounds['collect'].play()
                return defined_state
    return current_state

def handle_speedsters(screen, speedsters, player_rect, camera_x, camera_y, stamina):
        for x, y, r, color in speedsters:
            # Draw the button as a circle
            if not stamina:
                pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        for speedster in speedsters:
            speedster_x, speedster_y, speedster_radius, _ = speedster

        # Find the closest point on the player's rectangle to the button's center
            closest_x = max(player_rect.left, min(speedster_x, player_rect.right))
            closest_y = max(player_rect.top, min(speedster_y, player_rect.bottom))

            # Calculate the distance between the closest point and the button's center
            dx = closest_x - speedster_x
            dy = closest_y - speedster_y
            distance = (dx**2 + dy**2)**0.5

            # If distance is less than radius, stronger gravity activated
            if distance < speedster_radius and not stamina:
                if not manage_data.is_mute:
                    manage_data.sounds['button'].play()
                return True
        return False

def handle_light_blocks(screen, lights, on_ground, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, lights_off, SCREEN_WIDTH, SCREEN_HEIGHT, is_mute, button_sound):
  
  for lights in lights:    

    if not lights_off:
        light_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        light_mask.fill((0, 0, 0, 255)) 
        spotlight_center = (player_x + img_width // 2 - camera_x, player_y + img_width // 2 - camera_y)
        radius = 320 
        pygame.draw.circle(light_mask, (0, 0, 0, 0), spotlight_center, radius)
        screen.blit(light_mask, (0, 0))

    else:

        pygame.draw.rect(screen, (104, 102, 204), (lights['button'].x - camera_x, lights['button'].y - camera_y, lights['button'].width, lights['button'].height))
        pygame.draw.rect(screen, (104, 102, 204), (lights['block'].x - camera_x, lights['block'].y - camera_y, lights['block'].width, lights['block'].height))

        if player_rect.colliderect(lights['block']):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= lights['block'].y:
                    player_y = lights['block'].y - img_height
                    velocity_y = 0
                    on_ground = True

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > lights['block'].x and player_x < lights['block'].x + lights['block'].width:
                    if player_x < lights['block'].x:  # Colliding with the left side of the block
                        player_x = lights['block'].x - img_width
                    elif player_x + img_width > lights['block'].x + lights['block'].width:  # Colliding with the right side
                        player_x = lights['block'].x + lights['block'].width
    
    if player_rect.colliderect(lights['button']):
            if not is_mute and lights_off:
                button_sound.play()
            lights_off = False
    
    return player_x, player_y, velocity_y, on_ground, player_rect, lights_off