import pygame
import math
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

def draw_spikes(screen, spikes, player):
    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - player.camera_x, y - player.camera_y) for x, y in spike])

def pre_render_saws(saw_img, saws):
    if not saws:
        return
    # Extract ONLY the unique radii from your saw tuples
    unique_radii = set(s[2] for s in saws)
    for r in unique_radii:
        if (r, 0) in manage_data.saw_cache:
            continue  # Skip if already cached
        size = int(r * 2.5)
        scaled = pygame.transform.scale(saw_img, (size, size))
        for angle in range(0, 360, 5):
            manage_data.saw_cache[(r, angle)] = pygame.transform.rotate(scaled, angle)

# 3. THE DRAW (Run this INSIDE the loop)
def draw_saws(screen, saws, player):
    angle = (pygame.time.get_ticks() // 3) % 360
    angle_key = (angle // 5) * 5
    
    for x, y, r in saws:
        cache_key = (r, angle_key)
        # Use the pre-rendered image
        if cache_key in manage_data.saw_cache:
            rotated_img = manage_data.saw_cache[cache_key]
            rect = rotated_img.get_rect(center=(x - player.camera_x, y - player.camera_y))
            screen.blit(rotated_img, rect)

def check_saw_collisions(player, saws):
    for x, y, r in saws:
        # Circle-to-AABB collision math
        closest_x = max(player.rect.left, min(x, player.rect.right))
        closest_y = max(player.rect.top, min(y, player.rect.bottom))
        dx = closest_x - x
        dy = closest_y - y
        if (dx**2 + dy**2) < r**2:
            return True
    return False

def handle_rotating_saws(screen, rotating_saws, blocks, player_rect, saw_img, camera_x, camera_y, saw_cache):
    """Updates, draws, and checks collisions for saws that orbit blocks."""
    collision = False
    
    # NEW: Calculate the spinning angle for the "classic" saw look
    spin_angle = (pygame.time.get_ticks() // 3) % 360
    angle_key = (spin_angle // 5) * 5

    for saw in rotating_saws:
        # 1. Update Position (Orbit)
        saw['angle'] = (saw['angle'] + saw['speed']) % 360
        rad = math.radians(saw['angle'])
        orbit_center_x, orbit_center_y = blocks[saw['block']].centerx, blocks[saw['block']].centery
        saw_x = orbit_center_x + saw['orbit_radius'] * math.cos(rad)
        saw_y = orbit_center_y + saw['orbit_radius'] * math.sin(rad)

        # 2. Draw with Cache (Optimization)
        cache_key = (saw['r'], angle_key)
        if cache_key not in saw_cache:
            size = int(saw['r'] * 2.5)
            scaled = pygame.transform.scale(saw_img, (size, size))
            saw_cache[cache_key] = pygame.transform.rotate(scaled, angle_key)
        
        rotated_saw = saw_cache[cache_key]
        rect = rotated_saw.get_rect(center=(int(saw_x - camera_x), int(saw_y - camera_y)))
        screen.blit(rotated_saw, rect)

        # 3. Collision Math
        closest_x = max(player_rect.left, min(saw_x, player_rect.right))
        closest_y = max(player_rect.top, min(saw_y, player_rect.bottom))
        if ((closest_x - saw_x)**2 + (closest_y - saw_y)**2)**0.5 < saw['r']:
            collision = True
            
    return collision

def handle_moving_saws(screen, moving_saws, player_rect, saw_img, camera_x, camera_y, saw_cache):
    """Updates, draws, and checks collisions for saws that bounce up and down."""
    collision = False
    
    # NEW: Spin logic
    spin_angle = (pygame.time.get_ticks() // 3) % 360
    angle_key = (spin_angle // 5) * 5

    for saw in moving_saws:
        # 1. Update Position (Bounce)
        saw['cy'] += saw['speed']
        if saw['cy'] > saw['max'] or saw['cy'] < saw['min']:
            saw['speed'] = -saw['speed']

        # 2. Draw with Cache
        cache_key = (saw['r'], angle_key)
        if cache_key not in saw_cache:
            size = int(saw['r'] * 2.5)
            scaled = pygame.transform.scale(saw_img, (size, size))
            saw_cache[cache_key] = pygame.transform.rotate(scaled, angle_key)
            
        rotated_saw = saw_cache[cache_key]
        rect = rotated_saw.get_rect(center=(int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)))
        screen.blit(rotated_saw, rect)

        # 3. Collision Math
        closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
        closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
        if ((closest_x - saw['cx'])**2 + (closest_y - saw['cy'])**2)**0.5 < saw['r']:
            collision = True
            
    return collision

def handle_moving_saws_x(screen, moving_saws_x, player_rect, saw_img, camera_x, camera_y, saw_cache):
    collision = False
    
    spin_angle = (pygame.time.get_ticks() // 3) % 360
    angle_key = (spin_angle // 5) * 5

    for saw in moving_saws_x:
        # 1. Update Position (Bounce)
        saw['cx'] += saw['speed']
        if saw['cx'] > saw['max'] or saw['cx'] < saw['min']:
            saw['speed'] = -saw['speed']

        # 2. Draw with Cache
        cache_key = (saw['r'], angle_key)
        if cache_key not in saw_cache:
            size = int(saw['r'] * 2.5)
            scaled = pygame.transform.scale(saw_img, (size, size))
            saw_cache[cache_key] = pygame.transform.rotate(scaled, angle_key)
            
        rotated_saw = saw_cache[cache_key]
        rect = rotated_saw.get_rect(center=(int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)))
        screen.blit(rotated_saw, rect)

        # 3. Collision Math
        closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
        closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
        if ((closest_x - saw['cx'])**2 + (closest_y - saw['cy'])**2)**0.5 < saw['r']:
            collision = True
            
    return collision

def handle_rushing_saws(screen, rushing_saws, player_rect, saw_img, camera_x, camera_y, saw_cache):
    collision = False
    
    spin_angle = (pygame.time.get_ticks() // 3) % 360
    angle_key = (spin_angle // 5) * 5

    for saw in rushing_saws:
        # 1. Update Position (Bounce)
        saw['cx'] += saw['speed']
        if saw['cx'] > saw['max']:
            saw['cx'] = saw['min']

        # 2. Draw with Cache
        cache_key = (saw['r'], angle_key)
        if cache_key not in saw_cache:
            size = int(saw['r'] * 2.5)
            scaled = pygame.transform.scale(saw_img, (size, size))
            saw_cache[cache_key] = pygame.transform.rotate(scaled, angle_key)
            
        rotated_saw = saw_cache[cache_key]
        rect = rotated_saw.get_rect(center=(int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)))
        screen.blit(rotated_saw, rect)

        # 3. Collision Math
        closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
        closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
        if ((closest_x - saw['cx'])**2 + (closest_y - saw['cy'])**2)**0.5 < saw['r']:
            collision = True
            
    return collision