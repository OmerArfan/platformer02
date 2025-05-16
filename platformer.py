import pygame
import json
import os
import math
import time  # Import time to track time(for future use in scoring)

pygame.mixer.init()
click_sound = pygame.mixer.Sound("click.wav")
death_sound = pygame.mixer.Sound("death.wav")
laser_sound = pygame.mixer.Sound("laser.wav")
fall_sound = pygame.mixer.Sound("fall.wav")
open_sound = pygame.mixer.Sound("unlock.wav")
checkpoint_sound = pygame.mixer.Sound("checkpoint.wav")
warp_sound = pygame.mixer.Sound("warp.wav")

# Load and set window icon
icon = pygame.image.load("roboticon.ico")
pygame.display.set_icon(icon)

complete_levels = 0  # Keep track of how many levels have been completed
locked_levels = ["lvl2", "lvl3", "lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9"] # Keep track of how many levels are locked

pygame.init()
SCREEN_WIDTH = 1530
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Platformer 02!")

# Load logo image
logo = pygame.image.load("logo.png").convert_alpha()

# Declare font size
font = pygame.font.SysFont(None, 40)

# Load the Chinese font (ensure the font file path is correct)
font_path = 'NotoSansSC-SemiBold.ttf'  # Adjust if the path is different
font = pygame.font.Font(font_path, 25)


site_text = font.render("Sound effects from: pixabay.com", True, (255, 255, 255))
site_pos = (SCREEN_WIDTH - 405, SCREEN_HEIGHT - 54)
logo_text = font.render("Logo made with: canva.com", True, (255, 255, 255))
logo_pos = (SCREEN_WIDTH - 349, SCREEN_HEIGHT - 84)
credit_text = font.render("Made by: Omer Arfan", True, (255, 255, 255))
credit_pos = (SCREEN_WIDTH - 265, SCREEN_HEIGHT - 114)
ver_text = font.render("Version 1.0.8", True, (255, 255, 255))
ver_pos = (SCREEN_WIDTH - 167, SCREEN_HEIGHT - 144)

# Load language function and rendering part remain the same
def load_language(lang_code):
    with open(f'lang/{lang_code}.json', encoding='utf-8') as f:
        return json.load(f)

def loading_screen():
    global lang_code
    screen.fill((30, 30, 30))
    messages = load_language(lang_code).get('messages', {})  # Fetch localized messages
    loading_text = messages.get("loading", "Loading...")  # Get the localized "Loading..." text
    rendered_loading = font.render(loading_text, True, (255, 255, 255))
    loading_rect = rendered_loading.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(rendered_loading, loading_rect)
    pygame.display.flip()
    pygame.time.delay(1300)  # Delay to show the loading screen

lang_code = 'english'

# Page states
current_page = 'main_menu'
buttons = []
current_lang = {}

# New variable to track last page change time
pending_level = None
level_load_time = 0
click_delay = 1  # Delay between clicks isn seconds
last_page_change_time = 0  # Initialize the last page change time

def create_main_menu_buttons():
    global current_lang, buttons
    current_lang = load_language(lang_code)['main_menu']
    buttons.clear()
    button_texts = ["start", "achievements", "settings", "quit", "language"]

    # Center buttons vertically and horizontally
    button_spacing = 60
    start_y = (SCREEN_HEIGHT // 2) - (len(button_texts) * button_spacing // 2) + 230

    for i, key in enumerate(button_texts):
        text = current_lang[key]
        rendered = font.render(text, True, (255, 255, 255))
        rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * button_spacing)) 
        buttons.append((rendered, rect, key))

