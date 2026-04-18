import pygame
import math
import manage_data

ctime = None # global only for resetting
def resetting():
    global ctime
    if ctime is None:
        ctime = pygame.time.get_ticks()

def score_calc(current_time, deathcount, medal):
    base_score = 100000 # From where the score is added to/subtracted from
    token_score = 0
    time_score = int(current_time * 160)
    if medal == "Diamond":
        medal_score = -10000
    elif medal == "Gold":
        medal_score = 5000
    elif medal == "Silver":
        medal_score = 10000
    elif medal == "Bronze":
        medal_score = 15000
    else:
        medal_score = 25000
    death_score = deathcount * 300
    score = max(500, base_score - medal_score - death_score - time_score + token_score)
    return score, base_score, medal_score, death_score, time_score

# ALgorithm for logic stuff when level is completed
def fin_lvl_logic(current_time, deathcount, medal, lvl):
            print(manage_data.progress["lvls"]["score"][f"lvl{lvl}"])
            if manage_data.progress["lvls"]["complete_levels"] < lvl:
                manage_data.progress["lvls"]["complete_levels"] = lvl

            if not manage_data.is_mute:
                manage_data.sounds['warp'].play()

            if current_time < manage_data.progress["lvls"]["times"][f"lvl{lvl}"] or manage_data.progress["lvls"]["times"][f"lvl{lvl}"] == 0:
                manage_data.progress["lvls"]["times"][f"lvl{lvl}"] = round(current_time, 2)
            
            if manage_data.progress["lvls"]["score"][f"lvl{lvl}"] < 100000:
                manage_data.progress["lvls"]["medals"][f"lvl{lvl}"] = get_medal(lvl, manage_data.progress["lvls"]["times"][f"lvl{lvl}"])
            else:
                manage_data.progress["lvls"]["medals"][f"lvl{lvl}"] = "Diamond"

            medal = get_medal(lvl, current_time)

            if medal == "Gold" and deathcount == 0:
                medal = "Diamond"
                manage_data.progress["lvls"]["medals"][f"lvl{lvl}"] = medal
            score, base_score, medal_score, death_score, time_score = score_calc(current_time, deathcount, medal)
            if manage_data.progress["lvls"]["score"][f"lvl{lvl}"] < score or manage_data.progress["lvls"]["score"][f"lvl{lvl}"] == 0:
                manage_data.progress["lvls"]["score"][f"lvl{lvl}"] = score
                new_hs = True
                hs = score
            else:
                new_hs = False
                hs = manage_data.progress["lvls"]["score"][f"lvl{lvl}"]
            print(new_hs)

            manage_data.update_locked_levels(manage_data.progress, manage_data.manifest)
            stars = get_stars(lvl, score)
            return score, base_score, medal_score, death_score, time_score, stars, new_hs, hs

# Function to get medal based on time
def get_medal(level, time_taken):
    thresholds = next((t for t in manage_data.level_thresholds if t['level'] == level), None)
    if not thresholds:
        return "None"
    if time_taken <= thresholds['gold']:
        return "Gold"
    elif time_taken <= thresholds['silver']:
        return "Silver"
    elif time_taken <= thresholds['bronze']:
        return "Bronze"
    else:
        return "None"

def get_stars(level, score):
    thresholds = next((t for t in manage_data.score_thresholds if t['level'] == level), None)
    if not thresholds:
        return 0
    if score >= thresholds['3']:
        return 3
    elif score >= thresholds['2']:
        return 2
    elif score >= thresholds['1']:
        return 1
    else:
        return 0

def draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_text, reset_text, quit_text, timer_text):
    screen.blit(deaths_text, (20, 20))
    screen.blit(timer_text, (SCREEN_WIDTH - timer_text.get_width() - 10, 20))
    screen.blit(reset_text, (10, SCREEN_HEIGHT - 54))
    screen.blit(quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))

def draw_medals(screen, medal_type, deathcount, images, timer_width, SCREEN_WIDTH):
    # The logic tweak you just thought of:
    if medal_type == "Gold" and deathcount == 0:
        medal_type = "Diamond"
    img = images.get(medal_type)
    if img:
        screen.blit(img, (SCREEN_WIDTH - timer_width - 110, 20))

def player_image(current_time, moving_img, moving_img_l, player_img, blink_img, screen, keys, player_x, player_y, camera_x, camera_y):
    if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
    elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
    else:
        screen.blit(player_img, (player_x - camera_x, player_y - camera_y))
        if current_time % 4 < 0.25:
            screen.blit(blink_img, (player_x - camera_x, player_y - camera_y))

def draw_portal(screen, img, portal, camera_x, camera_y):
    bobbing_offset = math.sin(pygame.time.get_ticks() * 0.005) * 5
    screen.blit(img, (portal.x - camera_x, portal.y + bobbing_offset - camera_y))

def death_message(screen, death_text, wait_time, duration=2500):
    if wait_time is not None:
        if pygame.time.get_ticks() - wait_time < duration:
            screen.blit(death_text, (20, 50))
            return wait_time # Keep the timer running
        else:
            return None # Reset the timer
    return None

def block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground):

    for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True
                
                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width
    
    return player_x, player_y, velocity_y, on_ground, player_rect

