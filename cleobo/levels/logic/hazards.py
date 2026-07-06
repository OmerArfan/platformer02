import pygame
import math
import copy
import cleobo.data.manage_data as manage_data

"""
The purpose of this levels submodule is to store different types of hazards in one place.
For now, only three main types of hazards exist in the game, but as the games progress and so does the engine, hopefully more will be added.
If you do have an idea for a hazard, do make sure to add it here without any hesitation, and hopefully, I will be able to check it out and test it.
"""

def point_in_triangle(px, py, a, b, c):
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    b1 = sign((px, py), a, b) < 0.0
    b2 = sign((px, py), b, c) < 0.0
    b3 = sign((px, py), c, a) < 0.0
    return b1 == b2 == b3

def check_spike_collisions(spikes, player):
    # Quick Rect check
    potential_spikes = []
    for spike in spikes:
        # We can use min/max on the tuples directly
        xs = [p[0] for p in spike]
        ys = [p[1] for p in spike]
        
        s_left = min(xs)
        s_top = min(ys)
        s_width = max(xs) - s_left
        s_height = max(ys) - s_top
        
        # Check if player rect touches the spike's bounding box
        if player.rect.colliderect(pygame.Rect(s_left, s_top, s_width, s_height)):
            potential_spikes.append(spike)

    # If no spikes are nearby, stop here!
    if not potential_spikes:
        return False

    # Precise point checking
    points = [
        (player.rect.centerx, player.rect.bottom), 
        (player.rect.left + 5, player.rect.bottom), 
        (player.rect.right - 5, player.rect.bottom),
        (player.rect.centerx, player.rect.top), 
        (player.rect.left + 5, player.rect.top), 
        (player.rect.right - 5, player.rect.top)
    ]

    for spike in potential_spikes:
        # Flatten the tuples for point_in_triangle function
        for pt in points:
            if point_in_triangle(pt[0], pt[1], spike[0], spike[1], spike[2]):
                return True 
    return False

def handle_cacti_spikes(screen, player, spikes):
    collision = False
    
    for spike in spikes:
        # Check if player has crossed the trigger threshold
        if not spike['activated'] and spike['cycle_complete']:
            if spike['axis'] == "'y'":
                spike_y = max([p[1] for p in spike['def_cord']])
                spike_x_min = min([p[0] for p in spike['def_cord']])
                spike_x_max = max([p[0] for p in spike['def_cord']])
                
                # Check if player is horizontally aligned with spike
                player_aligned = player.rect.x + player.rect.width >= spike_x_min and player.rect.x <= spike_x_max
                
                if spike['dir'] < 0:
                    if player.rect.bottom >= spike_y + spike['limit'] and player.rect.bottom < spike_y and player_aligned:
                        spike['activated'] = True
                        spike['cycle_complete'] = False
                
                else:  
                    if player.rect.top <= spike_y + spike['limit'] and player.rect.top > spike_y and player_aligned:
                        spike['activated'] = True
                        spike['cycle_complete'] = False
        
            elif spike['axis'] == "'x'":
                spike_x = max([p[0] for p in spike['def_cord']])  
                spike_y_min = min([p[1] for p in spike['def_cord']])  
                spike_y_max = max([p[1] for p in spike['def_cord']])  
                
                player_aligned = player.rect.y + player.rect.height >= spike_y_min and player.rect.y <= spike_y_max
                
                if spike['dir'] < 0:
                    if player.rect.right < spike_x and player.rect.right + spike_x > spike['limit'] and player_aligned: 
                        spike['activated'] = True
                        spike['cycle_complete'] = False
                else: 
                    if player.rect.left > spike_x and player.rect.left < spike_x + spike['limit'] and player_aligned:                
                        spike['activated'] = True
                        spike['cycle_complete'] = False
        
        # Only move if activated or still completing a cycle
        if spike['activated'] or not spike['cycle_complete']:
            spike['speed'] += spike['acc']
            new_cords = []
            for x, y in spike['cord']:
                if spike['axis'] == "'x'":
                    new_cords.append([x + spike['speed'], y])
                elif spike['axis'] == "'y'":
                    new_cords.append([x, y + spike['speed']])
            spike['cord'] = new_cords

            # Check if limit is reached
            xs = [p[0] for p in spike['cord']]
            ys = [p[1] for p in spike['cord']]
            def_xs = [p[0] for p in spike['def_cord']]
            def_ys = [p[1] for p in spike['def_cord']]

            has_reached_limit = False
            
            if spike['axis'] == "'x'":
                distance_traveled = max(xs) - max(def_xs) if spike['dir'] > 0 else min(xs) - min(def_xs)
                if abs(distance_traveled) >= abs(spike['limit']):
                    has_reached_limit = True

            elif spike['axis'] == "'y'":
                distance_traveled = max(ys) - max(def_ys) if spike['dir'] > 0 else min(ys) - min(def_ys)
                if abs(distance_traveled) >= abs(spike['limit']):
                    has_reached_limit = True

            if has_reached_limit:
                spike['cord'] = copy.deepcopy(spike['def_cord'])
                spike['activated'] = False
                spike['cycle_complete'] = True
                spike['speed'] = spike['init_speed']
        
        # Draw the spike
        pts = [(x - player.camera_x, y - player.camera_y) for x, y in spike['cord']]
        if len(pts) >= 3:
            pygame.draw.polygon(screen, (3, 104, 0), pts)
    
    # Collision detection (same as before)
        s_left = min([p[0] for p in spike['cord']])
        s_top = min([p[1] for p in spike['cord']])
        s_width = max([p[0] for p in spike['cord']]) - s_left
        s_height = max([p[1] for p in spike['cord']]) - s_top
        
        if player.rect.colliderect(pygame.Rect(s_left, s_top, s_width, s_height)):
            points = [
                (player.rect.centerx, player.rect.bottom), 
                (player.rect.left + 5, player.rect.bottom), 
                (player.rect.right - 5, player.rect.bottom),
                (player.rect.centerx, player.rect.top), 
                (player.rect.left + 5, player.rect.top), 
                (player.rect.right - 5, player.rect.top)
            ]
            
            for pt in points:
                if point_in_triangle(pt[0], pt[1], spike['cord'][0], spike['cord'][1], spike['cord'][2]):
                    collision = True
                    break
    
    return collision

