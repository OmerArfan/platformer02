import pygame
import time
from PIL import Image
import cleobo.data.manage_data as manage_data
from cleobo.data.manage_data import resource_path
from os.path import join

"""
The purpose of this levels submodule is to store all the different entities the game needs to function.
The purpose of the Player and PlayerSprite class is to store all the physics, functions, configurations and behaviour of the player when a button is pressed or a specific event may happen.
The purpose of the LevelManager class, meanwhile, is to handle the interface and important variables of the Level UI.
"""

class Player:
    def __init__(self, x, y):
        self.sprite = PlayerSprites()

        self.rect = pygame.FRect(x, y, self.sprite.width, self.sprite.height)

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

        # Jump Settings
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
        # Smooth Horizontal Camera
        target_x = self.rect.x - manage_data.SCREEN_WIDTH // 2 + self.rect.width // 2
        self.camera_x += (target_x - self.camera_x) * self.camera_speed

        # Smooth Vertical Camera
        if self.rect.y <= 200: # Threshold where moving by y-axis starts
            target_y = self.rect.y - 200 
        else:
            target_y = 0
        
        # Use interpolation for Y as well to stop the jitter
        self.camera_y += (target_y - self.camera_y) * self.camera_speed
    
    def fall(self, manager, rendered_fall_text):
    # Fall death
        if self.rect.y > 1100:
            self.die()
            manager.death_text = rendered_fall_text
            manager.wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['fall'].play()
            
    def die(self):
        self.rect.x, self.rect.y = self.spawn_x, self.spawn_y
        self.velocity_y = 0
        self.deathcount += 1
        self.jump_mode = "normal"

    def update(self, keys, manager, rendered_fall_text):
        self.input_update(keys)
        self.camera_update()
        self.fall(manager, rendered_fall_text)
        self.jump = self.grav_strength.get(self.jump_mode, "normal")

    def reset_stats(self):
        self.rect.x, self.rect.y = self.spawn_x, self.spawn_y
        self.velocity_y = 0
        self.deathcount = 0
        self.jump_mode = "normal"

class PlayerSprites:
    def __init__(self):
        self.default, self.blink, self.move_r, self.move_l, self.jump, self.width, self.height, self.move_r_start_frames, self.move_r_end_frames , self.move_l_start_frames, self.move_l_end_frames = self.char_assets()
        
        # Animation tracking
        self.move_r_was_pressed = False
        self.move_l_was_pressed = False
        self.animation_start_time = None
        self.current_animation = None  # 'start', 'end', or None
        self.animation_direction = None  # 'left' or 'right'
        self.frame_duration = 50  # milliseconds per frame
        self.animation_complete = False

    def load_gif_frames(self, gif_path):
        """Load all frames from a gif file"""
        frames = []
        try:
            gif = Image.open(gif_path)
            for frame_idx in range(gif.n_frames):
                gif.seek(frame_idx)
                frame_image = gif.convert("RGBA")
                frame_data = pygame.image.fromstring(
                    frame_image.tobytes(),
                    frame_image.size,
                    frame_image.mode
                ).convert_alpha()
                frames.append(frame_data)
        except Exception as e:
            print(f"Error loading gif {gif_path}: {e}")
        return frames

    def get_animation_frame(self):
        """Get current frame based on elapsed time since animation started"""
        if self.animation_start_time is None or self.current_animation is None:
            return None
        
        elapsed = pygame.time.get_ticks() - self.animation_start_time
        frame_index = elapsed // self.frame_duration
        
        if self.current_animation == 'start':
            frames = self.move_r_start_frames if self.animation_direction == 'right' else self.move_l_start_frames
            if frame_index >= len(frames):
                self.animation_complete = True
                return frames[-1]  # Return last frame
            return frames[frame_index]
        
        elif self.current_animation == 'end':
            frames = self.move_r_end_frames if self.animation_direction == 'right' else self.move_l_end_frames
            if frame_index >= len(frames):
                self.animation_complete = True
                return frames[-1]  # Return last frame
            return frames[frame_index]
        
        return None

    def draw(self, screen, player, keys, manager):
        draw_pos = (player.rect.x - player.camera_x, player.rect.y - player.camera_y)
        
        # Check if right/D key is currently pressed
        is_pressing_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        is_pressing_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        
        # Detect transition from not pressed to pressed
        if is_pressing_right and not self.move_r_was_pressed:
            self.current_animation = 'start'
            self.animation_direction = 'right'
            self.animation_start_time = pygame.time.get_ticks()
            self.animation_complete = False
        
        # Detect transition from pressed to not pressed
        if not is_pressing_right and self.move_r_was_pressed:
            self.current_animation = 'end'
            self.animation_direction = 'right'
            self.animation_start_time = pygame.time.get_ticks()
            self.animation_complete = False

        # Detect transition from not pressed to pressed
        if is_pressing_left and not self.move_l_was_pressed:
            self.current_animation = 'start'
            self.animation_direction = 'left'
            self.animation_start_time = pygame.time.get_ticks()
            self.animation_complete = False
        
        # Detect transition from pressed to not pressed
        if not is_pressing_left and self.move_l_was_pressed:
            self.current_animation = 'end'
            self.animation_direction = 'left'
            self.animation_start_time = pygame.time.get_ticks()
            self.animation_complete = False
        
        self.move_r_was_pressed = is_pressing_right
        self.move_l_was_pressed = is_pressing_left
        
        # Draw based on animation state
        frame = self.get_animation_frame()
        
        if frame is not None:
            # Animation is playing or completed
            screen.blit(frame, draw_pos)
        elif is_pressing_right:
            screen.blit(self.move_r, draw_pos)
        elif is_pressing_left:
            screen.blit(self.move_l, draw_pos)
        else:
            screen.blit(self.default, draw_pos)
            if manager.current_time % 4 < 0.25:
                screen.blit(self.blink, draw_pos)
    
    def char_assets(self):
        # Load player image
        CHAR_PATH = resource_path("assets/imgs/char")
        char = manage_data.selected_character
        player_img = pygame.image.load(join(CHAR_PATH, f"{char}/idle.png")).convert_alpha()
        blink_img = pygame.image.load(join(CHAR_PATH, f"{char}/blink.png")).convert_alpha()
        moving_img_l = pygame.image.load(join(CHAR_PATH, f"{char}/move_l.png")).convert_alpha() # Resize to fit the game
        moving_img = pygame.image.load(join(CHAR_PATH, f"{char}/move_r.png")).convert_alpha() # Resize to fit the game
        moving_gif_start_frames = self.load_gif_frames(join(CHAR_PATH, f"{char}/move_r_start.gif"))
        moving_gif_end_frames = self.load_gif_frames(join(CHAR_PATH, f"{char}/move_r_end.gif"))
        moving_gif_l_start_frames = self.load_gif_frames(join(CHAR_PATH, f"{char}/move_l_start.gif"))
        moving_gif_l_end_frames = self.load_gif_frames(join(CHAR_PATH, f"{char}/move_l_end.gif"))
        img_width, img_height = player_img.get_size()
        jump_img = blink_img
        return player_img, blink_img, moving_img, moving_img_l, jump_img, img_width, img_height, moving_gif_start_frames, moving_gif_end_frames, moving_gif_l_start_frames, moving_gif_l_end_frames