def handle_bottom_collisions(blocks, player_rect, velocity_y):
    for block in blocks:
            if block.width <= 100:
                laser_rect = pygame.FRect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.FRect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            
            if player_rect.colliderect(laser_rect) and velocity_y < 0:  # Only if jumping upward
                return True
    return False


def jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, is_mute, bounce_sound, strong_grav, weak_grav):
        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (jump_block.x - camera_x, jump_block.y - camera_y, jump_block.width, jump_block.height))

            adj_x = jump_block.x + 5 - camera_x
            adj_y = jump_block.y + 5 - camera_y # Changed to +5 to keep it inside the top of the block
            adj_w = jump_block.width - 10
            adj_h = jump_block.height - 10

            # 3. Define the three points of the triangle
            points = [
                (adj_x + adj_w / 2, adj_y),          # Top Tip (Middle)
                (adj_x, adj_y + adj_h),              # Bottom Left
                (adj_x + adj_w, adj_y + adj_h)       # Bottom Right
            ]

            # 4. Draw the triangle
            pygame.draw.polygon(screen, (255, 190, 81), points)
            
        for jump_block in jump_blocks:
            if player_rect.colliderect(jump_block):
                # Falling onto a jump block
                if velocity_y > 0 and player_y + img_height - velocity_y <= jump_block.y:
                    player_y = jump_block.y - img_height
                    if strong_grav:
                        velocity_y = -21
                    elif weak_grav:
                        velocity_y = -54
                    else:
                        velocity_y = -33  # Apply upward velocity for the jump
                    if not is_mute:
                        bounce_sound.play()

                # Hitting the bottom of a jump block
                elif velocity_y < 0 and player_y >= jump_block.y + jump_block.height - velocity_y:
                    player_y = jump_block.y + jump_block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the jump block)
                elif player_x + img_width > jump_block.x and player_x < jump_block.x + jump_block.width:
                    if player_x < jump_block.x:  # Colliding with the left side of the jump block
                        player_x = jump_block.x - img_width
                    elif player_x + img_width > jump_block.x + jump_block.width:  # Colliding with the right side
                        player_x = jump_block.x + jump_block.width
        
        return player_x, player_y, velocity_y

def handle_key_blocks(screen, open_sound, key_block_pairs, is_mute, on_ground, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y):
    # player_pos would be [x, y, on_ground]
    for pair in key_block_pairs:
        if not pair["collected"]:
            block = pair["block"]
            if player_rect.colliderect(block):
        # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = int(block.y - img_height)
                    velocity_y = 0
                    on_ground = True
                    player_rect.y = player_y

        # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

        # Horizontal collisions
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:
                        player_x = block.x + block.width

            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            # Check collision if not yet collected
            if not pair["collected"]:
                key_rect = pygame.FRect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)
            if player_rect.colliderect(key_rect):
                if not pair["collected"] and not is_mute:
                    open_sound.play()
                pair["collected"] = True
            
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)

            # Draw block only if key is not collected
            if not pair["collected"]:
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

    return player_x, player_y, velocity_y, on_ground, player_rect

def handle_key_blocks_timed(screen, key_block_pairs_timed, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y, on_ground):
    for pair in key_block_pairs_timed:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            key_rect = pygame.FRect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)

            if player_rect.colliderect(key_rect):
                if not pair["collected"]:
                    pair["locked_time"] = pygame.time.get_ticks()
                    pair["collected"] = True
                    if not manage_data.is_mute:
                        manage_data.sounds['open'].play()

            # Draw key and block only if not collected
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

            # Reset after duration
            if pair.get("locked_time") is not None:
                if pair["collected"] and (pygame.time.get_ticks() - pair["locked_time"]) > pair["duration"]:
                    pair["collected"] = False
                    pair["locked_time"] = None  # Reset timer
                    # Check if player is inside block when it reappears
            
                    if player_rect.colliderect(pair["block"]):
                        return True, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y, on_ground

            if not pair["collected"]:  # Only active locked blocks
                block = pair["block"]
                if player_rect.colliderect(block):
            # Falling onto a block
                    if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                        player_y = block.y - img_height
                        velocity_y = 0
                        on_ground = True

            # Horizontal collisions
                    elif player_x + img_width > block.x and player_x < block.x + block.width:
                        if player_x < block.x:
                            player_x = block.x - img_width
                        elif player_x + img_width > block.x + block.width:
                            player_x = block.x + block.width

    return False, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y, on_ground

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

def handling_gravity_weakers(screen, gravity_weakers, player_rect, camera_x, camera_y, weak_grav):
        for x, y, r, color in gravity_weakers:
            # Draw the button as a circle
            if not weak_grav:
                pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        for gravity_weaker in gravity_weakers:
            gravity_weaker_x, gravity_weaker_y, gravity_weaker_radius, _ = gravity_weaker

        # Find the closest point on the player's rectangle to the button's center
            closest_x = max(player_rect.left, min(gravity_weaker_x, player_rect.right))
            closest_y = max(player_rect.top, min(gravity_weaker_y, player_rect.bottom))

            # Calculate the distance between the closest point and the button's center
            dx = closest_x - gravity_weaker_x
            dy = closest_y - gravity_weaker_y
            distance = (dx**2 + dy**2)**0.5

            # If distance is less than radius, weaker gravity activated
            if distance < gravity_weaker_radius and not weak_grav:
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