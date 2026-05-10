import pygame
import math
import time
import cleobo.data.manage_data as manage_data

class Player:
    def __init__(self, x, y, width, height):
        self.rect = pygame.FRect(x, y, width, height)

        # Spawn data
        self.spawn_x = 0
        self.spawn_y = 0

        # Physics
        self.gravity = 1
        self.velocity_y = 0

        # Speed settings
        self.speeds = {
            "normal": 8,
            "stamina": 19
        }
        self.speed_mode = "normal" # To keep track of the speed mode (For easy switching)
        self.velocity_x = self.speeds[self.speed_mode]

        # Jump Settings (Replaced the dots with underscores)
        self.grav_strength = {
            "strong": 15,
            "normal": 21,
            "weak": 37
        }
        self.jump_mode = "normal" # To keep track of the gravity mode for our convenience in game logic
        self.jump = self.grav_strength[self.jump_mode]
        
        # State
        self.on_ground = False
        self.moving = False
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.camera_speed = 0.05
        self.lights_on = True

        # Other
        self.deathcount = 0
    
    def input_update(self, keys):
        # === JUMPING ===
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.velocity_y = -self.jump # Using your self.jump from grav_strength
            self.on_ground = False
            if not manage_data.is_mute:
                manage_data.sounds['jump'].play()
        
        # === MOVEMENT ===
        self.moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d])
        
        if self.moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.rect.x -= self.velocity_x
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.rect.x += self.velocity_x
            
            # Sound logic
            if self.on_ground and not self.moving and not manage_data.is_mute:
                manage_data.sounds['move'].play()
            self.moving = True
        else:
            self.moving = False
        
        self.velocity_y += self.gravity
        self.rect.y += self.velocity_y
        self.on_ground = False
    
    def camera_update(self):
    # === UPDATE CAMERA (before rendering) ===
        self.camera_x += (self.rect.x - self.camera_x - manage_data.SCREEN_WIDTH // 2 + self.rect.width // 2) * self.camera_speed
        if self.rect.y <= 200:
            self.camera_y = self.rect.y - 200
        else:
            self.camera_y = 0
    
    def fall(self, manager, rendered_fall_text):
    # Fall death
        if self.rect.y > 1100:
            self.rect.x, self.rect.y = self.spawn_x, self.spawn_y
            manager.death_text = rendered_fall_text
            manager.wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['fall'].play()
            self.velocity_y = 0
            self.deathcount += 1
    
    def update(self, keys, manager, rendered_fall_text):
        self.input_update(keys)
        self.camera_update()
        self.fall(manager, rendered_fall_text)

    def reset_stats(self):
        self.rect.x, self.rect.y = self.spawn_x, self.spawn_y
        self.velocity_y = 0
        self.deathcount = 0

class LevelManager:
    def __init__(self):
        self.medal = None
        self.death_text = None
        self.wait_time = None
        self.start_time = time.time()
        self.current_time = 0

    def reset_stats(self):
        self.start_time = time.time()
        self.death_text = None

    def score_calc(self, player):
        base_score = 100000 # From where the score is added to/subtracted from
        token_score = 0
        time_score = int(self.current_time * 160)
        if self.medal == "Diamond":
            medal_score = -10000
        elif self.medal == "Gold":
            medal_score = 5000
        elif self.medal == "Silver":
            medal_score = 10000
        elif self.medal == "Bronze":
            medal_score = 15000
        else:
            medal_score = 25000
        death_score = player.deathcount * 300
        score = max(500, base_score - medal_score - death_score - time_score + token_score)
        return score, base_score, medal_score, death_score, time_score

    # ALgorithm for logic stuff when level is completed
    def fin_lvl_logic(self, lvl, player):
        print(manage_data.progress["lvls"]["score"][f"lvl{lvl}"])
        if manage_data.progress["lvls"]["complete_levels"] < lvl:
            manage_data.progress["lvls"]["complete_levels"] = lvl

        if not manage_data.is_mute:
            manage_data.sounds['warp'].play()

        if self.current_time < manage_data.progress["lvls"]["times"][f"lvl{lvl}"] or manage_data.progress["lvls"]["times"][f"lvl{lvl}"] == 0:
            manage_data.progress["lvls"]["times"][f"lvl{lvl}"] = round(self.current_time, 2)
        
        if manage_data.progress["lvls"]["score"][f"lvl{lvl}"] < 100000:
            manage_data.progress["lvls"]["medals"][f"lvl{lvl}"] = self.get_medal(lvl, manage_data.progress["lvls"]["times"][f"lvl{lvl}"])
        else:
            manage_data.progress["lvls"]["medals"][f"lvl{lvl}"] = "Diamond"

        medal = self.get_medal(lvl, self.current_time)

        if medal == "Gold" and player.deathcount == 0:
            medal = "Diamond"
            manage_data.progress["lvls"]["medals"][f"lvl{lvl}"] = medal

        score, base_score, medal_score, death_score, time_score = self.score_calc(player)
        
        if manage_data.progress["lvls"]["score"][f"lvl{lvl}"] < score or manage_data.progress["lvls"]["score"][f"lvl{lvl}"] == 0:
            manage_data.progress["lvls"]["score"][f"lvl{lvl}"] = score
            new_hs = True
            hs = score
        else:
            new_hs = False
            hs = manage_data.progress["lvls"]["score"][f"lvl{lvl}"]

        manage_data.update_locked_levels(manage_data.progress, manage_data.manifest)
        stars = self.get_stars(lvl, score)
        return score, base_score, medal_score, death_score, time_score, stars, new_hs, hs

    def draw_level_ui(self, screen, deaths_text, reset_text, quit_text, timer_text):
        screen.blit(deaths_text, (20, 20))
        screen.blit(timer_text, (manage_data.SCREEN_WIDTH - timer_text.get_width() - 10, 20))
        screen.blit(reset_text, (10, manage_data.SCREEN_HEIGHT - 54))
        screen.blit(quit_text, (manage_data.SCREEN_WIDTH - quit_text.get_width() - 10, manage_data.SCREEN_HEIGHT - 54))

    def draw_medals(self, screen, player, timer_width):
        if self.medal == "Gold" and player.deathcount == 0:
            self.medal = "Diamond"
        if self.medal != None:
            img = manage_data.medals[self.medal]
            screen.blit(img, (manage_data.SCREEN_WIDTH - timer_width - 110, 20))
    
    def death_message(self, screen, duration=2500):
        if self.wait_time is not None:
            if pygame.time.get_ticks() - self.wait_time < duration:
                screen.blit(self.death_text, (20, 50))
            else:
                self.wait_time = None

    # Function to get medal based on time
    @staticmethod
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

    @staticmethod
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

    def update(self, screen, player, deaths_text, reset_text, quit_text, timer_text): # Any ideas?
        self.draw_medals(screen, player, timer_text.get_width())
        self.draw_level_ui(screen, deaths_text, reset_text, quit_text, timer_text)
        self.death_message(screen)

def player_image(manager, moving_img, moving_img_l, player_img, blink_img, screen, keys, player):
    if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player.rect.x - player.camera_x, player.rect.y - player.camera_y))  # Draw the moving block image
    elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player.rect.x - player.camera_x, player.rect.y - player.camera_y))  # Draw the moving block image
    else:
        screen.blit(player_img, (player.rect.x - player.camera_x, player.rect.y - player.camera_y))
        if manager.current_time % 4 < 0.25:
            screen.blit(blink_img, (player.rect.x - player.camera_x, player.rect.y - player.camera_y))