class LevelManager:
    def __init__(self):
        self.medal = None
        self.death_text = None
        self.wait_time = None
        self.start_time = time.time()
        self.current_time = 0

    def reset_stats(self):
        self.start_time = time.time()
        self.current_time = 0
        self.death_text = None
        self.wait_time = None

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
    def fin_lvl_logic(self, level_num, player, world_name, subsection='1'):
        level_key = f"lvl{level_num}"
        
        # Get current level data
        level_data = manage_data.progress["lvls"][world_name][subsection][level_key]
        
        # Play completion sound
        if not manage_data.is_mute:
            manage_data.sounds['warp'].play()

        # Update time 
        current_best = level_data.get('time', 0)
        if self.current_time < current_best or current_best == 0:
            level_data['time'] = round(self.current_time, 2)
        
        # Calculate medal based on time
        medal = self.get_medal(level_num, world_name, self.current_time)
        
        # Diamond medal if Gold with 0 deaths
        if medal == "Gold" and player.deathcount == 0:
            medal = "Diamond"
        
        # Update stored medal if new medal is better
        stored_medal = level_data.get('medal', 'None')
        medal_hierarchy = {'Diamond': 4, 'Gold': 3, 'Silver': 2, 'Bronze': 1, 'None': 0}
        if medal_hierarchy.get(medal, 0) > medal_hierarchy.get(stored_medal, 0):
            level_data['medal'] = medal
        else:
            medal = stored_medal
        
        # Calculate score
        score, base_score, medal_score, death_score, time_score = self.score_calc(player)
        
        # Update score if new personal best 
        stored_score = level_data.get('score', 0)
        new_hs = False
        if score > stored_score:
            level_data['score'] = score
            new_hs = True
            hs = score
        else:
            hs = stored_score
        
        next_lvl_num = level_num + 1
        next_level = f"lvl{next_lvl_num}"
        world_sub = manage_data.progress['lvls'][world_name][subsection]
        if next_level in world_sub:
            # Mark as unlocked since it's been played 
            next_level_data = manage_data.progress["lvls"][world_name][subsection][next_level]
            next_level_data['locked'] = False
        
        # Trigger unlock system 
        manage_data.update_locked_levels(manage_data.progress, manage_data.manifest)
        
        # Calculate stars
        stars = self.get_stars(level_num, world_name, score)
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
    def get_medal(level, world, time_taken):
        thresh = manage_data.thresholds(world, "medal")
        thresholds = next((t for t in thresh if t['level'] == level), None)
        if not thresholds:
            return "None"
        if time_taken <= thresholds['gold']:
            return "Gold"
        elif time_taken <= thresholds['silver']:
            return "Silver"
        elif time_taken <= thresholds['bronze']:
            return "Bronze"
        else:
            return None

    @staticmethod
    def get_stars(level, world, score):
        thresh = manage_data.thresholds(world, "star")
        thresholds = next((t for t in thresh if t['level'] == level), None)
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