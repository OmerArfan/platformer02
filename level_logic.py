import pygame
import math

def point_in_triangle(px, py, a, b, c):
    def sign(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    b1 = sign((px, py), a, b) < 0.0
    b2 = sign((px, py), b, c) < 0.0
    b3 = sign((px, py), c, a) < 0.0
    return b1 == b2 == b3

def check_spike_collisions(spikes, p_x, p_y, p_w, p_h):
    # Define collision points relative to the passed-in coordinates
    points = [
        (p_x + p_w // 2, p_y + p_h), (p_x + 5, p_y + p_h), (p_x + p_w - 5, p_y + p_h), # Bottom
        (p_x + p_w // 2, p_y), (p_x + 5, p_y), (p_x + p_w - 5, p_y) # Top
    ]

    for spike in spikes:
        for pt in points:
            if point_in_triangle(pt[0], pt[1], *spike):
                return True 
    return False

def draw_spikes(screen, spikes, camera_x, camera_y):
    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

def draw_saws(screen, saws, saw_img, camera_x, camera_y, saw_cache):
    # Calculate angle once for all saws to sync them
    angle = (pygame.time.get_ticks() // 3) % 360
    angle_key = (angle // 5) * 5
    
    for x, y, r, color in saws:
        # Rotation & Cache Logic
        cache_key = (r, angle_key)
        if cache_key not in saw_cache:
            size = int(r * 2.2)
            scaled = pygame.transform.scale(saw_img, (size, size))
            saw_cache[cache_key] = pygame.transform.rotate(scaled, angle_key)
        
        rotated_img = saw_cache[cache_key]
        curr_w, curr_h = rotated_img.get_size()
        
        # Centering and Blitting
        draw_x = (x - camera_x) - (curr_w / 2)
        draw_y = (y - camera_y) - (curr_h / 2)
        screen.blit(rotated_img, (draw_x, draw_y))

def check_saw_collisions(player_rect, saws):
    for x, y, r, color in saws:
        # Circle-to-AABB collision math
        closest_x = max(player_rect.left, min(x, player_rect.right))
        closest_y = max(player_rect.top, min(y, player_rect.bottom))
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