def draw_portal(screen, img, portal, player):
    bobbing_offset = math.sin(pygame.time.get_ticks() * 0.005) * 5
    screen.blit(img, (portal.x - player.camera_x, portal.y + bobbing_offset - player.camera_y))

def block_func(screen, blocks, player):
    for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (block.x - player.camera_x, block.y - player.camera_y, block.width, block.height))
            if player.rect.colliderect(block):
                # Falling onto a block
                if player.velocity_y > 0 and player.rect.y + player.rect.height - player.velocity_y <= block.y:
                    player.rect.y = block.y - player.rect.height
                    player.velocity_y = 0
                    player.on_ground = True
                # Horizontal collision (left or right side of the block)
                elif player.rect.x + player.rect.width > block.x and player.rect.x < block.x + block.width:
                    if player.rect.x < block.x:  # Colliding with the left side of the block
                        player.rect.x = block.x - player.rect.width
                    elif player.rect.x + player.rect.width > block.x + block.width:  # Colliding with the right side
                        player.rect.x = block.x + block.width
    return player

def handle_bottom_collisions(blocks, player):
    for block in blocks:
            if block.width <= 100:
                laser_rect = pygame.FRect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.FRect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            
            if player.rect.colliderect(laser_rect) and player.velocity_y < 0:  # Only if jumping upward
                return True
    return False

