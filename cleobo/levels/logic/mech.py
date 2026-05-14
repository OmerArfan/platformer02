import pygame
import cleobo.data.manage_data as manage_data

"""
The purpose of this levels submodule is to store the mechanics altering features in one place.
It is pretty much just buttons for now, as you need to activate them by touching them so that you can do things you normally cannot do!
"""

def handle_buttons(screen, buttons, player, active_state):
    for x, y, r, color in buttons:
        # Draw only if the state isn't already active
        if not active_state:
            pygame.draw.circle(screen, color, (int(x - player.camera_x), int(y - player.camera_y)), int(r))

            # Circle-to-AABB Collision Math
            closest_x = max(player.rect.left, min(x, player.rect.right))
            closest_y = max(player.rect.top, min(y, player.rect.bottom))
            distance = ((closest_x - x)**2 + (closest_y - y)**2)**0.5

            if distance < r:
                if not manage_data.is_mute:
                    manage_data.sounds['button'].play()
                return True
    return active_state

def handling_gravity_weakers(screen, gravity_weakers, player_rect, camera_x, camera_y, weak_grav):
        for x, y, r, color in gravity_weakers:
            # Draw the button as a circle
            if not weak_grav:
                pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        for gravity_stronger in gravity_weakers:
            gravity_stronger_x, gravity_stronger_y, gravity_stronger_radius, _ = gravity_stronger

        # Find the closest point on the player's rectangle to the button's center
            closest_x = max(player_rect.left, min(gravity_stronger_x, player_rect.right))
            closest_y = max(player_rect.top, min(gravity_stronger_y, player_rect.bottom))

            # Calculate the distance between the closest point and the button's center
            dx = closest_x - gravity_stronger_x
            dy = closest_y - gravity_stronger_y
            distance = (dx**2 + dy**2)**0.5

            # If distance is less than radius, stronger gravity activated
            if distance < gravity_stronger_radius and not weak_grav:
                if not manage_data.is_mute:
                    manage_data.sounds['button'].play()
                return True
        return False

def handling_gravity_strongers(screen, gravity_strongers, player_rect, camera_x, camera_y, strong_grav):
        for x, y, r, color in gravity_strongers:
            # Draw the button as a circle
            if not strong_grav:
                pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        for gravity_stronger in gravity_strongers:
            gravity_stronger_x, gravity_stronger_y, gravity_stronger_radius, _ = gravity_stronger

        # Find the closest point on the player's rectangle to the button's center
            closest_x = max(player_rect.left, min(gravity_stronger_x, player_rect.right))
            closest_y = max(player_rect.top, min(gravity_stronger_y, player_rect.bottom))

            # Calculate the distance between the closest point and the button's center
            dx = closest_x - gravity_stronger_x
            dy = closest_y - gravity_stronger_y
            distance = (dx**2 + dy**2)**0.5

            # If distance is less than radius, stronger gravity activated
            if distance < gravity_stronger_radius and not strong_grav:
                if not manage_data.is_mute:
                    manage_data.sounds['button'].play()
                return True
        return False

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