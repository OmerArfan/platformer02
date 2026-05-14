import pygame
import time
import cleobo.data.manage_data as manage_data
from cleobo.data.manage_data import resource_path
from os.path import join

"""
The purpose of this levels submodule is to store all the different entities the game needs to function.
The purpose of the Player and PlayerSprite class is to store all the physics, functions, configurations and behaviour of the player when a button is pressed or a specific event may happen.
The purpose of the LevelManager class, meanwhile, is to handle the interface of the Level UI.
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
            self.rect.x, self.rect.y = self.spawn_x, self.spawn_y
            manager.death_text = rendered_fall_text
            manager.wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['fall'].play()
            self.velocity_y = 0
            self.deathcount += 1
    
    def update(self, screen, keys, manager, rendered_fall_text):
        self.input_update(keys)
        self.sprite.draw(screen, self, keys, manager)
        self.camera_update()
        self.fall(manager, rendered_fall_text)

    def reset_stats(self):
        self.rect.x, self.rect.y = self.spawn_x, self.spawn_y
        self.velocity_y = 0
        self.deathcount = 0

class PlayerSprites:
    def __init__(self):
        self.default, self.move_r, self.move_l, self.blink, self.jump, self.width, self.height = self.char_assets()

    def draw(self, screen, player, keys, manager):
        # Calculate draw position once
        draw_pos = (player.rect.x - player.camera_x, player.rect.y - player.camera_y)

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            screen.blit(self.move_r, draw_pos)
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            screen.blit(self.move_l, draw_pos)
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            screen.blit(self.blink, draw_pos)
        else:
            screen.blit(self.default, draw_pos)
            if manager.current_time % 4 < 0.25:
                screen.blit(self.blink, draw_pos)
    
    def char_assets():
        # Load player image
        CHAR_PATH = resource_path("assets/imgs/char")
        char = manage_data.selected_character
        if char == "robot": 
            player_img = pygame.image.load(join(CHAR_PATH, "robot/robot.png")).convert_alpha()
            blink_img = pygame.image.load(join(CHAR_PATH, "robot/blinkrobot.png")).convert_alpha()
            moving_img_l = pygame.image.load(join(CHAR_PATH, "robot/smilerobotL.png")).convert_alpha() # Resize to fit the game
            moving_img = pygame.image.load(join(CHAR_PATH, "robot/smilerobot.png")).convert_alpha() # Resize to fit the game
        elif char == "evilrobot":
            player_img = pygame.image.load(join(CHAR_PATH, "evilrobot/evilrobot.png")).convert_alpha()
            blink_img = pygame.image.load(join(CHAR_PATH, "evilrobot/blinkevilrobot.png")).convert_alpha()
            moving_img_l = pygame.image.load(join(CHAR_PATH, "evilrobot/movevilrobotL.png")).convert_alpha() # Resize to fit the game
            moving_img = pygame.image.load(join(CHAR_PATH, "evilrobot/movevilrobot.png")).convert_alpha() # Resize to fit the game
        elif char == "greenrobot":
            player_img = pygame.image.load(join(CHAR_PATH, "greenrobot/greenrobot.png")).convert_alpha()
            blink_img = pygame.image.load(join(CHAR_PATH, "greenrobot/blinkgreenrobot.png")).convert_alpha()
            moving_img_l = pygame.image.load(join(CHAR_PATH, "greenrobot/movegreenrobotL.png")).convert_alpha() # Resize to fit the game
            moving_img = pygame.image.load(join(CHAR_PATH, "greenrobot/movegreenrobot.png")).convert_alpha() # Resize to fit the game
        elif char == "ironrobot":
            player_img = pygame.image.load(join(CHAR_PATH, "ironrobot/ironrobo.png")).convert_alpha()
            blink_img = pygame.image.load(join(CHAR_PATH, "ironrobot/blinkironrobo.png")).convert_alpha()
            moving_img_l = pygame.image.load(join(CHAR_PATH, "ironrobot/ironrobomoveL.png")).convert_alpha() # Resize to fit the game
            moving_img = pygame.image.load(join(CHAR_PATH, "ironrobot/ironrobomove.png")).convert_alpha() # Resize to fit the game
        elif char == "cakebot":
            player_img = pygame.image.load(join(CHAR_PATH, "cakebot/cakebot.png")).convert_alpha()
            blink_img = pygame.image.load(join(CHAR_PATH, "cakebot/blinkcakebot.png")).convert_alpha()
            moving_img_l = pygame.image.load(join(CHAR_PATH, "cakebot/movecakebotL.png")).convert_alpha() # Resize to fit the game
            moving_img = pygame.image.load(join(CHAR_PATH, "cakebot/movecakebot.png")).convert_alpha() # Resize to fit the game
        img_width, img_height = player_img.get_size()
        jump_img = blink_img
        return player_img, blink_img, moving_img, moving_img_l, jump_img, img_width, img_height

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