def handle_moving_blocks(screen, moving_blocks, player):
        for mb in moving_blocks:
            pygame.draw.rect(screen, (128, 0, 128), (mb['rect'].x - player.camera_x, mb['rect'].y - player.camera_y, mb['rect'].width, mb['rect'].height))
            mb['rect'].x += mb['speed'] * mb['direction']
            if mb['rect'].x < mb['limit_left'] or mb['rect'].x > mb['limit_right']:
                mb['direction'] *= -1
            
            if player.rect.colliderect(mb['rect']):
                # Standing on top of the moving block
                if player.velocity_y > 0 and player.rect.y + player.rect.height - player.velocity_y <= mb['rect'].y:
                    player.rect.y = mb['rect'].y - player.rect.height
                    player.velocity_y = 0
                    player.on_ground = True
                    # Carry the player along with the block's horizontal movement
                    player.rect.x += mb['speed'] * mb['direction']
                # Hitting from the side
                elif player.rect.x + player.rect.width > mb['rect'].x and player.rect.x < mb['rect'].x + mb['rect'].width:
                    if player.rect.x < mb['rect'].x:
                        player.rect.x = mb['rect'].x - player.rect.width
                    elif player.rect.x + player.rect.width > mb['rect'].x + mb['rect'].width:
                        player.rect.x = mb['rect'].x + mb['rect'].width
        
        return player, moving_blocks

def jump_block_func(screen, jump_blocks, player):
        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (jump_block.x - player.camera_x, jump_block.y - player.camera_y, jump_block.width, jump_block.height))

            adj_x = jump_block.x + 5 - player.camera_x
            adj_y = jump_block.y + 5 - player.camera_y # Changed to +5 to keep it inside the top of the block
            adj_w = jump_block.width - 10
            adj_h = jump_block.height - 10

            #  Define the three points of the triangle
            points = [
                (adj_x + adj_w / 2, adj_y),          # Top Tip (Middle)
                (adj_x, adj_y + adj_h),              # Bottom Left
                (adj_x + adj_w, adj_y + adj_h)       # Bottom Right
            ]

            # Draw the triangle
            pygame.draw.polygon(screen, (255, 190, 81), points)
            
            if player.rect.colliderect(jump_block):
                # Falling onto a jump block
                if player.velocity_y > 0 and player.rect.y + player.rect.height - player.velocity_y < jump_block.y + 5:
                    player.rect.bottom = jump_block.y
                    if player.jump_mode == "strong":
                        player.velocity_y = -21
                    elif player.jump_mode == "weak":
                        player.velocity_y = -54
                    else:
                        player.velocity_y = -33  # Apply upward velocity for the jump
                    if not manage_data.is_mute:
                        manage_data.sounds["bounce"].play()

                # Hitting the bottom of a jump block
                elif player.velocity_y < 0 and player.rect.y >= jump_block.y + jump_block.height - player.velocity_y:
                    player.rect.y = jump_block.y + jump_block.height
                    player.velocity_y = 0

                # Horizontal collision (left or right side of the jump block)
                elif player.rect.x + player.rect.width > jump_block.x and player.rect.x < jump_block.x + jump_block.width:
                    if player.rect.x < jump_block.x:  # Colliding with the left side of the jump block
                        player.rect.x = jump_block.x - player.rect.width
                    elif player.rect.x + player.rect.width > jump_block.x + jump_block.width:  # Colliding with the right side
                        player.rect.x = jump_block.x + jump_block.width
        
        return player

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