def create_language_buttons():
    global current_lang, buttons
    current_lang = load_language(lang_code).get('language_select', {})
    buttons.clear()

    language_options = ["English", "Français", "Español", "Deutsch", "简体中文", "O'zbekcha", "Português(Brasil)", "Русский"]
    buttons_per_row = 4
    spacing_x = 200
    spacing_y = 70

    # Calculate starting positions to center the grid
    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (SCREEN_WIDTH - grid_width) // 2
    start_y = (SCREEN_HEIGHT // 2) - (len(language_options) // buttons_per_row * spacing_y // 2)

    for i, lang in enumerate(language_options):
        text = lang.capitalize()
        rendered = font.render(text, True, (255, 255, 255))

        col = i % buttons_per_row
        row = i // buttons_per_row

        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        rect = rendered.get_rect(center=(x, y))
        buttons.append((rendered, rect, lang))

    # Add a "Back" button at the bottom center
    back_text = current_lang.get("back", "Back")
    rendered_back = font.render(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(SCREEN_WIDTH // 2, y + spacing_y + 40))
    buttons.append((rendered_back, back_rect, "back"))

def create_levels_buttons():
    global current_lang, buttons
    current_lang = load_language(lang_code).get('levels', {})
    buttons.clear()

    # Render "Select a Level" text
    select_text = current_lang.get("level_display", "SELECT A LEVEL")
    rendered_select_text = font.render(select_text, True, (255, 255, 255))
    select_text_rect = rendered_select_text.get_rect(center=(SCREEN_WIDTH // 2, 50))  # Center at the top

    # Store the rendered text and its position for later drawing
    global select_level_text, select_level_rect
    select_level_text = rendered_select_text
    select_level_rect = select_text_rect

    level_options = ["lvl1", "lvl2", "lvl3", "lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9"]
    buttons_per_row = 3
    spacing_x = 180
    spacing_y = 70

    # Calculate starting positions to center the grid
    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (SCREEN_WIDTH - grid_width) // 2
    start_y = (SCREEN_HEIGHT // 2) - (len(level_options) // buttons_per_row * spacing_y // 2)

    for i, level in enumerate(level_options):
        text = current_lang.get(level, level.capitalize())
        is_locked = level in locked_levels  # Check if the level is locked

        # Render the level text
        color = (150, 150, 150) if is_locked else (255, 255, 255)  # Gray out locked levels
        rendered = font.render(text, True, color)

        col = i % buttons_per_row
        row = i // buttons_per_row

        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        rect = rendered.get_rect(center=(x, y))

        # Add the button only if the level is not locked
        if not is_locked:
            buttons.append((rendered, rect, level))
        else:
            # Add the locked button for display purposes (no interaction)
            buttons.append((rendered, rect, None))  # Use `None` as the key for locked levels

    # Back button at bottom center
    back_text = current_lang.get("back", "Back")
    rendered_back = font.render(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(SCREEN_WIDTH // 2, y + spacing_y + 40))
    buttons.append((rendered_back, back_rect, "back"))

def load_level(level_id):
    global current_page, buttons

    # Show "Loading..." text
    screen.fill((30, 30, 30))
    messages = load_language(lang_code).get('messages', {})  # Reload messages with the current language
    loading_text = messages.get("loading", "Loading...")
    rendered_loading = font.render(loading_text, True, (255, 255, 255))
    loading_rect = rendered_loading.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))  # Center dynamically
    screen.blit(rendered_loading, loading_rect)
    pygame.display.flip()

    # Short delay to let the user see the loading screen
    pygame.time.delay(800)  # 800 milliseconds

    # Now switch the page
    current_page = level_id
    buttons.clear()

    # Add a "Back" button
    back_text = "Back"
    rendered_back = font.render(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))  # Center at the bottom
    buttons.append((rendered_back, back_rect, "back"))

    print(f"Loading level: {level_id}")


# Button actions
def start_game():
    print(f"Complete Levels: {complete_levels}")
    pygame.time.delay(200)  # Delay 200 ms to avoid click pass-through
    set_page('levels')

def open_achievements():
    print("Opening achievements...")

def open_settings():
    print("Opening settings...")

def quit_game():
    pygame.quit()
    exit()

def change_language(lang):
    global lang_code, last_page_change_time, current_lang
    lang_code = lang
    print(f"Language changed to: {lang_code}")
    last_page_change_time = time.time()  # Track the time when the language changes
    current_lang = load_language(lang_code)  # Reload the language data
    set_page('main_menu')

def go_back():
    global last_page_change_time
    last_page_change_time = time.time()  # Track the time when going back
    set_page('main_menu')

def update_locked_levels():
    global locked_levels
    if complete_levels == 0:
        locked_levels = ["lvl2","lvl3", "lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9"]  # Example of locked levels
    elif complete_levels == 1:
        locked_levels = ["lvl3", "lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9"]
    elif complete_levels == 2:
        locked_levels = ["lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9"]
    elif complete_levels == 3:
        locked_levels = ["lvl5", "lvl6", "lvl7", "lvl8", "lvl9"]
    elif complete_levels == 4:
        locked_levels = ["lvl6", "lvl7", "lvl8", "lvl9"]
    elif complete_levels == 5:
        locked_levels = ["lvl7", "lvl8", "lvl9"]
    elif complete_levels == 6:
        locked_levels = ["lvl8", "lvl9"]
    elif complete_levels == 7:
        locked_levels = ["lvl9"]
    elif complete_levels == 8:
        locked_levels = []

# Central page switcher
def set_page(page):
    global current_page, current_lang  # Explicitly mark current_page and current_lang as global
    current_page = page

    # Reload the current language data for the new page
    if page == 'main_menu':
        current_lang = load_language(lang_code).get('main_menu', {})
        create_main_menu_buttons()
    elif page == 'language_select':
        current_lang = load_language(lang_code).get('language_select', {})
        create_language_buttons()
    elif page == 'levels':
        current_lang = load_language(lang_code).get('levels', {})
        create_levels_buttons()
    elif page == 'quit_confirm':
        current_lang = load_language(lang_code).get('messages', {})
        create_quit_confirm_buttons()
    elif page == 'lvl1_screen':  # New page for Level 1
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl1_screen()
    elif page == 'lvl2_screen':  # New page for Level 2
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl2_screen()
    elif page == 'lvl3_screen':  # New page for Level 3
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl3_screen()
    elif page == 'lvl4_screen':  # New page for Level 4
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl4_screen()
    elif page == 'lvl5_screen':  # New page for Level 5
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl5_screen()
    elif page == 'lvl6_screen':
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl6_screen()
    elif page == 'lvl7_screen':
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl7_screen()
    elif page == 'lvl8_screen':
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl8_screen()

def create_quit_confirm_buttons():
    global current_lang, buttons, quit_text, quit_text_rect
    buttons.clear()

    # Get the quit confirmation text from the current language
    messages = load_language(lang_code).get('messages', {})
    confirm_quit = messages.get("confirm_quit", "Are you sure you want to quit?")

    # Store the quit confirmation text for rendering in the main loop
    quit_text = font.render(confirm_quit, True, (255, 255, 255))
    quit_text_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))

    # Create "Yes" button
    yes_text = messages.get("yes", "Yes")
    rendered_yes = font.render(yes_text, True, (255, 255, 255))
    yes_rect = rendered_yes.get_rect(center=(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50))
    buttons.append((rendered_yes, yes_rect, "yes"))

    # Create "No" button
    no_text = messages.get("no", "No")
    rendered_no = font.render(no_text, True, (255, 255, 255))
    no_rect = rendered_no.get_rect(center=(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 + 50))
    buttons.append((rendered_no, no_rect, "no"))

def create_lvl1_screen():
    global player_img, font, screen, complete_levels

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 0  
    camera_y = 0
    player_x, player_y = 600, 200
    running = True
    gravity = 1
    jump_strength = 20
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.05
    deathcount = 0

    # Load player image
    player_img = pygame.image.load("robot.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    blocks = [
        pygame.Rect(600, 450, 200, 50),
        pygame.Rect(1000, 400, 200, 50),
        pygame.Rect(1700, 300, 200, 50),
        pygame.Rect(2100, 300, 200, 50),
        pygame.Rect(2500, 250, 500, 50),
        pygame.Rect(1850, 400, 320, 50),
    ]

    moving_block = pygame.Rect(1300, 300, 100, 20)
    moving_block2 = pygame.Rect(400, 500, 100, 20)
    moving_direction1 = 1
    moving_speed = 2
    moving_limit_left1 = 1300
    moving_limit_right1 = 1500

    spikes = [
        [(1850, 400), (1900, 350), (1950, 400)],
        [(1960, 400), (2010, 350), (2060, 400)],
        [(2070, 400), (2120, 350), (2170, 400)],
    ]

    exit_portal = pygame.Rect(2850, 150, 50, 100)
    clock = pygame.time.Clock()

    def point_in_triangle(px, py, a, b, c):
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        b1 = sign((px, py), a, b) < 0.0
        b2 = sign((px, py), b, c) < 0.0
        b3 = sign((px, py), c, a) < 0.0
        return b1 == b2 == b3
    
    # Render the texts
    warning_text = in_game.get("warning_message", "Watch out for spikes!")
    rendered_warning_text = font.render(warning_text, True, (255, 0, 0))  # Render the warning text

    up_text = in_game.get("up_message", "Press UP to Jump!")
    rendered_up_text = font.render(up_text, True, (0, 0, 0))  # Render the up text

    exit_text = in_game.get("exit_message", "Exit Portal! Come here to win!")
    rendered_exit_text = font.render(exit_text, True, (0, 255, 0))  # Render the exit text

    moving_text = in_game.get("moving_message", "Not all blocks stay still...")
    rendered_moving_text = font.render(moving_text, True, (128, 0, 128))  # Render the moving text

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                set_page('levels')

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength

        if (keys[pygame.K_LEFT] or keys[pygame.K_a]):
            player_x -= move_speed

        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            player_x += move_speed

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y


        # Moving blocks
        moving_block.x += moving_speed * moving_direction1
        if moving_block.x < moving_limit_left1 or moving_block.x > moving_limit_right1:
            moving_direction1 *= -1

        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in blocks + [moving_block]:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        if player_y > (SCREEN_HEIGHT + 50):
            player_x, player_y = 600, 200
            fall_text = in_game.get("fall_message", "Fell too far!")
            screen.blit(font.render(fall_text, True, (255, 0, 0)), (20, 50))
            fall_sound.play()
            pygame.display.update()
            pygame.time.delay(300)
            velocity_y = 0
            deathcount += 1

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if complete_levels < 1:
              complete_levels = 1
              update_locked_levels()
            warp_sound.play()
            running = False
            set_page('lvl2_screen')
            

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 100:
            camera_y = player_y - 100
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Drawing
        screen.fill((0, 102, 51))

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))
            pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

            for spike in spikes:
                pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])
                        # Spike death
            bottom_points = [
                (player_x + img_width // 2, player_y + img_height),
                (player_x + 5, player_y + img_height),
                (player_x + img_width - 5, player_y + img_height)
            ]
            collision_detected = False  # Flag to stop further checks after a collision
            for spike in spikes:
                if collision_detected:
                    break  # Exit the outer loop if a collision has already been detected
                for point in bottom_points:
                    if point_in_triangle(point[0], point[1], *spike):
                        player_x, player_y = 600, 200
                        death_text = in_game.get("dead_message", "You Died")
                        screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                        death_sound.play()
                        pygame.display.update()
                        pygame.time.delay(300)
                        velocity_y = 0
                        deathcount += 1
                        collision_detected = True  # Set the flag to stop further checks
                        break

        # Spike death (including top collision detection)
            top_points = [
                (player_x + img_width // 2, player_y),  # Center top point
                (player_x + 5, player_y),               # Left top point
                (player_x + img_width - 5, player_y)    # Right top point
            ]
            collision_detected = False  # Flag to stop further checks after a collision
            for spike in spikes:
                if collision_detected:
                    break  # Exit the outer loop if a collision has already been detected
                for point in top_points:
                    if point_in_triangle(point[0], point[1], *spike):
                        # Trigger death logic
                        player_x, player_y = 150, 200  # Reset player position
                        death_text = in_game.get("dead_message", "You Died")
                        screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                        pygame.display.update()
                        pygame.time.delay(300)
                        velocity_y = 0
                        deathcount += 1
                        collision_detected = True  # Set the flag to stop further checks
                        break

        pygame.draw.rect(screen, (0, 205, 0), (exit_portal.x - camera_x, exit_portal.y - camera_y, exit_portal.width, exit_portal.height))
        screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

            # Inside the game loop:
        screen.blit(rendered_up_text, (700 - camera_x, 200 - camera_y))  # Draws the rendered up text
        screen.blit(rendered_warning_text, (1900 - camera_x, 150 - camera_y))  # Draws the rendered warning text
        screen.blit(rendered_moving_text, (1350 - camera_x, 170 - camera_y))  # Draws the rendered moving text
        screen.blit(rendered_exit_text, (2400 - camera_x, 300 - camera_y))  # Draws the rendered exit text

        levels = load_language(lang_code).get('levels', {})
        lvl1_text = levels.get("lvl1", "Level 1")  # Render the level text
        screen.blit(font.render(lvl1_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        pygame.display.update()    

def create_lvl2_screen():
    global player_img, font, screen, complete_levels

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 0  
    camera_y = 0
    player_x, player_y = 150, 500
    running = True
    gravity = 1
    jump_strength = 20
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.05
    deathcount = 0

    # Load player image
    player_img = pygame.image.load("robot.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    blocks = [
        pygame.Rect(100, 650, 1000, 50),
        pygame.Rect(500, 500, 200, 50),
        pygame.Rect(1900, 200, 200, 50),
        pygame.Rect(2900, 450, 500, 50),
        pygame.Rect(2150, 530, 250, 50),
        pygame.Rect(2080, 750, 620, 50),
        pygame.Rect(2400, 50, 50, 530),
        pygame.Rect(3300, 650, 300, 50),
        pygame.Rect(3760, 650, 300, 50),
        pygame.Rect(4220, 650, 300, 50),
        pygame.Rect(3300, 200, 1000, 50),
    ]

    jump_blocks = [
        pygame.Rect(1000, 550, 100, 100), # Jump blocks to help the character go up and then fall down
        pygame.Rect(2700, 751, 100, 100),
        pygame.Rect(3600, 651, 160, 100),
        pygame.Rect(4060, 651, 160, 100),
    ]

    moving_block = pygame.Rect(1500, 300, 100, 20)
    moving_direction1 = 1
    moving_speed = 2
    moving_limit_left1 = 1300
    moving_limit_right1 = 1700

    spikes = [
        [(350, 650), (400, 600), (450, 650)],
        [(460, 650), (510, 600), (560, 650)],
        [(570, 650), (620, 600), (670, 650)],
        [(680, 650), (730, 600), (780, 650)],
        [(790, 650), (840, 600), (890, 650)],
        [(900, 650), (950, 600), (1000, 650)],
        [(2040, 200), (2070, 150), (2100, 200)],
        [(2150, 580), (2300, 610), (2450, 580)],
        [(3100, 450), (3135, 400), (3170, 450)],
        [(3300, 250), (3350, 300), (3400, 250)],
        [(3400, 250), (3450, 300), (3500, 250)],
        [(3500, 250), (3550, 300), (3600, 250)],
        [(3600, 250), (3650, 300), (3700, 250)],
        [(3700, 250), (3750, 300), (3800, 250)],
        [(3800, 250), (3850, 300), (3900, 250)],
        [(3900, 250), (3950, 300), (4000, 250)],
        [(4000, 250), (4050, 300), (4100, 250)],
        [(4100, 250), (4150, 300), (4200, 250)],
        [(4200, 250), (4250, 300), (4300, 250)],
    ]

    exit_portal = pygame.Rect(4400, 550, 50, 100)
    clock = pygame.time.Clock()

    def point_in_triangle(px, py, a, b, c):
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        b1 = sign((px, py), a, b) < 0.0
        b2 = sign((px, py), b, c) < 0.0
        b3 = sign((px, py), c, a) < 0.0
        return b1 == b2 == b3
    
    # Render the texts
    jump_message = in_game.get("jump_message", "Use orange blocks to jump high distances!")
    rendered_jump_text = font.render(jump_message, True, (255, 128, 0))  # Render the jump text

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        if keys[pygame.K_r]:
            player_x, player_y = 150, 200
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                set_page('levels')

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength

        if (keys[pygame.K_LEFT] or keys[pygame.K_a]):
            player_x -= move_speed

        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            player_x += move_speed

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

        # Moving blocks
        moving_block.x += moving_speed * moving_direction1
        if moving_block.x < moving_limit_left1 or moving_block.x > moving_limit_right1:
            moving_direction1 *= -1


        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in blocks + [moving_block]:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        # Jump block logic
        for jump_block in jump_blocks:
            if player_rect.colliderect(jump_block):
                # Falling onto a jump block
                if velocity_y > 0 and player_y + img_height - velocity_y <= jump_block.y:
                    player_y = jump_block.y - img_height
                    velocity_y = -25  # Apply upward velocity for the jump
                    on_ground = True

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

            if player_y > (SCREEN_HEIGHT + 50):
                fall_text = in_game.get("fall_message", "Fell too far!")
                screen.blit(font.render(fall_text, True, (255, 0, 0)), (20, 50))
                fall_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = 150, 500
                velocity_y = 0
                deathcount += 1

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if complete_levels < 2:
                complete_levels = 2
                update_locked_levels()
            warp_sound.play()
            running = False
            set_page('lvl3_screen')    

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 100:
            camera_y = player_y - 100
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Drawing
        screen.fill((0, 102, 51))

        for spike in spikes:
            pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])
            # Spike death
            bottom_points = [
                (player_x + img_width // 2, player_y + img_height),
                (player_x + 5, player_y + img_height),
                (player_x + img_width - 5, player_y + img_height)
            ]
            collision_detected = False  # Flag to stop further checks after a collision
            if collision_detected:
                    break  # Exit the outer loop if a collision has already been detected
            for point in bottom_points:
                    if point_in_triangle(point[0], point[1], *spike):
                        player_x, player_y = 150, 500
                        death_text = in_game.get("dead_message", "You Died")
                        screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                        death_sound.play()
                        pygame.display.update()
                        pygame.time.delay(300)
                        velocity_y = 0
                        deathcount += 1
                        collision_detected = True  # Set the flag to stop further checks
                        break

            # Spike death (including top collision detection)
            top_points = [
                    (player_x + img_width // 2, player_y),  # Center top point
                    (player_x + 5, player_y),               # Left top point
                    (player_x + img_width - 5, player_y)    # Right top point
            ]
            collision_detected = False  # Flag to stop further checks after a collision
            if collision_detected:
                break  # Exit the outer loop if a collision has already been detected
            for point in top_points:
                if point_in_triangle(point[0], point[1], *spike):
                    # Trigger death logic
                        player_x, player_y = 150, 500  # Reset player position
                        death_text = in_game.get("dead_message", "You Died")
                        screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                        death_sound.play()
                        pygame.display.update()
                        pygame.time.delay(300)
                        velocity_y = 0
                        deathcount += 1
                        collision_detected = True  # Set the flag to stop further checks
                        break

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))
        
        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))
  
        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (jump_block.x - camera_x, jump_block.y - camera_y, jump_block.width, jump_block.height))

        pygame.draw.rect(screen, (0, 205, 0), (exit_portal.x - camera_x, exit_portal.y - camera_y, exit_portal.width, exit_portal.height))
        screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

            # Inside the game loop:
        screen.blit(rendered_jump_text, (900 - camera_x, 500 - camera_y))  # Draws the rendered up text

        levels = load_language(lang_code).get('levels', {})
        lvl2_text = levels.get("lvl2", "Level 2")  # Render the level text
        screen.blit(font.render(lvl2_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        pygame.display.update()    

def create_lvl3_screen():
    global player_img, font, screen, complete_levels

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 0  
    camera_y = 0
    spawn_x, spawn_y = 150, 600
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0

    # Load player image
    player_img = pygame.image.load("robot.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(200, 200, 80, 50)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(2000, -300, 80, 50)  # x, y, width, height
    checkpoint_reached2 = False

    key_block_pairs = [
        {
            "key": (300, 200, 30, (255, 255, 0)),
            "block": pygame.Rect(2550, 250, 200, 200),
            "collected": False
        },
    ]

    saws = [
        (650, 750, 80,(255, 0, 0)),  # (x, y, radius, color)
        (1700, 335, 100,(255, 0, 0)),  # (x, y, radius, color)
        (1200, 335, 100,(255, 0, 0)),
        (800, 335, 100,(255, 0, 0)),
        (1850, -170, 80,(255, 0, 0)),
        (1550, -400, 80,(255, 0, 0)),
        (1250, -400, 80,(255, 0, 0)),
        (950, -170, 80,(255, 0, 0)),
    ]

    blocks=[
        pygame.Rect(-1500, 906, 900, 100),
        pygame.Rect(100, 750, 2000, 900),
        pygame.Rect(100, 300, 2000, 50),
        pygame.Rect(100, -150, 2200, 50),
        pygame.Rect(-900, -360, 1000, 9000),
        pygame.Rect(1250, -450, 300, 50),
    ]

    jump_blocks = [
        pygame.Rect(950, 700, 100, 50), # Jump blocks to help the character go up and then fall down
        pygame.Rect(2300, 751, 100, 100),
        pygame.Rect(2600, 285, 120, 100),
    ]


    spikes = [
    [(700, 350), (750, 400), (800, 350)],
    [(900, 350), (950, 400), (1000, 350)],
    [(1000, 350), (1050, 400), (1100, 350)],
    [(1100, 350), (1150, 400), (1200, 350)],
    [(2000, 750), (2050, 700), (2100, 750)],
    ]

    exit_portal = pygame.Rect(500, -250, 50, 100)
    clock = pygame.time.Clock()

    def point_in_triangle(px, py, a, b, c):
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        b1 = sign((px, py), a, b) < 0.0
        b2 = sign((px, py), b, c) < 0.0
        b3 = sign((px, py), c, a) < 0.0
        return b1 == b2 == b3
    
    # Render the texts

    saw_text = in_game.get("saws_message", "Saws are also dangerous!")
    rendered_saw_text = font.render(saw_text, True, (255, 0, 0))  # Render the saw text

    key_text = in_game.get("key_message", "Grab the coin and open the block!")
    rendered_key_text = font.render(key_text, True, (255, 255, 0))  # Render the key text

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        if keys[pygame.K_r]:
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 150, 600
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength

        if (keys[pygame.K_LEFT] or keys[pygame.K_a]):
            player_x -= move_speed

        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            player_x += move_speed

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

        # Moving blocks

        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in blocks:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        # Jump block logic
        for jump_block in jump_blocks:
            if player_rect.colliderect(jump_block):
                # Falling onto a jump block
                if velocity_y > 0 and player_y + img_height - velocity_y <= jump_block.y:
                    player_y = jump_block.y - img_height
                    velocity_y = -33  # Apply upward velocity for the jump
                    on_ground = True

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

            if player_y > (SCREEN_HEIGHT + 50):
                fall_text = in_game.get("fall_message", "Fell too far!")
                screen.blit(font.render(fall_text, True, (255, 0, 0)), (20, 50))
                fall_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                velocity_y = 0
                deathcount += 1

        for pair in key_block_pairs:
            if not pair["collected"]:  # Only active locked blocks
                block = pair["block"]
                if player_rect.colliderect(block):
            # Falling onto a block
                    if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                        player_y = block.y - img_height
                        velocity_y = 0
                        on_ground = True

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


        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 200, 100  # Store checkpoint position
            checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 2020, -400  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if complete_levels < 3:
                complete_levels = 3
                update_locked_levels()
            warp_sound.play()
            running = False
            set_page('lvl4_screen')

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 100:
            camera_y = player_y - 100
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Drawing
        screen.fill((0, 102, 51))

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint
        
        # Draw key only if not collected
 
        # Draw all saws first
        for x, y, r, color in saws:
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        # Now check for collision with all saws
        collision_detected = False
        for x, y, r, color in saws:
            closest_x = max(player_rect.left, min(x, player_rect.right))
            closest_y = max(player_rect.top, min(y, player_rect.bottom))
            dx = closest_x - x
            dy = closest_y - y
            distance = (dx**2 + dy**2)**0.5
            if distance < r:
                if not collision_detected:
                    sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                    screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                    death_sound.play()
                    pygame.display.update()
                    pygame.time.delay(300)
                    player_x, player_y = spawn_x, spawn_y
                    deathcount += 1
                    collision_detected = True
                break  # Only die once per frame

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
  
        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

        for spike in spikes:
            pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])
            # Spike death
            bottom_points = [
                (player_x + img_width // 2, player_y + img_height),
                (player_x + 5, player_y + img_height),
                (player_x + img_width - 5, player_y + img_height)
            ]
            collision_detected = False  # Flag to stop further checks after a collision
            if collision_detected:
                    break  # Exit the outer loop if a collision has already been detected
            for point in bottom_points:
                    if point_in_triangle(point[0], point[1], *spike):
                        player_x, player_y = spawn_x, spawn_y
                        death_text = in_game.get("dead_message", "You Died")
                        death_sound.play()
                        collision_detected = True  # Set the flag to stop further checks
                        screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                        pygame.display.update()
                        pygame.time.delay(300)
                        velocity_y = 0
                        deathcount += 1
                        break

            # Spike death (including top collision detection)
            top_points = [
                    (player_x + img_width // 2, player_y),  # Center top point
                    (player_x + 5, player_y),               # Left top point
                    (player_x + img_width - 5, player_y)    # Right top point
            ]
            collision_detected = False  # Flag to stop further checks after a collision
            if collision_detected:
                break  # Exit the outer loop if a collision has already been detected
            for point in top_points:
                if point_in_triangle(point[0], point[1], *spike):
                    # Trigger death logic
                        player_x, player_y = spawn_x, spawn_y  # Reset player position
                        death_text = in_game.get("dead_message", "You Died")
                        screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                        death_sound.play()
                        pygame.display.update()
                        pygame.time.delay(300)
                        velocity_y = 0
                        deathcount += 1
                        collision_detected = True  # Set the flag to stop further checks
                        break

        
        for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            # Check collision if not yet collected
            if not pair["collected"]:
                key_rect = pygame.Rect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)
            if player_rect.colliderect(key_rect):
                if not pair["collected"]:
                    open_sound.play()
                pair["collected"] = True
            
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)

            # Draw block only if key is not collected
            if not pair["collected"]:
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

        pygame.draw.rect(screen, (0, 205, 0), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        screen.blit(rendered_saw_text, (int(1550 - camera_x), int(150 - camera_y)))  # Draws the rendered up text
        screen.blit(rendered_key_text, (int(2500 - camera_x), int(200 - camera_y)))  # Draws the rendered up text


        levels = load_language(lang_code).get('levels', {})
        lvl3_text = levels.get("lvl3", "Level 3")  # Render the level text
        screen.blit(font.render(lvl3_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text
        pygame.display.update()    

def create_lvl4_screen():
    global player_img, font, screen, complete_levels

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 0  
    camera_y = 0
    spawn_x, spawn_y = 250, 450
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0

    # Load player image
    player_img = pygame.image.load("robot.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(2650, 30, 80, 50)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(3200, 100, 80, 50)  # x, y, width, height
    checkpoint_reached2 = False

    key_block_pairs = [
        {
            "key": (3820, -130, 30, (255, 255, 0)),
            "block": pygame.Rect(2800, 30, 200, 200),
            "collected": False
        },
    ]

    moving_blocks = [
        {
        'rect': pygame.Rect(4050, 450, 100, 20),
        'axis': 'x',  # 'x' for horizontal, 'y' for vertical
        'speed': 2,
        'min': 4050,
        'max': 4350
        },
        {
        'rect': pygame.Rect(4850, 450, 100, 20),
        'axis': 'x',
        'speed': 2,
        'min': 4550,
        'max': 4850
        },
    ]

    lasers = [
        pygame.Rect(3000, -50, 1000, 15),
    ]

    blocks = [
        pygame.Rect(200, 650, 650, 100),
        pygame.Rect(1100, 510, 100, 100),
        pygame.Rect(1450, 650, 650, 100),
        pygame.Rect(2300, 230, 1000, 800),
        pygame.Rect(2800, 400, 1200, 600),
        pygame.Rect(2800, -370, 200, 400),
        pygame.Rect(3100, -300, 450, 100),
        pygame.Rect(3700, -100, 200, 100),
        pygame.Rect(4000, -370, 200, 400),
    ]

    moving_saws = [ 
        {'r': 100, 'speed': 5, 'cx': 3800, 'cy': -300, 'max': -50, 'min': -700},
    ]

    saws = [
        (650, 630, 80,(255, 0, 0)),  # (x, y, radius, color)
        (2520, 230 , 90,(255, 0, 0)),
        (3320, 400, 100,(255, 0, 0)),  # (x, y, radius, color)
        (4950, 150, 100,(255, 0, 0)),  # (x, y, radius, color)
        (4950, 550, 100,(255, 0, 0)),  # (x, y, radius, color)
        (4500, 425, 60, (255, 0, 0)),  # (x, y, radius, color)
    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 2},
        {'r': 40, 'orbit_radius': 230, 'angle': 90, 'speed': 2},
        {'r': 40, 'orbit_radius': 230, 'angle': 180, 'speed': 2},
        {'r': 40, 'orbit_radius': 230, 'angle': 270, 'speed': 2},
    ]


    jump_blocks = [
        pygame.Rect(2200, 751, 100, 100),
        pygame.Rect(2400, 130, 120, 100),
        
    ]

    spikes = [
    [(2000, 650), (2050, 600), (2100, 650)],
    [(3300,-300), (3350, -350), (3400, -300)],
    [(3800, 400), (3850, 350), (3900, 400)],
    [(3900, 400), (3950, 350), (4000, 400)],
    ]
    exit_portal = pygame.Rect(4950, 350, 50, 100)
    clock = pygame.time.Clock()

    def point_in_triangle(px, py, a, b, c):
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        b1 = sign((px, py), a, b) < 0.0
        b2 = sign((px, py), b, c) < 0.0
        b3 = sign((px, py), c, a) < 0.0
        return b1 == b2 == b3

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        if keys[pygame.K_r]:
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 250, 450
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength

        if (keys[pygame.K_LEFT] or keys[pygame.K_a]):
            player_x -= move_speed

        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            player_x += move_speed

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in blocks:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        for block in moving_blocks:
            rect = block['rect']
            axis = block['axis']
            speed = block['speed']

    # Update the block's position
            if axis == 'x':
                rect.x += speed
                if rect.x < block['min'] or rect.x > block['max']:
                    block['speed'] = -speed  # Reverse direction
            elif axis == 'y':
                rect.y += speed
                if rect.y < block['min'] or rect.y > block['max']:
                    block['speed'] = -speed  # Reverse direction

    # Check if the player is standing on the block
            if player_rect.colliderect(rect):
        # Falling onto the block
                if velocity_y > 0 and player_y + img_height - velocity_y <= rect.y:
                    player_y = rect.y - img_height
                    velocity_y = 0
                    on_ground = True

            # Move the player with the block
                    if axis == 'x':
                        player_x += speed
                    elif axis == 'y':
                        player_y += speed

        # Jump block logic
        for jump_block in jump_blocks:
            if player_rect.colliderect(jump_block):
                # Falling onto a jump block
                if velocity_y > 0 and player_y + img_height - velocity_y <= jump_block.y:
                    player_y = jump_block.y - img_height
                    velocity_y = -33  # Apply upward velocity for the jump
                    on_ground = True

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

        if player_y > (SCREEN_HEIGHT + 50):
            fall_text = in_game.get("fall_message", "Fell too far!")
            screen.blit(font.render(fall_text, True, (255, 0, 0)), (20, 50))
            fall_sound.play()
            pygame.display.update()
            pygame.time.delay(300)
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Saw collision detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        for pair in key_block_pairs:
            if not pair["collected"]:  # Only active locked blocks
                block = pair["block"]
                if player_rect.colliderect(block):
            # Falling onto a block
                    if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                        player_y = block.y - img_height
                        velocity_y = 0
                        on_ground = True

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


        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2670, 15  # Store checkpoint position
            checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3150, 100  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):

            if complete_levels < 4:
                complete_levels = 4
                update_locked_levels()
            warp_sound.play()
            running = False
            set_page('lvl5_screen') 

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Drawing
        screen.fill((0, 102, 51))

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        collision_detected = False  
        for rotating_saw in rotating_saws:
            if collision_detected:
                break  # Exit the loop if a collision has already been detected

    # Update angle
            rotating_saw['angle'] = (rotating_saw['angle'] + rotating_saw['speed']) % 360
            rad = math.radians(rotating_saw['angle'])

    # Orbit around block center
            orbit_center_x = blocks[1].centerx
            orbit_center_y = blocks[1].centery
            x = orbit_center_x + rotating_saw['orbit_radius'] * math.cos(rad)
            y = orbit_center_y + rotating_saw['orbit_radius'] * math.sin(rad)

    # Draw the saw
            pygame.draw.circle(screen, (255, 0, 0), (int(x - camera_x), int(y - camera_y)), rotating_saw['r'])

    # Collision detection
            closest_x = max(player_rect.left, min(x, player_rect.right))
            closest_y = max(player_rect.top, min(y, player_rect.bottom))
            dx = closest_x - x
            dy = closest_y - y
            distance = (dx**2 + dy**2)**0.5

            if distance < rotating_saw['r'] and not collision_detected:
            # Trigger death logic                
                collision_detected = True  # Set the flag to stop further checks
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")    
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))               
                player_x, player_y = spawn_x, spawn_y  # Reset player position    
                deathcount += 1        
                death_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                key_block_pairs[0]["collected"] = False
                break
                

        for saw in moving_saws:
    # Update the circle's position (move vertically)
            saw['cy'] += saw['speed']  # Move down or up depending on speed

    # Check if the saw has reached the limits
            if saw['cy'] > saw['max'] or saw['cy'] < saw['min']:
                saw['speed'] = -saw['speed']  # Reverse direction if we hit a limit

    # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

    # Collision detection (if needed)
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5
            if distance < saw['r']:
        # Trigger death logic
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                death_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Draw all saws first
        for x, y, r, color in saws:
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        # Now check for collision with all saws
        for saw in saws:
            saw_x, saw_y, saw_radius, _ = saw

        # Find the closest point on the player's rectangle to the saw's center
            closest_x = max(player_rect.left, min(saw_x, player_rect.right))
            closest_y = max(player_rect.top, min(saw_y, player_rect.bottom))

            # Calculate the distance between the closest point and the saw's center
            dx = closest_x - saw_x
            dy = closest_y - saw_y
            distance = (dx**2 + dy**2)**0.5

            # Check if the distance is less than the saw's radius
            if distance < saw_radius:
                    # Trigger death logic
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_sound.play()
                deathcount += 1
                pygame.display.update()
                pygame.time.delay(300)  
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Draw all lasers first
        for laser in lasers:
            pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))

        # Then check for collision with lasers
        for laser in lasers:
            # Check if the player collides with the laser
            if player_rect.colliderect(laser):
                # Trigger death logic
                player_x, player_y = spawn_x, spawn_y
                laser_text = in_game.get("laser_message", "Lasered!")
                screen.blit(font.render(laser_text, True, (255, 0, 0)), (20, 50))
                laser_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
  
        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

        for spike in spikes:
            pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])
            # Spike death
            bottom_points = [
                (player_x + img_width // 2, player_y + img_height),
                (player_x + 5, player_y + img_height),
                (player_x + img_width - 5, player_y + img_height)
            ]
            collision_detected = False  # Flag to stop further checks after a collision
            if collision_detected:
                    break  # Exit the outer loop if a collision has already been detected
            for point in bottom_points:
                    if point_in_triangle(point[0], point[1], *spike):
                        player_x, player_y = spawn_x, spawn_y
                        death_text = in_game.get("dead_message", "You Died")
                        death_sound.play()
                        collision_detected = True  # Set the flag to stop further checks
                        screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                        pygame.display.update()
                        pygame.time.delay(300)
                        velocity_y = 0
                        deathcount += 1
                        key_block_pairs[0]["collected"] = False  # Reset the collected status for the key
                        break

            # Spike death (including top collision detection)
            top_points = [
                    (player_x + img_width // 2, player_y),  # Center top point
                    (player_x + 5, player_y),               # Left top point
                    (player_x + img_width - 5, player_y)    # Right top point
            ]
            collision_detected = False  # Flag to stop further checks after a collision
            if collision_detected:
                break  # Exit the outer loop if a collision has already been detected
            for point in top_points:
                if point_in_triangle(point[0], point[1], *spike):
                    # Trigger death logic
                        player_x, player_y = spawn_x, spawn_y  # Reset player position
                        death_text = in_game.get("dead_message", "You Died")
                        screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                        death_sound.play()
                        pygame.display.update()
                        pygame.time.delay(300)
                        velocity_y = 0
                        deathcount += 1
                        collision_detected = True  # Set the flag to stop further checks
                        break

        
        for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            # Check collision if not yet collected
            if not pair["collected"]:
                key_rect = pygame.Rect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)
            if player_rect.colliderect(key_rect):
                if not pair["collected"]:
                    open_sound.play()
                pair["collected"] = True
            
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)

            # Draw block only if key is not collected
            if not pair["collected"]:
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

        for block in moving_blocks:
            rect = block['rect']
            axis = block['axis']
            speed = block['speed']

            if axis == 'x':
                rect.x += speed
                if rect.x < block['min'] or rect.x > block['max']:
                    block['speed'] = -speed  # Reverse direction
            elif axis == 'y':
                rect.y += speed
                if rect.y < block['min'] or rect.y > block['max']:
                    block['speed'] = -speed  # Reverse direction

            # Draw the block
            pygame.draw.rect(screen, (128, 0, 128), rect.move(-camera_x, -camera_y))


        pygame.draw.rect(screen, (0, 205, 0), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))


        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts

        levels = load_language(lang_code).get('levels', {})
        lvl4_text = levels.get("lvl4", "Level 4")  # Render the level text
        screen.blit(font.render(lvl4_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        pygame.display.update()   

def create_lvl5_screen():
    global player_img, font, screen, complete_levels

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 0  
    camera_y = 0
    spawn_x, spawn_y = 220, 400
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0

    # Load player image
    player_img = pygame.image.load("robot.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(2100, -150, 80, 50)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(3450, -450, 80, 50)  # x, y, width, height
    checkpoint_reached2 = False

    key_block_pairs = [
        {
            "key": (4050, -800, 30, (255, 255, 0)),
            "block": pygame.Rect(1300, -250, 200, 200),
            "collected": False
        },
    ]

    blocks = [
        pygame.Rect(200, 650, 750, 100),
        pygame.Rect(900, 510, 100, 100),
        pygame.Rect(1450, 650, 650, 100),
        pygame.Rect(1500, -50, 700, 50),
        pygame.Rect(1700, -350, 1050, 50),
        pygame.Rect(1500, -250, 50, 200),
        pygame.Rect(2700, -349, 50, 130),
        pygame.Rect(2700, -220, 200, 50),
        pygame.Rect(2880, -345, 50, 175),
        pygame.Rect(2880, -350, 700, 50),
        pygame.Rect(3700, -350, 100, 30),
        pygame.Rect(3700, -50, 100, 30),
        pygame.Rect(3700, -650, 100, 30),
        pygame.Rect(4000, -150, 100, 30),
        pygame.Rect(4000, -750, 100, 30),
        pygame.Rect(4000, -450, 100, 30),
        pygame.Rect(4300, -50, 100, 30),
        pygame.Rect(4300, -350, 100, 30),
        pygame.Rect(4300, -650, 100, 30),
        pygame.Rect(4600, -150, 100, 30),
        pygame.Rect(4600, -750, 100, 30),
        pygame.Rect(4600, -450, 100, 30),        
    ]
    
    moving_saws = [ 
        {'r': 100, 'speed': 6, 'cx': 1200, 'cy': 200, 'max': 700, 'min': 200},
    ]

    moving_saws_x = [
        {'r': 100, 'speed': 8, 'cx': 2400, 'cy': -500, 'max': 3300, 'min': 2400},
    ]

    saws = [
        (500, 630, 80,(255, 0, 0)),  # (x, y, radius, color)
        (1000, 630 , 80,(255, 0, 0)),
        (2000, -360, 80,(255, 0, 0)),  # (x, y, radius, color)
        (2400, -360, 80,(255, 0, 0)),  # (x, y, radius, color)
    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 2},
        {'r': 40, 'orbit_radius': 230, 'angle': 180, 'speed': 2},
    ]


    jump_blocks = [
        pygame.Rect(2200, 751, 100, 100),
        pygame.Rect(2400, 420, 120, 100),
    ]

    spikes = [
        [(1660, 650), (1710, 600), (1760, 650)],
        [(2000, 650), (2050, 600), (2100, 650)],
        [(3300,-350), (3350, -400), (3400, -350)],
        [(3700, -50), (3750, -100), (3800, -50)],
        [(3700, -650), (3750, -700), (3800, -650)],
        [(4000, -450), (4050, -500), (4100, -450)],
        [(4300, -50), (4350, -100), (4400, -50)],
        [(4600, -750), (4650, -800), (4700, -750)],
        [(4600, -150), (4650, -200), (4700, -150)],
    ]

    spikes_01 = [
    [(3700, -350), (3750, -400), (3800, -350)],
    [(4000, -150), (4050, -200), (4100, -150)],
    [(4300, -350), (4350, -400), (4400, -350)],
    [(4300, -650), (4350, -700), (4400, -650)],
    [(4600, -450), (4650, -500), (4700, -450)],
    ]

    exit_portal = pygame.Rect(1375, 0, 50, 100)
    clock = pygame.time.Clock()

    def point_in_triangle(px, py, a, b, c):
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        b1 = sign((px, py), a, b) < 0.0
        b2 = sign((px, py), b, c) < 0.0
        b3 = sign((px, py), c, a) < 0.0
        return b1 == b2 == b3
    
    # Render the texts

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        if keys[pygame.K_r]:
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 220, 400
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength

        if (keys[pygame.K_LEFT] or keys[pygame.K_a]):
            player_x -= move_speed

        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            player_x += move_speed

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in blocks:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

    # Draw the block
            pygame.draw.rect(screen, (0, 255, 0), rect.move(-camera_x, -camera_y))

        # Jump block logic
        for jump_block in jump_blocks:
            if player_rect.colliderect(jump_block):
                # Falling onto a jump block
                if velocity_y > 0 and player_y + img_height - velocity_y <= jump_block.y:
                    player_y = jump_block.y - img_height
                    velocity_y = -33  # Apply upward velocity for the jump
                    on_ground = True

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

        if player_y > (SCREEN_HEIGHT + 50):
            fall_text = in_game.get("fall_message", "Fell too far!")
            screen.blit(font.render(fall_text, True, (255, 0, 0)), (20, 50))
            fall_sound.play()
            pygame.display.update()
            pygame.time.delay(300)
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Saw collision detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        for pair in key_block_pairs:
            if not pair["collected"]:  # Only active locked blocks
                block = pair["block"]
                if player_rect.colliderect(block):
            # Falling onto a block
                    if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                        player_y = block.y - img_height
                        velocity_y = 0
                        on_ground = True

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


        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2050, -200  # Store checkpoint position
            checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3450, -550  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            running = False
            if complete_levels < 5:
                complete_levels =  5
                update_locked_levels()
            warp_sound.play()
            set_page('lvl6_screen')
            
        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Drawing
        screen.fill((0, 102, 51))

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        collision_detected = False  
        for rotating_saw in rotating_saws:
            if collision_detected:
                break  # Exit the loop if a collision has already been detected

    # Update angle
            rotating_saw['angle'] = (rotating_saw['angle'] + rotating_saw['speed']) % 360
            rad = math.radians(rotating_saw['angle'])

    # Orbit around block center
            orbit_center_x = blocks[1].centerx
            orbit_center_y = blocks[1].centery
            x = orbit_center_x + rotating_saw['orbit_radius'] * math.cos(rad)
            y = orbit_center_y + rotating_saw['orbit_radius'] * math.sin(rad)

    # Draw the saw
            pygame.draw.circle(screen, (255, 0, 0), (int(x - camera_x), int(y - camera_y)), rotating_saw['r'])

    # Collision detection
            closest_x = max(player_rect.left, min(x, player_rect.right))
            closest_y = max(player_rect.top, min(y, player_rect.bottom))
            dx = closest_x - x
            dy = closest_y - y
            distance = (dx**2 + dy**2)**0.5

            if not any(distance < rotating_saw['r'] for rotating_saw in rotating_saws):
                recently_died = False  # Reset the flag when the player is no longer colliding

            if distance < rotating_saw['r'] and not collision_detected:
            # Trigger death logic                
                collision_detected = True  # Set the flag to stop further checks
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")    
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))               
                player_x, player_y = spawn_x, spawn_y  # Reset player position    
                death_sound.play()
                deathcount += 1        
                pygame.display.update()
                pygame.time.delay(300)
                key_block_pairs[0]["collected"] = False
                break
                

        for saw in moving_saws:
    # Update the circle's position (move vertically)
            saw['cy'] += saw['speed']  # Move down or up depending on speed

    # Check if the saw has reached the limits
            if saw['cy'] > saw['max'] or saw['cy'] < saw['min']:
                saw['speed'] = -saw['speed']  # Reverse direction if we hit a limit

    # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

    # Collision detection (if needed)
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5
            if distance < saw['r']:
        # Trigger death logic
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                death_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        for saw in moving_saws_x:
    # Update the circle's position (move vertically)
            saw['cx'] += saw['speed']
    # Check if the saw has reached the limits
            if saw['cx'] > saw['max'] or saw['cx'] < saw['min']:
                saw['speed'] = -saw['speed']  # Reverse direction if we hit a limit

    # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

    # Collision detection (if needed)
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5
            if distance < saw['r']:
        # Trigger death logic
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                death_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        for x, y, r, color in saws:
            # Draw the saw as a circle
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        for saw in saws:
            saw_x, saw_y, saw_radius, _ = saw

        # Find the closest point on the player's rectangle to the saw's center
            closest_x = max(player_rect.left, min(saw_x, player_rect.right))
            closest_y = max(player_rect.top, min(saw_y, player_rect.bottom))

            # Calculate the distance between the closest point and the saw's center
            dx = closest_x - saw_x
            dy = closest_y - saw_y
            distance = (dx**2 + dy**2)**0.5

            # Check if the distance is less than the saw's radius
            if distance < saw_radius:
                # Trigger death logic
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                death_sound.play()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                pygame.display.update()
                pygame.time.delay(300)  
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key


        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
  
        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

        for spike in spikes:
            pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])
            # Spike death
            bottom_points = [
                (player_x + img_width // 2, player_y + img_height),
                (player_x + 5, player_y + img_height),
                (player_x + img_width - 5, player_y + img_height)
            ]
            collision_detected = False  # Flag to stop further checks after a collision
            if collision_detected:
                    break  # Exit the outer loop if a collision has already been detected
            for point in bottom_points:
                    if point_in_triangle(point[0], point[1], *spike):
                        player_x, player_y = spawn_x, spawn_y
                        death_text = in_game.get("dead_message", "You Died")
                        death_sound.play()
                        collision_detected = True  # Set the flag to stop further checks
                        screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                        pygame.display.update()
                        pygame.time.delay(300)
                        velocity_y = 0
                        deathcount += 1
                        key_block_pairs[0]["collected"] = False  # Reset the collected status for the key
                        break

            # Spike death (including top collision detection)
            top_points = [
                    (player_x + img_width // 2, player_y),  # Center top point
                    (player_x + 5, player_y),               # Left top point
                    (player_x + img_width - 5, player_y)    # Right top point
            ]
            collision_detected = False  # Flag to stop further checks after a collision
            if collision_detected:
                break  # Exit the outer loop if a collision has already been detected
            for point in top_points:
                if point_in_triangle(point[0], point[1], *spike):
                    # Trigger death logic
                        player_x, player_y = spawn_x, spawn_y  # Reset player position
                        death_text = in_game.get("dead_message", "You Died")
                        screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                        death_sound.play()
                        pygame.display.update()
                        pygame.time.delay(300)
                        velocity_y = 0
                        deathcount += 1
                        collision_detected = True  # Set the flag to stop further checks
                        break


        for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            # Check collision if not yet collected
            if not pair["collected"]:
                key_rect = pygame.Rect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)
            if player_rect.colliderect(key_rect):
                if not pair["collected"]:
                    open_sound.play()
                pair["collected"] = True
            
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)

            # Draw block only if key is not collected
            if not pair["collected"]:
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

        if key_block_pairs[0]["collected"]:
    # Draw the spikes
            for spike in spikes_01:
                pygame.draw.polygon(screen, (255, 0, 0), [((x - camera_x), (y - camera_y)) for x, y in spike])

            bottom_points = [
            (player_x + img_width // 2, player_y + img_height),
            (player_x + 5, player_y + img_height),
            (player_x + img_width - 5, player_y + img_height)
            ]

    # Check collision with spikes_01
            collision_detected = False
            for spike in spikes_01:
                if collision_detected:
                    break  # Exit the loop if a collision has already been detected
                for point in bottom_points:  # Use bottom points of the player for collision
                    if point_in_triangle(point[0], point[1], *spike):
                        # Trigger death logic
                        player_x, player_y = spawn_x, spawn_y  # Reset player position
                        death_text = in_game.get("dead_message", "You Died")
                        screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                        death_sound.play()
                        pygame.display.update()
                        pygame.time.delay(300)
                        velocity_y = 0
                        deathcount += 1
                        collision_detected = True  # Set the flag to stop further checks
                        key_block_pairs[0]["collected"] = False  # Reset the collected status for the key
                        break


        pygame.draw.rect(screen, (0, 205, 0), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts

        levels = load_language(lang_code).get('levels', {})
        lvl5_text = levels.get("lvl5", "Level 5")  # Render the level text
        screen.blit(font.render(lvl5_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        pygame.display.update()   

def create_lvl6_screen():
    global player_img, font, screen, complete_levels

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = 0
    spawn_x, spawn_y = 220, 500
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0

    # Load player image
    player_img = pygame.image.load("robot.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(2400, 450, 80, 50)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(3200, 470, 80, 50)  # x, y, width, height
    checkpoint_reached2 = False

    key_block_pairs = [
        {
            "key": (5800, 50, 30, (255, 255, 0)),
            "block": pygame.Rect(2950, 10, 200, 170),
            "collected": False
        },
    ]

    invisible_blocks = [
        pygame.Rect(1400, 400, 100, 100),
        pygame.Rect(1700, 400, 100, 100),
        pygame.Rect(2000, 400, 100, 100),
    ]

    lasers = [
        pygame.Rect(5870, 180, 15, 350),
    ]

    blocks = [
        pygame.Rect(-200, 700, 1200, 100),
        pygame.Rect(800, 400, 100, 100),
        pygame.Rect(2300, 500, 450, 50),
        pygame.Rect(2900, 10, 50, 540),
        pygame.Rect(3150, 10, 50, 120),
        pygame.Rect(2900, 530, 3000, 50),
        pygame.Rect(3150, 130, 2750, 50)
    ]
    
    moving_saws = [ 
        {'r': 100, 'speed': 20, 'cx': 3800, 'cy': -400, 'max': 600, 'min': -400},
    ]

    moving_saws_x = [
        {'r': 100, 'speed':16, 'cx': 4900, 'cy': 165, 'max': 5800, 'min': 4900}
    ]

    saws = [
        (1450, 450, 28, (255, 0, 127)),
        (1750, 450, 28, (255, 0, 127)),
        (2050, 450, 28, (255, 0, 127)),  # (x, y, radius, color)
        (5000, 550, 100, (255, 0, 0)),
        (5400, 550, 100, (255, 0, 0)),

    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 2},
        {'r': 40, 'orbit_radius': 230, 'angle': 120, 'speed': 2},
        {'r': 40, 'orbit_radius': 230, 'angle': 240, 'speed': 2},
    ]


    jump_blocks = [
        pygame.Rect(1000, 600, 100, 50),
        pygame.Rect(400, 650, 100, 50),
        pygame.Rect(2650, 400, 100, 100),
    ]

    spikes = [
    [(500, 700), (545, 600), (590, 700)],
    [(600,700), (645, 600), (690, 700)],
    [(700, 700), (745, 600), (790, 700)],
    [(4100, 130), (4150, 80), (4200, 130)],
    [(4210, 130), (4260, 80), (4310, 130)],
    [(4500, 130), (4550, 80), (4600, 130)],
    [(4610, 130),(4660, 80),(4710, 130)],
    [(4300, 530),(4345, 480), (4390, 530)],
    [(4400, 530), (4445, 480), (4490, 530)],
    ]

    exit_portal = pygame.Rect(5700, 430, 50, 100)
    clock = pygame.time.Clock()

    def point_in_triangle(px, py, a, b, c):
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        b1 = sign((px, py), a, b) < 0.0
        b2 = sign((px, py), b, c) < 0.0
        b3 = sign((px, py), c, a) < 0.0
        return b1 == b2 == b3

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        if keys[pygame.K_r]:
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 220, 500
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength

        if (keys[pygame.K_LEFT] or keys[pygame.K_a]):
            player_x -= move_speed

        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            player_x += move_speed

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in blocks:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        # Jump block logic
        for jump_block in jump_blocks:
            if player_rect.colliderect(jump_block):
                # Falling onto a jump block
                if velocity_y > 0 and player_y + img_height - velocity_y <= jump_block.y:
                    player_y = jump_block.y - img_height
                    velocity_y = -33  # Apply upward velocity for the jump
                    on_ground = True

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

        if player_y > (SCREEN_HEIGHT + 50):
            fall_text = in_game.get("fall_message", "Fell too far!")
            screen.blit(font.render(fall_text, True, (255, 0, 0)), (20, 50))
            fall_sound.play()
            pygame.display.update()
            pygame.time.delay(300)
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Saw collision detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        for pair in key_block_pairs:
            if not pair["collected"]:  # Only active locked blocks
                block = pair["block"]
                if player_rect.colliderect(block):
            # Falling onto a block
                    if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                        player_y = block.y - img_height
                        velocity_y = 0
                        on_ground = True

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


        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2400, 350  # Store checkpoint position
            checkpoint_sound.play()
            print("Checkpoint reached!")
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3150, 400  # Checkpoint position
            print("Checkpoint reached!")

        # Exit portal
        if player_rect.colliderect(exit_portal):
            running = False
            if complete_levels < 6:
                complete_levels =  6
                update_locked_levels()
            warp_sound.play()
            set_page('lvl7_screen')


        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        for block in invisible_blocks:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width
            
        for block in invisible_blocks:
            # Draw the invisible block as a gray rectangle 
            pygame.draw.rect(screen, (0, 0, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))        

        # Drawing
        screen.fill((0, 102, 51))

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        collision_detected = False  
        for rotating_saw in rotating_saws:
            if collision_detected:
                break  # Exit the loop if a collision has already been detected

    # Update angle
            rotating_saw['angle'] = (rotating_saw['angle'] + rotating_saw['speed']) % 360
            rad = math.radians(rotating_saw['angle'])

    # Orbit around block center
            orbit_center_x = blocks[1].centerx
            orbit_center_y = blocks[1].centery
            x = orbit_center_x + rotating_saw['orbit_radius'] * math.cos(rad)
            y = orbit_center_y + rotating_saw['orbit_radius'] * math.sin(rad)

    # Draw the saw
            pygame.draw.circle(screen, (255, 0, 0), (int(x - camera_x), int(y - camera_y)), rotating_saw['r'])

    # Collision detection
            closest_x = max(player_rect.left, min(x, player_rect.right))
            closest_y = max(player_rect.top, min(y, player_rect.bottom))
            dx = closest_x - x
            dy = closest_y - y
            distance = (dx**2 + dy**2)**0.5

            if distance < rotating_saw['r'] and not collision_detected:
            # Trigger death logic                
                collision_detected = True  # Set the flag to stop further checks
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")    
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))               
                player_x, player_y = spawn_x, spawn_y  # Reset player position    
                deathcount += 1        
                death_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                key_block_pairs[0]["collected"] = False
                break
                
        for saw in moving_saws:
    # Update the circle's position (move vertically)
            saw['cy'] += saw['speed']  # Move down or up depending on speed

    # Check if the saw has reached the limits
            if saw['cy'] > saw['max'] or saw['cy'] < saw['min']:
                saw['speed'] = -saw['speed']  # Reverse direction if we hit a limit

    # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

    # Collision detection (if needed)
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5
            if distance < saw['r']:
        # Trigger death logic
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                death_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        for saw in moving_saws_x:
    # Update the circle's position (move vertically)
            saw['cx'] += saw['speed']
    # Check if the saw has reached the limits
            if saw['cx'] > saw['max'] or saw['cx'] < saw['min']:
                saw['speed'] = -saw['speed']  # Reverse direction if we hit a limit

    # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

    # Collision detection (if needed)
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5
            if distance < saw['r']:
        # Trigger death logic
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                death_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key


        for x, y, r, color in saws:
            # Draw the saw as a circle
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        for saw in saws:
            saw_x, saw_y, saw_radius, _ = saw

        # Find the closest point on the player's rectangle to the saw's center
            closest_x = max(player_rect.left, min(saw_x, player_rect.right))
            closest_y = max(player_rect.top, min(saw_y, player_rect.bottom))

            # Calculate the distance between the closest point and the saw's center
            dx = closest_x - saw_x
            dy = closest_y - saw_y
            distance = (dx**2 + dy**2)**0.5

            # Check if the distance is less than the saw's radius
            if distance < saw_radius:
                    # Trigger death logic
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                death_sound.play()
                pygame.display.update()
                pygame.time.delay(300)  
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key


        for laser in lasers:
            pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))

        for laser in lasers:
            # Check if the player collides with the laser
            if player_rect.colliderect(laser):
                # Trigger death logic
                laser_text = in_game.get("laser_message", "Lasered!")
                screen.blit(font.render(laser_text, True, (255, 0, 0)), (20, 50))
                laser_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
  
        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

        for spike in spikes:
            pygame.draw.polygon(screen, (255, 0, 0), [((x - camera_x),( y - camera_y)) for x, y in spike])
        
        # Spike death
        bottom_points = [
            (player_x + img_width // 2, player_y + img_height),
            (player_x + 5, player_y + img_height),
            (player_x + img_width - 5, player_y + img_height)
        ]
        collision_detected = False  # Flag to stop further checks after a collision
        for spike in spikes:
            if collision_detected:
                break  # Exit the outer loop if a collision has already been detected
            for point in bottom_points:
                if point_in_triangle(point[0], point[1], *spike):
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                    death_sound.play()
                    pygame.display.update()
                    pygame.time.delay(300)
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    key_block_pairs[0]["collected"] = False  # Reset the collected status for the key
                    break

        # Spike death (including top collision detection)
        top_points = [
            (player_x + img_width // 2, player_y),  # Center top point
            (player_x + 5, player_y),               # Left top point
            (player_x + img_width - 5, player_y)    # Right top point
        ]
        collision_detected = False  # Flag to stop further checks after a collision
        for spike in spikes:
             if collision_detected:
               break  # Exit the outer loop if a collision has already been detected
             for point in top_points:
                if point_in_triangle(point[0], point[1], *spike):
            # Trigger death logic
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                    death_sound.play()
                    pygame.display.update()
                    pygame.time.delay(300)
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    key_block_pairs[0]["collected"] = False  # Reset the collected status for the key
                    break


        for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            # Check collision if not yet collected
            if not pair["collected"]:
                key_rect = pygame.Rect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)
            if player_rect.colliderect(key_rect):
                if not pair["collected"]:
                    open_sound.play()
                pair["collected"] = True
            
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)

            # Draw block only if key is not collected
            if not pair["collected"]:
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

        pygame.draw.rect(screen, (0, 205, 0), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        
        levels = load_language(lang_code).get('levels', {})
        lvl6_text = levels.get("lvl6", "Level 6")  # Render the level text
        screen.blit(font.render(lvl6_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        invisible_text = in_game.get("invisible_message", "These saws won't hurt you... promise!")
        screen.blit(font.render(invisible_text, True, (255, 51, 153)), (900 - camera_x, 250 - camera_y)) # Render the invisible block text

        pygame.display.update()   

def create_lvl7_screen():
    global player_img, font, screen, complete_levels

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = 0
    spawn_x, spawn_y = 100, 200
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0

    # Load player image
    player_img = pygame.image.load("robot.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(2600, 300, 80, 50)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(240, -1420, 80, 50)  # x, y, width, height
    checkpoint_reached2 = False

    blocks = [
        pygame.Rect(0, 400, 3000, 50),
        pygame.Rect(3200, 500, 500, 50),
        pygame.Rect(3900, 500, 500, 50),
        pygame.Rect(4600, 500, 700, 50),
        pygame.Rect(100, -1250, 300, 50),
        pygame.Rect(600, -1000, 700, 50),
        pygame.Rect(1450, -1125, 650, 50)
    ]
    
    moving_saws = [ 
        {'r': 100, 'speed': 9, 'cx': 3800, 'cy': 200, 'max': 700, 'min': 200},
        {'r': 100, 'speed': 9, 'cx': 4500, 'cy': 600, 'max': 700, 'min': 200},
    ]

    moving_saws_x = [
        {'r': 100, 'speed':11, 'cx': 700, 'cy': -975, 'max': 1200, 'min': 700},
        {'r': 100, 'speed': 7, 'cx': 1550, 'cy': -1100, 'max': 2000, 'min': 1550}
    ]

    saws = [
        (5000, 550, 100, (255, 0, 0)),
    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 3},
        {'r': 40, 'orbit_radius': 230, 'angle': 120, 'speed': 3},
        {'r': 40, 'orbit_radius': 230, 'angle': 240, 'speed': 3},
        {'r': 60, 'orbit_radius': 500, 'angle': 60, 'speed': 2},
        {'r': 60, 'orbit_radius': 500, 'angle': 180, 'speed': 2},
        {'r': 60, 'orbit_radius': 500, 'angle': 300, 'speed': 2},
        {'r': 80, 'orbit_radius': 900, 'angle': 0, 'speed': 1},
        {'r': 80, 'orbit_radius': 900, 'angle': 120, 'speed': 1},
        {'r': 80, 'orbit_radius': 900, 'angle': 240, 'speed': 1},
    ]

    spikes = [
    [(3400, 500), (3450, 450), (3500, 500)],
    [(4100, 500), (4150, 450), (4200, 500)],
    ]

    exit_portal = pygame.Rect(2050, -1225, 50, 100)
    clock = pygame.time.Clock()

    teleporters = [
        {
            "entry": pygame.Rect(5200, 400, 50, 100),
            "exit": pygame.Rect(100, -1400, 50, 100),
            "color": (0, 196, 255)
        }
    ]

    def point_in_triangle(px, py, a, b, c):
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        b1 = sign((px, py), a, b) < 0.0
        b2 = sign((px, py), b, c) < 0.0
        b3 = sign((px, py), c, a) < 0.0
        return b1 == b2 == b3

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        if keys[pygame.K_r]:
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 100, 200
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength

        if (keys[pygame.K_LEFT] or keys[pygame.K_a]):
            player_x -= move_speed

        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            player_x += move_speed

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in blocks:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        if player_y > SCREEN_HEIGHT:
            fall_text = in_game.get("fall_message", "Fell too far!")
            screen.blit(font.render(fall_text, True, (255, 0, 0)), (20, 50))
            pygame.display.update()
            pygame.time.delay(300)
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
        # Spike death
        bottom_points = [
            (player_x + img_width // 2, player_y + img_height),
            (player_x + 5, player_y + img_height),
            (player_x + img_width - 5, player_y + img_height)
        ]
        collision_detected = False  # Flag to stop further checks after a collision
        for spike in spikes:
            if collision_detected:
                break  # Exit the outer loop if a collision has already been detected
            for point in bottom_points:
                if point_in_triangle(point[0], point[1], *spike):
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                    pygame.display.update()
                    pygame.time.delay(300)
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    break

        # Spike death (including top collision detection)
        top_points = [
            (player_x + img_width // 2, player_y),  # Center top point
            (player_x + 5, player_y),               # Left top point
            (player_x + img_width - 5, player_y)    # Right top point
        ]
        collision_detected = False  # Flag to stop further checks after a collision
        for spike in spikes:
             if collision_detected:
               break  # Exit the outer loop if a collision has already been detected
             for point in top_points:
                if point_in_triangle(point[0], point[1], *spike):
            # Trigger death logic
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                    pygame.display.update()
                    pygame.time.delay(300)
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    break

        # Saw collision detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        player_center = player_rect.center

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2600, 250  # Store checkpoint position
            print("Checkpoint reached!")
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 150, -1500  # Checkpoint position
            print("Checkpoint reached!")

        for saw in saws:
            saw_x, saw_y, saw_radius, _ = saw

        # Find the closest point on the player's rectangle to the saw's center
            closest_x = max(player_rect.left, min(saw_x, player_rect.right))
            closest_y = max(player_rect.top, min(saw_y, player_rect.bottom))

            # Calculate the distance between the closest point and the saw's center
            dx = closest_x - saw_x
            dy = closest_y - saw_y
            distance = (dx**2 + dy**2)**0.5

            # Check if the distance is less than the saw's radius
            if distance < saw_radius:
                    # Trigger death logic
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                pygame.display.update()
                pygame.time.delay(300)  

        # Exit portal
        if player_rect.colliderect(exit_portal):
            running = False
            if complete_levels < 7:
                complete_levels = 7
                update_locked_levels()
            warp_sound.play()
            set_page('lvl8_screen')

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Drawing
        screen.fill((0, 102, 51))

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        collision_detected = False  
        for rotating_saw in rotating_saws:
            if collision_detected:
                break  # Exit the loop if a collision has already been detected

    # Update angle
            rotating_saw['angle'] = (rotating_saw['angle'] + rotating_saw['speed']) % 360
            rad = math.radians(rotating_saw['angle'])

    # Orbit around block center
            orbit_center_x = blocks[0].centerx
            orbit_center_y = blocks[0].centery
            x = orbit_center_x + rotating_saw['orbit_radius'] * math.cos(rad)
            y = orbit_center_y + rotating_saw['orbit_radius'] * math.sin(rad)

    # Draw the saw
            pygame.draw.circle(screen, (255, 0, 0), (int(x - camera_x), int(y - camera_y)), rotating_saw['r'])

    # Collision detection
            closest_x = max(player_rect.left, min(x, player_rect.right))
            closest_y = max(player_rect.top, min(y, player_rect.bottom))
            dx = closest_x - x
            dy = closest_y - y
            distance = (dx**2 + dy**2)**0.5

            if distance < rotating_saw['r'] and not collision_detected:
            # Trigger death logic                
                collision_detected = True  # Set the flag to stop further checks
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")    
                screen.blit(font.render(sawed_text, True, (0, 0, 0)), (20, 50))               
                player_x, player_y = spawn_x, spawn_y  # Reset player position    
                deathcount += 1        
                pygame.display.update()
                pygame.time.delay(300)
                break
                

        for saw in moving_saws:
    # Update the circle's position (move vertically)
            saw['cy'] += saw['speed']  # Move down or up depending on speed

    # Check if the saw has reached the limits
            if saw['cy'] > saw['max'] or saw['cy'] < saw['min']:
                saw['speed'] = -saw['speed']  # Reverse direction if we hit a limit

    # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

    # Collision detection (if needed)
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5
            if distance < saw['r']:
        # Trigger death logic
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1

        for saw in moving_saws_x:
    # Update the circle's position (move vertically)
            saw['cx'] += saw['speed']
    # Check if the saw has reached the limits
            if saw['cx'] > saw['max'] or saw['cx'] < saw['min']:
                saw['speed'] = -saw['speed']  # Reverse direction if we hit a limit

    # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

    # Collision detection (if needed)
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5
            if distance < saw['r']:
        # Trigger death logic
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 50))
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1

        for teleporter in teleporters:
            # Draw the entry rectangle
            pygame.draw.rect(screen, teleporter["color"], teleporter["entry"].move(-camera_x, -camera_y))
    
            # Draw the exit rectangle
            pygame.draw.rect(screen, teleporter["color"], teleporter["exit"].move(-camera_x, -camera_y))
    
           # Check if the player collides with the entry rectangle
            if player_rect.colliderect(teleporter["entry"]):
                # Teleport the player to the exit rectangle
                warp_sound.play()
                player_x, player_y = teleporter["exit"].x, teleporter["exit"].y
        
        for x, y, r, color in saws:
            # Draw the saw as a circle
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

        for spike in spikes:
            pygame.draw.polygon(screen, (255, 0, 0), [((x - camera_x),( y - camera_y)) for x, y in spike])

        pygame.draw.rect(screen, (0, 205, 0), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        
        levels = load_language(lang_code).get('levels', {})
        lvl7_text = levels.get("lvl7", "Level 7")  # Render the level text
        screen.blit(font.render(lvl7_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        portal_text = in_game.get("portal_message", "These blue portals teleport you! But to good places... mostly!")
        screen.blit(font.render(portal_text, True, (0, 196, 255)), (4400 - camera_x, 300 - camera_y))

        pygame.display.update()   

def create_lvl8_screen():
    global player_img, font, screen, complete_levels

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = 0
    spawn_x, spawn_y = 100, -1500
    player_x, player_y = spawn_x, spawn_y
    normal_speed = 50
    sprint_speed = 10
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    max_stamina = 100
    stamina = max_stamina
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0

    # Load player image
    player_img = pygame.image.load("robot.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(2600, 300, 80, 50)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(240, -1420, 80, 50)  # x, y, width, height
    checkpoint_reached2 = False

    key_block_pairs = [
        {
            "key": (5800, 50, 30, (255, 255, 0)),
            "block": pygame.Rect(2950, 10, 200, 170),
            "collected": False
        },
    ]

    invisible_blocks = [
        pygame.Rect(14000, 400, 100, 100),
        pygame.Rect(17000, 400, 100, 100),
        pygame.Rect(20000, 400, 100, 100),
    ]

    lasers = [
        pygame.Rect(5870, 180, 15, 350),
    ]

    blocks = [
        pygame.Rect(0, 400, 3000, 50),
        pygame.Rect(3200, 500, 500, 50),
        pygame.Rect(3900, 500, 500, 50),
        pygame.Rect(4600, 500, 700, 50),
        pygame.Rect(100, -1250, 300, 50),
        pygame.Rect(600, -1000, 700, 50),
        pygame.Rect(1450, -1125, 650, 50)
    ]
    
    moving_saws = [ 
        {'r': 100, 'speed': 9, 'cx': 3800, 'cy': 200, 'max': 700, 'min': 200},
        {'r': 100, 'speed': 9, 'cx': 4500, 'cy': 600, 'max': 700, 'min': 200},
    ]

    moving_saws_x = [
        {'r': 100, 'speed':11, 'cx': 700, 'cy': -975, 'max': 1200, 'min': 700},
        {'r': 100, 'speed': 7, 'cx': 1550, 'cy': -1100, 'max': 2000, 'min': 1550}
    ]

    saws = [
        (1450, 450, 28, (255, 0, 127)),
        (1750, 450, 28, (255, 0, 127)),
        (2050, 450, 28, (255, 0, 127)),  # (x, y, radius, color)
        (5000, 550, 100, (255, 0, 0)),
    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 3},
        {'r': 40, 'orbit_radius': 230, 'angle': 120, 'speed': 3},
        {'r': 40, 'orbit_radius': 230, 'angle': 240, 'speed': 3},
        {'r': 60, 'orbit_radius': 500, 'angle': 60, 'speed': 2},
        {'r': 60, 'orbit_radius': 500, 'angle': 180, 'speed': 2},
        {'r': 60, 'orbit_radius': 500, 'angle': 300, 'speed': 2},
        {'r': 80, 'orbit_radius': 900, 'angle': 0, 'speed': 1},
        {'r': 80, 'orbit_radius': 900, 'angle': 120, 'speed': 1},
        {'r': 80, 'orbit_radius': 900, 'angle': 240, 'speed': 1},
    ]

    jump_blocks = [
        pygame.Rect(1000, 600, 100, 50),
        pygame.Rect(400, 650, 100, 50),
    ]

    spikes = [
    [(3400, 500), (3450, 450), (3500, 500)],
    [(4100, 500), (4150, 450), (4200, 500)],
    ]

    exit_portal = pygame.Rect(2050, -1225, 50, 100)
    clock = pygame.time.Clock()

    teleporters = [
        {
            "entry": pygame.Rect(5200, 400, 50, 100),
            "exit": pygame.Rect(100, -1400, 50, 100),
            "color": (0, 196, 255)
        }
    ]

    def point_in_triangle(px, py, a, b, c):
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        b1 = sign((px, py), a, b) < 0.0
        b2 = sign((px, py), b, c) < 0.0
        b3 = sign((px, py), c, a) < 0.0
        return b1 == b2 == b3
    
    # Render the texts

    saw_text = in_game.get("saws_message", "Saws are also dangerous!")
    rendered_saw_text = font.render(saw_text, True, (255, 0, 0))  # Render the saw text

    key_text = in_game.get("key_message", "Grab the coin and open the block!")
    rendered_key_text = font.render(key_text, True, (255, 255, 0))  # Render the key text

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        if keys[pygame.K_r]:
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 100, 200
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength

        if (keys[pygame.K_LEFT] or keys[pygame.K_a]):
            player_x -= move_speed

        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            player_x += move_speed

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in blocks:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        # Jump block logic
        for jump_block in jump_blocks:
            if player_rect.colliderect(jump_block):
                # Falling onto a jump block
                if velocity_y > 0 and player_y + img_height - velocity_y <= jump_block.y:
                    player_y = jump_block.y - img_height
                    velocity_y = -33  # Apply upward velocity for the jump
                    on_ground = True

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

        if player_y > SCREEN_HEIGHT:
            screen.fill((255, 255, 255))
            fall_text = in_game.get("fall_message", "Fell too far!")
            screen.blit(font.render(fall_text, True, (0, 0, 0)), (700, 400))
            pygame.display.update()
            pygame.time.delay(300)
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Spike death
        bottom_points = [
            (player_x + img_width // 2, player_y + img_height),
            (player_x + 5, player_y + img_height),
            (player_x + img_width - 5, player_y + img_height)
        ]
        collision_detected = False  # Flag to stop further checks after a collision
        for spike in spikes:
            if collision_detected:
                break  # Exit the outer loop if a collision has already been detected
            for point in bottom_points:
                if point_in_triangle(point[0], point[1], *spike):
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    screen.fill((255, 255, 255))
                    death_text = in_game.get("dead_message", "You Died")
                    screen.blit(font.render(death_text, True, (0, 0, 0)), (700, 400))
                    pygame.display.update()
                    pygame.time.delay(300)
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    key_block_pairs[0]["collected"] = False  # Reset the collected status for the key
                    break

        # Spike death (including top collision detection)
        top_points = [
            (player_x + img_width // 2, player_y),  # Center top point
            (player_x + 5, player_y),               # Left top point
            (player_x + img_width - 5, player_y)    # Right top point
        ]
        collision_detected = False  # Flag to stop further checks after a collision
        for spike in spikes:
             if collision_detected:
               break  # Exit the outer loop if a collision has already been detected
             for point in top_points:
                if point_in_triangle(point[0], point[1], *spike):
            # Trigger death logic
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    screen.fill((255, 255, 255))
                    death_text = in_game.get("dead_message", "You Died")
                    screen.blit(font.render(death_text, True, (0, 0, 0)), (700, 400))
                    pygame.display.update()
                    pygame.time.delay(300)
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    key_block_pairs[0]["collected"] = False  # Reset the collected status for the key
                    break

        # Saw collision detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        player_center = player_rect.center

        for pair in key_block_pairs:
            if not pair["collected"]:  # Only active locked blocks
                block = pair["block"]
                if player_rect.colliderect(block):
            # Falling onto a block
                    if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                        player_y = block.y - img_height
                        velocity_y = 0
                        on_ground = True

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


        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2600, 250  # Store checkpoint position
            print("Checkpoint reached!")
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 150, -1500  # Checkpoint position
            print("Checkpoint reached!")

        for laser in lasers:
            # Check if the player collides with the laser
            if player_rect.colliderect(laser):
                # Trigger death logic
                screen.fill((255, 255, 255))
                laser_text = in_game.get("laser_message", "Lasered!")
                screen.blit(font.render(laser_text, True, (0, 0, 0)), (500, 400))
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        for saw in saws:
            saw_x, saw_y, saw_radius, _ = saw

        # Find the closest point on the player's rectangle to the saw's center
            closest_x = max(player_rect.left, min(saw_x, player_rect.right))
            closest_y = max(player_rect.top, min(saw_y, player_rect.bottom))

            # Calculate the distance between the closest point and the saw's center
            dx = closest_x - saw_x
            dy = closest_y - saw_y
            distance = (dx**2 + dy**2)**0.5

            # Check if the distance is less than the saw's radius
            if distance < saw_radius:
                    # Trigger death logic
                screen.fill((255, 255, 255))
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (0, 0, 0)), (500, 400))
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                pygame.display.update()
                pygame.time.delay(300)  
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Exit portal
        if player_rect.colliderect(exit_portal):
            running = False
            if complete_levels < 6:
                complete_levels = 7
                update_locked_levels()
            set_page('main_menu')

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        for block in invisible_blocks:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width
            
        for block in invisible_blocks:
            # Draw the invisible block as a gray rectangle 
            pygame.draw.rect(screen, (0, 0, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))        

        # Drawing
        screen.fill((0, 102, 51))

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 255, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 255, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        collision_detected = False  
        for rotating_saw in rotating_saws:
            if collision_detected:
                break  # Exit the loop if a collision has already been detected

    # Update angle
            rotating_saw['angle'] = (rotating_saw['angle'] + rotating_saw['speed']) % 360
            rad = math.radians(rotating_saw['angle'])

    # Orbit around block center
            orbit_center_x = blocks[0].centerx
            orbit_center_y = blocks[0].centery
            x = orbit_center_x + rotating_saw['orbit_radius'] * math.cos(rad)
            y = orbit_center_y + rotating_saw['orbit_radius'] * math.sin(rad)

    # Draw the saw
            pygame.draw.circle(screen, (255, 0, 0), (int(x - camera_x), int(y - camera_y)), rotating_saw['r'])

    # Collision detection
            closest_x = max(player_rect.left, min(x, player_rect.right))
            closest_y = max(player_rect.top, min(y, player_rect.bottom))
            dx = closest_x - x
            dy = closest_y - y
            distance = (dx**2 + dy**2)**0.5

            if distance < rotating_saw['r'] and not collision_detected:
            # Trigger death logic                
                collision_detected = True  # Set the flag to stop further checks
                screen.fill((255, 255, 255)) 
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")    
                screen.blit(font.render(sawed_text, True, (0, 0, 0)), (500, 400))               
                player_x, player_y = spawn_x, spawn_y  # Reset player position    
                deathcount += 1        
                pygame.display.update()
                pygame.time.delay(300)
                key_block_pairs[0]["collected"] = False
                break
                

        for saw in moving_saws:
    # Update the circle's position (move vertically)
            saw['cy'] += saw['speed']  # Move down or up depending on speed

    # Check if the saw has reached the limits
            if saw['cy'] > saw['max'] or saw['cy'] < saw['min']:
                saw['speed'] = -saw['speed']  # Reverse direction if we hit a limit

    # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

    # Collision detection (if needed)
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5
            if distance < saw['r']:
        # Trigger death logic
                screen.fill((255, 255, 255))
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (0, 0, 0)), (500, 400))
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        for saw in moving_saws_x:
    # Update the circle's position (move vertically)
            saw['cx'] += saw['speed']
    # Check if the saw has reached the limits
            if saw['cx'] > saw['max'] or saw['cx'] < saw['min']:
                saw['speed'] = -saw['speed']  # Reverse direction if we hit a limit

    # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

    # Collision detection (if needed)
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5
            if distance < saw['r']:
        # Trigger death logic
                screen.fill((255, 255, 255))
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (0, 0, 0)), (500, 400))
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        for teleporter in teleporters:
            # Draw the entry rectangle
            pygame.draw.rect(screen, teleporter["color"], teleporter["entry"].move(-camera_x, -camera_y))
    
            # Draw the exit rectangle
            pygame.draw.rect(screen, teleporter["color"], teleporter["exit"].move(-camera_x, -camera_y))
    
           # Check if the player collides with the entry rectangle
            if player_rect.colliderect(teleporter["entry"]):
                # Teleport the player to the exit rectangle
                player_x, player_y = teleporter["exit"].x, teleporter["exit"].y
        
        for x, y, r, color in saws:
            # Draw the saw as a circle
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        for laser in lasers:
            pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
  
        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

        for spike in spikes:
            pygame.draw.polygon(screen, (255, 0, 0), [((x - camera_x),( y - camera_y)) for x, y in spike])
        
        for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            # Check collision if not yet collected
            if not pair["collected"]:
                key_rect = pygame.Rect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)
            if player_rect.colliderect(key_rect):
                pair["collected"] = True
            
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)

            # Draw block only if key is not collected
            if not pair["collected"]:
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

        pygame.draw.rect(screen, (0, 205, 0), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        
        levels = load_language(lang_code).get('levels', {})
        lvl8_text = levels.get("lvl8", "Level 8")  # Render the level text
        screen.blit(font.render(lvl8_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        placeholder = font.render("Under development!", True, (255, 255, 255))
        screen.blit(placeholder, (20, 50))

        pygame.display.update()   

# Handle actions based on current page
def handle_action(key):
    global current_page, pending_level, level_load_time

    if current_page == 'main_menu':
        if key == "start":
            start_game()
            print(complete_levels)
        elif key == "achievements":
            open_achievements()
        elif key == "settings":
            open_settings()
        elif key == "quit":
            set_page("quit_confirm")
        elif key == "language":
            set_page('language_select')
    elif current_page == 'language_select':
        if key == "back":
            go_back()
        elif key in ["English", "Français", "Español", "Deutsch", "简体中文", "O'zbekcha", "Português(Brasil)", "Русский"]:
            change_language(key)
    elif current_page == 'levels':
        if key is None:  # Ignore clicks on locked levels
            return
        if key == "lvl1":  # Trigger the Level 1 screen
            set_page("lvl1_screen")
        elif key == "lvl2":
            set_page("lvl2_screen")
        elif key == "lvl3":
            set_page("lvl3_screen")
        elif key == "lvl4":
            set_page("lvl4_screen")
        elif key == "lvl5":
            set_page("lvl5_screen")
        elif key == "lvl6":
            set_page("lvl6_screen")
        elif key == "lvl7":
            set_page("lvl7_screen")
        elif key == "lvl8":
            set_page("lvl8_screen")
        elif key == "back":
            set_page("main_menu")
    elif current_page.startswith("lvl"):
        if key == "back":
            set_page("levels")
        else:
            print(f"Action in {current_page}: {key}")
    elif current_page == "quit_confirm":
        if key == "yes":
            quit_game()
        elif key == "no":
            set_page("main_menu")

# Start with main menu
set_page('main_menu')

# Main loop
running = True
while running:
    screen.fill((30, 30, 30))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Only process clicks if enough time has passed since last page change
            if time.time() - last_page_change_time > click_delay:  
                for _, rect, key in buttons:
                    if rect.collidepoint(event.pos):
                        if key != "back":
                            click_sound.play()
                        print(f"Clicked on: {key}")
                        handle_action(key)
                        last_page_change_time = time.time()  # Update the time after handling the click

    if current_page == "main_menu":
        screen.blit(logo, ((SCREEN_WIDTH // 2 - 400), 30))
        screen.blit(logo_text, logo_pos)
        screen.blit(site_text, site_pos)
        screen.blit(credit_text, credit_pos)
        screen.blit(ver_text, ver_pos)
    # Render the main menu buttons
        for rendered, rect, key in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)

    # Render the credit text


    if current_page == "quit_confirm":
        # Render the quit confirmation text
        screen.blit(quit_text, quit_text_rect)

        # Render the "Yes" and "No" buttons
        for rendered, rect, key in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)

        # Allow returning to the main menu with ESC
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            set_page("main_menu")

    elif current_page == "lvl1_screen":
        # Render the Level 1 screen
        screen.fill((30, 30, 30))  # Background color
        create_lvl1_screen()

        # Render the "Back" button
        for rendered, rect, key in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)

    elif current_page == "lvl2_screen":
        create_lvl2_screen()
        
        for rendered, rect, key in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)
    
    elif current_page == "lvl3_screen":
        create_lvl3_screen()
        
        for rendered, rect, key in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)

    elif current_page == "lvl4_screen":
        create_lvl4_screen()
        
        for rendered, rect, key in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)

    elif current_page == "lvl5_screen":
        create_lvl5_screen()
        
        for rendered, rect, key in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)

    elif current_page == "lvl6_screen":
        create_lvl6_screen()

        for rendered, rect, key in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)

    elif current_page == "lvl7_screen":
        create_lvl7_screen()

        for rendered, rect, key in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)

    elif current_page == "lvl8_screen":
        create_lvl8_screen()

        for rendered, rect, key in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)

    elif current_page == "levels":
        # Fetch the localized "Select a Level" text dynamically
        select_text = current_lang.get("select_level", "Select a Level")
        rendered_select_text = font.render(select_text, True, (255, 255, 255))
        select_text_rect = rendered_select_text.get_rect(center=(SCREEN_WIDTH // 2, 50))

        # Draw the "Select a Level" text
        screen.blit(rendered_select_text, select_text_rect)

        # Render buttons for levels
        for rendered, rect, _ in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)

    else:
        # Render buttons for other pages
        for rendered, rect, _ in buttons:
            pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
            screen.blit(rendered, rect)

    # Handle delayed level load
    if pending_level and time.time() >= level_load_time:
        load_level(pending_level)
        pending_level = None

    pygame.display.flip()

pygame.quit()