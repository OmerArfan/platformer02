import pygame
import json
import os
import math
import sys
import time  # Import time to track time(for future use in scoring)
import random

# Path to sound folder
SOUND_FOLDER = os.path.join("audio")

# Initialize audio
pygame.mixer.init()

# Load sounds using the path
click_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "click.wav"))
hover_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "hover.wav"))
death_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "death.wav"))
laser_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "laser.wav"))
fall_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "fall.wav"))
open_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "unlock.wav"))
checkpoint_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "checkpoint.wav"))
warp_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "warp.wav"))
button_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "button.wav"))
bounce_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "bounce.wav"))
move_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "travel.wav"))
jump_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "jump.wav"))
hit_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "hit.wav"))
notify_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "notify.wav"))
overheat_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "overheat.wav"))
freeze_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "freeze.wav"))

# Load and set window icon
icon = pygame.image.load("robots.ico")
pygame.display.set_icon(icon)

# Ambient themes
pygame.mixer.music.load("audio/amb/ambience.wav")
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)  # Loop forever

def change_ambience(new_file):
    pygame.mixer.music.load(new_file)
    pygame.mixer.music.set_volume(2)  # Adjust as needed
    pygame.mixer.music.play(-1)

# Save file name
SAVE_FILE = "save_data.json"

# Default progress dictionary
default_progress = {
    "complete_levels": 0,
    "locked_levels": ["lvl2", "lvl3", "lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9", "lvl10", "lvl11", "lvl12", "lvl13", "lvl14", "lvl15"],
    "times": {f"lvl{i}": 0 for i in range(1, 14)},
    "medals": {f"lvl{i}": "None" for i in range(1, 14)},
    "language": "en",
    "selected_character": "robot",
    "is_mute": False,
    "evilrobo_unlocked": False,
    "icerobo_unlocked": False,
    "lavarobo_unlocked": False,
    "greenrobo_unlocked": False,
}

# Load progress from save file or return default
def load_progress():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        # Merge missing keys from default_progress
        for key, value in default_progress.items():
            if key not in data:
                data[key] = value
        # Also merge nested dicts (like "times" and "medals")
        for key in ["times", "medals"]:
            if key in default_progress and key in data:
                for subkey, subval in default_progress[key].items():
                    if subkey not in data[key]:
                        data[key][subkey] = subval
        # Merge new locked levels
        if "locked_levels" in default_progress and "locked_levels" in data:
            for lvl in default_progress["locked_levels"]:
                if lvl not in data["locked_levels"]:
                    data["locked_levels"].append(lvl)
        return data
    else:
        return default_progress.copy()

# Save progress to file
def save_progress(data):
    with open(SAVE_FILE, "w", encoding="utf-8" ) as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Load progress at start
progress = load_progress()

# Get just the language code, default to English
lang_code = progress.get("language", "en")

is_mute = progress.get("is_mute", default_progress["is_mute"])  # Global variable to track mute state

# Define shortcuts for easier access if needed
complete_levels = progress.get("complete_levels", 0)

# Level rank thresholds
level_thresholds = [
    {'level': 1 ,'gold': 7, 'silver': 9, 'bronze': 12},
    {'level': 2 ,'gold': 25, 'silver': 30, 'bronze': 40},
    {'level': 3 ,'gold': 35, 'silver': 45, 'bronze': 60},
    {'level': 4 ,'gold': 40, 'silver': 50, 'bronze': 60},
    {'level': 5 ,'gold': 50, 'silver': 65, 'bronze': 80},
    {'level': 6 ,'gold': 50, 'silver': 70, 'bronze': 90},
    {'level': 7 ,'gold': 35, 'silver': 40, 'bronze': 45},
    {'level': 8 ,'gold': 25, 'silver': 35, 'bronze': 45},
    {'level': 9 ,'gold': 60, 'silver': 80, 'bronze': 100},
    {'level': 10,'gold': 35, 'silver': 50, 'bronze': 60},
    {'level': 11,'gold': 35, 'silver': 55, 'bronze': 75},
]

# Function to get medal based on time
def get_medal(level, time_taken):
    thresholds = next((t for t in level_thresholds if t['level'] == level), None)
    if not thresholds:
        return None
    if time_taken <= thresholds['gold']:
        return "Gold"
    elif time_taken <= thresholds['silver']:
        return "Silver"
    elif time_taken <= thresholds['bronze']:
        return "Bronze"
    else:
        return None

# Initializing screen resolution
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Platformer 02!")
MIN_WIDTH = 1000
if SCREEN_WIDTH < 1300:
    MIN_HEIGHT = 800
else:
    MIN_HEIGHT = 760

# Load logo image
logo = pygame.image.load("logo.png").convert_alpha()