def draw_spikes(screen, spikes, player):
    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - player.camera_x, y - player.camera_y) for x, y in spike])

def pre_render_saws(saw_img, saws):
    if not saws:
        return
    # Extract unique radii (handle both dict key names 'radius' or 'r')
    unique_radii = (s['radius'] for s in saws)
    for r in unique_radii:
        if (r, 0) in manage_data.saw_cache:
            continue
        size = int(r * 2.5)
        scaled = pygame.transform.scale(saw_img, (size, size))
        for angle in range(0, 360, 5):
            manage_data.saw_cache[(r, angle)] = pygame.transform.rotate(scaled, angle)
            
def handle_all_saws(screen, saws, player, blocks):
    angle = (pygame.time.get_ticks() // 3) % 360
    angle_key = (angle // 5) * 5
    collision = False

    for saw in saws:
        saw_type = saw.get('type', 'static')

        # --- 1. UPDATE POSITION ---
        if saw_type == "'rotating'":
            saw['angle'] = (saw['angle'] + saw.get('speed', 2)) % 360
            rad = math.radians(saw['angle'])
            orbit_center = blocks[saw['block']].center
            saw['x'] = orbit_center[0] + saw['orbit_radius'] * math.cos(rad)
            saw['y'] = orbit_center[1] + saw['orbit_radius'] * math.sin(rad)
            
        elif saw_type == "'moving_y'":
            saw['y'] += saw['speed']
            if saw['y'] > saw['max'] or saw['y'] < saw['min']:
                saw['speed'] *= -1
                
        elif saw_type == "'moving_x'":
            saw['x'] += saw['speed']
            if saw['x'] > saw['max'] or saw['x'] < saw['min']:
                saw['speed'] *= -1
                
        elif saw_type == "'rushing_x'":
            if saw['dir'] > 0:
                saw['x'] += saw['speed']
                if saw['x'] > saw['max']:
                    saw['x'] = saw['min']
            else:
                saw['x'] -= saw['speed']
                if saw['x'] < saw['min']:
                    saw['x'] = saw['max']
        
        elif saw_type == "'rushing_y'":
            if saw['dir'] > 0:
                saw['y'] += saw['speed']
                if saw['y'] > saw['max']:
                    saw['y'] = saw['min']
            else:
                saw['y'] -= saw['speed']
                if saw['y'] < saw['min']:
                    saw['y'] = saw['max']

        r = saw.get('radius') or saw.get('r')
        cache_key = (r, angle_key)

        if cache_key in manage_data.saw_cache:
            img = manage_data.saw_cache[cache_key]
            
            curr_x = saw.get('x')
            curr_y = saw.get('y')
            
            if curr_x is not None and curr_y is not None:
                pos = (curr_x - player.camera_x, curr_y - player.camera_y) 
                rect = img.get_rect(center=pos)
                screen.blit(img, rect)

                closest_x = max(player.rect.left, min(curr_x, player.rect.right))
                closest_y = max(player.rect.top, min(curr_y, player.rect.bottom))
                if ((closest_x - curr_x)**2 + (closest_y - curr_y)**2) < r**2:
                    collision = True

    return collision

def handle_lasers(screen, lasers, player):
    for laser in lasers:
        pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - player.camera_x), int(laser.y - player.camera_y), laser.width, laser.height))
        # Check if the player collides with the laser
        if player.rect.colliderect(laser):
            return True
    return False