# Load and scale backgrounds
background_img = pygame.image.load("bgs/Background.png").convert()
background = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
ice_background_img = pygame.image.load("bgs/IceBackground.png").convert()
ice_background = pygame.transform.scale(ice_background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
green_background_img = pygame.image.load("bgs/GreenBackground.png").convert()
green_background = pygame.transform.scale(green_background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Load and initalize Images!
nact_cp = pygame.image.load("oimgs/checkpoints/yellow_flag.png").convert_alpha()
act_cp = pygame.image.load("oimgs/checkpoints/green_flag.png").convert_alpha()

# Load the Chinese font (ensure the font file path is correct)
font_path_ch = 'NotoSansSC-SemiBold.ttf'
font_path = 'NotoSansDisplay-SemiBold.ttf'
font_def = pygame.font.Font(font_path, 25)

if lang_code == "zh_cn":
    font = pygame.font.Font(font_path_ch, 25)
else:
    font = pygame.font.Font(font_path, 25)

def render_text(text, color = (255, 255, 255)):
    # Use Chinese font if any CJK character is present
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return pygame.font.Font('NotoSansSC-SemiBold.ttf', 25).render(text, True, color)
    else:
        return font.render(text, True, color)

site_text = font_def.render("Sound effects from: pixabay.com", True, (255, 255, 255))
site_pos = (SCREEN_WIDTH - 398, SCREEN_HEIGHT - 84)
logo_text = font_def.render("Logo and Background made with: canva.com", True, (255, 255, 255))
logo_pos = (SCREEN_WIDTH - 538, SCREEN_HEIGHT - 54)
credit_text = font_def.render("Made by: Omer Arfan", True, (255, 255, 255))
credit_pos = (SCREEN_WIDTH - 266, SCREEN_HEIGHT - 114)
ver_text = font_def.render("Version 1.2.22", True, (255, 255, 255))
ver_pos = (SCREEN_WIDTH - 180, SCREEN_HEIGHT - 144)

# Load language function and rendering part remain the same
def load_language(lang_code):
    with open(f'lang/{lang_code}.json', encoding='utf-8') as f:
        return json.load(f)

# Load the actual language strings from file
current_lang = load_language(lang_code)

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

# Page states
current_page = 'main_menu'
buttons = []
progress["language"] = lang_code

# New variable to track last page change time
pending_level = None
level_load_time = 0
click_delay = 1  # Delay between clicks isn seconds
last_page_change_time = 0  # Initialize the last page change time
# Display Green Robo Unlocked for a limited time
greenrobo_unlocked_message_time = 0
show_greenrobo_unlocked = False

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

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            set_page("quit_confirm")


def create_language_buttons():
    global current_lang, buttons
    current_lang = load_language(lang_code).get('language_select', {})
    buttons.clear()

    language_options = [
        ("English", "en"),
        ("Français", "fr"),
        ("Español", "es"),
        ("Deutsch", "de"),
        ("简体中文", "zh_cn"),
        ("O'zbekcha", "uz"),
        ("Português(Brasil)", "pt_br"),
        ("Русский", "ru")
    ]
    buttons_per_row = 4
    spacing_x = 200
    spacing_y = 70

    # Calculate starting positions to center the grid
    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (SCREEN_WIDTH - grid_width) // 2
    start_y = (SCREEN_HEIGHT // 2) - (len(language_options) // buttons_per_row * spacing_y // 2)

    for i, (display_name, code) in enumerate(language_options):
        text = display_name
        rendered = render_text(text, (255, 255, 255))

        col = i % buttons_per_row
        row = i // buttons_per_row

        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        rect = rendered.get_rect(center=(x, y))
        buttons.append((rendered, rect, code))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            set_page("quit_confirm")

    # Add a "Back" button at the bottom center
    back_text = current_lang.get("back", "Back")
    rendered_back = font.render(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(SCREEN_WIDTH // 2, y + spacing_y + 40))
    buttons.append((rendered_back, back_rect, "back"))

def green_world_buttons():
    global current_lang, buttons
    levels = load_language(lang_code).get('levels', {})
    buttons.clear()

    # Render "Select a Level" text
    select_text = levels.get("level_display", "SELECT A LEVEL")
    rendered_select_text = font.render(select_text, True, (255, 255, 255))
    select_text_rect = rendered_select_text.get_rect(center=(SCREEN_WIDTH // 2, 50))  # Center at the top

    # Store the rendered text and its position for later drawing
    global select_level_text, select_level_rect
    select_level_text = rendered_select_text
    select_level_rect = select_text_rect

    level_options = ["lvl1", "lvl2", "lvl3", "lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9", "lvl10", "lvl11"]
    buttons_per_row = 4
    spacing_x = 140
    spacing_y = 70

    # Calculate starting positions to center the grid
    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (SCREEN_WIDTH - grid_width) // 2 
    start_y = ((SCREEN_HEIGHT // 2) - (1.25*(len(level_options) // buttons_per_row * spacing_y // 2)))

    for i, level in enumerate(level_options):
        text = levels.get(level, level.capitalize())
        is_locked = level in progress["locked_levels"]  # Check if the level is locked

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
    back_rect = rendered_back.get_rect(center=(90, SCREEN_HEIGHT // 2))
    buttons.append((rendered_back, back_rect, "back"))

        # Next button at bottom center
    next_text = current_lang.get("next", "next")
    rendered_next = font.render(next_text, True, (255, 255, 255))
    next_rect = rendered_next.get_rect(center=(SCREEN_WIDTH - 80, SCREEN_HEIGHT // 2))
    buttons.append((rendered_next, next_rect, "next"))

def ice_world_buttons():
    global current_lang, buttons
    levels = load_language(lang_code).get('levels', {})
    buttons.clear()

    rendered_select_text = font.render(select_text, True, (0, 0, 0))
    select_text_rect = rendered_select_text.get_rect(center=(SCREEN_WIDTH // 2, 50))  # Center at the top

    # Store the rendered text and its position for later drawing
    global select_level_text, select_level_rect
    select_level_text = rendered_select_text
    select_level_rect = select_text_rect

    level_options = ["lvl12", "lvl13", "lvl14", "lvl15"]
    buttons_per_row = 4
    spacing_x = 140
    spacing_y = 70

    # Calculate starting positions to center the grid
    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (SCREEN_WIDTH - grid_width) // 2
    start_y = (SCREEN_HEIGHT // 2) - (len(level_options) // buttons_per_row * spacing_y // 2)

    for i, level in enumerate(level_options):
        text = levels.get(level, level.capitalize())
        is_locked = level in progress["locked_levels"]  # Check if the level is locked

        # Render the level text
        color = (79, 79, 79) if is_locked else (0, 0, 0)  # Gray out locked levels
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
    back_rect = rendered_back.get_rect(center=(50, SCREEN_HEIGHT // 2 - 50))
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

def check_green_gold():
    global show_greenrobo_unlocked, greenrobo_unlocked_message_time
    all_gold = all(progress["medals"][f"lvl{i}"] == "Gold" for i in range(1, 12))
    if all_gold:
        unlock = progress.get("greenrobo_unlocked", False)
        if not unlock:
            if not is_mute:
                notify_sound.play()
            unlock = True
            progress["greenrobo_unlocked"] = unlock
            save_progress(progress)
            show_greenrobo_unlocked = True
            greenrobo_unlocked_message_time = time.time()

# Button actions
def start_game():
    pygame.time.delay(200)  # Delay 200 ms to avoid click pass-through
    set_page('levels')

# Load character images
robot_img = pygame.image.load("char/robot.png").convert_alpha()
evilrobot_img = pygame.image.load("char/evilrobot.png").convert_alpha()
icerobot_img = pygame.image.load("char/icerobot.png").convert_alpha()
lavarobot_img = pygame.image.load("char/lavarobot.png").convert_alpha()
greenrobot_img = pygame.image.load("char/greenrobot.png").convert_alpha()
locked_img = pygame.image.load("char/lockedrobot.png").convert_alpha()

#Initialize default character
selected_character = progress.get("selected_character", default_progress["selected_character"])

# Get rects and position them
robot_rect = robot_img.get_rect(topleft=(SCREEN_WIDTH // 2 - 350, SCREEN_HEIGHT // 2 - 50))
#Evil Robot
evilrobot_rect = evilrobot_img.get_rect(topleft=(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50))
#Ice and lava robot
icerobot_rect = icerobot_img.get_rect(topleft=(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 50))
lavarobot_rect = lavarobot_img.get_rect(topleft=(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 - 50))
greenrobot_rect = greenrobot_img.get_rect(topleft=(SCREEN_WIDTH // 2 + 250, SCREEN_HEIGHT // 2 - 50))
def open_achievements():
    global selected_character, set_page, current_page
    
    # Clear screen
    buttons.clear()

    for event in pygame.event.get():#
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # left click
            mouse_pos = event.pos
            if robot_rect.collidepoint(mouse_pos):
                selected_character = "robot"
                set_page("main_menu")
            elif evilrobot_rect.collidepoint(mouse_pos):
                selected_character = "evilrobot"
                set_page("main_menu")
            elif icerobot_rect.collidepoint(mouse_pos):
                selected_character = "icerobot"
                set_page("main_menu")
            elif lavarobot_rect.collidepoint(mouse_pos):
                selected_character = "lavarobot"
                set_page("main_menu")   
            elif greenrobot_rect.collidepoint(mouse_pos):
                selected_character = "greenrobot"
                set_page("main_menu")
    pygame.display.flip()


def open_settings():
    global is_mute
    if is_mute:
        is_mute = False
    else:
        is_mute = True

def quit_game():
    pygame.quit()
    exit()

def change_language(lang):
    global lang_code, last_page_change_time, current_lang, font, font_path_ch, font_path
    lang_code = lang
    last_page_change_time = time.time()  # Track the time when the language changes
    current_lang = load_language(lang_code)  # Reload the language data
    progress["language"] = lang_code
    save_progress(progress)
    if lang_code == "zh_cn":
        font = pygame.font.Font(font_path_ch, 25)
    else:
        font = pygame.font.Font(font_path, 25)
    set_page('main_menu')

def go_back():
    global last_page_change_time
    last_page_change_time = time.time()  # Track the time when going back
    set_page('main_menu')

def update_locked_levels():
    all_levels = ["lvl2", "lvl3", "lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9", "lvl10", "lvl11", "lvl12", "lvl13", "lvl14", "lvl15"]
    # Always start with all levels locked except lvl2 (which unlocks after lvl1 is completed)
    locked = set(all_levels)
    times = progress.get("times", {})

    # Unlock levels if the previous level's time is not 0
    for i, lvl in enumerate(all_levels):
        prev_lvl = f"lvl{i+1}"
        if times.get(prev_lvl, 0) != 0:
            locked.discard(lvl)  # Unlock this level

    progress["locked_levels"] = list(locked)
    save_progress(progress)

# Central page switcher
def set_page(page):
    global current_page, current_lang  # Explicitly mark current_page and current_lang as global
    current_page = page

    # Reload the current language data for the new page
    if page == 'main_menu':
        current_lang = load_language(lang_code).get('main_menu', {})
        create_main_menu_buttons()
    elif page == 'character_select':
        open_achievements()
    elif page == 'language_select':
        current_lang = load_language(lang_code).get('language_select', {})
        create_language_buttons()
    elif page == 'levels':
        current_lang = load_language(lang_code).get('levels', {})
        green_world_buttons()
        change_ambience("audio/amb/greenambience.wav")
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
    elif page == 'lvl9_screen':
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl9_screen()
    elif page == 'lvl10_screen':
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl10_screen()
    elif page == 'lvl11_screen':
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl11_screen()
    elif page == 'lvl12_screen':
        current_lang = load_language(lang_code).get('in_game', {})
        create_lvl12_screen()   
    elif page == 'ice_levels':
        current_lang = load_language(lang_code).get('levels', {})
        ice_world_buttons()
        change_ambience("audio/amb/iceambience.wav")

def create_quit_confirm_buttons():
    global current_lang, buttons, quit_text, quit_text_rect, selected_character
    buttons.clear()

    # Get the quit confirmation text from the current language
    messages = load_language(lang_code).get('messages', {})
    confirm_quit = messages.get("confirm_quit", "Are you sure you want to quit?")

    # Store the quit confirmation text for rendering in the main loop
    quit_text = font.render(confirm_quit, True, (255, 255, 255))
    quit_text_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 25))

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

    pygame.display.flip()  # Update the display to show the quit confirmation screen

def create_lvl1_screen():
    global player_img, font, screen, complete_levels, is_mute, show_greenrobo_unlocked

    in_game = load_language(lang_code).get('in_game', {})

    wait_time = None
    start_time = time.time()

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
    was_moving = False
    just_collided = False
    
    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
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
    rendered_exit_text = font.render(exit_text, True, (0, 73, 0))  # Render the exit text

    moving_text = in_game.get("moving_message", "Not all blocks stay still...")
    rendered_moving_text = font.render(moving_text, True, (128, 0, 128))  # Render the moving text

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        print(wait_time)

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page('levels')

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            collided_with_block = False
            just_collided = True
            if not is_mute:
                jump_sound.play()
        

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False

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
        collided_with_block = False

        for block in blocks + [moving_block]:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True
                    if just_collided:
                        collided_with_block = True
                        just_collided = False

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
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                fall_sound.play()
            velocity_y = 0
            deathcount += 1

        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 1:
                progress["complete_levels"] = 1
                update_locked_levels()

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl1"] or progress["times"]["lvl1"] == 0:
                progress["times"]["lvl1"] = round(current_time, 2)
            
            progress["medals"]["lvl1"] = get_medal(1, progress["times"]["lvl1"])

            update_locked_levels()

            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
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
        screen.blit(green_background, (0, 0))

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))
            pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = 600, 200  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1 

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
                        wait_time = pygame.time.get_ticks()
                        if not is_mute:
                            death_sound.play()
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
                        wait_time = pygame.time.get_ticks()
                        if not is_mute:
                            death_sound.play()
                        velocity_y = 0
                        deathcount += 1
                        collision_detected = True  # Set the flag to stop further checks
                        break

        pygame.draw.rect(screen, (129, 94, 123), (exit_portal.x - camera_x, exit_portal.y - camera_y, exit_portal.width, exit_portal.height))
        screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

            # Inside the game loop:
        screen.blit(rendered_up_text, (700 - camera_x, 200 - camera_y))  # Draws the rendered up text
        screen.blit(rendered_warning_text, (1900 - camera_x, 150 - camera_y))  # Draws the rendered warning text
        screen.blit(rendered_moving_text, (1350 - camera_x, 170 - camera_y))  # Draws the rendered moving text
        screen.blit(rendered_exit_text, (2400 - camera_x, 300 - camera_y))  # Draws the rendered exit text

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        # Initialize and draw the quit text
        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        levels = load_language(lang_code).get('levels', {})
        lvl1_text = levels.get("lvl1", "Level 1")  # Render the level text
        screen.blit(font.render(lvl1_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None

        pygame.display.update()    

def create_lvl2_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, wait_time

    in_game = load_language(lang_code).get('in_game', {})

    wait_time = None
    start_time = time.time()

    # Camera settings
    camera_x = 0  
    camera_y = 0
    player_x, player_y = 150, 500
    spawn_x, spawn_y = player_x, player_y  # Set the spawn point
    running = True
    gravity = 1
    jump_strength = 20
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.05
    deathcount = 0
    was_moving = False

    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(2150, 650, 80, 50)  # x, y, width, height
    checkpoint_reached = False
    flag_1_x, flag_1_y = 2150, 650

    blocks = [
        pygame.Rect(100, 650, 1000, 50),
        pygame.Rect(500, 500, 200, 50),
        pygame.Rect(1900, 200, 200, 50),
        pygame.Rect(2900, 450, 500, 50),
        pygame.Rect(2150, 530, 250, 50),
        pygame.Rect(2080, 750, 620, 50),
        pygame.Rect(2400, 50, 50, 530),
        pygame.Rect(3300, 650, 260, 50),
        pygame.Rect(3800, 650, 220, 50),
        pygame.Rect(4260, 650, 220, 50),
        pygame.Rect(3300, 200, 1000, 50),
    ]

    jump_blocks = [
        pygame.Rect(1000, 550, 100, 100), # Jump blocks to help the character go up and then fall down
        pygame.Rect(2730, 751, 100, 100),
        pygame.Rect(3600, 645, 160, 100),
        pygame.Rect(4060, 645, 160, 100),
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
        if wait_time is not None:
            print(pygame.time.get_ticks() - wait_time)

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            current_time = 0
            checkpoint_reached = False  # Reset checkpoint status
            spawn_x, spawn_y = 150, 500
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page('levels')

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not is_mute:
                jump_sound.play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False

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

            if player_y > (SCREEN_HEIGHT + 50):
                death_text = in_game.get("fall_message", "Fell too far!")
                if not is_mute:
                    fall_sound.play()
                wait_time = pygame.time.get_ticks()
                player_x, player_y = spawn_x, spawn_y
                velocity_y = 0
                deathcount += 1

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 2:
                progress["complete_levels"] = 2
                update_locked_levels()

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl2"] or progress["times"]["lvl2"] == 0:
                progress["times"]["lvl2"] = round(current_time, 2)
            
            progress["medals"]["lvl2"] = get_medal(2, progress["times"]["lvl2"])

            update_locked_levels()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
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
        screen.blit(green_background, (0, 0))

        if player_rect.colliderect(flag) and not checkpoint_reached:
            checkpoint_reached = True
            spawn_x, spawn_y = 2150, 620  # Store checkpoint position
            if not is_mute:
                checkpoint_sound.play()
            
        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))

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
                        wait_time = pygame.time.get_ticks()
                        if not is_mute:
                            death_sound.play()
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
                        player_x, player_y = spawn_x, spawn_y  # Reset player position
                        death_text = in_game.get("dead_message", "You Died")
                        wait_time = pygame.time.get_ticks()
                        if not is_mute:
                            death_sound.play()
                        velocity_y = 0
                        deathcount += 1
                        collision_detected = True  # Set the flag to stop further checks
                        break

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1  

        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (jump_block.x - camera_x, jump_block.y - camera_y, jump_block.width, jump_block.height))

        pygame.draw.rect(screen, (129, 94, 123), (exit_portal.x - camera_x, exit_portal.y - camera_y, exit_portal.width, exit_portal.height))
        screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

            # Inside the game loop:
        screen.blit(rendered_jump_text, (900 - camera_x, 500 - camera_y))  # Draws the rendered up text

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = font.render(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        levels = load_language(lang_code).get('levels', {})
        lvl2_text = levels.get("lvl2", "Level 2")  # Render the level text
        screen.blit(font.render(lvl2_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None

        pygame.display.update()    

def create_lvl3_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked

    wait_time = None
    start_time = time.time()

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
    was_moving = False

    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(200, 200, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(2080, -260, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 200, 200
    flag_2_x, flag_2_y = 2080, -260

    key_block_pairs = [
        {
            "key": (310, 225, 30, (255, 255, 0)),
            "block": pygame.Rect(2550, 250, 200, 200),
            "collected": False
        },
    ]

    saws = [
        (620, 750, 80,(255, 0, 0)),  # (x, y, radius, color)
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

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            current_time = 0
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 150, 600
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not is_mute:
                jump_sound.play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False


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

            if player_y > (SCREEN_HEIGHT + 50):
                death_text = in_game.get("fall_message", "Fell too far!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    fall_sound.play()
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
            if not is_mute:
                checkpoint_sound.play()
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not is_mute:
                checkpoint_sound.play()
            spawn_x, spawn_y = 2100, -400  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 3:
                progress["complete_levels"] = 3
                update_locked_levels()

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl3"] or progress["times"]["lvl3"] == 0:
                progress["times"]["lvl3"] = round(current_time, 2)
            
            progress["medals"]["lvl3"] = get_medal(3, progress["times"]["lvl3"])

            update_locked_levels()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl4_screen')

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 100:
            camera_y = player_y - 100
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(green_background, (0, 0))

        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(act_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
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
                    death_text = in_game.get("sawed_message", "Sawed to bits!")
                    wait_time = pygame.time.get_ticks()
                    if not is_mute:
                        death_sound.play()
                    velocity_y = 0
                    player_x, player_y = spawn_x, spawn_y
                    deathcount += 1
                    collision_detected = True
                break  # Only die once per frame

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                wait_time = pygame.time.get_ticks()
                key_block_pairs[0]["collected"] = False  # Reset key block status
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1 

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
                        if not is_mute:
                            death_sound.play()
                        collision_detected = True  # Set the flag to stop further checks
                        wait_time = pygame.time.get_ticks()
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
                        wait_time = pygame.time.get_ticks()
                        if not is_mute:
                            death_sound.play()
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
                if not pair["collected"] and not is_mute:
                    open_sound.play()
                pair["collected"] = True
            
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)

            # Draw block only if key is not collected
            if not pair["collected"]:
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        screen.blit(rendered_saw_text, (int(550 - camera_x), int(600 - camera_y)))  # Draws the rendered up text
        screen.blit(rendered_key_text, (int(2500 - camera_x), int(200 - camera_y)))  # Draws the rendered up text

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = font.render(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        levels = load_language(lang_code).get('levels', {})
        lvl3_text = levels.get("lvl3", "Level 3")  # Render the level text
        screen.blit(font.render(lvl3_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text
        
        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None

        pygame.display.update()    

def create_lvl4_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked

    wait_time = None
    start_time = time.time()

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
    was_moving = False

    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(1500, 550, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(3200, 120, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 1500, 550
    flag_2_x, flag_2_y = 3200, 120

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

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 250, 450
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not is_mute:
                jump_sound.play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False


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

        if player_y > (SCREEN_HEIGHT + 50):
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                fall_sound.play()
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
            spawn_x, spawn_y = 1500, 500  # Store checkpoint position
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3150, 100  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 4:
                progress["complete_levels"] = 4

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl4"] or progress["times"]["lvl4"] == 0:
                progress["times"]["lvl4"] = round(current_time, 2)
            
            progress["medals"]["lvl4"] = get_medal(4, progress["times"]["lvl4"])

            update_locked_levels()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl5_screen') 

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(green_background, (0, 0))

        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(act_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")    
                wait_time = pygame.time.get_ticks()
                player_x, player_y = spawn_x, spawn_y  # Reset player position    
                deathcount += 1        
                if not is_mute:
                    death_sound.play()
                velocity_y = 0
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    death_sound.play()
                deathcount += 1
                velocity_y = 0
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                if not is_mute:
                    death_sound.play()
                deathcount += 1
                velocity_y = 0 
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
                death_text = in_game.get("laser_message", "Lasered!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    laser_sound.play()
                velocity_y = 0
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                wait_time = pygame.time.get_ticks()
                key_block_pairs[0]["collected"] = False  # Reset key block status
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1 

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
                        if not is_mute:
                            death_sound.play()
                        collision_detected = True  # Set the flag to stop further checks
                        wait_time = pygame.time.get_ticks()
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
                        wait_time = pygame.time.get_ticks()
                        if not is_mute:
                            death_sound.play()
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
                if not pair["collected"] and not is_mute:
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


        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))


        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = font.render(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        levels = load_language(lang_code).get('levels', {})
        lvl4_text = levels.get("lvl4", "Level 4")  # Render the level text
        screen.blit(font.render(lvl4_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None

        pygame.display.update()   

def create_lvl5_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked

    wait_time = None
    start_time = time.time()

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 0  
    camera_y = 0
    spawn_x, spawn_y = 20, 500
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False

    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(2100, -150, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(3450, -450, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 2100, -150
    flag_2_x, flag_2_y = 3450, -450

    key_block_pairs = [
        {
            "key": (4050, -800, 30, (255, 255, 0)),
            "block": pygame.Rect(1300, -250, 200, 200),
            "collected": False
        },
    ]

    blocks = [
        pygame.Rect(-50, 650, 1000, 100),
        pygame.Rect(900, 510, 100, 100),
        pygame.Rect(1450, 650, 650, 100),
        pygame.Rect(1500, -50, 700, 50),
        pygame.Rect(1700, -350, 1050, 50),
        pygame.Rect(1500, -250, 50, 200),
        pygame.Rect(2700, -310, 50, 91),
        pygame.Rect(2700, -220, 200, 50),
        pygame.Rect(2880, -310, 50, 140),
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

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 20, 500
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not is_mute:
                jump_sound.play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False


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

        if player_y > (SCREEN_HEIGHT + 50):
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                fall_sound.play()
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
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3450, -550  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 5:
                progress["complete_levels"] = 5

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl5"] or progress["times"]["lvl5"] == 0:
                progress["times"]["lvl5"] = round(current_time, 2)
            
            progress["medals"]["lvl5"] = get_medal(5, progress["times"]["lvl5"])

            update_locked_levels()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl6_screen')
            
        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(green_background, (0, 0))

        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(act_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")    
                wait_time = pygame.time.get_ticks()             
                player_x, player_y = spawn_x, spawn_y  # Reset player position    
                if not is_mute:
                    death_sound.play()
                deathcount += 1       
                velocity_y = 0
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    death_sound.play()
                velocity_y = 0
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    death_sound.play()
                velocity_y = 0
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    death_sound.play()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                velocity_y = 0
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key


        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                wait_time = pygame.time.get_ticks()
                key_block_pairs[0]["collected"] = False  # Reset key block status
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1  

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
                        if not is_mute:
                            death_sound.play()
                        collision_detected = True  # Set the flag to stop further checks
                        wait_time = pygame.time.get_ticks()
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
                        wait_time = pygame.time.get_ticks()
                        if not is_mute:
                            death_sound.play()
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
                if not pair["collected"] and not is_mute:
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
                        wait_time = pygame.time.get_ticks()
                        if not is_mute:
                            death_sound.play()
                        velocity_y = 0
                        deathcount += 1
                        collision_detected = True  # Set the flag to stop further checks
                        key_block_pairs[0]["collected"] = False  # Reset the collected status for the key
                        break


        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = font.render(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        levels = load_language(lang_code).get('levels', {})
        lvl5_text = levels.get("lvl5", "Level 5")  # Render the level text
        screen.blit(font.render(lvl5_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None

        pygame.display.update()   

def create_lvl6_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked
    start_time = time.time()

    wait_time = None
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
    was_moving = False

    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(2400, 380, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(3200, 410, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 2400, 380
    flag_2_x, flag_2_y = 3200, 410

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

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 220, 500
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not is_mute:
                jump_sound.play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False


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

        if player_y > (SCREEN_HEIGHT + 50):
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                fall_sound.play()
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
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3150, 400  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 6:
                progress["complete_levels"] = 6

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl6"] or progress["times"]["lvl6"] == 0:
                progress["times"]["lvl6"] = round(current_time, 2)
            
            progress["medals"]["lvl6"] = get_medal(6, progress["times"]["lvl6"])

            update_locked_levels()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
            running = False
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

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(green_background, (0, 0))

        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(act_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")    
                wait_time = pygame.time.get_ticks()               
                player_x, player_y = spawn_x, spawn_y  # Reset player position    
                deathcount += 1        
                if not is_mute:
                    death_sound.play()
                velocity_y = 0
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    death_sound.play()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                velocity_y = 0
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    death_sound.play()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                velocity_y = 0
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play() 
                velocity_y = 0
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key


        for laser in lasers:
            pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))

        for laser in lasers:
            # Check if the player collides with the laser
            if player_rect.colliderect(laser):
                # Trigger death logic
                death_text = in_game.get("laser_message", "Lasered!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    laser_sound.play()
                player_x, player_y = spawn_x, spawn_y
                deathcount += 1
                velocity_y = 0
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                wait_time = pygame.time.get_ticks()
                key_block_pairs[0]["collected"] = False  # Reset key block status
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1  

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
                    wait_time = pygame.time.get_ticks()
                    if not is_mute:
                        death_sound.play()
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
                    wait_time = pygame.time.get_ticks()
                    if not is_mute:
                        death_sound.play()
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
                if not pair["collected"] and not is_mute:
                    open_sound.play()
                pair["collected"] = True
            
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)

            # Draw block only if key is not collected
            if not pair["collected"]:
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        
        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = font.render(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        levels = load_language(lang_code).get('levels', {})
        lvl6_text = levels.get("lvl6", "Level 6")  # Render the level text
        screen.blit(font.render(lvl6_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        invisible_text = in_game.get("invisible_message", "These saws won't hurt you... promise!")
        screen.blit(font.render(invisible_text, True, (255, 51, 153)), (900 - camera_x, 250 - camera_y)) # Render the invisible block text

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None

        pygame.display.update()   

def create_lvl7_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked
    start_time = time.time()

    wait_time = None
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
    was_moving = False

    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(2600, 300, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(240, -1360, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 2600, 300
    flag_2_x, flag_2_y = 240, -1360

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

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 100, 200
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not is_mute:
                jump_sound.play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False


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
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                fall_sound.play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

        # Checkpoint Logic
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2600, 250  # Store checkpoint position
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 150, -1500  # Checkpoint position
            if not is_mute:
                checkpoint_sound.play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 7:
                progress["complete_levels"] = 7

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl7"] or progress["times"]["lvl7"] == 0:
                progress["times"]["lvl7"] = round(current_time, 2)
            
            progress["medals"]["lvl7"] = get_medal(7, progress["times"]["lvl7"])

            update_locked_levels()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl8_screen')

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(green_background, (0, 0))

        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(act_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")    
                wait_time = pygame.time.get_ticks()             
                velocity_y = 0
                player_x, player_y = spawn_x, spawn_y  # Reset player position    
                deathcount += 1  
                if not is_mute:          
                    death_sound.play()
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                velocity_y = 0
                if not is_mute:
                    death_sound.play()
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                velocity_y = 0
                if not is_mute:
                    death_sound.play()
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
                if not is_mute:
                    warp_sound.play()
                player_x, player_y = teleporter["exit"].x, teleporter["exit"].y
        
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
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                velocity_y = 0
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1  

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
                    wait_time = pygame.time.get_ticks()
                    if not is_mute:
                        death_sound.play()
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
                    wait_time = pygame.time.get_ticks()
                    if not is_mute:
                        death_sound.play()
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    break

        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        
        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = font.render(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        levels = load_language(lang_code).get('levels', {})
        lvl7_text = levels.get("lvl7", "Level 7")  # Render the level text
        screen.blit(font.render(lvl7_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        portal_text = in_game.get("portal_message", "These blue portals teleport you! But to good places... mostly!")
        screen.blit(font.render(portal_text, True, (0, 196, 255)), (4400 - camera_x, 300 - camera_y))

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False
        
        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None

        pygame.display.update()   

def create_lvl8_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked
    
    wait_time = None
    start_time = time.time()

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y = -25, 260
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    # When the gravity is weaker
    weak_jump_strength = 37
    weak_grav = False
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False

    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(8470, -320, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(10200, -320, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 8470, -320
    flag_2_x, flag_2_y = 10200, -320

    blocks = [
        pygame.Rect(0, 400, 100, 100),
        pygame.Rect(460, 650, 540, 50),
        pygame.Rect(1200, 200, 1000, 50),
        pygame.Rect(8200, -200, 6000, 400),
        pygame.Rect(9000, -750, 50, 600),
        pygame.Rect(9600, -750, 50, 600),
        pygame.Rect(10000, -1300, 2000, 500),
    ]
    
    jump_blocks = [
        pygame.Rect(1100, 600, 100, 100),
        pygame.Rect(11000, -300, 100, 100),
    ]

    moving_saws = [
        {'r': 60, 'speed': 11, 'cx': 350, 'cy': 200, 'max': 800, 'min': 0},
    ]

    moving_saws_x = [
        {'r': 100, 'speed':14, 'cx': 11000, 'cy': -705, 'max': 11300, 'min': 10700}
    ]

    saws = [
        (1850, 200, 80, (255, 0, 0)),
        (9025, -175, 150, (255, 0, 0)),
        (9625, -175, 150, (255, 0, 0)),
        
    ]

    spikes = [
    [(700, 650), (750, 600), (800, 650)],
    [(1400, 200), (1475, 120), (1550, 200)],
    [(9000, -750), (9025, -800), (9050, -750)],
    [(9600, -750), (9625, -800), (9650, -750)],
    [(10000, -800), (10050, -750), (10100, -800)],
    [(10100, -800), (10150, -750), (10200, -800)],
    [(10200, -800), (10250, -750), (10300, -800)],
    [(10300, -800), (10350, -750), (10400, -800)],
    [(10400, -800), (10450, -750), (10500, -800)],
    [(10500, -800), (10550, -750), (10600, -800)],
    [(10600, -800), (10650, -750), (10700, -800)],
    [(10700, -800), (10750, -750), (10800, -800)],
    [(10800, -800), (10850, -750), (10900, -800)],
    [(10900, -800), (10950, -750), (11000, -800)],
    [(11000, -800), (11050, -750), (11100, -800)],
    [(11100, -800), (11150, -750), (11200, -800)],
    [(11200, -800), (11250, -750), (11300, -800)],
    [(11300, -800), (11350, -750), (11400, -800)],
    ]

    exit_portal = pygame.Rect(11050, -750, 50, 100)
    clock = pygame.time.Clock()

    gravity_weakers = [
        (8600, -300, 30, (0, 102, 204)),
    ]

    teleporters = [
        {
            "entry": pygame.Rect(2150, 100, 50, 100),
            "exit": pygame.Rect(8300, -400, 50, 100),
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
        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()  # Reset the timer
            weak_grav = False # Reset weak gravity status
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = -25, 260
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if weak_grav:
                velocity_y = -weak_jump_strength
            else:
                velocity_y = -jump_strength
            if not is_mute:
                jump_sound.play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False

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


        if player_y > SCREEN_HEIGHT:
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()
            weak_grav = False # Reset weak gravity status
            if not is_mute:
                fall_sound.play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

        # Checkpoint Logic
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            weak_grav = False # Reset weak gravity status
            spawn_x, spawn_y = 8470, -500  # Store checkpoint position
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            weak_grav = False # Reset weak gravity status
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 10200, -350  # Checkpoint position
            if not is_mute:
                checkpoint_sound.play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 8:
                progress["complete_levels"] = 8

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl8"] or progress["times"]["lvl8"] == 0:
                progress["times"]["lvl8"] = round(current_time, 2)
            
            progress["medals"]["lvl8"] = get_medal(8, progress["times"]["lvl8"])

            update_locked_levels()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl9_screen')

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 440:
            camera_y = player_y - 440
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(green_background, (0, 0))

        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(act_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
# Saw collision detection and drawing
        collision_detected = False 
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
                weak_grav = False # Reset weak gravity status
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                velocity_y = 0
                if not is_mute:
                    death_sound.play()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1

        for saw in moving_saws:
    # Update the circle's position (move vertically)
            saw['cy'] += saw['speed']
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
                weak_grav = False # Reset weak gravity status
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                velocity_y = 0
                if not is_mute:
                    death_sound.play()
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
                if not is_mute:
                    warp_sound.play()
                player_x, player_y = teleporter["exit"].x, teleporter["exit"].y
        
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
                weak_grav = False # Reset weak gravity status
                    # Trigger death logic
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                velocity_y = 0
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                wait_time = pygame.time.get_ticks()
                weak_grav = False
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1

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
                    weak_grav = False # Reset weak gravity status
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    wait_time = pygame.time.get_ticks()
                    if not is_mute:
                        death_sound.play()
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
                    weak_grav = False # Reset weak gravity status
            # Trigger death logic
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    wait_time = pygame.time.get_ticks()
                    if not is_mute:
                        death_sound.play()
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    break

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
                if not is_mute:
                    button_sound.play()
                weak_grav = True


        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = font.render(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text 
               
        levels = load_language(lang_code).get('levels', {})
        lvl8_text = levels.get("lvl8", "Level 8")  # Render the level text
        screen.blit(font.render(lvl8_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        button1_text = in_game.get("button1_message", "Blue buttons, upon activation, will make you jump higher!")
        screen.blit(font.render(button1_text, True, (0, 102, 204)), (8400 - camera_x, -150 - camera_y))

        clarify_text = in_game.get("clarify_message", "Until you reach a checkpoint, of course!")
        screen.blit(font.render(clarify_text, True, (0, 102, 204)), (9800 - camera_x, -150 - camera_y))

        mock_text = in_game.get("mock_message", "Wrong way my guy nothing to see here...")
        screen.blit(font.render(mock_text, True, (255, 0, 0)), (13200 - camera_x, -300 - camera_y))

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None

        pygame.display.update()   

def create_lvl9_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked
    
    wait_time = None
    start_time = time.time()

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y =  50, -50
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    # When the gravity is stronger
    strong_jump_strength = 15
    strong_grav = False
    weak_grav_strength = 37
    # When the gravity is weaker
    weak_grav = False
    move_speed = 8
    on_ground = False

    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(2350, 300, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(5600, 550, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 2350, 300
    flag_2_x, flag_2_y = 5600, 550

    key_block_pairs = [
        {
            "key": (3700, 550, 30, (255, 255, 0)),
            "block": pygame.Rect(3200, 0, 400, 200),
            "collected": False
        },
    ]

    blocks = [
        pygame.Rect(0, 100, 1000, 50),
        pygame.Rect(500, 60, 500, 80),
        pygame.Rect(0, -300, 1000, 100),
        pygame.Rect(2300, 400, 600, 100),
        pygame.Rect(2800, -300, 100, 500),
        pygame.Rect(3200, 200, 100, 530),
        pygame.Rect(2900, -600, 1100, 100),
        pygame.Rect(3500, 200, 100, 850),
        pygame.Rect(3550, 200, 1980, 100),
        pygame.Rect(3550, 650, 2280, 100)
    ]

    jump_blocks = [
        pygame.Rect(1250, 600, 100, 100),
        pygame.Rect(2970, 420, 100, 100),
        pygame.Rect(5730, 550, 100, 100),
    ]

    moving_saws = [ 
        {'r': 70, 'speed': 6, 'cx': 3700, 'cy': 500, 'max': 900, 'min': 300},
        {'r': 70, 'speed': 10, 'cx': 4500, 'cy': 600, 'max': 700, 'min': -60},
    ]

    moving_saws_x = [
        {'r': 100, 'speed':14, 'cx': 3800, 'cy': 700, 'min': 3700, 'max': 5400}
    ]

    deceiver_saws = [
        (1700, 650, 28, (255, 0 , 127)),
        (1900, 650, 28, (255, 0 , 127)),
        (2100, 550, 28, (255, 0 , 127)),
    ]        

    invisible_blocks = [
        pygame.Rect(1600, 600, 500, 100),
        pygame.Rect(2050, 500, 100, 100),
    ]

    spikes = [
    [(0, -200), (50, -150), (100, -200)],
    [(110, -200), (160, -150), (210, -200)],
    [(220, -200), (270, -150), (320, -200)],
    [(330, -200), (380, -150), (430, -200)],    
    [(440, -200), (490, -150), (540, -200)],
    [(550, -200), (600, -150), (650, -200)],    
    [(660, -200), (710, -150), (760, -200)],
    [(770, -200), (820, -150), (870, -200)],
    [(880, -200), (930, -150), (980, -200)],
    [(2900, 200), (2950, 150), (2900, 100)],
    [(2900, 90), (2950, 40), (2900, -10)],
    [(2900, -20), (2950, -70), (2900, -120)],
    [(2900, -130), (2950, -180), (2900, -230)],
    [(2900, -240), (2950, -265), (2900, -290)],
    [(3200, 0), (3150, 50), (3200, 100)],
    [(3200, 110), (3150, 160), (3200, 210)],
    [(3200, 220), (3150, 270), (3200, 320)],
    [(3200, 330), (3150, 380), (3200, 430)],
    [(2900, -500), (2950, -450), (3000, -500)],
    [(3010, -500), (3060, -450), (3110, -500)],
    [(3120, -500), (3170, -450), (3220, -500)],
    [(3230, -500), (3280, -450), (3330, -500)],
    [(3340, -500), (3390, -450), (3440, -500)],
    [(3450, -500), (3500, -450), (3550, -500)],
    [(3560, -500), (3610, -450), (3660, -500)],
    [(3670, -500), (3720, -450), (3770, -500)],
    [(3780, -500), (3830, -450), (3880, -500)],
    [(3890, -500), (3940, -450), (3990, -500)],
    [(4000, 200), (4050, 150), (4100, 200)],
    [(4110, 200), (4160, 150), (4210, 200)],
    [(4220, 200), (4270, 150), (4320, 200)],
    [(4330, 200), (4380, 150), (4430, 200)],
    [(4440, 200), (4490, 150), (4540, 200)],
    [(4550, 200), (4600, 150), (4650, 200)],
    [(4660, 200), (4710, 150), (4760, 200)],
    [(4770, 200), (4820, 150), (4870, 200)],
    [(4880, 200), (4930, 150), (4980, 200)],
    [(4990, 200), (5040, 150), (5090, 200)],
    [(5100, 200), (5150, 150), (5200, 200)],
    [(5210, 200), (5260, 150), (5310, 200)],
    [(5320, 200), (5370, 150), (5420, 200)],
    [(5430, 200), (5480, 150), (5530, 200)],
    [(4950, 300), (5000, 350), (5050, 300)],
    [(4350, 300), (4400, 350), (4450, 300)],
    ]

    exit_portal = pygame.Rect(3400, 500, 50, 100)
    clock = pygame.time.Clock()

    gravity_strongers = [
        (300, 50, 30, (204, 102, 204)),
    ]

    gravity_weakers = [
        (2550, 350, 30, (0, 102, 204)),
    ]

    moving_block = pygame.Rect(4200, 30, 100, 20)
    moving_direction1 = 1
    moving_speed = 5
    moving_limit_left1 = 4050
    moving_limit_right1 = 5600

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
        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()  # Reset the timer
            key_block_pairs[0]["collected"] = False  # Reset key block status
            weak_grav = False
            strong_grav = False # Reset gravity status
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 50, -50
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if strong_grav:
                velocity_y = -strong_jump_strength
            elif weak_grav:
                velocity_y = -weak_grav_strength
            else:
                velocity_y = -jump_strength
            if not is_mute:
                jump_sound.play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

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
                    if strong_grav:
                        velocity_y = -21
                    elif weak_grav:
                        velocity_y = -54
                    else:
                        velocity_y = -33  # Apply upward velocity for the jump
                    on_ground = True
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


        if player_y > SCREEN_HEIGHT:
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()
            key_block_pairs[0]["collected"] = False  # Reset key block status
            strong_grav = False # Reset strong gravity status
            weak_grav = False # Reset weak gravity status
            if not is_mute:    
                fall_sound.play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

                # Moving blocks
        moving_block.x += moving_speed * moving_direction1
        if moving_block.x < moving_limit_left1 or moving_block.x > moving_limit_right1:
            moving_direction1 *= -1

        # Checkpoint Logic
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            weak_grav = False # Reset weak gravity status
            strong_grav = False # Reset strong gravity status
            spawn_x, spawn_y = 2300, 260  # Store checkpoint position
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            weak_grav = False
            strong_grav = False # Reset gravity status
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 5600, 500  # Checkpoint position
            if not is_mute:
                checkpoint_sound.play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 9:
                progress["complete_levels"] = 9

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl9"] or progress["times"]["lvl9"] == 0:
                progress["times"]["lvl9"] = round(current_time, 2)
            
            progress["medals"]["lvl9"] = get_medal(9, progress["times"]["lvl9"])

            update_locked_levels()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl10_screen')

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 440:
            camera_y = player_y - 440
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

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(green_background, (0, 0))

        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(act_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
        for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            # Check collision if not yet collected
            if not pair["collected"]:
                key_rect = pygame.Rect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)
            if player_rect.colliderect(key_rect):
                if not pair["collected"] and not is_mute:
                    open_sound.play()
                pair["collected"] = True
            
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)

            # Draw block only if key is not collected
            if not pair["collected"]:
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

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
                key_block_pairs[0]["collected"] = False  # Reset key block status
                weak_grav = False # Reset weak gravity status
                strong_grav = False # Reset strong gravity status
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                velocity_y = 0
                if not is_mute:
                    death_sound.play()
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
                key_block_pairs[0]["collected"] = False  # Reset key block status
        # Trigger death logic
                weak_grav = False # Reset weak gravity status
                strong_grav = False # Reset strong gravity status
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                velocity_y = 0
                if not is_mute:
                    death_sound.play()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                wait_time = pygame.time.get_ticks()
                weak_grav = False
                strong_grav = False
                key_block_pairs[0]["collected"] = False  # Reset key block status
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1

        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))        

        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

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
                    key_block_pairs[0]["collected"] = False  # Reset key block status
                    strong_grav = False # Reset gravity status
                    weak_grav = False # Reset weak gravity status
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    wait_time = pygame.time.get_ticks()
                    if not is_mute:
                        death_sound.play()
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
                    key_block_pairs[0]["collected"] = False  # Reset key block status
                    weak_grav = False
                    strong_grav = False # Reset gravity status
            # Trigger death logic
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    wait_time = pygame.time.get_ticks()
                    if not is_mute:
                        death_sound.play()
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    break

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
                if not is_mute:
                    button_sound.play()
                strong_grav = True
                weak_grav = False

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
                if not is_mute:
                    button_sound.play()
                weak_grav = True
                strong_grav = False

        for x, y, r, color in deceiver_saws:
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        
        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = font.render(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        levels = load_language(lang_code).get('levels', {})
        lvl9_text = levels.get("lvl9", "Level 9")  # Render the level text
        screen.blit(font.render(lvl9_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        button2_text = in_game.get("button2_message", "Lavender buttons, upon activation, will make you jump lower!")
        screen.blit(font.render(button2_text, True, (204, 102, 204)), (100 - camera_x, 100 - camera_y))

        clarify2_text = in_game.get("clarify_message2", "They also affect your jumps on jump blocks!")
        screen.blit(font.render(clarify2_text, True, (204, 102, 204)), (1000 - camera_x, 450 - camera_y))

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None

        pygame.display.update() 

def create_lvl10_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked
    
    wait_time = None
    start_time = time.time()

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y =  0, 50
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    # When the gravity is weaker
    strong_jump_strength = 15
    strong_grav = False
    weak_grav_strength = 37
    weak_grav = False
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    lights_off = True

    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(3100, 370, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(5000, 370, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 3100, 370
    flag_2_x, flag_2_y = 5000, 370

    blocks = [
        pygame.Rect(-100, 500, 1200, 50),
        pygame.Rect(1300, 400, 200, 50),
        pygame.Rect(1625, 500, 200, 50),
        pygame.Rect(3000, 480, 300, 50),
        pygame.Rect(3500, 480, 100, 300),
        pygame.Rect(3800, 260, 100, 520),
        pygame.Rect(4100, 40, 100, 740),
        pygame.Rect(4400, 260, 100, 520),
        pygame.Rect(4700, 480, 100, 300),
        pygame.Rect(4950, 480, 1200, 100)
    ]

    jump_blocks = [
        pygame.Rect(11000, 600, 100, 100),
        pygame.Rect(14000, 600, 100, 100),
    ]

    moving_saws = [ 
        {'r': 70, 'speed': 7, 'cx': 5900, 'cy': 400, 'max': 600, 'min': 100},
    ]

    moving_saws_x = [
        {'r': 100, 'speed':4, 'cx': 600, 'cy': 500, 'min': 600, 'max': 1000},
        {'r': 50, 'speed': 14, 'cx':3550, 'cy': 430, 'min': 3550, 'max': 4750},
        {'r': 50, 'speed': 14, 'cx':3550, 'cy': -10, 'min': 3550, 'max': 4750},
        {'r': 50, 'speed': 9, 'cx':5200, 'cy': 480, 'min': 5200, 'max': 6000},
        {'r': 50, 'speed': 9, 'cx':5200, 'cy': 180, 'min': 5200, 'max': 6000},
    ]

    saws = [
        (1500, 425, 80, (255, 0, 0)),
        (1825, 525, 80, (255, 0, 0)),
        (2500, 310, 50, (255, 0, 0)),
    ]

    deceiver_saws = [
        (1970, 450, 28, (255, 0 , 127)),
    ]        

    invisible_blocks = [
        pygame.Rect(1920, 400, 100, 100),
    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 300, 'angle': 0, 'speed': 3},
    ]

    light_off_button = pygame.Rect(400, 380, 50, 50)
    
    light_blocks = [
        pygame.Rect(1300, 0, 200, 400),
    ]

    exit_portal = pygame.Rect(6100, 380, 50, 100)
    clock = pygame.time.Clock()

    gravity_strongers = [
        (5050, 420, 30, (204, 102, 204)),
    ]

    teleporters = [
        {
            "entry": pygame.Rect(1110, 1100, 50, 100),
            "exit": pygame.Rect(8300, -400, 50, 100),
            "color": (0, 196, 255)
        },
    ]

    moving_block = pygame.Rect(2200, 300, 100, 20)
    moving_direction1 = 1
    moving_speed = 5
    moving_limit_left1 = 2200
    moving_limit_right1 = 2800

    while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()
        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()  # Reset the timer
            lights_off = True
            strong_grav = False # Reset gravity status
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 50, -50
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if strong_grav:
                velocity_y = -strong_jump_strength
            elif weak_grav:
                velocity_y = -weak_grav_strength
            else:
                velocity_y = -jump_strength
            if not is_mute:
                jump_sound.play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

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
                    if strong_grav:
                        velocity_y = -21
                    else:
                        velocity_y = -33  # Apply upward velocity for the jump
                    on_ground = True
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

        if player_y > SCREEN_HEIGHT:
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()
            lights_off = True
            strong_grav = False # Reset strong gravity status
            if not is_mute:    
                fall_sound.play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

                # Moving blocks
        moving_block.x += moving_speed * moving_direction1
        if moving_block.x < moving_limit_left1 or moving_block.x > moving_limit_right1:
            moving_direction1 *= -1

        # Checkpoint Logic
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            lights_off = True
            strong_grav = False # Reset strong gravity status
            spawn_x, spawn_y = 3100, 260  # Store checkpoint position
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            lights_off = True
            strong_grav = False # Reset gravity status
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 4950, 300  # Checkpoint position
            if not is_mute:
                checkpoint_sound.play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 10:
                progress["complete_levels"] = 10
            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl10"] or progress["times"]["lvl10"] == 0:
                progress["times"]["lvl10"] = round(current_time, 2)
            
            progress["medals"]["lvl10"] = get_medal(10, progress["times"]["lvl10"])

            update_locked_levels()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl11_screen')

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 440:
            camera_y = player_y - 440
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

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(green_background, (0, 0))

        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(act_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))

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
                lights_off = True 
                strong_grav = False # Reset strong gravity status
                collision_detected = True  # Set the flag to stop further checks
                death_text = in_game.get("sawed_message", "Sawed to bits!")    
                wait_time = pygame.time.get_ticks()
                velocity_y = 0            
                player_x, player_y = spawn_x, spawn_y  # Reset player position    
                deathcount += 1        
                if not is_mute:
                    death_sound.play()
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
                lights_off = True
                strong_grav = False # Reset strong gravity status
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                velocity_y = 0
                if not is_mute:
                    death_sound.play()
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
                lights_off = True
                strong_grav = False # Reset strong gravity status
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                velocity_y = 0
                if not is_mute:
                    death_sound.play()
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
                lights_off = True
                strong_grav = False # Reset strong gravity status
                    # Trigger death logic
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                velocity_y = 0
                if not is_mute:
                    death_sound.play()

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                wait_time = pygame.time.get_ticks()
                weak_grav = False
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1

        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))        

        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

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
                if not is_mute:
                    button_sound.play()
                strong_grav = True
                weak_grav = False

        for x, y, r, color in deceiver_saws:
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        # Draw the texts

        button2_text = in_game.get("button3_message", "Purple buttons, upon activation, will turn out almost all the lights!")
        screen.blit(font.render(button2_text, True, (104, 102, 204)), (100 - camera_x, 300 - camera_y))

        if player_rect.colliderect(light_off_button):
            if not is_mute and lights_off:
                button_sound.play()
            lights_off = False

        if not lights_off:
            # Create a full dark surface
            pygame.draw.rect(screen, (0, 0, 0), (0, 0, SCREEN_WIDTH // 2 -  320 , SCREEN_HEIGHT ))
            pygame.draw.rect(screen, (0, 0, 0), (SCREEN_WIDTH // 2 + 320, 0, SCREEN_WIDTH // 2 + 320, SCREEN_HEIGHT))
            pygame.draw.rect(screen, (0, 0, 0), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2 - 320))
            pygame.draw.rect(screen, (0, 0, 0), (0, SCREEN_HEIGHT // 2 + 320, SCREEN_WIDTH, SCREEN_HEIGHT // 2 + 320))
        
        if lights_off:
            pygame.draw.rect(screen, (104, 102, 204), (light_off_button.x - camera_x, light_off_button.y - camera_y, light_off_button.width, light_off_button.height))
            for light_block in light_blocks:
                pygame.draw.rect(screen, (104, 102, 204), (light_block.x - camera_x, light_block.y - camera_y, light_block.width, light_block.height))

        if lights_off:
            for block in light_blocks:
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

        levels = load_language(lang_code).get('levels', {})
        lvl10_text = levels.get("lvl10", "Level 10")  # Render the level text
        screen.blit(font.render(lvl10_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = font.render(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None

        pygame.display.update() 

def create_lvl11_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked

    in_game = load_language(lang_code).get('in_game', {})
    messages = load_language(lang_code).get('messages', {})

    wait_time = None
    start_time = time.time()

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y =  -400, 300
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21

    # Gravity buttons
    strong_jump_strength = 15
    strong_grav = False
    weak_grav_strength = 37
    weak_grav = False
    
    # Speed settings
    move_speed = 8
    stamina = False
    stamina_speed = 19

    # Other settings
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    lights_off = True

    # Preparation for fight with Evil Robo
    suspicious_x = 4200
    trigger_x = 4650
    espawn_x, espawn_y = 5200, -400
    epos_x, epos_y = espawn_x, espawn_y
    evilrobo_mascot = pygame.image.load(f"char/evilrobot.png").convert_alpha()
    evilrobo_phase = 0    

    # Logic for unlocking Evil Robo
    unlock = progress.get("evilrobo_unlocked", False)
    unlock_time = None

    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(1400, 420, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(5400, 330, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 1400, 420
    flag_2_x, flag_2_y = 5400, 330

    key_block_pairs = [
        {
            "key": (3700, 1550, 30, (255, 255, 0)),
            "block": pygame.Rect(3200, 1000, 400, 200),
            "collected": False
        },
    ]

    blocks = [
        pygame.Rect(-600, 525, 2850, 50),
        pygame.Rect(1065, 200, 70, 375),
        pygame.Rect(1625, -200, 100, 590),
        pygame.Rect(1625, 50, 150, 50),
        pygame.Rect(2200, 400, 100, 50),
        pygame.Rect(2250, -300, 600, 1000),
        pygame.Rect(2300, 200, 3000, 100),
        pygame.Rect(3100, -300, 2600, 100),
        pygame.Rect(3050, -500, 120, 300),
        pygame.Rect(5180, 250, 120, 300),
        pygame.Rect(5250, 450, 1500, 100),
        pygame.Rect(5600, -1400, 520, 1700),
    ]

    jump_blocks = [
        pygame.Rect(630, 425, 100, 100),
        pygame.Rect(14000, 600, 100, 100),
    ]

    moving_saws = [ 
        {'r': 70, 'speed': 6, 'cx': 3500, 'cy': -350, 'max': 500, 'min': -500},
        {'r': 70, 'speed': 6, 'cx': 4000, 'cy': -200, 'max': 500, 'min': -500},
        {'r': 70, 'speed': 6, 'cx': 4500, 'cy': -50, 'max': 500, 'min': -500},
        {'r': 70, 'speed': 6, 'cx': 5000, 'cy': 50, 'max': 500, 'min': -500},
    ]

    moving_saws_x = [
        {'r': 30, 'speed': 3, 'cx': 1700, 'cy': 320, 'min': 1650, 'max': 1900},
        {'r': 30, 'speed': 4, 'cx': 2100, 'cy': -130, 'min': 1750, 'max': 2100},
    ]

    rushing_saws = [
        {'r': 200, 'speed': 21, 'cx': 3000, 'cy': 0, 'max': 5920},
    ]

    moving_block = [
        {'x': 1700, 'y': 270, 'width': 110, 'height': 100, 'direction': 1, 'speed': 3, 'left_limit': 1650, 'right_limit': 1900 },
        {'x': 2100, 'y': -180, 'width': 110, 'height': 100, 'direction': 1, 'speed': 4, 'left_limit': 1750, 'right_limit': 2100 },
    ]

    saws = [
        (1100, 200, 200, (255, 0, 0)),
        (6300, 450, 80, (255, 0, 0)),
    ]

    spikes = [
    [(0, 525), (100, 475), (200, 525)],
    [(210, 525), (310, 475), (410, 525)],
    [(420, 525), (520, 475), (620, 525)],
    [(1625, -50), (1575, 0), (1625, 50)],
    [(1625, 60), (1575, 110), (1625, 160)],
    [(1625, 170), (1575, 220), (1625, 270)],
    [(1625, 280), (1575, 330), (1625, 380)],
    ]

    light_off_button = pygame.Rect(2350, -425, 50, 50)
    
    light_blocks = [
        pygame.Rect(5300, 200, 300, 100),
    ]

    exit_portal = pygame.Rect(6620, 350, 50, 100)
    clock = pygame.time.Clock()

    speedsters = [
        (-100, 400, 30, (51, 255, 51)),
        (2450, -400, 30, (51, 255, 51)),
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

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            lights_off = True
            stamina = False
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = -400, 300
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if strong_grav:
                velocity_y = -strong_jump_strength
            elif weak_grav:
                velocity_y = -weak_grav_strength
            else:
                velocity_y = -jump_strength
            if not is_mute:
                jump_sound.play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                if stamina:
                    player_x -= stamina_speed
                else:
                    player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if stamina:
                    player_x += stamina_speed
                else:
                    player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False

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
                    if strong_grav:
                        velocity_y = -21
                    elif weak_grav:
                        velocity_y = -54
                    else:
                        velocity_y = -33  # Apply upward velocity for the jump
                    on_ground = True
                    if not is_mute:
                        bounce_sound.play()

                # Horizontal collision (left or right side of the jump block)
                elif player_x + img_width > jump_block.x and player_x < jump_block.x + jump_block.width:
                    if player_x < jump_block.x:  # Colliding with the left side of the jump block
                        player_x = jump_block.x - img_width
                    elif player_x + img_width > jump_block.x + jump_block.width:  # Colliding with the right side
                        player_x = jump_block.x + jump_block.width

        for block in moving_block:
            rect = pygame.Rect(block['x'], block['y'], block['width'], block['height'])
            if player_rect.colliderect(rect):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= rect.y:
                    player_y = rect.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > rect.x and player_x < rect.x + rect.width:
                    if player_x < rect.x:  # Colliding with the left side of the block
                        player_x = rect.x - img_width
                    elif player_x + img_width > rect.x + rect.width:  # Colliding with the right side
                        player_x = rect.x + rect.width

        for pair in key_block_pairs:
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


        if player_y > (SCREEN_HEIGHT + 100):
            death_text = in_game.get("fall_message", "Fell too far!")
            evilrobo_phase = 0
            epos_x, epos_y = espawn_x, espawn_y
            lights_off = True
            stamina = False
            wait_time = pygame.time.get_ticks()
            if not is_mute:    
                fall_sound.play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

        # Moving blocks
        for block in moving_block:
            block['x'] += block['speed'] * block['direction']
            if block['x'] < block['left_limit'] or block['x'] > block['right_limit']:
                block['direction'] *= -1

        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        # Checkpoint logic
        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            stamina = False  # Reset stamina status
            lights_off = True
            spawn_x, spawn_y = 1400, 420  # Store checkpoint position
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            lights_off = True
            stamina = False
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 5400, 280  # Checkpoint position
            if not is_mute:
                checkpoint_sound.play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 11:
                progress["complete_levels"] = 11

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl11"] or progress["times"]["lvl11"] == 0:
                progress["times"]["lvl11"] = round(current_time, 2)
            
            progress["medals"]["lvl11"] = get_medal(11, progress["times"]["lvl11"])

            update_locked_levels()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl12_screen')    

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 440:
            camera_y = player_y - 440
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(green_background, (0, 0))

        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(act_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))

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
                lights_off = True
                stamina = False
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                velocity_y = 0
                evilrobo_phase = 0
                epos_x, epos_y = espawn_x, espawn_y
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    death_sound.play()
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
                lights_off = True
                stamina = False
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                velocity_y = 0
                evilrobo_phase = 0
                epos_x, epos_y = espawn_x, espawn_y
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    death_sound.play()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1

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
                lights_off = True
                stamina = False
                    # Trigger death logic
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()
                velocity_y = 0
                evilrobo_phase = 0
                epos_x, epos_y = espawn_x, espawn_y
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()

        for saw in rushing_saws:
            saw['cx'] += saw['speed']
            if saw['cx'] > saw['max']:
                saw['cx'] = 2700
            # Find the closest point on the player's rectangle to the saw's center
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))

            # Calculate the distance between the closest point and the saw's center
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5

            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

            if distance < saw['r']:
                lights_off = True
                stamina = False
                    # Trigger death logic
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                velocity_y = 0
                evilrobo_phase = 0
                epos_x, epos_y = espawn_x, espawn_y
                wait_time = pygame.time.get_ticks()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()

        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))        

        for block in moving_block:
            pygame.draw.rect(screen, (128, 0, 128), (block['x'] - camera_x, block['y'] - camera_y, block['width'], block['height']))
        
        for block in moving_block:
            pygame.draw.rect(screen, (128, 0, 128), ((block['x'] - camera_x), (block['y'] - camera_y), block['width'], block['height']))
            if block['width'] < 100:
                laser_rect = pygame.Rect(block['x'], block['y'] + block['height'] +10, block['width'], 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block['x'] + 4, block['y'] + block['height'] + 5, block['width'] - 8 , 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground and player_x != block['x']:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                evilrobo_phase = 0
                epos_x, epos_y = espawn_x, espawn_y
                stamina = False
                wait_time = pygame.time.get_ticks()
                lights_off = True
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1
                
        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                evilrobo_phase = 0
                wait_time = pygame.time.get_ticks()
                epos_x, epos_y = espawn_x, espawn_y
                stamina = False
                lights_off = True
                if not is_mute:    
                    hit_sound.play()
                velocity_y = 0
                deathcount += 1

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
                    lights_off = True
                    stamina = False
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    wait_time = pygame.time.get_ticks()
                    evilrobo_phase = 0
                    epos_x, epos_y = espawn_x, espawn_y
                    if not is_mute:
                        death_sound.play()
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
                    lights_off = True
                    stamina = False
            # Trigger death logic
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    evilrobo_phase = 0
                    velocity_y = 0
                    epos_x, epos_y = espawn_x, espawn_y
                    wait_time = pygame.time.get_ticks()
                    if not is_mute:
                        death_sound.play()
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    break

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
                if not is_mute:
                    button_sound.play()
                strong_grav = False
                stamina = True
                weak_grav = False

        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))
        # Player Image
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        # Boss Trigger Area

        if player_x > suspicious_x and player_y < -300 and lights_off:
            screen.blit(evilrobo_mascot, ((epos_x - camera_x), (epos_y - camera_y)))

            if evilrobo_phase == 0 and player_x < trigger_x:
                sus_message = font.render("Huh? Is there anyone there?", True, (255, 20, 12))
                screen.blit(sus_message, (4800 - camera_x, -450 - camera_y))
            else:
                if evilrobo_phase < 1:
                    evilrobo_phase = 1  # Prevents repeating

        if evilrobo_phase == 1 and player_y < -300 and lights_off:
            holup_message = font.render("HEY! Get away from here!", True, (185, 0, 0))
            screen.blit(holup_message, (4800 - camera_x, -450 - camera_y))
            
        if evilrobo_phase == 1 and lights_off:
            screen.blit(evilrobo_mascot, (int(epos_x - camera_x), int(epos_y - camera_y)))
            if epos_x > player_x + 10:
                epos_x -= 20
            elif epos_x < player_x - 10:
                epos_x += 20
            else:
                epos_x = player_x

        if evilrobo_phase == 2:
            screen.blit(evilrobo_mascot, (int(epos_x - camera_x), int(epos_y - camera_y)))
            if player_y > -300:
                confused_text = font.render("WHERE DID HE GO????", True, (82, 0, 0))
                screen.blit(confused_text, ((epos_x - camera_x), (epos_y - camera_y)))
                if not unlock:
                    if not is_mute:
                        notify_sound.play()
                    unlock = True
                    unlock_time = pygame.time.get_ticks()
                    progress["evilrobo_unlocked"] = unlock
                    save_progress(progress)
            epos_x -= 12

        if epos_x < 2150:
            evilrobo_phase = 2

        if unlock and unlock_time is not None:
            current_time = pygame.time.get_ticks()
            if current_time - unlock_time <= 5000:
                unlock_text = messages.get("evilrobo_unlocked", "Evil Robo unlocked!")
                rendered_unlock_text = font.render(unlock_text, True, (41, 255, 11))
                screen.blit(rendered_unlock_text , (SCREEN_WIDTH // 2 - rendered_unlock_text .get_width() // 2, 80))

        evilrobo_rect = pygame.Rect(int(epos_x), int(epos_y), evilrobo_mascot.get_width(), evilrobo_mascot.get_height())
        
        if player_rect.colliderect(evilrobo_rect) and lights_off:
            evilrobo_phase = 0
            velocity_y = 0
            epos_x, epos_y = espawn_x, espawn_y
            player_x, player_y = spawn_x, spawn_y
            screen.fill((255, 255, 255))
            stamina = False
            if not is_mute:
                hit_sound.play()
            deathcount += 1

        if player_x > 4800 and player_y < -300 and not lights_off:
            epos_x = 4799
            epos_y = player_y
            screen.blit(evilrobo_mascot, ((epos_x - camera_x), (epos_y - camera_y)))
            if player_rect.colliderect(evilrobo_rect):
                screen.fill((255, 255, 255))
                epos_x, epos_y = espawn_x, espawn_y
                player_x, player_y = spawn_x, spawn_y
                hit_sound.play()
                

        button4_text = in_game.get("button4_message", "Green buttons, upon activation, will give you a massive speed boost!")
        rendered_button4_text = font.render(button4_text, True, (51, 255, 51))
        screen.blit(rendered_button4_text, (-320 - camera_x, 300 - camera_y))

        if player_rect.colliderect(light_off_button) and evilrobo_phase != 1:
            if not is_mute and lights_off:
                button_sound.play()
            lights_off = False

        if not lights_off:
            # Create a full dark surface
            pygame.draw.rect(screen, (0, 0, 0), (0, 0, SCREEN_WIDTH // 2 -  320 , SCREEN_HEIGHT ))
            pygame.draw.rect(screen, (0, 0, 0), (SCREEN_WIDTH // 2 + 320, 0, SCREEN_WIDTH // 2 + 320, SCREEN_HEIGHT))
            pygame.draw.rect(screen, (0, 0, 0), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2 - 320))
            pygame.draw.rect(screen, (0, 0, 0), (0, SCREEN_HEIGHT // 2 + 320, SCREEN_WIDTH, SCREEN_HEIGHT // 2 + 320))
        
        if lights_off and evilrobo_phase != 1:
            pygame.draw.rect(screen, (104, 102, 204), (light_off_button.x - camera_x, light_off_button.y - camera_y, light_off_button.width, light_off_button.height))
            for light_block in light_blocks:
                pygame.draw.rect(screen, (104, 102, 204), (light_block.x - camera_x, light_block.y - camera_y, light_block.width, light_block.height))

        if lights_off:
            for block in light_blocks:
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


        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        levels = load_language(lang_code).get('levels', {})
        lvl11_text = levels.get("lvl11", "Level 11")  # Render the level text
        screen.blit(font.render(lvl11_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = font.render(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner
        
        if show_greenrobo_unlocked:
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None

        pygame.display.update() 

# Check snow effects!
class Particle:
    def __init__(self, x, y, color=(255,255,255), size=5, lifetime=30, vx = None, vy = None):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2) if vx is None else vx
        self.vy = random.uniform(-2, 2) if vy is None else vy
        self.color = color
        self.size = size
        self.lifetime = lifetime

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)

# Snow
snow = []

def create_lvl12_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, particles

    in_game = load_language(lang_code).get('in_game', {})

    start_time = time.time()

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y =  2100, 400
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21

    # Gravity buttons
    strong_jump_strength = 15
    strong_grav = False
    weak_grav_strength = 37
    weak_grav = False
    
    # Speed settings
    move_speed = 8
    stamina = False
    stamina_speed = 19
    velocity_x = move_speed
    ice_dece = 0.2 # Velocity X deceleration when on ice

    # Which key was the last one pressed?
    leftkey_prev = False
    rightkey_prev = False

    # Other settings
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    lights_off = True
    
    # Robo Temperature and Ice
    start_temp = 24.0
    on_ground_heatup = 0.08
    air_heatup = 0.02
    ice_cooldown = 0.11
    max_temp = 55.0
    min_temp = 5.0
    current_temp = start_temp
    ice_melt = 0.3
    on_ice = False

    # Load player image
    player_img = pygame.image.load(f"char/{selected_character}.png").convert_alpha()
    img_width, img_height = player_img.get_size()

    # Draw flag
    flag = pygame.Rect(5250, 460, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(54000, 300, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 5250, 460
    flag_2_x, flag_2_y = 54900, 300

    key_block_pairs = [
        {
            "key": (3650, -50, 30, (255, 255, 0)),
            "block": pygame.Rect(4200, 350, 200, 200),
            "collected": False
        },
    ]

    blocks = [
        pygame.Rect(4200, 550, 1200, 100),
        pygame.Rect(3100, 50, 125, 125),
        pygame.Rect(3800, 50, 125, 125),
        pygame.Rect(4200, -100, 200, 450)
    ]

    jump_blocks = [
        pygame.Rect(3700, 450, 100, 100),
    ]

    class IceBlock:
        def __init__(self, rect):
            self.rect = rect
            self.initial_height = float(rect.height)
            self.float_height = self.initial_height

    ice_blocks = [
        IceBlock(pygame.Rect(2000, 550, 2000, 150)),
        IceBlock(pygame.Rect(5670, 550, 6000, 50))
    ]

    moving_saws = [ 
        {'r': 70, 'speed': 4, 'cx': 2870, 'cy': 350, 'max': 750, 'min': 200},
        {'r': 70, 'speed': 6, 'cx': 3230, 'cy': 600, 'max': 850, 'min': 200},
    ]

    moving_saws_x = [
        {'r': 30, 'speed': 9, 'cx': 6300, 'cy': 550, 'min': 6250, 'max': 7800},
        {'r': 30, 'speed': 4, 'cx': 2100, 'cy': -130, 'min': 1750, 'max': 2100},
    ]

    rushing_saws = [
        {'r': 50, 'speed': 12, 'cx': 3150, 'cy': 120 ,'max': 3850},
    ]

    moving_block = [
        {'x': 1700, 'y': 270, 'width': 110, 'height': 100, 'direction': 1, 'speed': 3, 'left_limit': 1650, 'right_limit': 1900 },
        {'x': 2100, 'y': -180, 'width': 110, 'height': 100, 'direction': 1, 'speed': 4, 'left_limit': 1750, 'right_limit': 2100 },
    ]

    saws = [
        (4600, 550, 80, (255, 0, 0)),
        (5000, 550, 80, (255, 0, 0)),
    ]

    spikes = [
    [(2600, 550), (2645, 500), (2690, 550)],
    [(2700, 550), (2745, 500), (2790, 550)],
    [(3300, 550), (3345, 500), (3390, 550)],
    [(3400, 550), (3445, 500), (3490, 550)],
    [(3100, 50), (3162, -100), (3225, 50)],
    [(3800, 50), (3862, -100), (3925, 50)],
    ]

    light_off_button = pygame.Rect(2350, -425, 50, 50)
    
    light_blocks = [
        pygame.Rect(5300, 200, 300, 100),
    ]

    exit_portal = pygame.Rect(1200, 350, 50, 100)
    clock = pygame.time.Clock()

    speedsters = [
        (5300, 450, 30, (51, 255, 51)),
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

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            lights_off = True
            stamina = False
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            current_temp = start_temp
            spawn_x, spawn_y = 2100, 400
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("ice_levels")

        # Ice and Ground temeprature logic
        if not keys[pygame.K_r]:
            if not on_ice and on_ground:
                current_temp += on_ground_heatup
            elif not on_ice and not on_ground:
                current_temp += air_heatup
            else:
                current_temp -= ice_cooldown

        # Minimum and Maximum Temperature Logic
        if current_temp > max_temp:
            player_x, player_y = spawn_x, spawn_y
            if not is_mute:
                overheat_sound.play()
            current_temp = start_temp
            for ice in ice_blocks:
                ice.float_height = ice.initial_height
                ice.rect.height = int(ice.float_height)
        elif current_temp < min_temp:
            player_x, player_y = spawn_x, spawn_y
            if not is_mute:
                freeze_sound.play()
            current_temp = start_temp            
            for ice in ice_blocks:
                ice.float_height = ice.initial_height
                ice.rect.height = int(ice.float_height)

        # Rounded off value
        current_temp = round(current_temp, 2)
        
        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if strong_grav:
                velocity_y = -strong_jump_strength
            elif weak_grav:
                velocity_y = -weak_grav_strength
            else:
                velocity_y = -jump_strength
            if not is_mute:
                jump_sound.play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                if stamina:
                    velocity_x = stamina_speed
                    player_x -= velocity_x
                else:
                    velocity_x = move_speed
                    player_x -= velocity_x
                leftkey_prev = True
                rightkey_prev = False
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if stamina:
                    velocity_x = stamina_speed
                    player_x += velocity_x
                else:
                    velocity_x = move_speed
                    player_x += velocity_x
                leftkey_prev = False
                rightkey_prev = True

            if on_ground and not was_moving and not is_mute:
                move_sound.play()
            was_moving = True
        else:
            was_moving = False

        if on_ice and velocity_x > 0:
            if leftkey_prev:
                velocity_x = velocity_x - ice_dece
                player_x -= velocity_x
            elif rightkey_prev:
                velocity_x = velocity_x - ice_dece
                player_x += velocity_x

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False
        on_ice = False

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

        for ice in ice_blocks:
            block = ice.rect
            if player_rect.colliderect(block):
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True
                    on_ice = True
                    ice.float_height -= ice_melt
                    block.height = int(ice.float_height)

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
                    if strong_grav:
                        velocity_y = -21
                    elif weak_grav:
                        velocity_y = -54
                    else:
                        velocity_y = -33  # Apply upward velocity for the jump
                    on_ground = True
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

        for block in moving_block:
            rect = pygame.Rect(block['x'], block['y'], block['width'], block['height'])
            if player_rect.colliderect(rect):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= rect.y:
                    player_y = rect.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= rect.y + rect.height - velocity_y:
                    player_y = rect.y + rect.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > rect.x and player_x < rect.x + rect.width:
                    if player_x < rect.x:  # Colliding with the left side of the block
                        player_x = rect.x - img_width
                    elif player_x + img_width > rect.x + rect.width:  # Colliding with the right side
                        player_x = rect.x + rect.width

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

        # Moving blocks
        for block in moving_block:
            block['x'] += block['speed'] * block['direction']
            if block['x'] < block['left_limit'] or block['x'] > block['right_limit']:
                block['direction'] *= -1

        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        # Checkpoint logic
        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            stamina = False  # Reset stamina status
            lights_off = True
            spawn_x, spawn_y = 5300, 400  # Store checkpoint position
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            lights_off = True
            stamina = False
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 5400, 280  # Checkpoint position
            if not is_mute:
                checkpoint_sound.play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 12:
                progress["complete_levels"] = 12
                # You might want to update locked_levels here as well if needed

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl12"] or progress["times"]["lvl12"] == 0:
                progress["times"]["lvl12"] = round(current_time, 2)
            
            progress["medals"]["lvl12"] = get_medal(1, progress["times"]["lvl12"])

            update_locked_levels()
            save_progress(progress)  # Save progress to JSON file

            running = False
            set_page('main_menu')    

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 440:
            camera_y = player_y - 440
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(ice_background, (0, 0))

        # Update and draw particles
        for particle in snow[:]:
            particle.update()
            particle.draw(screen)
            if particle.lifetime <= 0:
                snow.remove(particle)

        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(act_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))

        for saw in moving_saws:
                # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

        for saw in moving_saws_x:
    # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

        for x, y, r, color in saws:
            # Draw the saw as a circle
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        for saw in rushing_saws:
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))        

        for block in moving_block:
            pygame.draw.rect(screen, (128, 0, 128), (block['x'] - camera_x, block['y'] - camera_y, block['width'], block['height']))
        
        for block in moving_block:
            pygame.draw.rect(screen, (128, 0, 128), ((block['x'] - camera_x), (block['y'] - camera_y), block['width'], block['height']))
                
        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

        for ice in ice_blocks:
            block = ice.rect
            pygame.draw.rect(screen, (0, 205, 255), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
        
        for spike in spikes:
            pygame.draw.polygon(screen, (255, 0, 0), [((x - camera_x),( y - camera_y)) for x, y in spike])

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
                if not is_mute:
                    button_sound.play()
                strong_grav = False
                stamina = True
                weak_grav = False

        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))

        button4_text = in_game.get("button4_message", "Green buttons, upon activation, will give you a massive speed boost!")
        rendered_button4_text = font.render(button4_text, True, (51, 255, 51))
        screen.blit(rendered_button4_text, (-320 - camera_x, 300 - camera_y))

        if player_rect.colliderect(light_off_button):
            if not is_mute and lights_off:
                button_sound.play()
            lights_off = False

        if not lights_off:
            # Create a full dark surface
            pygame.draw.rect(screen, (0, 0, 0), (0, 0, SCREEN_WIDTH // 2 -  320 , SCREEN_HEIGHT ))
            pygame.draw.rect(screen, (0, 0, 0), (SCREEN_WIDTH // 2 + 320, 0, SCREEN_WIDTH // 2 + 320, SCREEN_HEIGHT))
            pygame.draw.rect(screen, (0, 0, 0), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2 - 320))
            pygame.draw.rect(screen, (0, 0, 0), (0, SCREEN_HEIGHT // 2 + 320, SCREEN_WIDTH, SCREEN_HEIGHT // 2 + 320))
        
        if lights_off:
            pygame.draw.rect(screen, (104, 102, 204), (light_off_button.x - camera_x, light_off_button.y - camera_y, light_off_button.width, light_off_button.height))
            for light_block in light_blocks:
                pygame.draw.rect(screen, (104, 102, 204), (light_block.x - camera_x, light_block.y - camera_y, light_block.width, light_block.height))

        if lights_off:
            for block in light_blocks:
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

        pygame.draw.rect(screen, (96, 96, 96), (0, 0, 300 , 130 ))
        pygame.draw.rect(screen, (96, 96, 96), (SCREEN_WIDTH // 2 - 80, 0, 160 , 70))
        pygame.draw.rect(screen, (96, 96, 96), (SCREEN_WIDTH - 250, 0, 250 , 80 ))

        levels = load_language(lang_code).get('levels', {})
        lvl_text = levels.get("lvl12", "Level 12")  # Render the level text
        rendered_lvl_text = font.render(lvl_text, True, (255, 255, 255))
        screen.blit(rendered_lvl_text, (SCREEN_WIDTH //2 - rendered_lvl_text.get_width() // 2, 20)) # Draws the level text

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        temp_val = in_game.get("temp", "Temperature: {current_temp}").format(current_temp=current_temp)
        if current_temp >= 4 and current_temp <= 13:
            screen.blit(font.render(temp_val, True, (0, 188, 255)), (20, 50))
        elif current_temp >= 13 and current_temp <= 20:
            screen.blit(font.render(temp_val, True, (0, 255, 239)), (20, 50))
        elif current_temp >= 20 and current_temp <= 27:
            screen.blit(font.render(temp_val, True, (0, 255, 43)), (20, 50))
        elif current_temp >= 27 and current_temp <= 35:
            screen.blit(font.render(temp_val, True, (205, 255, 0)), (20, 50))
        elif current_temp >= 35 and current_temp <= 43:             
            screen.blit(font.render(temp_val, True, (255, 162, 0)), (20, 50))
        elif current_temp >= 43 and current_temp <= 50: 
            screen.blit(font.render(temp_val, True, (230, 105, 0)), (20, 50))
        elif current_temp >= 50:
            screen.blit(font.render(temp_val, True, (255, 0, 0)), (20, 50))

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = font.render(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = font.render(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = font.render(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        # Locked blocks logic!
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

        for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            # Check collision if not yet collected
            if not pair["collected"]:
                key_rect = pygame.Rect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)
            if player_rect.colliderect(key_rect):
                if not pair["collected"] and not is_mute:
                    open_sound.play()
                pair["collected"] = True
            
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)

            # Draw block only if key is not collected
            if not pair["collected"]:
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

        # DEATH LOGICS
        for block in moving_block:
            if block['width'] < 100:
                laser_rect = pygame.Rect(block['x'], block['y'] + block['height'] +10, block['width'], 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block['x'] + 4, block['y'] + block['height'] + 5, block['width'] - 8 , 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground and player_x != block['x']:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                fall_text = in_game.get("hit_message", "Hit on the head!")
                screen.blit(font.render(fall_text, True, (255, 0, 0)), (20, 80))
                stamina = False
                lights_off = True
                if not is_mute:    
                    hit_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                velocity_y = 0
                deathcount += 1
                for ice in ice_blocks:
                    ice.float_height = ice.initial_height
                    ice.rect.height = int(ice.float_height)

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
                lights_off = True
                stamina = False
                    # Trigger death logic
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 80))
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()
                pygame.display.update()
                pygame.time.delay(300) 
                for ice in ice_blocks:
                    ice.float_height = ice.initial_height
                    ice.rect.height = int(ice.float_height)

        for saw in rushing_saws:
            saw['cx'] += saw['speed']
            if saw['cx'] > saw['max']:
                saw['cx'] = 3150
            # Find the closest point on the player's rectangle to the saw's center
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))

            # Calculate the distance between the closest point and the saw's center
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5

            if distance < saw['r']:
                lights_off = True
                stamina = False
                    # Trigger death logic
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 80))
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()
                pygame.display.update()
                pygame.time.delay(300) 
                for ice in ice_blocks:
                    ice.float_height = ice.initial_height
                    ice.rect.height = int(ice.float_height)


        for saw in moving_saws_x:
    # Update the circle's position (move vertically)
            saw['cx'] += saw['speed']
    # Check if the saw has reached the limits
            if saw['cx'] > saw['max'] or saw['cx'] < saw['min']:
                saw['speed'] = -saw['speed']  # Reverse direction if we hit a limit

    # Collision detection (if needed)
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5
            if distance < saw['r']:
        # Trigger death logic
                lights_off = True
                stamina = False
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 80))
                if not is_mute:
                    death_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                for ice in ice_blocks:
                    ice.float_height = ice.initial_height
                    ice.rect.height = int(ice.float_height)


        for saw in moving_saws:
    # Collision detection (if needed)
            closest_x = max(player_rect.left, min(saw['cx'], player_rect.right))
            closest_y = max(player_rect.top, min(saw['cy'], player_rect.bottom))
            dx = closest_x - saw['cx']
            dy = closest_y - saw['cy']
            distance = (dx**2 + dy**2)**0.5
            # Update the circle's position (move vertically)
            saw['cy'] += saw['speed']  # Move down or up depending on speed

            # Check if the saw has reached the limits
            if saw['cy'] > saw['max'] or saw['cy'] < saw['min']:
                saw['speed'] = -saw['speed']  # Reverse direction if we hit a limit
            
            if distance < saw['r']:
        # Trigger death logic
                lights_off = True
                stamina = False
                sawed_text = in_game.get("sawed_message", "Sawed to bits!")
                screen.blit(font.render(sawed_text, True, (255, 0, 0)), (20, 80))
                if not is_mute:
                    death_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                for ice in ice_blocks:
                    ice.float_height = ice.initial_height
                    ice.rect.height = int(ice.float_height)


        for block in blocks:
            if block.width <= 100:
                laser_rect = pygame.Rect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                fall_text = in_game.get("hit_message", "Hit on the head!")
                screen.blit(font.render(fall_text, True, (255, 0, 0)), (20, 80))
                stamina = False
                lights_off = True
                if not is_mute:    
                    hit_sound.play()
                pygame.display.update()
                pygame.time.delay(300)
                velocity_y = 0
                deathcount += 1
                for ice in ice_blocks:
                    ice.float_height = ice.initial_height
                    ice.rect.height = int(ice.float_height)


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
                    lights_off = True
                    stamina = False
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 80))
                    if not is_mute:
                        death_sound.play()
                    pygame.display.update()
                    pygame.time.delay(300)
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    for ice in ice_blocks:
                        ice.float_height = ice.initial_height
                        ice.rect.height = int(ice.float_height)
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
                    lights_off = True
                    stamina = False
            # Trigger death logic
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 80))
                    if not is_mute:
                        death_sound.play()
                    pygame.display.update()
                    pygame.time.delay(300)
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    for ice in ice_blocks:
                        ice.float_height = ice.initial_height
                        ice.rect.height = int(ice.float_height)
                    break

        if player_y > (SCREEN_HEIGHT + 100):
            fall_text = in_game.get("fall_message", "Fell too far!")
            screen.blit(font.render(fall_text, True, (255, 0, 0)), (20, 80))
            lights_off = True
            stamina = False
            if not is_mute:    
                fall_sound.play()
            pygame.display.update()
            pygame.time.delay(300)
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            for ice in ice_blocks:
                ice.float_height = ice.initial_height
                ice.rect.height = int(ice.float_height)

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        # Player Image
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        pygame.display.update() 

# Handle actions based on current page
def handle_action(key):
    global current_page, pending_level, level_load_time

    if current_page == 'main_menu':
        if key == "start":
            start_game()
        elif key == "achievements":
            set_page("character_select")
        elif key == "settings":
            open_settings()
            progress["is_mute"] = is_mute
            save_progress(progress)
        elif key == "quit":
            set_page("quit_confirm")
        elif key == "language":
            set_page('language_select')
    elif current_page == 'language_select':
        if key == "back":
            go_back()
        elif key in ["en", "fr", "es", "de", "zh_cn", "uz", "pt_br", "ru"]:
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
        elif key == "lvl9":
            set_page("lvl9_screen")
        elif key == "lvl10":
            set_page("lvl10_screen")
        elif key == "lvl11":
            set_page("lvl11_screen")
        elif key == "lvl12":
            set_page("lvl12_screen")
        elif key == "back":
            set_page("main_menu")
        elif key == "next":
            set_page("ice_levels")
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
    elif current_page == "ice_levels":
        if key == "back":
            set_page("levels")
        elif key in ["lvl12", "lvl13", "lvl14", "lvl15"]:
            set_page(f"{key}_screen")

# Start with main menu
set_page('main_menu')
button_hovered_last_frame = False
update_locked_levels() # Update locked levels every frame!
wait_time = None

# Main loop
running = True
while running:
    # Clear screen!
    screen.blit(background, (0, 0))
    mouse_pos = pygame.mouse.get_pos()
    if SCREEN_WIDTH < MIN_WIDTH or SCREEN_HEIGHT < MIN_HEIGHT:
        countdown = 5  # seconds
        clock = pygame.time.Clock()
        start_time = pygame.time.get_ticks()

        while countdown > 0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Calculate time left
            elapsed = (pygame.time.get_ticks() - start_time) // 1000
            countdown = 5 - elapsed

            # Clear the screen
            screen.fill((0, 0, 0))

            # Display the robo image
            screen.blit(lavarobot_img, (SCREEN_WIDTH // 2 - lavarobot_img.get_width() // 2, SCREEN_HEIGHT // 2 - 200))

            # Render the text
            messages = load_language(lang_code).get('messages', {})
            deny_text = messages.get("deny_message", "Access denied!")
            rendered_deny_text = font.render(deny_text, True, (255, 100, 100))
            error_text = messages.get("error_message","Your screen resolution is too small! Increase the screen")
            rendered_error_text = font.render(error_text, True, (255, 255, 255))
            error_text2 = messages.get("error_message2", "resolution in your system settings.")
            rendered_error_text2 = font.render(error_text2, True, (255, 255, 255))
            countdown_text = messages.get("countdown_message", "Closing in {countdown} second(s)...").format(countdown=countdown)
            rendered_countdown_text = font.render(countdown_text, True, (255, 100, 100))

            # Center the text
            screen.blit(rendered_deny_text, (SCREEN_WIDTH // 2 - rendered_deny_text.get_width() // 2, SCREEN_HEIGHT // 2 - 280))            
            screen.blit(rendered_error_text, (SCREEN_WIDTH // 2 - rendered_error_text.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
            screen.blit(rendered_error_text2, (SCREEN_WIDTH // 2 - rendered_error_text2.get_width() // 2, SCREEN_HEIGHT // 2))
            screen.blit(rendered_countdown_text, (SCREEN_WIDTH // 2 - rendered_countdown_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

            pygame.display.flip()
            clock.tick(30)

        pygame.quit()
        sys.exit()

    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                set_page("quit_confirm")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Only process clicks if enough time has passed since last page change
                if time.time() - last_page_change_time > click_delay:  
                    for _, rect, key in buttons:
                        if rect.collidepoint(event.pos):
                            if key != "back" and not is_mute:
                                click_sound.play()
                            handle_action(key)
                            last_page_change_time = time.time()  # Update the time after handling the click

        if current_page == "main_menu":

            screen.blit(logo, ((SCREEN_WIDTH // 2 - 473), 30))
            screen.blit(logo_text, logo_pos)
            screen.blit(site_text, site_pos)
            screen.blit(credit_text, credit_pos)
            screen.blit(ver_text, ver_pos)
        # Render the main menu buttons
            for rendered, rect, key in buttons:
                if rect.collidepoint(mouse_pos):

                    if key == "start":
                        menu_text = font.render("Play the game.", True, (255, 255, 0))
                        screen.blit(menu_text, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT - 50))
                    elif key == "achievements":
                        achieve_text = font.render("Select your character! Under Development.", True, (255, 255, 0))
                        screen.blit(achieve_text, (SCREEN_WIDTH // 2 - 260, SCREEN_HEIGHT - 50))
                    elif key == "settings": 
                        settings_text = font.render("Turn on the audio or turn it off, depending on current mode.", True, (255, 255, 0))
                        screen.blit(settings_text, (SCREEN_WIDTH // 2 - 400, SCREEN_HEIGHT - 50))
                    elif key == "quit":
                        quit_text = font.render("Exit the game.", True, (255, 255, 0))
                        screen.blit(quit_text, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT - 50))
                    elif key == "language":
                        lang_text = font.render("Select your language.", True, (255, 255, 0))
                        screen.blit(lang_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT - 50))
                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((153, 51, 255, 0))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                screen.blit(rendered, rect)

        if current_page == "character_select":
            # Initalize locked sound effect
            locked_sound_played = False
            messages = load_language(lang_code).get('messages', {})  # Fetch localized messages
            #Check if characters are locked
            icerobo_unlock = progress.get("icerobo_unlocked", False)
            evilrobo_unlock = progress.get("evilrobo_unlocked", False)
            lavarobo_unlock = progress.get("lavarobo_unlocked", False)
            greenrobo_unlock = progress.get("greenrobo_unlocked", False)
            save_progress(progress)
            # Draw images
            screen.blit(robot_img, robot_rect)
            if evilrobo_unlock:
                screen.blit(evilrobot_img, evilrobot_rect)
            else:
                screen.blit(locked_img, evilrobot_rect)
            if icerobo_unlock:
                screen.blit(icerobot_img, icerobot_rect)
            else:
                screen.blit(locked_img, icerobot_rect)
            if lavarobo_unlock:
                screen.blit(lavarobot_img, lavarobot_rect)
            else:
                screen.blit(locked_img, lavarobot_rect)
            if greenrobo_unlock:
                screen.blit(greenrobot_img, greenrobot_rect)
            else:
                screen.blit(locked_img, greenrobot_rect)
            # Draw a highlight border around the selected character
            if selected_character == "robot":
                pygame.draw.rect(screen, (63, 72, 204), robot_rect.inflate(5, 5), 5)
            elif selected_character == "evilrobot":
                pygame.draw.rect(screen, (128, 0, 128), evilrobot_rect.inflate(5, 5), 5)
            elif selected_character == "icerobot":
                pygame.draw.rect(screen, (51, 254, 255), icerobot_rect.inflate(5, 5), 5)
            elif selected_character == "lavarobot":
                pygame.draw.rect(screen, (136, 0, 21), lavarobot_rect.inflate(5, 5), 5)
            elif selected_character == "greenrobot":
                pygame.draw.rect(screen, (25, 195, 21), greenrobot_rect.inflate(5, 5), 5)

            # Handle events from the main loop, not a new event loop!
            if pygame.mouse.get_pressed()[0]:  # Left mouse button is pressed
                mouse_pos = pygame.mouse.get_pos()
                if robot_rect.collidepoint(mouse_pos):
                    selected_character = "robot"
                    progress["selected_character"] = selected_character
                    save_progress(progress)
                    if not is_mute:
                        click_sound.play()
                    set_page("main_menu")
                
                elif evilrobot_rect.collidepoint(mouse_pos):
                    if evilrobo_unlock:
                        selected_character = "evilrobot"
                        progress["selected_character"] = selected_character
                        save_progress(progress)
                        if not is_mute:
                            click_sound.play()
                        set_page("main_menu")
                    else:
                        if not is_mute and not locked_sound_played:
                            death_sound.play()
                            locked_sound_played = True
                            # Initialize the time
                        if wait_time is None:
                            wait_time = pygame.time.get_ticks()                            
                        locked_text = messages.get("evillocked_message", "Encounter this robot in an alternative route to unlock him!")
                
                elif icerobot_rect.collidepoint(mouse_pos):
                    if icerobo_unlock:
                        selected_character = "icerobot"
                        progress["selected_character"] = selected_character
                        save_progress(progress)
                        if not is_mute:
                            click_sound.play()
                        set_page("main_menu")
                    else:
                        if not is_mute and not locked_sound_played:
                            death_sound.play()
                            locked_sound_played = True
                        # Initialize the time
                        if wait_time is None:
                            wait_time = pygame.time.get_ticks()
                        locked_text = messages.get("icelocked_message", "This robot is coming soon!")
                
                elif lavarobot_rect.collidepoint(mouse_pos):
                    if lavarobo_unlock:
                        selected_character = "lavarobot"
                        progress["selected_character"] = selected_character
                        save_progress(progress)
                        if not is_mute:
                            click_sound.play()
                        set_page("main_menu")
                    else:
                        if not is_mute and not locked_sound_played:
                            death_sound.play()
                            locked_sound_played = True
                            # Initialize the time                    
                        locked_text = messages.get("lavalocked_message", "This robot is coming soon!")
                        if wait_time is None:
                            wait_time = pygame.time.get_ticks()

                elif greenrobot_rect.collidepoint(mouse_pos):
                    if greenrobo_unlock:
                        selected_character = "greenrobot"
                        progress["selected_character"] = selected_character
                        save_progress(progress)
                        if not is_mute:
                            click_sound.play()
                        set_page("main_menu")
                    else:
                        if not is_mute and not locked_sound_played:
                            death_sound.play()
                            locked_sound_played = True
                            # Initialize the time
                        if wait_time is None:
                            wait_time = pygame.time.get_ticks()
                        locked_text = messages.get("greenlocked_message", "Get GOLD rank in all Green World Levels to unlock this robot!")

            if not pygame.mouse.get_pressed()[0]:
                locked_sound_played = False

            keys = pygame.key.get_pressed() 
            if keys[pygame.K_ESCAPE]:
                set_page("main_menu")
            if wait_time is not None:
                if pygame.time.get_ticks() - wait_time < 5000:
                    rendered_locked_text = font.render(locked_text, True, (255, 255, 0))
                    screen.blit(rendered_locked_text, ((SCREEN_WIDTH // 2 - rendered_locked_text.get_width() // 2), SCREEN_HEIGHT - 700))
                else:
                    wait_time = None
        if current_page == "quit_confirm":
            # Render the quit confirmation text
            screen.blit(quit_text, quit_text_rect)
            screen.blit(icerobot_img, (SCREEN_WIDTH // 2 - icerobot_img.get_width() // 2, SCREEN_HEIGHT // 2 - 200))

            # Render the "Yes" and "No" buttons
            for rendered, rect, key in buttons:
                if rect.collidepoint(mouse_pos):
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered
                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((153, 51, 255, 0))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                screen.blit(rendered, rect)

            # Allow returning to the main menu with ESC
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                set_page("main_menu")

        elif current_page == "lvl1_screen":
            # Render the Level 1 screen
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

        elif current_page == "lvl9_screen":
            create_lvl9_screen()

            for rendered, rect, key in buttons:
                pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
                screen.blit(rendered, rect)

        elif current_page == "lvl10_screen":
            create_lvl10_screen()

            for rendered, rect, key in buttons:
                pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
                screen.blit(rendered, rect)

        elif current_page == "lvl11_screen":
            create_lvl11_screen()

            for rendered, rect, key in buttons:
                pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
                screen.blit(rendered, rect)

        elif current_page == "lvl12_screen":
            create_lvl12_screen()

            for rendered, rect, key in buttons:
                pygame.draw.rect(screen, (50, 50, 100), rect.inflate(20, 10))
                screen.blit(rendered, rect)

        elif current_page == "levels":
            screen.blit(green_background, (0, 0))
            # Fetch the localized "Select a Level" text dynamically
            select_text = current_lang.get("level_display", "Select a Level")
            rendered_select_text = font.render(select_text, True, (255, 255, 255))
            select_text_rect = rendered_select_text.get_rect(center=(SCREEN_WIDTH // 2, 50))

            # Draw the "Select a Level" text
            screen.blit(rendered_select_text, select_text_rect)

            # Render buttons for levels
            for rendered, rect, key in buttons:
                if rect.collidepoint(mouse_pos):
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered
                # Show lvl1_time if hovering Level 1 button
                    
                    if key == "lvl1":
                        lvl1_time_text = font.render(f"Best Time: {progress['times']['lvl1']}s", True, (255, 255, 0))
                        # Adjust position as needed
                        screen.blit(lvl1_time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                        if progress['medals']['lvl1'] == "Gold":
                            lvl1_medal_text = font.render(f"Medal: {progress['medals']['lvl1']}", True, (255, 255, 0))
                            screen.blit(lvl1_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl1'] == "Silver":
                            lvl1_medal_text = font.render(f"Medal: {progress['medals']['lvl1']}", True, (160, 160, 160))
                            screen.blit(lvl1_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl1'] == "Bronze":
                            lvl1_medal_text = font.render(f"Medal: {progress['medals']['lvl1']}", True, (153, 76, 0))
                            screen.blit(lvl1_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        else:
                            lvl1_medal_text = font.render(f"Medal: {progress['medals']['lvl1']}", True, (255, 255, 255))
                            screen.blit(lvl1_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                    
                    elif key == "lvl2":
                        lvl2_time_text = font.render(f"Best Time: {progress['times']['lvl2']}s", True, (255, 255, 0))
                        # Adjust position as needed
                        screen.blit(lvl2_time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                        if progress['medals']['lvl2'] == "Gold":
                            lvl2_medal_text = font.render(f"Medal: {progress['medals']['lvl2']}", True, (255, 255, 0))
                            screen.blit(lvl2_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl2'] == "Silver":
                            lvl2_medal_text = font.render(f"Medal: {progress['medals']['lvl2']}", True, (160, 160, 160))
                            screen.blit(lvl2_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl2'] == "Bronze":
                            lvl2_medal_text = font.render(f"Medal: {progress['medals']['lvl2']}", True, (153, 76, 0))
                            screen.blit(lvl2_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        else:
                            lvl2_medal_text = font.render("Medal: None", True, (255, 255, 255))
                            screen.blit(lvl2_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                    
                    elif key == "lvl3":
                        lvl3_time_text = font.render(f"Best Time: {progress['times']['lvl3']}s", True, (255, 255, 0))
                        # Adjust position as needed
                        screen.blit(lvl3_time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                        if progress['medals']['lvl3'] == "Gold":
                            lvl3_medal_text = font.render(f"Medal: {progress['medals']['lvl3']}", True, (255, 255, 0))
                            screen.blit(lvl3_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl3'] == "Silver":
                            lvl3_medal_text = font.render(f"Medal: {progress['medals']['lvl3']}", True, (160, 160, 160))
                            screen.blit(lvl3_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl3'] == "Bronze":
                            lvl3_medal_text = font.render(f"Medal: {progress['medals']['lvl3']}", True, (153, 76, 0))
                            screen.blit(lvl3_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        else:
                            lvl3_medal_text = font.render("Medal: None", True, (255, 255, 255))
                            screen.blit(lvl3_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                    
                    elif key == "lvl4":
                        lvl4_time_text = font.render(f"Best Time: {progress['times']['lvl4']}s", True, (255, 255, 0))
                        # Adjust position as needed
                        screen.blit(lvl4_time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                        if progress['medals']['lvl4'] == "Gold":
                            lvl4_medal_text = font.render(f"Medal: {progress['medals']['lvl4']}", True, (255, 255, 0))
                            screen.blit(lvl4_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl4'] == "Silver":
                            lvl4_medal_text = font.render(f"Medal: {progress['medals']['lvl4']}", True, (160, 160, 160))
                            screen.blit(lvl4_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl4'] == "Bronze":
                            lvl4_medal_text = font.render(f"Medal: {progress['medals']['lvl4']}", True, (153, 76, 0))
                            screen.blit(lvl4_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        else:
                            lvl4_medal_text = font.render("Medal: None", True, (255, 255, 255))
                            screen.blit(lvl4_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))                    
                    
                    elif key == "lvl5":
                        lvl5_time_text = font.render(f"Best Time: {progress['times']['lvl5']}s", True, (255, 255, 0))
                        # Adjust position as needed
                        screen.blit(lvl5_time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                        if progress['medals']['lvl5'] == "Gold":
                            lvl5_medal_text = font.render(f"Medal: {progress['medals']['lvl5']}", True, (255, 255, 0))
                            screen.blit(lvl5_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl5'] == "Silver":
                            lvl5_medal_text = font.render(f"Medal: {progress['medals']['lvl5']}", True, (160, 160, 160))
                            screen.blit(lvl5_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl5'] == "Bronze":
                            lvl5_medal_text = font.render(f"Medal: {progress['medals']['lvl5']}", True, (153, 76, 0))
                            screen.blit(lvl5_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        else:
                            lvl5_medal_text = font.render("Medal: None", True, (255, 255, 255))
                            screen.blit(lvl5_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100)) 
                    
                    elif key == "lvl6":
                        lvl6_time_text = font.render(f"Best Time: {progress['times']['lvl6']}s", True, (255, 255, 0))
                        # Adjust position as needed
                        screen.blit(lvl6_time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                        if progress['medals']['lvl6'] == "Gold":
                            lvl6_medal_text = font.render(f"Medal: {progress['medals']['lvl6']}", True, (255, 255, 0))
                            screen.blit(lvl6_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl6'] == "Silver":
                            lvl6_medal_text = font.render(f"Medal: {progress['medals']['lvl6']}", True, (160, 160, 160))
                            screen.blit(lvl6_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl6'] == "Bronze":
                            lvl6_medal_text = font.render(f"Medal: {progress['medals']['lvl6']}", True, (153, 76, 0))
                            screen.blit(lvl6_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        else:
                            lvl6_medal_text = font.render("Medal: None", True, (255, 255, 255))
                            screen.blit(lvl6_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100)) 
                    
                    elif key == "lvl7":
                        lvl7_time_text = font.render(f"Best Time: {progress['times']['lvl7']}s", True, (255, 255, 0))
                        # Adjust position as needed
                        screen.blit(lvl7_time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                        if progress['medals']['lvl7'] == "Gold":
                            lvl7_medal_text = font.render(f"Medal: {progress['medals']['lvl7']}", True, (255, 255, 0))
                            screen.blit(lvl7_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl7'] == "Silver":
                            lvl7_medal_text = font.render(f"Medal: {progress['medals']['lvl7']}", True, (160, 160, 160))
                            screen.blit(lvl7_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl7'] == "Bronze":
                            lvl7_medal_text = font.render(f"Medal: {progress['medals']['lvl7']}", True, (153, 76, 0))
                            screen.blit(lvl7_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        else:
                            lvl7_medal_text = font.render("Medal: None", True, (255, 255, 255))
                            screen.blit(lvl7_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))

                    elif key == "lvl8":
                        lvl8_time_text = font.render(f"Best Time: {progress['times']['lvl8']}s", True, (255, 255, 0))
                        # Adjust position as needed
                        screen.blit(lvl8_time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                        if progress['medals']['lvl8'] == "Gold":
                            lvl8_medal_text = font.render(f"Medal: {progress['medals']['lvl8']}", True, (255, 255, 0))
                            screen.blit(lvl8_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl8'] == "Silver":
                            lvl8_medal_text = font.render(f"Medal: {progress['medals']['lvl8']}", True, (160, 160, 160))
                            screen.blit(lvl8_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl8'] == "Bronze":
                            lvl8_medal_text = font.render(f"Medal: {progress['medals']['lvl8']}", True, (153, 76, 0))
                            screen.blit(lvl8_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        else:
                            lvl8_medal_text = font.render("Medal: None", True, (255, 255, 255))
                            screen.blit(lvl8_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100)) 
                    elif key == "lvl9":
                        lvl9_time_text = font.render(f"Best Time: {progress['times']['lvl9']}s", True, (255, 255, 0))
                        # Adjust position as needed
                        screen.blit(lvl9_time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                        if progress['medals']['lvl9'] == "Gold":
                            lvl9_medal_text = font.render(f"Medal: {progress['medals']['lvl9']}", True, (255, 255, 0))
                            screen.blit(lvl9_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl9'] == "Silver":
                            lvl9_medal_text = font.render(f"Medal: {progress['medals']['lvl9']}", True, (160, 160, 160))
                            screen.blit(lvl9_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl9'] == "Bronze":
                            lvl9_medal_text = font.render(f"Medal: {progress['medals']['lvl9']}", True, (153, 76, 0))
                            screen.blit(lvl9_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        else:
                            lvl9_medal_text = font.render("Medal: None", True, (255, 255, 255))
                            screen.blit(lvl9_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100)) 
                    elif key == "lvl10":
                        lvl10_time_text = font.render(f"Best Time: {progress['times']['lvl10']}s", True, (255, 255, 0))
                        # Adjust position as needed
                        screen.blit(lvl10_time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                        if progress['medals']['lvl10'] == "Gold":
                            lvl10_medal_text = font.render(f"Medal: {progress['medals']['lvl10']}", True, (255, 255, 0))
                            screen.blit(lvl10_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl10'] == "Silver":
                            lvl10_medal_text = font.render(f"Medal: {progress['medals']['lvl10']}", True, (160, 160, 160))
                            screen.blit(lvl10_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl10'] == "Bronze":
                            lvl10_medal_text = font.render(f"Medal: {progress['medals']['lvl10']}", True, (153, 76, 0))
                            screen.blit(lvl10_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        else:
                            lvl10_medal_text = font.render("Medal: None", True, (255, 255, 255))
                            screen.blit(lvl10_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100)) 
                    elif key == "lvl11":
                        lvl11_time_text = font.render(f"Best Time: {progress['times']['lvl11']}s", True, (255, 255, 0))
                        screen.blit(lvl11_time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                        if progress['medals']['lvl11'] == "Gold":
                            lvl11_medal_text = font.render(f"Medal: {progress['medals']['lvl11']}", True, (255, 255, 0))
                            screen.blit(lvl11_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl11'] == "Silver":
                            lvl11_medal_text = font.render(f"Medal: {progress['medals']['lvl11']}", True, (160, 160, 160))
                            screen.blit(lvl11_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        elif progress['medals']['lvl11'] == "Bronze":
                            lvl11_medal_text = font.render(f"Medal: {progress['medals']['lvl11']}", True, (153, 76, 0))
                            screen.blit(lvl11_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100))
                        else:
                            lvl11_medal_text = font.render("Medal: None", True, (255, 255, 255))
                            screen.blit(lvl11_medal_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 100)) 
                    elif key == "lvl12":
                        lvl11_txt = font.render(f"Coming soon!", True, (255, 255, 0))
                        screen.blit(lvl11_txt, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))

                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((153, 51, 255, 0))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                screen.blit(rendered, rect)

        elif current_page == "ice_levels":
            screen.blit(ice_background, (0, 0))
            # Fetch the localized "Select a Level" text dynamically
            select_text = current_lang.get("level_display", "Select a Level")
            rendered_select_text = font.render(select_text, True, (0, 0, 0))
            select_text_rect = rendered_select_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            screen.blit(rendered_select_text, select_text_rect)

            for _ in range(2):
                px = random.randint(-200, SCREEN_WIDTH + 200)
                py = -300
                snow.append(Particle(px, py, color=(255, 255, 255), size=3, lifetime=1400))

            # Update and draw particles
            for particle in snow[:]:
                particle.update()
                particle.draw(screen)
                if particle.lifetime <= 0:
                    snow.remove(particle)

    # Render buttons for ice world levels
            for rendered, rect, key in buttons:
                if rect.collidepoint(mouse_pos):
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered
                    if key == "lvl12":
                        lvl12_txt = font.render(f"Coming soon!", True, (255, 255, 0))
                        screen.blit(lvl12_txt, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50))
                    else:
                        lvl_txt = font.render(f"I don't even know if I'll make this...", True, (255, 0, 0))
                        screen.blit(lvl_txt, (SCREEN_WIDTH // 2 - lvl_txt.get_width() // 2, SCREEN_HEIGHT - 50))
                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((153, 51, 255, 0))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                screen.blit(rendered, rect)
        

        else:
            # Render buttons for other pages
            for rendered, rect, key in buttons:
                if rect.collidepoint(mouse_pos):
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered
                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((153, 51, 255, 0))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                screen.blit(rendered, rect)

        # Handle delayed level load
        if pending_level and time.time() >= level_load_time:
            load_level(pending_level)
            pending_level = None

        if show_greenrobo_unlocked:
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = font.render("Green Robo Unlocked!", True, (51, 255, 51))
                screen.blit(unlocked_text, (SCREEN_WIDTH // 2 - unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False
        
        pygame.display.flip()

pygame.quit()