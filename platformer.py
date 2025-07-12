import pygame
import json
import os
import math
import sys
import time
import random
import webbrowser
import shutil

# For extracting data from the news section of the website!
from bs4 import BeautifulSoup
import urllib.request
import html2text
import re

# Path to sound folder
SOUND_FOLDER = os.path.join("audio")

# Initialize audio
pygame.mixer.init()

# Initialize pygame
pygame.init()

# Load and set window icon
icon = pygame.image.load("robots.ico")
pygame.display.set_icon(icon)

def change_ambience(new_file):
    pygame.mixer.music.load(new_file)
    pygame.mixer.music.set_volume(2)  # Adjust as needed
    pygame.mixer.music.play(-1)

# Save file name
SAVE_FILE = "save_data.json"

notif = False
er = False
pygame.mouse.set_visible(False)  # Hide the system cursor
# Default progress dictionary
default_progress = {
    "complete_levels": 0,
    "locked_levels": ["lvl2", "lvl3", "lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9", "lvl10", "lvl11", "lvl12", "lvl13", "lvl14", "lvl15"],
    "times": {f"lvl{i}": 0 for i in range(1, 16)},
    "medals": {f"lvl{i}": "None" for i in range(1, 16)},
    "score": {f"lvl{i}": 0 for i in range(1, 16)},
    "language": "en",
    "selected_character": "robot",
    "icerobo_scenes": 0,
    "is_mute": False,
    "evilrobo_unlocked": False,
    "icerobo_unlocked": False,
    "lavarobo_unlocked": False,
    "greenrobo_unlocked": False,
    "cakebo_unlocked": False,
}

notification_time = None

def load_progress():
    global notification_time, notification_text
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not data:  # Handle empty file
                    raise ValueError("Empty save file")
        except Exception as e:
            print(f"Main save corrupted: {e}")
            # Try to load from backup
            if os.path.exists(SAVE_FILE + ".bak"):
                print("Loading from backup...")
                try:
                    with open(SAVE_FILE + ".bak", "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        with open(SAVE_FILE, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)
                        print("Backup restored to main save file.")

                except Exception as e:
                    print(f"Backup also corrupted: {e}")
                    data = default_progress.copy()
            else:
                print("No backup found. Using default progress.")
                data = default_progress.copy()
    else:
        print("Save file not found. Using default progress.")
        data = default_progress.copy()

    # Merge missing keys
    for key, value in default_progress.items():
        if key not in data:
            data[key] = value

    for key in ["times", "medals", "score"]:
        if key in default_progress and key in data:
            for subkey, subval in default_progress[key].items():
                if subkey not in data[key]:
                    data[key][subkey] = subval

    if "locked_levels" in default_progress and "locked_levels" in data:
        for lvl in default_progress["locked_levels"]:
            if lvl not in data["locked_levels"]:
                data["locked_levels"].append(lvl)

    return data

# Load the fonts (ensure the font file path is correct)
font_path_ch = 'fonts/NotoSansSC-SemiBold.ttf'
font_path_jp = 'fonts/NotoSansJP-SemiBold.ttf'
font_path_kr = 'fonts/NotoSansKR-SemiBold.ttf'
font_path = 'fonts/NotoSansDisplay-SemiBold.ttf'
font_ch = pygame.font.Font(font_path_ch, 25)
font_jp = pygame.font.Font(font_path_jp, 25)
font_kr = pygame.font.Font(font_path_kr, 25)
font_def = pygame.font.Font(font_path, 25)
font_text = pygame.font.Font(font_path, 55)

# Initializing screen resolution
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Platformer 02!")
MIN_WIDTH, MIN_HEIGHT = 1300, 800

# Save progress to file
def save_progress(data):
    global notification_text, notification_time, error_code, notif, er
    if not data or "complete_levels" not in data:
        hit_sound.play()
        notification_text = font_def.render("Refusing to save empty or invalid progress!", True, (255, 0, 0))
        if notification_time is None:
            notif = True
            notification_time = time.time()
        return
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        shutil.copy(SAVE_FILE, SAVE_FILE + ".bak")  # ✅ Only backup after a good save
    except PermissionError:
        hit_sound.play()
        notification_text = font_def.render("Error: Unable to save progress.", True, (255, 0, 0))
        if notification_time is None:
            notif = True
            notification_time = time.time()
    except Exception as e:
        er = True
        error_code = font_def.render(f"Unexpected error: {e}", True, (255, 0, 0))
    pygame.display.flip()

# Load progress at start
progress_loaded = False
language_loaded = False
sounds_loaded = False
images_loaded = False

background_img = pygame.image.load("bgs/Background.png").convert()
background = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

def draw_loading_bar(stage_name, percent):
    screen.blit(background, (0, 0))
    text = font_def.render(f"{stage_name}...", True, (255, 255, 255))
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
    screen.blit(text, text_rect)
    pygame.draw.rect(screen, (0, 0, 255), (0, SCREEN_HEIGHT - 10, (SCREEN_WIDTH / 100)*percent, 10))
    pygame.display.flip()

if not sounds_loaded:
    # Load sounds using the path
    draw_loading_bar("Loading sounds...", 17)
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
    token_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "token.wav"))
    star1 = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/1star.wav"))
    star2 = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/2star.wav"))
    star3 = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/3star.wav"))
    hscore = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/hs.wav"))
    star1.set_volume(4.0)
    star2.set_volume(4.0)
    star3.set_volume(4.0)
    sounds_loaded = True
    # Ambient themes
    pygame.mixer.music.load("audio/amb/ambience.wav")
    pygame.display.flip()

if not images_loaded:
    draw_loading_bar("Loading images...", 31)
    cursor_img = pygame.image.load("oimgs/cursor/cursor.png").convert_alpha()

    # Load logo images
    logo = pygame.image.load("oimgs/logos/logo.png").convert_alpha()
    studio_logo = pygame.image.load("oimgs/logos/studiologodef.png").convert_alpha()
    studio_logo = pygame.transform.scale(studio_logo, (390, 150))
    studio_logo_rect = studio_logo.get_rect(topleft=(20, SCREEN_HEIGHT - 170))
    studio_glow = pygame.image.load("oimgs/logos/studiologoglow.png").convert_alpha()
    studio_glow = pygame.transform.scale(studio_glow, (420, 170))
    studio_glow_rect = studio_glow.get_rect(topleft=(20, SCREEN_HEIGHT - 190))

    # Load and scale backgrounds
    plain_background_img = pygame.image.load("bgs/PlainBackground.png").convert()
    plain_background = pygame.transform.scale(plain_background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    ice_background_img = pygame.image.load("bgs/IceBackground.png").convert()
    ice_background = pygame.transform.scale(ice_background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    green_background_img = pygame.image.load("bgs/GreenBackground.png").convert()
    green_background = pygame.transform.scale(green_background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    trans = pygame.image.load("bgs/trans.png").convert()
    trans = pygame.transform.scale(trans, ((SCREEN_WIDTH), (SCREEN_HEIGHT)))
    end = pygame.image.load("bgs/EndScreen.png").convert_alpha()
    end = pygame.transform.scale(end, ((SCREEN_WIDTH), (SCREEN_HEIGHT)))

    # Load and initalize Images!
    nact_cp = pygame.image.load("oimgs/checkpoints/yellow_flag.png").convert_alpha()
    act_cp = pygame.image.load("oimgs/checkpoints/green_flag.png").convert_alpha()


if not progress_loaded and sounds_loaded:
    draw_loading_bar("Loading progress...", 91)
    progress = load_progress()
    complete_levels = progress.get("complete_levels", 0)
    progress_loaded = True
    pygame.display.flip()

if not language_loaded and progress_loaded:
# Get just the language code, default to English
    draw_loading_bar("Loading configured settings...", 100)
    lang_code = progress.get("language", "en")
    progress["language"] = lang_code
    is_mute = progress.get("is_mute", default_progress["is_mute"])  # Global variable to track mute state
    language_loaded = True
    pygame.display.flip()

pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)  # Loop forever

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
    {'level': 12,'gold': 45, 'silver': 60, 'bronze': 85},
    {'level': 13,'gold': 30, 'silver': 50, 'bronze': 70},
]

# Level score thresholds
score_thresholds = [
    {'level': 1,  '1': 10000, '2': 80000, '3': 85000},
    {'level': 2,  '1': 10000, '2': 70000, '3': 85000},
    {'level': 3,  '1': 10000, '2': 70000, '3': 85000},
    {'level': 4,  '1': 10000, '2': 70000, '3': 85000},
    {'level': 5,  '1': 10000, '2': 65000, '3': 80000},
    {'level': 6,  '1': 10000, '2': 65000, '3': 86000},
    {'level': 7,  '1': 10000, '2': 74000, '3': 86000},
    {'level': 8,  '1': 10000, '2': 76000, '3': 84500},
    {'level': 9,  '1': 10000, '2': 66000, '3': 82000},
    {'level': 10, '1': 10000, '2': 75000, '3': 85000},
    {'level': 11, '1': 10000, '2': 73000, '3': 86000},
    {'level': 12, '1': 10000, '2': 73000, '3': 84000},
    {'level': 13, '1': 10000, '2': 76000, '3': 80000},
]
# Function to get medal based on time
def get_medal(level, time_taken):
    thresholds = next((t for t in level_thresholds if t['level'] == level), None)
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
    thresholds = next((t for t in score_thresholds if t['level'] == level), None)
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
    

if lang_code == "zh_cn":
    font = pygame.font.Font(font_path_ch, 25)
if lang_code == "jp":
    font = pygame.font.Font(font_path_jp, 25)
if lang_code == "kr":
    font = pygame.font.Font(font_path_kr, 25)
else:
    font = pygame.font.Font(font_path, 25)

def render_text(text, color=(255, 255, 255)):
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return font_ch.render(text, True, color)
    if any('\uAC00' <= c <= '\uD7A3' for c in text):
        return font_kr.render(text, True, color)
    else:
        return font_def.render(text, True, color)
    
class TransitionManager:
    def __init__(self, screen, image, speed=40):
        self.screen = screen
        self.image = image
        self.speed = speed
        self.active = False
        self.direction = 1  # 1 for slide-in, -2 for slide-out
        self.x = -screen.get_width()
        self.target_page = None

    def start(self, target_page):
        self.active = True
        self.direction = 1
        self.x = -self.screen.get_width()
        self.target_page = target_page

    def update(self):
        if not self.active:
            return

        self.x += self.speed * self.direction

        if self.direction == 1 and self.x >= 0:
            self.x = 0
            # Switch page when screen is fully covered
            set_page(self.target_page)
            self.direction = -2  # Start sliding out

        elif self.direction == -2 and self.x >= self.screen.get_width():
            self.active = False  # Done with transition

        # Draw the image
        self.screen.blit(self.image, (self.x, 0))

transition = TransitionManager(screen, trans)

site_text = font_def.render("Sound effects from: pixabay.com", True, (255, 255, 255))
site_pos = (SCREEN_WIDTH - 398, SCREEN_HEIGHT - 98)
logo_text = font_def.render("Logo and Background made with: canva.com", True, (255, 255, 255))
logo_pos = (SCREEN_WIDTH - 537, SCREEN_HEIGHT - 68)
credit_text = font_def.render("Made by: Omer Arfan", True, (255, 255, 255))
credit_pos = (SCREEN_WIDTH - 264, SCREEN_HEIGHT - 128)
ver_text = font_def.render("Version 1.2.65", True, (255, 255, 255))
ver_pos = (SCREEN_WIDTH - 177, SCREEN_HEIGHT - 158)

# Load language function and rendering part remain the same
def load_language(lang_code):
    try:
        with open(f"lang/{lang_code}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[WARN] Language '{lang_code}' not found. Falling back to English.")
        progress["language"] = "en"
        save_progress(progress)
        with open("lang/en.json", "r", encoding="utf-8") as f:
            return json.load(f)


current_lang = load_language(lang_code)
# Page states
current_page = 'main_menu'
buttons = []

# Display Green Robo Unlocked for a limited time
greenrobo_unlocked_message_time = 0
show_greenrobo_unlocked = False

def create_main_menu_buttons():

    global current_lang, buttons
    current_lang = load_language(lang_code)['main_menu']
    buttons.clear()
    button_texts = ["start", "character_select", "settings", "news", "language", "quit"]

    # Center buttons vertically and horizontally
    button_spacing = 60
    start_y = (SCREEN_HEIGHT // 2) - (len(button_texts) * button_spacing // 2) + 150

    for i, key in enumerate(button_texts):
        text = current_lang[key]
        rendered = font.render(text, True, (255, 255, 255))
        rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * button_spacing)) 
        buttons.append((rendered, rect, key, False))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            set_page("quit_confirm")


def create_language_buttons():
    global current_lang, buttons, heading_text
    current_lang = load_language(lang_code).get('language_select', {})
    buttons.clear()
    start = load_language(lang_code).get('main_menu', {})

    language_options = [
        ("English", "en"),
        ("Français", "fr"),
        ("Español", "es"),
        ("Deutsch", "de"),
        ("Italiano", "it"),
        ("Português(Brasil)", "pt_br"),
        ("Türkçe", "tr"),
        ("Bahasa Indonesia", "id"),
        ("Русский", "ru"),
        ("简体中文", "zh_cn"),
        ("日本語", "jp"),
        ("한국인", "kr"),
    ]
    buttons_per_row = 4
    spacing_x = 200
    spacing_y = 70

    # Calculate starting positions to center the grid
    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (SCREEN_WIDTH - grid_width) // 2
    start_y = (SCREEN_HEIGHT // 2) - (len(language_options) // buttons_per_row * spacing_y // 2)

    heading = start.get("language", "Change Language")
    heading_text = font.render(heading, True, (255 , 255, 255))

    for i, (display_name, code) in enumerate(language_options):
        text = display_name
        rendered = render_text(text, (255, 255, 255))

        col = i % buttons_per_row
        row = i // buttons_per_row

        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        rect = rendered.get_rect(center=(x, y))
        buttons.append((rendered, rect, code, False))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            set_page("quit_confirm")

    # Add a "Back" button at the bottom center
    back_text = current_lang.get("back", "Back")
    rendered_back = font.render(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(SCREEN_WIDTH // 2, y + spacing_y + 40))
    buttons.append((rendered_back, back_rect, "back", False))

greendisk_img = pygame.image.load("oimgs/disks/greendisk.png").convert_alpha()
greendisk_img = pygame.transform.scale(greendisk_img, (100, 100))  # Resize as needed
icedisk_img = pygame.image.load("oimgs/disks/icedisk.png").convert_alpha()
icedisk_img = pygame.transform.scale(icedisk_img, (100, 100))  # Resize as needed
lockeddisk_img = pygame.image.load("oimgs/disks/lockeddisk.png").convert_alpha()
lockeddisk_img = pygame.transform.scale(lockeddisk_img, (100, 100))  # Resize as needed
token_img = pygame.image.load("oimgs/ig/roboken.png").convert_alpha()
token_img = pygame.transform.scale(token_img, (80, 80))
star_img = pygame.image.load("oimgs/ig/star.png").convert_alpha()
star_img = pygame.transform.scale(star_img, (150, 140))
s_star_img = pygame.transform.scale(star_img, (20, 17))

def green_world_buttons():
    global current_lang, buttons
    buttons.clear()

    # Store the rendered text and its position for later drawing
    global text_rect, level_key

    level_options = ["lvl1", "lvl2", "lvl3", "lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9", "lvl10", "lvl11"]
    level_no = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]
    buttons_per_row = 4
    spacing_x = 160
    spacing_y = 120

    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (SCREEN_WIDTH - grid_width) // 2
    start_y = ((SCREEN_HEIGHT // 2) - ((len(level_options) // buttons_per_row) * spacing_y // 2))

    for i, level in enumerate(level_options):
        col = i % buttons_per_row
        row = i // buttons_per_row
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        is_locked = level in progress["locked_levels"]
        text_surface = font_text.render(level_no[i], True, (255, 255, 255))
        disk_rect = greendisk_img.get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = font.render(back_text, True, (255, 255, 255))

    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.Rect(0, 0, 100, 100)
    back_rect.center = (90, SCREEN_HEIGHT // 2)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))

    next_text = current_lang.get("next", "next")
    rendered_next = font.render(next_text, True, (255, 255, 255))

    next_rect = pygame.Rect(0, 0, 100, 100)
    next_rect.center = (SCREEN_WIDTH - 90, SCREEN_HEIGHT // 2)

    text_rect = rendered_next.get_rect(center=next_rect.center)
    screen.blit(rendered_next, text_rect)

    buttons.append((rendered_next, next_rect, "next", False))

def ice_world_buttons():
    global current_lang, buttons
    buttons.clear()

    # Store the rendered text and its position for later drawing
    global text_rect, level_key

    level_options = ["lvl12", "lvl13", "lvl14", "lvl15"]
    level_no = ["12", "13", "14", "15"]
    buttons_per_row = 4
    spacing_x = 160
    spacing_y = 120

    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (SCREEN_WIDTH - grid_width) // 2
    start_y = ((SCREEN_HEIGHT // 2) - ((len(level_options) // buttons_per_row) * spacing_y // 2))

    for i, level in enumerate(level_options):
        col = i % buttons_per_row
        row = i // buttons_per_row
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        is_locked = level in progress["locked_levels"]
        if not is_locked:
            color = (0, 0, 0)
        else:
            color = (255, 255, 255)
        text_surface = font_text.render(level_no[i], True, color)
        disk_rect = icedisk_img.get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

        # --- Draw stars for completed levels ---
        stars = get_stars(int(level_no[i]), progress["score"].get(level, 0))
        for s in range(stars):
            star_x = x - 30 + s * 30  # Adjust as needed for spacing
            star_y = y + 50            # Adjust as needed for vertical position
            screen.blit(s_star_img, (star_x, star_y))

    # Back button at bottom center

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = font.render(back_text, True, (255, 255, 255))


    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.Rect(0, 0, 100, 100)
    back_rect.center = (90, SCREEN_HEIGHT // 2)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))

def map():
    global buttons, mappy, map_x
    buttons.clear()

    level_options = ["lvl1", "lvl2", "lvl3", "lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9", "lvl10", "lvl11", "lvl12", "lvl13", "lvl14", "lvl15"]

    mappy = pygame.image.load("bgs/map.png").convert_alpha()
    target_height = SCREEN_HEIGHT

    map_width, map_height = mappy.get_width(), mappy.get_height()
    scale_factor = target_height / map_height
    scaled_width = int(map_width * scale_factor)
    scaled_height = target_height

    # Use scale for sharpness if needed
    mappy = pygame.transform.scale(mappy, (scaled_width, scaled_height))

    # Optional: Loop the map (if you want it to repeat)
    if map_x <= -scaled_width:
        map_x = SCREEN_WIDTH

    pygame.display.flip()

#def load_level(level_id):
#    global current_page, buttons
#
   # Show "Loading..." text
#    screen.fill((30, 30, 30))
#    messages = load_language(lang_code).get('messages', {})  # Reload messages with the current language
#    loading_text = messages.get("loading", "Loading...")
#    rendered_loading = font.render(loading_text, True, (255, 255, 255))
#    loading_rect = rendered_loading.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))  # Center dynamically
#    screen.blit(rendered_loading, loading_rect)
#    pygame.display.flip()

 #   # Short delay to let the user see the loading screen
  #  pygame.time.delay(800)  # 800 milliseconds

    # Now switch the page
   # buttons.clear()

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

# Load character images
robot_img = pygame.image.load("char/robot/robot.png").convert_alpha()
evilrobot_img = pygame.image.load("char/evilrobot/evilrobot.png").convert_alpha()
icerobot_img = pygame.image.load("char/icerobot/icerobot.png").convert_alpha()
lavarobot_img = pygame.image.load("char/lavarobot/lavarobot.png").convert_alpha()
greenrobot_img = pygame.image.load("char/greenrobot/greenrobot.png").convert_alpha()
cakebot_img = pygame.image.load("char/cakebot/cakebot.png").convert_alpha()
locked_img = pygame.image.load("char/lockedrobot.png").convert_alpha()

#Initialize default character
selected_character = progress.get("selected_character", default_progress["selected_character"])

# Get rects and position them
robot_rect = robot_img.get_rect(topleft=(SCREEN_WIDTH // 2 - 425, SCREEN_HEIGHT // 2 - 50))
#Evil Robot
evilrobot_rect = evilrobot_img.get_rect(topleft=(SCREEN_WIDTH // 2 - 275, SCREEN_HEIGHT // 2 - 50))
#Ice and lava robot
icerobot_rect = icerobot_img.get_rect(topleft=(SCREEN_WIDTH // 2 - 125, SCREEN_HEIGHT // 2 - 50))
lavarobot_rect = lavarobot_img.get_rect(topleft=(SCREEN_WIDTH // 2 + 25, SCREEN_HEIGHT // 2 - 50))
greenrobot_rect = greenrobot_img.get_rect(topleft=(SCREEN_WIDTH // 2 + 175, SCREEN_HEIGHT // 2 - 50))
cakebot_rect = cakebot_img.get_rect(topleft=(SCREEN_WIDTH // 2 + 325, SCREEN_HEIGHT // 2 - 50))
def character_select():
    global selected_character, set_page, current_page
    
    # Clear screen
    buttons.clear()
    current_lang = load_language(lang_code)['language_select']
    button_texts = ["back"]

    for i, key in enumerate(button_texts):
        text = current_lang[key]
        rendered = font.render(text, True, (255, 255, 255))
        rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)) 
        buttons.append((rendered, rect, key, False))
    
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
            elif cakebot_rect.collidepoint(mouse_pos):
                selected_character = "cakebot"
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
    sys.exit()

def change_language(lang):
    global lang_code, last_page_change_time, current_lang, font, font_path_ch, font_path
    lang_code = lang
    last_page_change_time = time.time()  # Track the time when the language changes
    current_lang = load_language(lang_code)  # Reload the language data
    progress["language"] = lang_code
    save_progress(progress)
    if lang_code == "zh_cn":
        font = pygame.font.Font(font_path_ch, 25)
    elif lang_code == "jp":
        font = pygame.font.Font(font_path_jp, 25)
    elif lang_code == "kr":
        font = pygame.font.Font(font_path_kr, 25)
    else:
        font = pygame.font.Font(font_path, 25)

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
    elif page == "map":
        map()
    elif page == 'character_select':
        character_select()
    elif page == 'language_select':
        current_lang = load_language(lang_code).get('language_select', {})
        create_language_buttons()
    elif page == 'levels':
        current_lang = load_language(lang_code).get('levels', {})
        green_world_buttons()
        change_ambience("audio/amb/greenambience.wav")
    elif page == "news":
        current_lang = load_language(lang_code).get('levels', {})
        fetch_news_html_and_convert()
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

def try_select_robo(unlock_flag, char_key, rect, locked_msg_key, fallback_msg):
    if rect.collidepoint(pygame.mouse.get_pos()):
        global wait_time, selected_character, locked_char_sound_time, locked_char_sound_played

        if unlock_flag:
            selected_character = char_key
            progress["selected_character"] = selected_character
            save_progress(progress)
            if not is_mute:
                click_sound.play()
            set_page("main_menu")
        else:
            handle_action("locked")
            if not locked_char_sound_played or time.time() - locked_char_sound_time > 1.5: # type: ignore
                if not is_mute:
                    death_sound.play()
                locked_char_sound_time = time.time()
                locked_char_sound_played = True
            if wait_time is None:
                wait_time = pygame.time.get_ticks()
            global locked_text
            locked_text = messages.get(locked_msg_key, fallback_msg)

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
    buttons.append((rendered_yes, yes_rect, "yes", False))

    # Create "No" button
    no_text = messages.get("no", "No")
    rendered_no = font.render(no_text, True, (255, 255, 255))
    no_rect = rendered_no.get_rect(center=(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 + 50))
    buttons.append((rendered_no, no_rect, "no", False))

    pygame.display.flip()  # Update the display to show the quit confirmation screen


def fetch_news_html_and_convert():
    try:
        url = "https://omerarfan.github.io/lilrobowebsite/gamestuff.html"
        with urllib.request.urlopen(url, timeout=5) as response:
            html = response.read().decode()

        soup = BeautifulSoup(html, "html.parser")

        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = False
        text_maker.ignore_images = True
        text_maker.body_width = 0

        text = text_maker.handle(html).splitlines()

        # Clean markdown links
        clean_text = []
        for line in text:
            line = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
            line = re.sub(r'\[\]\([^)]+\)', '', line)
            if line.strip():
                clean_text.append(line.strip())

        # Get image URLs
        image_urls = []
        image_paths = []
        os.makedirs("oimgs/news", exist_ok=True)

        for img in soup.find_all("img"):
            src = img.get("src") # type: ignore
            if src:
                full_url = "https://omerarfan.github.io/lilrobowebsite/" + src.lstrip("/")  # type: ignore
                image_urls.append(full_url)

                filename = os.path.basename(full_url)
                local_path = os.path.join("oimgs/news", filename)
                image_paths.append(local_path)

                if not os.path.exists(local_path):
                    try:
                        urllib.request.urlretrieve(full_url, local_path)
                        print("✅ Downloaded:", local_path)
                    except Exception as e:
                        print("❌ Download failed:", full_url, e)
                else:
                    print("✅ Already exists:", local_path)

        print("→ FOUND IMAGES:", image_urls)
        return clean_text, image_paths

    except Exception as e:
        return [f"Error loading news: {e}"], []

def low_detail():
    global LDM
    if LDM:
        LDM = False
    else:
        LDM = True

def score_calc():
    global current_time, medal, deathcount, score, collected_tokens

    # WIP!
    #if collected_tokens is not None:
     #   token_score =  len(collected_tokens)*150
    #else:
    token_score = 0
    time_score = int(current_time * 160)
    if medal == "Gold":
        medal_score = 5000
    elif medal == "Silver":
        medal_score = 10000
    elif medal == "Bronze":
        medal_score = 15000
    else:
        medal_score = 25000
    death_score = deathcount * 300
    score = max(500, 100000 - medal_score - death_score - time_score + token_score)
    print(score, medal_score, death_score, time_score)

class StarParticles:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = random.randint(2, 4)
        self.color = (255, 255, 100)
        self.life = 80  # frames
        # Wider horizontal spread, initial upward velocity
        self.vel = [random.uniform(-3, 3), random.uniform(-6, -3)]
        self.gravity = 0.35  # Gravity strength

    def update(self):
        self.vel[1] += self.gravity  # Apply gravity
        self.x += self.vel[0]
        self.y += self.vel[1]
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            
stareffects = []

def level_complete():
    global score, display_score, new_hs, collected_tokens, hs, stareffects, stars
    messages = load_language(lang_code).get('messages', {})
    display_score = 0
    star1_p, star2_p, star3_p = False, False, False
    star_time = time.time()
    running = True
    notified = False
    clock = pygame.time.Clock()
    star_channel = pygame.mixer.Channel(2)
    lvl_comp = messages.get("lvl_comp", "Level Complete!")
    rendered_lvl_comp = font.render(lvl_comp, True, (255, 255, 255))
    while running:
        screen.blit(end, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.blit(rendered_lvl_comp, (SCREEN_WIDTH // 2 - rendered_lvl_comp.get_width() // 2, 150))

        # Animate score
        
        if display_score < score:
          if not is_mute:
            hover_sound.play()
          display_score += max(5, (score // 71))
        if stars >= 1 and (time.time() - star_time > 0.5):
                screen.blit(star_img, (SCREEN_WIDTH // 2 - 231, 230))
                if not star1_p:
                 for _ in range(40):  # Add some particles at star position
                    stareffects.append(StarParticles(SCREEN_WIDTH // 2 - 230 + star_img.get_width() // 2, 230 + star_img.get_height() // 2)) 
                 star_channel.play(star1)
                 star1_p = True
        if stars >= 2 and (time.time() - star_time > 1.5):
                screen.blit(star_img, (SCREEN_WIDTH // 2 - 76, 230))
                if not star2_p and star1_p: 
                    for _ in range(40):  # Add some particles at star position
                     stareffects.append(StarParticles(SCREEN_WIDTH // 2 - 75 + star_img.get_width() // 2, 230 + star_img.get_height() // 2))  
                    star_channel.play(star2)
                    star2_p = True
        if stars >= 3 and (time.time() - star_time  >  2.5):
                screen.blit(star_img, (SCREEN_WIDTH // 2 + 79, 230)) 
                if  not star3_p and star2_p: 
                    for _ in range(40):  # Add some particles at star position
                      stareffects.append(StarParticles(SCREEN_WIDTH // 2 + 80 + star_img.get_width() // 2, 230 + star_img.get_height() // 2)) 
                    star_channel.play(star3)
                    star3_p = True

        for particle in stareffects[:]:
         particle.update()
         particle.draw(screen)
         if particle.life <= 0:
            stareffects.remove(particle)
        
        if display_score > score:
                display_score = score

        score_text = font_text.render(str(display_score), True, (255, 255, 255))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 - score_text.get_height() // 2))

        
        if time.time() - star_time > 4:  # Show for 3 seconds
                if new_hs:
                    new_hs_text = font.render("New High Score!", True, (255, 215, 0))
                    screen.blit(new_hs_text, (SCREEN_WIDTH // 2 - new_hs_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))
                    if not is_mute and not notified:
                        hscore.play()
                        notified = True
                else:
                    high_text = messages.get("hs_m", "Highscore: {hs}").format(hs=hs)
                    hs_text = font.render(high_text, True, (158, 158, 158))
                    screen.blit(hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))
        if time.time() - star_time > 6:
                running = False

        pygame.display.update()
        clock.tick(60)

def char_assets():
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
 # Load player image
    if selected_character == "robot": 
        player_img = pygame.image.load(f"char/robot/robot.png").convert_alpha()
        moving_img_l = pygame.image.load(f"char/robot/smilerobotL.png") # Resize to fit the game
        moving_img = pygame.image.load(f"char/robot/smilerobot.png") # Resize to fit the game
    elif selected_character == "evilrobot":
        player_img = pygame.image.load(f"char/evilrobot/evilrobot.png").convert_alpha()
        moving_img_l = pygame.image.load(f"char/evilrobot/movevilrobotL.png") # Resize to fit the game
        moving_img = pygame.image.load(f"char/evilrobot/movevilrobot.png") # Resize to fit the game
    elif selected_character == "greenrobot":
        player_img = pygame.image.load(f"char/greenrobot/greenrobot.png").convert_alpha()
        moving_img_l = pygame.image.load(f"char/greenrobot/movegreenrobotL.png") # Resize to fit the game
        moving_img = pygame.image.load(f"char/greenrobot/movegreenrobot.png") # Resize to fit the game
    elif selected_character == "icerobot":
        player_img = pygame.image.load(f"char/icerobot/icerobot.png").convert_alpha()
        moving_img_l = pygame.image.load(f"char/icerobot/moveicerobotL.png") # Resize to fit the game
        moving_img = pygame.image.load(f"char/icerobot/moveicerobot.png") # Resize to fit the game
    elif selected_character == "cakebot":
        player_img = pygame.image.load(f"char/cakebot/cakebot.png").convert_alpha()
        moving_img_l = pygame.image.load(f"char/cakebot/movecakebotL.png") # Resize to fit the game
        moving_img = pygame.image.load(f"char/cakebot/movecakebot.png") # Resize to fit the game
    img_width, img_height = player_img.get_size()

def point_in_triangle(px, py, a, b, c):
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        b1 = sign((px, py), a, b) < 0.0
        b2 = sign((px, py), b, c) < 0.0
        b3 = sign((px, py), c, a) < 0.0
        return b1 == b2 == b3
    
def draw_spikes(spikes):
            global x, y, spawn_x, spawn_y, camera_x, camera_y, player_x, player_y, img_width, img_height, deathcount, in_game, velocity_y, wait_time,death_text
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

def block_func(blocks):
    global x, y, camera_x,spawn_x, spawn_y,  camera_y, player_x, player_y, img_width, img_height, deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground
    
    for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))
    
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

def create_lvl1_screen():
    global player_img, font, screen, complete_levels, is_mute, show_greenrobo_unlocked, is_transitioning, transition_time, current_time, medal, deathcount, score, collected_tokens
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    global x, y, camera_x, camera_y, player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text,spawn_x, spawn_y,  player_rect, on_ground
    char_assets()
    new_hs = False

    buttons.clear()
    screen.blit(green_background, (0, 0))
    in_game = load_language(lang_code).get('in_game', {})

    wait_time = None
    start_time = time.time()

    # Camera settings
    camera_x = 0  
    camera_y = 0
    player_x, player_y = 600, 200
    spawn_x, spawn_y = player_x, player_y
    running = True
    gravity = 1
    jump_strength = 20
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.05
    deathcount = 0
    was_moving = False

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

    token_pos = [
        pygame.Rect(800, 200, 80, 80),
        pygame.Rect(1050, 320, 80, 80),
        pygame.Rect(1720, 220, 80, 80),
        pygame.Rect(1930, 50, 80, 80),
        pygame.Rect(2440, 180, 80, 80),
    ]

    collected_tokens = set()

    # Render the texts
    warning_text = in_game.get("warning_message", "Watch out for spikes!")
    rendered_warning_text = font.render(warning_text, True, (255, 0, 0))  # Render the warning text

    up_text = in_game.get("up_message", "Press UP to Jump!")
    rendered_up_text = font.render(up_text, True, (0, 0, 0))  # Render the up text

    exit_text = in_game.get("exit_message", "Exit Portal! Come here to win!")
    rendered_exit_text = font.render(exit_text, True, (0, 73, 0))  # Render the exit text

    moving_text = in_game.get("moving_message", "Not all blocks stay still...")
    rendered_moving_text = font.render(moving_text, True, (128, 0, 128))  # Render the moving text

    pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

    pygame.draw.rect(screen, (129, 94, 123), (exit_portal.x - camera_x, exit_portal.y - camera_y, exit_portal.width, exit_portal.height))

            # Inside the game loop:
    screen.blit(rendered_up_text, (700 - camera_x, 200 - camera_y))  # Draws the rendered up text
    screen.blit(rendered_warning_text, (1900 - camera_x, 150 - camera_y))  # Draws the rendered warning text
    screen.blit(rendered_moving_text, (1350 - camera_x, 170 - camera_y))  # Draws the rendered moving text
    screen.blit(rendered_exit_text, (2400 - camera_x, 300 - camera_y))  # Draws the rendered exit text

    for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))
    
    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
        show_greenrobo_unlocked = False

    if transition.x <= -transition.image.get_width():
       while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

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

        if player_y > 1100:
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

            medal = get_medal(1, current_time)
        
            score_calc()
            if progress["score"]["lvl1"] < score or progress["score"]["lvl1"] == 0:
                progress["score"]["lvl1"] = score
                new_hs = True
            if not new_hs:
                hs = progress["score"]["lvl1"]
            stars = get_stars(1, score)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
            running = False
            if display_score == score:
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


        for i, token in enumerate(token_pos):
            if i not in collected_tokens:
                screen.blit(token_img, (token.x - camera_x, token.y - camera_y))

        for i, token in enumerate(token_pos):
         if i not in collected_tokens and player_rect.colliderect(token):
          collected_tokens.add(i)
          if not is_mute:
           token_sound.play()

        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))
    
        block_func(blocks)

        draw_spikes(spikes)

        if player_rect.colliderect(moving_block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= moving_block.y:
                    player_y = moving_block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > moving_block.x and player_x < moving_block.x + moving_block.width:
                    if player_x < moving_block.x:  # Colliding with the left side of the block
                        player_x = moving_block.x - img_width
                    elif player_x + img_width > moving_block.x + moving_block.width:  # Colliding with the right side
                        player_x = moving_block.x + moving_block.width

        pygame.draw.rect(screen, (129, 94, 123), (exit_portal.x - camera_x, exit_portal.y - camera_y, exit_portal.width, exit_portal.height))
        
        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
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
        screen.blit(render_text(lvl1_text, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

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

        token_display = f"Tokens: {len(collected_tokens)}/{len(token_pos)}"
        screen.blit(font.render(token_display, True, (255, 255, 0)), (SCREEN_WIDTH - 200, 50))

        pygame.display.update()    

def create_lvl2_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, wait_time, transition_time, is_transitioning, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    global x, y, camera_x, camera_y, spawn_x, spawn_y,  player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground
    char_assets()
    new_hs = False

    screen.blit(green_background, (0, 0))
    in_game = load_language(lang_code).get('in_game', {})

    wait_time = None
    start_time = time.time()

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

    # Draw flag
    flag = pygame.Rect(2150, 650, 80, 50)  # x, y, width, height
    checkpoint_reached = False
    flag_1_x, flag_1_y = 2150, 650

    blocks = [
        pygame.Rect(100, 650, 1000, 50),
        pygame.Rect(500, 500, 200, 50),
        pygame.Rect(1900, 200, 200, 50),
        pygame.Rect(2080, 750, 620, 50),        
        pygame.Rect(2150, 530, 300, 50),
        pygame.Rect(2340, 50, 110, 500),
        pygame.Rect(2900, 450, 400, 50),
        pygame.Rect(3300, 650, 260, 50),
        pygame.Rect(3800, 650, 220, 50),
        pygame.Rect(4260, 650, 220, 50),
        pygame.Rect(3300, 200, 1300, 50),
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
        [(4300, 250), (4350, 300), (4400, 250)],
        [(4400, 250), (4450, 300), (4500, 250)],
        [(4500, 250), (4550, 300), (4600, 250)],        
        ]

    exit_portal = pygame.Rect(4400, 550, 50, 100)
    clock = pygame.time.Clock()
    
    token_pos = [
        pygame.Rect(1060, 140, 80, 80),
        pygame.Rect(550, 410, 80, 80),
        pygame.Rect(1400, 210, 80, 80),
        pygame.Rect(1900, 110, 80, 80),
        pygame.Rect(2030, -50, 80, 80),
        pygame.Rect(2200, 650, 80, 80),
        pygame.Rect(2300, 650, 80, 80),
        pygame.Rect(2400, 650, 80, 80),
        pygame.Rect(2550, 140, 80, 80),
        pygame.Rect(3640, 475, 80, 80),
        pygame.Rect(4100, 475, 80, 80),
    ]

    collected_tokens = set()

    # Render the texts
    jump_message = in_game.get("jump_message", "Use orange blocks to jump high distances!")
    rendered_jump_text = font.render(jump_message, True, (255, 128, 0))  # Render the jump text

    if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))



    pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

    for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (jump_block.x - camera_x, jump_block.y - camera_y, jump_block.width, jump_block.height))

    pygame.draw.rect(screen, (129, 94, 123), (exit_portal.x - camera_x, exit_portal.y - camera_y, exit_portal.width, exit_portal.height))

            # Inside the game loop:
    screen.blit(rendered_jump_text, (900 - camera_x, 500 - camera_y))  # Draws the rendered up text

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False

    if transition.x <= -transition.image.get_width():
      while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

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

            if player_y > 1100:
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
            
            medal = get_medal(2, current_time)
            score_calc()

            if progress["score"]["lvl2"] < score or progress["score"]["lvl2"] == 0:
                progress["score"]["lvl2"] = score
                new_hs = True
            if not new_hs:
                hs = progress["score"]["lvl2"]
            stars = get_stars(2, score)
            level_complete()
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

        for i, token in enumerate(token_pos):
            if i not in collected_tokens:
                screen.blit(token_img, (token.x - camera_x, token.y - camera_y))

        for i, token in enumerate(token_pos):
         if i not in collected_tokens and player_rect.colliderect(token):
          collected_tokens.add(i)
          if not is_mute:
           token_sound.play()

        if player_rect.colliderect(flag) and not checkpoint_reached:
            checkpoint_reached = True
            spawn_x, spawn_y = 2150, 620  # Store checkpoint position
            if not is_mute:
                checkpoint_sound.play()
            
        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))

        block_func(blocks)

        draw_spikes(spikes)
        
        if player_rect.colliderect(moving_block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= moving_block.y:
                    player_y = moving_block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > moving_block.x and player_x < moving_block.x + moving_block.width:
                    if player_x < moving_block.x:  # Colliding with the left side of the block
                        player_x = moving_block.x - img_width
                    elif player_x + img_width > moving_block.x + moving_block.width:  # Colliding with the right side
                        player_x = moving_block.x + moving_block.width

        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (jump_block.x - camera_x, jump_block.y - camera_y, jump_block.width, jump_block.height))

        pygame.draw.rect(screen, (129, 94, 123), (exit_portal.x - camera_x, exit_portal.y - camera_y, exit_portal.width, exit_portal.height))
        
        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
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

        token_display = f"Tokens: {len(collected_tokens)}/{len(token_pos)}"
        screen.blit(font.render(token_display, True, (255, 255, 0)), (SCREEN_WIDTH - 200, 50))

        pygame.display.update()    

def create_lvl3_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    screen.blit(green_background, (0, 0))
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

    # Render the texts
    token_pos = [
        pygame.Rect(550, 410, 80, 80),
        pygame.Rect(960, 410, 80, 80),
        pygame.Rect(100, 210, 80, 80),
        pygame.Rect(1900, 210, 80, 80),
        pygame.Rect(920, 210, 80, 80),
        pygame.Rect(2300, 250, 80, 80),
        pygame.Rect(2300, 450, 80, 80),
        pygame.Rect(2300, 650, 80, 80),
        pygame.Rect(2620, 0, 80, 80),
        pygame.Rect(2620, -200, 80, 80),
        pygame.Rect(3000, -100, 80, 80),
        pygame.Rect(2100, -260, 80, 80),
        pygame.Rect(1900, -400, 80, 80),
        pygame.Rect(1500, -260, 80, 80),
        pygame.Rect(500, -400, 80, 80),
        pygame.Rect(1200, -260, 80, 80),
        pygame.Rect(950, -400, 80, 80),
        pygame.Rect(300, -260, 80, 80),
        pygame.Rect(0, -500, 80, 80),
        pygame.Rect(-200, -500, 80, 80),
        pygame.Rect(-500, -500, 80, 80),
        pygame.Rect(-800, -500, 80, 80),
    ]

    collected_tokens = set()

    saw_text = in_game.get("saws_message", "Saws are also dangerous!")
    rendered_saw_text = font.render(saw_text, True, (255, 0, 0))  # Render the saw text

    key_text = in_game.get("key_message", "Grab the coin and open the block!")
    rendered_key_text = font.render(key_text, True, (255, 255, 0))  # Render the key text

    # Drawing
    screen.blit(green_background, (0, 0))

    screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
        # Draw all saws first
    for x, y, r, color in saws:
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

    for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

    for spike in spikes:
            pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    for pair in key_block_pairs:

     if not pair["collected"]:
        key_x, key_y, key_r, key_color = pair["key"]
        block = pair["block"]
        pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)

            # Draw block only if key is not collected
     if not pair["collected"]:
        pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

    pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))

        # Draw the texts
    screen.blit(rendered_saw_text, (int(550 - camera_x), int(600 - camera_y)))  # Draws the rendered up text
    screen.blit(rendered_key_text, (int(2500 - camera_x), int(200 - camera_y)))  # Draws the rendered up text
    if show_greenrobo_unlocked:
        messages = load_language(lang_code).get('messages', {})
        if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
            unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
            rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
            screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
        show_greenrobo_unlocked = False

    if transition.x <= -transition.image.get_width():
      while running:
        print(player_x, player_y)
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

            if player_y > 1100:
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
            medal = get_medal(3, current_time)
            score_calc()
            if progress["score"]["lvl3"] < score or progress["score"]["lvl3"] == 0:
                progress["score"]["lvl3"] = score
                new_hs = True
            if not new_hs:
                hs = progress["score"]["lvl3"]
            stars = get_stars(3, score)
            level_complete()    
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

        for i, token in enumerate(token_pos):
            if i not in collected_tokens:
                screen.blit(token_img, (token.x - camera_x, token.y - camera_y))

        for i, token in enumerate(token_pos):
         if i not in collected_tokens and player_rect.colliderect(token):
          collected_tokens.add(i)
          if not is_mute:
           token_sound.play()

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
        
        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

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

        token_display = f"Tokens: {len(collected_tokens)}/{len(token_pos)}"
        screen.blit(font.render(token_display, True, (255, 255, 0)), (SCREEN_WIDTH - 200, 50))

        pygame.display.update()    

def create_lvl4_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(green_background, (0, 0))
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
        pygame.Rect(2300, 230, 1000, 1800),
        pygame.Rect(2800, 400, 1200, 1600),
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

    # Drawing
    screen.blit(green_background, (0, 0))

    screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for rotating_saw in rotating_saws:
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


    for x, y, r, color in saws:
        pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        # Draw all lasers first
    for laser in lasers:
        pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))


    for jump_block in jump_blocks:
        pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

        
    for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]
            pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)
            pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

    for block in moving_blocks:
        rect = block['rect']
        axis = block['axis']
        speed = block['speed']
        pygame.draw.rect(screen, (128, 0, 128), rect.move(-camera_x, -camera_y))


    pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False

    if transition.x <= -transition.image.get_width():
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

        if player_y > 1100:
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
            medal = get_medal(4, current_time)
            score_calc()
            
            if progress["score"]["lvl4"] < score or progress["score"]["lvl4"] == 0:
                progress["score"]["lvl4"] = score
                new_hs = True
            if not new_hs:
                hs = progress["score"]["lvl4"]
            stars = get_stars(4, score)
            level_complete()
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
        
        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

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
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(green_background, (0, 0))
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

    walls = [        
        pygame.Rect(2700, -310, 50, 91),
        pygame.Rect(2880, -310, 50, 140)
        ]

    blocks = [
        pygame.Rect(-50, 650, 1000, 100),
        pygame.Rect(900, 510, 100, 100),
        pygame.Rect(1450, 650, 650, 100),
        pygame.Rect(1500, -50, 700, 50),
        pygame.Rect(1700, -350, 1050, 50),
        pygame.Rect(1500, -250, 50, 200),
        pygame.Rect(2700, -220, 200, 50),
        pygame.Rect(2880, -350, 700, 50),
        pygame.Rect(3900, -350, 100, 30),
        pygame.Rect(3900, -50, 100, 30),
        pygame.Rect(3900, -650, 100, 30),
        pygame.Rect(4200, -150, 100, 30),
        pygame.Rect(4200, -750, 100, 30),
        pygame.Rect(4200, -450, 100, 30),
        pygame.Rect(4500, -50, 100, 30),
        pygame.Rect(4500, -350, 100, 30),
        pygame.Rect(4500, -650, 100, 30),
        pygame.Rect(4800, -150, 100, 30),
        pygame.Rect(4800, -750, 100, 30),
        pygame.Rect(4800, -450, 100, 30),        
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
        [(3900, -50), (3950, -100), (4000, -50)],
        [(3900, -650), (3950, -700), (4000, -650)],
        [(4200, -450), (4250, -500), (4300, -450)],
        [(4500, -50), (4550, -100), (4600, -50)],
        [(4800, -750), (4850, -800), (4900, -750)],
        [(4800, -150), (4850, -200), (4900, -150)],
    ]

    spikes_01 = [
    [(4200, -150), (4250, -200), (4300, -150)],
    [(4500, -350), (4550, -400), (4600, -350)],
    [(4500, -650), (4550, -700), (4600, -650)],
    [(4800, -450), (4850, -500), (4900, -450)],
    ]

    exit_portal = pygame.Rect(1375, 0, 50, 100)
    clock = pygame.time.Clock()

    
    # Render the texts
    screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for rotating_saw in rotating_saws:
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


    for x, y, r, color in saws:
        pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))


    for jump_block in jump_blocks:
        pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

        
    for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]
            pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)
            pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))


    pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False

    if transition.x <= -transition.image.get_width():
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

        for block in walls:
            if player_rect.colliderect(block):
                # Horizontal collision (left or right side of the block)
                if player_x + img_width > block.x and player_x < block.x + block.width:
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

        if player_y > 1100:
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
            medal = get_medal(5, current_time)
            score_calc()
            if progress["score"]["lvl5"] < score or progress["score"]["lvl5"] == 0:
                progress["score"]["lvl5"] = score
                new_hs = True
            if not new_hs:
                hs = progress["score"]["lvl5"]
            stars = get_stars(5, score)
            level_complete()

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



        for block in walls:
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
       
        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

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
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    start_time = time.time()
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(green_background, (0, 0))

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
    val = 1
    guide = False

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
        pygame.Rect(2900, 10, 50, 570),
        pygame.Rect(3150, 10, 50, 170),
        pygame.Rect(2950, 530, 2950, 50),
        pygame.Rect(3200, 130, 2700, 50)
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
    [(800, 700), (845, 600), (890, 700)],
    [(900,700), (945, 600), (990, 700)],
    [(4100, 130), (4150, 80), (4200, 130)],
    [(4610, 130),(4660, 80),(4710, 130)],
    [(4300, 530),(4345, 480), (4390, 530)],
    [(4400, 530), (4445, 480), (4490, 530)],
    ]

    exit_portal = pygame.Rect(5700, 430, 50, 100)
    clock = pygame.time.Clock()


    screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for rotating_saw in rotating_saws:
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


    for x, y, r, color in saws:
        pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        # Draw all lasers first
    for laser in lasers:
        pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))


    for jump_block in jump_blocks:
        pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

        
    for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]
            pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)
            pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

    pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False

    if transition.x <= -transition.image.get_width():
      while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        if wait_time is None:
            val = random.random()
            print(val)

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

        if player_y > 1100:
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()
            if not is_mute and val > 0.35: # type: ignore
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
            medal = get_medal(6, current_time)
            score_calc()
            if progress["score"]["lvl6"] < score or progress["score"]["lvl6"] == 0:
                progress["score"]["lvl6"] = score
                new_hs = True
            if not new_hs:
                hs = progress["score"]["lvl6"]
            stars = get_stars(6, score)
            level_complete()
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
                if not is_mute and val > 0.35: # type: ignore
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
                if not is_mute and val > 0.35: # type: ignore
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
                if not is_mute and val > 0.35: # type: ignore
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
                if not is_mute and val > 0.35: # type: ignore
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
                if not is_mute and val > 0.35:
                    laser_sound.play()
                player_x, player_y = spawn_x, spawn_y # type: ignore
                deathcount += 1
                velocity_y = 0
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key
        
        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
            laser_rect = pygame.Rect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                wait_time = pygame.time.get_ticks()
                key_block_pairs[0]["collected"] = False  # Reset key block status
                if not is_mute and val > 0.35:    
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
                    if not is_mute and val > 0.35:
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
                    if not is_mute and val > 0.35:
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
        
        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

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
                if val > 0.3:
                    screen.blit(font.render(death_text, True, (255, 0, 0)), (20, 50))
                else:
                    if not guide:
                        hscore.play()
                        guide = True
                    
                    if val < 0.15:
                        screen.blit(font_def.render('"The strong is not the one who overcomes the people by his strength, but the strong is', True, (255, 255, 0)), (20, 50))
                        screen.blit(font_def.render('the one who controls himself while in anger." (Bukhari 6114)', True, (255, 255, 0)), (20, 80)) 
                    else:
                        screen.blit(font_def.render('"Indeed, with hardship comes ease." (Quran 94:6)', True, (255, 255, 0)), (20, 50))
            
            else:
                wait_time = None
                val = None


        pygame.display.update()   

def create_lvl7_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    start_time = time.time()
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(green_background, (0, 0))

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

    screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for rotating_saw in rotating_saws:
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


    for x, y, r, color in saws:
        pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False

    if transition.x <= -transition.image.get_width():
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


        if player_y > 1100:
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
            medal = get_medal(7, current_time)
            score_calc()
            if progress["score"]["lvl7"] < score or progress["score"]["lvl7"] == 0:
                progress["score"]["lvl7"] = score
                new_hs = True
            if not new_hs:
                hs = progress["score"]["lvl7"]
            stars = get_stars(7, score)
            level_complete()
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
        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

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
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()

    new_hs = False
    buttons.clear()
    screen.blit(green_background, (0, 0))

    wait_time = None
    start_time = time.time()

    in_game = load_language(lang_code).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y = 0, 260
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

    screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for x, y, r, color in saws:
        pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False

    if transition.x <= -transition.image.get_width():
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
            spawn_x, spawn_y = 0, 260
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


        if player_y > 1100:
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
            medal = get_medal(8, current_time)
            score_calc()
            if progress["score"]["lvl8"] < score or progress["score"]["lvl8"] == 0:
                progress["score"]["lvl8"] = score
                new_hs = True
            if not new_hs:
                hs = progress["score"]["lvl8"]
            stars = get_stars(8, score)
            level_complete()
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
        
        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

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
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(green_background, (0, 0))
    
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

    screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for x, y, r, color in gravity_strongers:
            # Draw the button as a circle
                pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False

    if transition.x <= -transition.image.get_width():
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


        if player_y > 1100:
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
            medal = get_medal(9, current_time)
            score_calc()
            if progress["score"]["lvl9"] < score or progress["score"]["lvl9"] == 0:
                new_hs = True
                progress["score"]["lvl9"] = score
            if not new_hs:
                hs = progress["score"]["lvl9"]
            stars = get_stars(9, score)
            level_complete()
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
        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

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
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    new_hs = False
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    buttons.clear()
    screen.blit(green_background, (0, 0))

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

    screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(nact_cp, ((flag_2_x - camera_x), (flag_2_y - camera_y)))

    for rotating_saw in rotating_saws:
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

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for x, y, r, color in saws:
            # Draw the saw as a circle
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False

    if transition.x <= -transition.image.get_width():
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

        if player_y > 1100:
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
            medal = get_medal(10, current_time)
            score_calc()
            if progress["score"]["lvl10"] < score or progress["score"]["lvl10"] == 0:
                new_hs = True
                progress["score"]["lvl10"] = score
            if not new_hs:
                hs = progress["score"]["lvl10"]
            stars = get_stars(10, score)
            level_complete()
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
        
        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

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
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(green_background, (0, 0))

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
    evilrobo_mascot = pygame.image.load(f"char/evilrobot/evilrobot.png").convert_alpha()
    evilrobo_phase = 0    

    # Logic for unlocking Evil Robo
    unlock = progress.get("evilrobo_unlocked", False)
    unlock_time = None

    # Draw flag
    flag = pygame.Rect(1400, 420, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(5600, 330, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 1400, 420
    flag_2_x, flag_2_y = 5600, 330

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
        pygame.Rect(2250, -300, 600, 2200),
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

    for x, y, r, color in saws:
            # Draw the saw as a circle
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [((x - camera_x),( y - camera_y)) for x, y in spike])

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False

    if transition.x <= -transition.image.get_width():
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


        if player_y > 1100:
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
            spawn_x, spawn_y = 5600, 330  # Checkpoint position
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
            medal = get_medal(11, current_time)
            score_calc()
            if progress["score"]["lvl11"] < score or progress["score"]["lvl11"] == 0:
                new_hs = True
                progress["score"]["lvl11"] = score
            if not new_hs:
                hs = progress["score"]["lvl11"]
            stars = get_stars(11, score)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            check_green_gold()

            save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('ice_levels')    

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

        if player_x > 4800 and player_y < -300 and not lights_off and evilrobo_phase == 2:
            epos_x = 4799
            epos_y = player_y
            screen.blit(evilrobo_mascot, ((epos_x - camera_x), (epos_y - camera_y)))
            if player_rect.colliderect(evilrobo_rect):
                evilrobo_phase = 0
                screen.fill((255, 255, 255))
                epos_x, epos_y = espawn_x, espawn_y
                player_x, player_y = spawn_x, spawn_y
                stamina = False
                lights_off = True
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


        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

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
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, snow
    global new_hs, hs, current_time, medal, deathcount, score, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(ice_background, (0, 0))
    in_game = load_language(lang_code).get('in_game', {})
    in_game_ice = load_language(lang_code).get('in_game_ice', {})

    wait_time = None
    start_time = time.time()

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y =  2100, 400
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    
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
        {'r': 50, 'speed': 11, 'cx': 6300, 'cy': 550, 'min': 6250, 'max': 7800},
        {'r': 50, 'speed': 13, 'cx': 6700, 'cy': 550, 'min': 6000, 'max': 8900},
        {'r': 50, 'speed': 14, 'cx': 7800, 'cy': 550, 'min': 7300, 'max': 9700},
        {'r': 50, 'speed': 15, 'cx': 8700, 'cy': 550, 'min': 7800, 'max': 10800},
    ]

    rushing_saws = [
        {'r': 50, 'speed': 12, 'cx': 3150, 'cy': 120 ,'max': 3850},
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

    exit_portal = pygame.Rect(11500, 450, 50, 100)
    clock = pygame.time.Clock()

    speedsters = [
        (5300, 450, 30, (51, 255, 51)),
    ]

    for x, y, r, color in saws:
            # Draw the saw as a circle
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [((x - camera_x),( y - camera_y)) for x, y in spike])

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False
    
    for ice in ice_blocks:
            block = ice.rect
            pygame.draw.rect(screen, (0, 205, 255), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
        
    if transition.x <= -transition.image.get_width():
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
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys

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
            stamina = False
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the key collection status
            death_text = in_game_ice.get("overheat_death_message", "Overheated!")
            wait_time = pygame.time.get_ticks()
            for ice in ice_blocks:
                ice.float_height = ice.initial_height
                ice.rect.height = int(ice.float_height)
        elif current_temp < min_temp:
            player_x, player_y = spawn_x, spawn_y
            if not is_mute:
                freeze_sound.play()
            current_temp = start_temp
            stamina = False
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the key collection status
            death_text = in_game_ice.get("freeze_death_message", "Frozen and malfunctioned!")
            wait_time = pygame.time.get_ticks()            
            for ice in ice_blocks:
                ice.float_height = ice.initial_height
                ice.rect.height = int(ice.float_height)

        # Rounded off value
        current_temp = round(current_temp, 2)
        
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
            
            progress["medals"]["lvl12"] = get_medal(12, progress["times"]["lvl12"])

            update_locked_levels()
            medal = get_medal(12, current_time)
            score_calc()
            if progress["score"]["lvl12"] < score or progress["score"]["lvl12"] == 0:
                new_hs = True
                progress["score"]["lvl12"] = score
            if not new_hs:
                hs = progress["score"]["lvl12"]
            stars = get_stars(12, score)
            level_complete()
            save_progress(progress)  # Save progress to JSON file

            running = False
            set_page('lvl13_screen')    

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
        if LDM:
            screen.fill((0, 146, 230))
        else:
         screen.blit(ice_background, (0, 0))

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
                stamina = True

        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))


        ice_text = in_game_ice.get("ice_message", "Ice Blocks melt when you stand on them! But they also cool you down!")
        rendered_ice_text = font.render(ice_text, True, (0, 0, 0))
        screen.blit(rendered_ice_text, (2050 - camera_x, 560 - camera_y))
        freeze_text = in_game_ice.get("freeze_message", "Just remember to get some warm ups and don't just freeze to death!")
        rendered_freeze_text = font.render(freeze_text, True, (0, 0, 0))
        screen.blit(rendered_freeze_text, (2055 - camera_x, 590 - camera_y))    
        overheat_text1 = in_game_ice.get("overheat_message1", "Also remember to keep track of your temperature and if")    
        rendered_overheat1_text = font.render(overheat_text1, True, (0, 0, 0))
        screen.blit(rendered_overheat1_text, (4600 - camera_x, 300 - camera_y))
        overheat_text2 = in_game_ice.get("overheat_message2", "you heat up too much, stand on an ice block nearby!")
        rendered_overheat2_text = font.render(overheat_text2, True, (0, 0, 0))
        screen.blit(rendered_overheat2_text, (4620 - camera_x, 340 - camera_y))

        # Draw Main text backgrounds
        pygame.draw.rect(screen, (96, 96, 96), (0, 0, 300 , 130 ))
        pygame.draw.rect(screen, (96, 96, 96), (SCREEN_WIDTH // 2 - 80, 0, 160 , 70))
        pygame.draw.rect(screen, (96, 96, 96), (SCREEN_WIDTH - 250, 0, 250 , 80 ))

        levels = load_language(lang_code).get('levels', {})
        lvl_text = levels.get("lvl12", "Level 12")  # Render the level text
        rendered_lvl_text = font.render(lvl_text, True, (255, 255, 255))
        screen.blit(rendered_lvl_text, (SCREEN_WIDTH //2 - rendered_lvl_text.get_width() // 2, 20)) # Draws the level text

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        temp_val = in_game_ice.get("temp", "Temperature: {current_temp}").format(current_temp=current_temp)
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
                stamina = False
                    # Trigger death logic
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()
                key_block_pairs[0]["collected"] = False  # Reset key block status
                velocity_y = 0
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
                velocity_y = 0
                    # Trigger death logic
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                key_block_pairs[0]["collected"] = False  # Reset key block status
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()
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
                velocity_y = 0
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                if not is_mute:
                    death_sound.play()
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
                velocity_y = 0
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                key_block_pairs[0]["collected"] = False  # Reset key block status
                if not is_mute:
                    death_sound.play()
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
                death_text = in_game.get("hit_message", "Hit on the head!")
                stamina = False
                lights_off = True
                if not is_mute:    
                    hit_sound.play()
                key_block_pairs[0]["collected"] = False  # Reset key block status
                velocity_y = 0
                wait_time = pygame.time.get_ticks()  # Start the wait time
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
                    wait_time = pygame.time.get_ticks()  # Start the wait time
                    if not is_mute:
                        death_sound.play()
                    key_block_pairs[0]["collected"] = False  # Reset key block status
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
                    wait_time = pygame.time.get_ticks()  # Start the wait time
                    if not is_mute:
                        death_sound.play()
                    key_block_pairs[0]["collected"] = False  # Reset key block status
                    velocity_y = 0
                    deathcount += 1
                    collision_detected = True  # Set the flag to stop further checks
                    for ice in ice_blocks:
                        ice.float_height = ice.initial_height
                        ice.rect.height = int(ice.float_height)
                    break

        if player_y > 1100:
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()  # Start the wait time
            lights_off = True
            stamina = False
            key_block_pairs[0]["collected"] = False  # Reset key block status
            if not is_mute:    
                fall_sound.play()
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
        if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
        else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 80))
            else:
                wait_time = None

        pygame.display.update() 

def create_lvl13_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, snow
    global new_hs, hs, current_time, medal, deathcount, score, stars
    new_hs = False
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    buttons.clear()
    screen.blit(ice_background, (0, 0))
    in_game = load_language(lang_code).get('in_game', {})
    in_game_ice = load_language(lang_code).get('in_game_ice', {})

    wait_time = None
    start_time = time.time()

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y =  100, 0
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
    visibility = 0
    fade_time = None

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

    ice_robo = pygame.image.load(f"char/icerobot/moveicerobotL.png").convert_alpha()
    ice_robo_x, ice_robo_y = 66200, 650
    ice_robo_move = pygame.image.load(f"char/icerobot/moveicerobot.png").convert_alpha()

    # Draw flag
    flag = pygame.Rect(3900, 200, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag_1_x, flag_1_y = 3900, 200

    gravity_strongers = [
        (3800, 250, 30, (204, 102, 204)),  # Strong gravity button
    ]

    gravity_weakers = [
        (5000, 700, 30, (0, 102, 204)),
    ]

    key_block_pairs = [
        {
            "key": (36500, -50, 30, (255, 255, 0)),
            "block": pygame.Rect(40200, 350, 200, 200),
            "collected": False
        },
    ]

    key_block_pairs_timed = [
        {
            "key": (300, 100, 30, (255, 119, 0)),
            "block": pygame.Rect(1900, 0, 100, 200),
            "collected": False,
            "timer": 0,  # Timer for the key block
            "duration": 5000,  # Duration for which the block is active
            "locked_time": None
        },
        {
            "key": (4000, 250, 30, (255, 119, 0)),
            "block": pygame.Rect(4150, 400, 50, 250),
            "collected": False,
            "timer": 0,  # Timer for the key block
            "duration": 3500,  # Duration for which the block is active
            "locked_time": None
        }
    ]

    blocks = [
        pygame.Rect(0, 200, 2000, 100),
        pygame.Rect(1900, -1000, 100, 1000),
        pygame.Rect(3200, -50, 800, 100),
        pygame.Rect(3600, 300, 600, 100),
        pygame.Rect(4100, -700, 100, 1000),
        pygame.Rect(3450, 650, 1000, 100),
        pygame.Rect(3350, 0, 100, 750),
        pygame.Rect(65000, 750, 70000, 200),
    ]

    jump_blocks = [
        pygame.Rect(3000, 250, 100, 100),
        pygame.Rect(4300, 550, 100, 100),
    ]

    class IceBlock:
        def __init__(self, rect):
            self.rect = rect
            self.initial_height = float(rect.height)
            self.float_height = self.initial_height

    ice_blocks = [
        IceBlock(pygame.Rect(-200, 200, 100, 100)),
        IceBlock(pygame.Rect(2300, 200, 150, 100)),
        IceBlock(pygame.Rect(2600, 20, 200, 100)),
        IceBlock(pygame.Rect(4500, 750, 60000, 200)),
    ]

    moving_saws = [ 
        {'r': 70, 'speed': 4, 'cx': 800, 'cy': 0, 'max': 500, 'min': -100},
        {'r': 70, 'speed': 5, 'cx': 1400, 'cy': 300, 'max': 600, 'min': 0},
    ]

    moving_saws_x = [
        {'r': 95, 'speed': 6, 'cx': 3350, 'cy': -50, 'min': 3300, 'max': 3900},
    ]

    rushing_saws = [
        {'r': 50, 'speed': 12, 'cx': 3050, 'cy': 120 ,'max': 300850},
    ]

    moving_block = [
        {'x': 17000, 'y': 270, 'width': 110, 'height': 100, 'direction': 1, 'speed': 3, 'left_limit': 1650, 'right_limit': 1900 },
        {'x': 21000, 'y': -180, 'width': 110, 'height': 100, 'direction': 1, 'speed': 4, 'left_limit': 1750, 'right_limit': 2100 },
    ]

    saws = [
        (4600, 550, 80, (255, 0, 0)),
    ]

    spikes = [
    [(1000, 200), (1050, 150), (1100, 200)],
    [(2710, 20), (2755, -30), (2800, 20)],
    [(3600, 300), (3650, 250), (3700, 300)],
    [(3650, 650), (3700, 600), (3750, 650)],
    [(3900, 650), (3950, 600), (4000, 650)]
    ]

    light_off_button = pygame.Rect(2350, -425, 50, 50)
    
    light_blocks = [
        pygame.Rect(5300, 200, 300, 100),
    ]

    exit_portal = pygame.Rect(4125, -800, 50, 100)
    clock = pygame.time.Clock()

    speedsters = [
        (5300, 450, 30, (51, 255, 51)),
    ]


    for x, y, r, color in saws:
            # Draw the saw as a circle
            pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [((x - camera_x),( y - camera_y)) for x, y in spike])

    for saw in moving_saws:
                # Draw the moving circle (saw)
            pygame.draw.circle(screen, (255, 0, 0), (int(saw['cx'] - camera_x), int(saw['cy'] - camera_y)), saw['r'])

    for block in blocks:    
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = font.render(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False
    
    for ice in ice_blocks:
            block = ice.rect
            pygame.draw.rect(screen, (0, 205, 255), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))
        

    if transition.x <= -transition.image.get_width():
       while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_v]:
            player_x, player_y = 64800, 400

        if keys[pygame.K_r]:
            start_time = time.time()
            lights_off = True
            stamina = False
            weak_grav = False
            strong_grav = False
            checkpoint_reached = False  # Reset checkpoint status
            current_temp = start_temp
            spawn_x, spawn_y = 100, 0
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["timer"] = 0  # Reset the timer for all key blocks

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("ice_levels")

        # Ice and Ground temeprature logic
        if not keys[pygame.K_r] and player_x < 65500:
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
            stamina = False
            lights_off = True
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["timer"] = 0  # Reset the timer for all key blocks
            death_text = in_game_ice.get("overheat_death_message", "Overheated!")
            wait_time = pygame.time.get_ticks()
            for ice in ice_blocks:
                ice.float_height = ice.initial_height
                ice.rect.height = int(ice.float_height)
        elif current_temp < min_temp:
            player_x, player_y = spawn_x, spawn_y
            if not is_mute:
                freeze_sound.play()
            current_temp = start_temp
            stamina = False
            lights_off = True
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["timer"] = 0  # Reset the timer for all key blocks
            death_text = in_game_ice.get("freeze_death_message", "Frozen and malfunctioned!")
            wait_time = pygame.time.get_ticks()            
            for ice in ice_blocks:
                ice.float_height = ice.initial_height
                ice.rect.height = int(ice.float_height)

        # Rounded off value
        current_temp = round(current_temp, 2)
        
        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground and player_x <= 65500:
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

        if moving and player_x <= 65500:
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
        if player_rect.colliderect(flag) and not checkpoint_reached:
            checkpoint_reached = True
            stamina = False  # Reset stamina status
            lights_off = True
            weak_grav = False
            strong_grav = False
            spawn_x, spawn_y = 3900, 150  # Store checkpoint position
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if progress["complete_levels"] < 13:
                progress["complete_levels"] = 13
                # You might want to update locked_levels here as well if needed

            if not is_mute:
                warp_sound.play()

            if current_time < progress["times"]["lvl13"] or progress["times"]["lvl13"] == 0:
                progress["times"]["lvl13"] = round(current_time, 2)
            
            progress["medals"]["lvl13"] = get_medal(13, progress["times"]["lvl13"])

            update_locked_levels()
            medal = get_medal(13, current_time)
            score_calc()
            if progress["score"]["lvl13"] < score or progress["score"]["lvl13"] == 0:
                new_hs = True
                progress["score"]["lvl13"] = score
            if not new_hs:
                hs = progress["score"]["lvl13"]
            stars = get_stars(13, score)
            level_complete()
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

        # Drawing
        if LDM:
            screen.fill((0, 146, 230))
        else:
         screen.blit(ice_background, (0, 0))

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

        if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))

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

        if player_rect.colliderect(light_off_button):
            if not is_mute and lights_off:
                button_sound.play()
            lights_off = False

        timed_coin_text = in_game_ice.get("timed_coin_message", "Orange coins are timed! They open blocks for a limited")
        rendered_timed_text = font.render(timed_coin_text, True, (0, 0, 0))
        screen.blit(rendered_timed_text, (0 - camera_x, -80 - camera_y))
        timed_coin_text_2 = in_game_ice.get("timed_coin_message_2", "time. Run before they close again, or at worst, crush you...")
        rendered_timed_text_2 = font.render(timed_coin_text_2, True, (0, 0, 0))
        screen.blit(rendered_timed_text_2, (-20 - camera_x, -30 - camera_y))
        ice_friendly = in_game_ice.get("ice_friendly", "Here's a ice block in case you need it!")
        ice_friendly_text = font.render(ice_friendly, True, (0, 0, 0))
        screen.blit(ice_friendly_text, (-450 - camera_x, 80 - camera_y))
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

            # Horizontal collisions
                    elif player_x + img_width > block.x and player_x < block.x + block.width:
                        if player_x < block.x:
                            player_x = block.x - img_width
                        elif player_x + img_width > block.x + block.width:
                            player_x = block.x + block.width

        for pair in key_block_pairs_timed:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            key_rect = pygame.Rect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)

            if player_rect.colliderect(key_rect):
                if not pair["collected"]:
                    pair["locked_time"] = pygame.time.get_ticks()
                    pair["collected"] = True
                    if not is_mute:
                        open_sound.play()

            # Draw key and block only if not collected
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

            # Reset after duration
            if pair["locked_time"] is not None:
                if pair["collected"] and (pygame.time.get_ticks() - pair["locked_time"]) > pair["duration"]:
                    pair["collected"] = False
                    pair["locked_time"] = None  # Reset timer
                    # Check if player is inside block when it reappears
            
                    if player_rect.colliderect(pair["block"]):
                        hit_sound.play()
                        deathcount += 1
                        stamina = False  # Reset stamina status
                        lights_off = True
                        weak_grav = False
                        strong_grav = False
                        player_x, player_y = spawn_x, spawn_y
                        for pair in key_block_pairs:
                            pair["collected"] = False  # Reset the collected status for all keys
                        for pair in key_block_pairs_timed:
                            pair["collected"] = False  # Reset the collected status for all keys
                            pair["timer"] = 0  # Reset the timer for all key blocks
                        velocity_y = 0  # Reset vertical speed
                        wait_time = pygame.time.get_ticks()  # Start the wait time
                        death_text = in_game_ice.get("crushed_message", "Crushed!")

        for pair in key_block_pairs_timed:
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

        if player_x < 65500:
         screen.blit(ice_robo, (ice_robo_x - camera_x, ice_robo_y - camera_y))
         pygame.draw.rect(screen, (96, 96, 96), (0, 0, 300 , 130 ))
         pygame.draw.rect(screen, (96, 96, 96), (SCREEN_WIDTH // 2 - 80, 0, 160 , 70))
         pygame.draw.rect(screen, (96, 96, 96), (SCREEN_WIDTH - 250, 0, 250 , 80 ))

         levels = load_language(lang_code).get('levels', {})
         lvl_text = levels.get("lvl13", "Level 13")  # Render the level text
         rendered_lvl_text = font.render(lvl_text, True, (255, 255, 255))
         screen.blit(rendered_lvl_text, (SCREEN_WIDTH //2 - rendered_lvl_text.get_width() // 2, 20)) # Draws the level text

         deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
         screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

         temp_val = in_game_ice.get("temp", "Temperature: {current_temp}").format(current_temp=current_temp)
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
        else:
            screen.blit(ice_robo_move, (ice_robo_x - camera_x, ice_robo_y - camera_y))
            ice_robo_x += 51
            player_x += 52
            on_ground = True

        # DEATH LOGICS
        for block in moving_block:
            if block['width'] < 100:
                laser_rect = pygame.Rect(block['x'], block['y'] + block['height'] +10, block['width'], 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block['x'] + 4, block['y'] + block['height'] + 5, block['width'] - 8 , 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground and player_x != block['x']:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                stamina = False  # Reset stamina status
                lights_off = True
                weak_grav = False
                strong_grav = False
                if not is_mute:    
                    hit_sound.play()
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                wait_time = pygame.time.get_ticks()  # Start the wait time
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
                stamina = False  # Reset stamina status
                lights_off = True
                weak_grav = False
                strong_grav = False
                    # Trigger death logic
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                velocity_y = 0
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
                stamina = False  # Reset stamina status
                lights_off = True
                weak_grav = False
                strong_grav = False
                velocity_y = 0
                    # Trigger death logic
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()
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
                stamina = False  # Reset stamina status
                lights_off = True
                weak_grav = False
                strong_grav = False
                velocity_y = 0
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                if not is_mute:
                    death_sound.play()
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
                stamina = False  # Reset stamina status
                lights_off = True
                weak_grav = False
                strong_grav = False
                velocity_y = 0
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                if not is_mute:
                    death_sound.play()
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
                death_text = in_game.get("hit_message", "Hit on the head!")
                stamina = False
                lights_off = True
                if not is_mute:    
                    hit_sound.play()
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                velocity_y = 0
                wait_time = pygame.time.get_ticks()  # Start the wait time
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
                    stamina = False  # Reset stamina status
                    lights_off = True
                    weak_grav = False
                    strong_grav = False
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    wait_time = pygame.time.get_ticks()  # Start the wait time
                    if not is_mute:
                        death_sound.play()
                    for pair in key_block_pairs:
                        pair["collected"] = False  # Reset the collected status for all keys
                    for pair in key_block_pairs_timed:
                        pair["collected"] = False  # Reset the collected status for all keys
                        pair["timer"] = 0  # Reset the timer for all key blocks
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
                    wait_time = pygame.time.get_ticks()  # Start the wait time
                    if not is_mute:
                        death_sound.play()
                    for pair in key_block_pairs:
                        pair["collected"] = False  # Reset the collected status for all keys
                    for pair in key_block_pairs_timed:
                        pair["collected"] = False  # Reset the collected status for all keys
                        pair["timer"] = 0  # Reset the timer for all key blocks
                    velocity_y = 0
                    deathcount += 1
                    stamina = False  # Reset stamina status
                    lights_off = True
                    weak_grav = False
                    strong_grav = False
                    collision_detected = True  # Set the flag to stop further checks
                    for ice in ice_blocks:
                        ice.float_height = ice.initial_height
                        ice.rect.height = int(ice.float_height)
                    break

        if player_y > 1100:
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()  # Start the wait time
            stamina = False  # Reset stamina status
            lights_off = True
            weak_grav = False
            strong_grav = False
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["timer"] = 0  # Reset the timer for all key blocks
            if not is_mute:    
                fall_sound.play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            for ice in ice_blocks:
                ice.float_height = ice.initial_height
                ice.rect.height = int(ice.float_height)

        # Player Image
        if player_x < 65500:
         if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
         elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
         else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))
        else:
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))

        if wait_time is not None and player_x < 65500:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 80))
            else:
                wait_time = None

        if player_x > 66000:
            fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surface.set_alpha(visibility)
            fade_surface.fill((0, 0, 0))
            screen.blit(fade_surface, (0, 0))
            if visibility < 255:
                if fade_time is None:
                    fade_time = pygame.time.get_ticks()
                else:
                    if pygame.time.get_ticks() - fade_time > 1:
                        visibility += 1
                        fade_time = None
            else:
                if fade_time is None:
                    fade_time = pygame.time.get_ticks()
                print(pygame.time.get_ticks() - fade_time)
                if pygame.time.get_ticks() - fade_time > 3000:
                    running = False
                    create_secret1_screen()
        
        pygame.display.update() 

def create_secret1_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, snow
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()

    in_game = load_language(lang_code).get('in_game', {})
    in_game_ice = load_language(lang_code).get('in_game_ice', {})

    wait_time = None
    start_time = time.time()

    # Camera settings
    camera_x = 0
    camera_y = -500
    spawn_x, spawn_y =  100, 0
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
    visibility = 255
    fade_time = None

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

    ice_robo = pygame.image.load(f"char/icerobot/moveicerobotL.png").convert_alpha()
    ice_robo_x, ice_robo_y = 67000, 650
    ice_robo_move = pygame.image.load(f"char/icerobot/moveicerobot.png").convert_alpha()

    # Draw flag
    flag = pygame.Rect(3900, 200, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(54000, 300, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 3900, 200
    flag_2_x, flag_2_y = 54900, 300

    gravity_strongers = [
        (3800, 250, 30, (204, 102, 204)),  # Strong gravity button
    ]

    gravity_weakers = [
        (5000, 700, 30, (0, 102, 204)),
    ]

    key_block_pairs = [
        {
            "key": (36500, -50, 30, (255, 255, 0)),
            "block": pygame.Rect(40200, 350, 200, 200),
            "collected": False
        },
    ]

    key_block_pairs_timed = [
        {
            "key": (300, 100, 30, (255, 119, 0)),
            "block": pygame.Rect(1900, 0, 100, 200),
            "collected": False,
            "timer": 0,  # Timer for the key block
            "duration": 5000,  # Duration for which the block is active
            "locked_time": None
        },
    ]

    blocks = [
        pygame.Rect(0, 200, 2000, 100),
    ]

    jump_blocks = [
        pygame.Rect(3000, 250, 100, 100),
        pygame.Rect(4300, 550, 100, 100),
    ]

    class IceBlock:
        def __init__(self, rect):
            self.rect = rect
            self.initial_height = float(rect.height)
            self.float_height = self.initial_height

    ice_blocks = [
        IceBlock(pygame.Rect(-200, 2200, 100, 100)),
    ]

    moving_saws = [ 
        {'r': 70, 'speed': 4, 'cx': 800, 'cy': 0, 'max': 500, 'min': -100},
        {'r': 70, 'speed': 5, 'cx': 1400, 'cy': 300, 'max': 600, 'min': 0},
    ]

    moving_saws_x = [
        {'r': 95, 'speed': 6, 'cx': 3350, 'cy': -50, 'min': 3300, 'max': 3900},
    ]

    rushing_saws = [
        {'r': 50, 'speed': 12, 'cx': 3050, 'cy': 120 ,'max': 300850},
    ]

    moving_block = [
        {'x': 17000, 'y': 270, 'width': 110, 'height': 100, 'direction': 1, 'speed': 3, 'left_limit': 1650, 'right_limit': 1900 },
        {'x': 21000, 'y': -180, 'width': 110, 'height': 100, 'direction': 1, 'speed': 4, 'left_limit': 1750, 'right_limit': 2100 },
    ]

    saws = [
        (4600, 550, 80, (255, 0, 0)),
    ]

    spikes = [
    [(1000, 200), (1050, 150), (1100, 200)],
    [(2710, 20), (2755, -30), (2800, 20)],
    [(3600, 300), (3650, 250), (3700, 300)],
    [(3650, 650), (3700, 600), (3750, 650)],
    [(3900, 650), (3950, 600), (4000, 650)]
    ]

    light_off_button = pygame.Rect(2350, -425, 50, 50)
    
    light_blocks = [
        pygame.Rect(5300, 200, 300, 100),
    ]

    exit_portal = pygame.Rect(4125, -800, 50, 100)
    clock = pygame.time.Clock()

    speedsters = [
        (5300, 450, 30, (51, 255, 51)),
    ]

    while running:
        print(visibility)
        print("cool!")

        clock.tick(60)
        keys = pygame.key.get_pressed()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            lights_off = True
            stamina = False
            weak_grav = False
            strong_grav = False
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            current_temp = start_temp
            spawn_x, spawn_y = 100, 0
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["timer"] = 0  # Reset the timer for all key blocks

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
            stamina = False
            lights_off = True
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["timer"] = 0  # Reset the timer for all key blocks
            death_text = in_game_ice.get("overheat_death_message", "Overheated!")
            wait_time = pygame.time.get_ticks()
            for ice in ice_blocks:
                ice.float_height = ice.initial_height
                ice.rect.height = int(ice.float_height)
        elif current_temp < min_temp:
            player_x, player_y = spawn_x, spawn_y
            if not is_mute:
                freeze_sound.play()
            current_temp = start_temp
            stamina = False
            lights_off = True
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["timer"] = 0  # Reset the timer for all key blocks
            death_text = in_game_ice.get("freeze_death_message", "Frozen and malfunctioned!")
            wait_time = pygame.time.get_ticks()            
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
            weak_grav = False
            strong_grav = False
            spawn_x, spawn_y = 3900, 150  # Store checkpoint position
            if not is_mute:
                checkpoint_sound.play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            lights_off = True
            stamina = False
            weak_grav = False
            strong_grav = False
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 5400, 280  # Checkpoint position
            if not is_mute:
                checkpoint_sound.play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            if not is_mute:
                warp_sound.play()

            save_progress(progress)  # Save progress to JSON file

            running = False
            set_page('ice_levels')    

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

        if player_rect.colliderect(light_off_button):
            if not is_mute and lights_off:
                button_sound.play()
            lights_off = False

        timed_coin_text = in_game_ice.get("sikrit", "Secret level... uhm work in progress no spoilers!!")
        rendered_timed_text = font.render(timed_coin_text, True, (0, 0, 0))
        screen.blit(rendered_timed_text, (0 - camera_x, -80 - camera_y))
        timed_coin_text_2 = in_game_ice.get("sikrit_2", "at least this game isnt mainstream... YET.")
        rendered_timed_text_2 = font.render(timed_coin_text_2, True, (0, 0, 0))
        screen.blit(rendered_timed_text_2, (-20 - camera_x, -30 - camera_y))
        ice_friendly = in_game_ice.get("ice_friendly", "Here's a ice block in case you need it!")
        ice_friendly_text = font.render(ice_friendly, True, (0, 0, 0))
        screen.blit(ice_friendly_text, (-450 - camera_x, 80 - camera_y))
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

            # Horizontal collisions
                    elif player_x + img_width > block.x and player_x < block.x + block.width:
                        if player_x < block.x:
                            player_x = block.x - img_width
                        elif player_x + img_width > block.x + block.width:
                            player_x = block.x + block.width

        for pair in key_block_pairs_timed:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            key_rect = pygame.Rect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)

            if player_rect.colliderect(key_rect):
                if not pair["collected"]:
                    pair["locked_time"] = pygame.time.get_ticks()
                    pair["collected"] = True
                    if not is_mute:
                        open_sound.play()

            # Draw key and block only if not collected
            if not pair["collected"]:
                pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)
                pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

            # Reset after duration
            if pair["locked_time"] is not None:
                if pair["collected"] and (pygame.time.get_ticks() - pair["locked_time"]) > pair["duration"]:
                    pair["collected"] = False
                    pair["locked_time"] = None  # Reset timer
                    # Check if player is inside block when it reappears
            
                    if player_rect.colliderect(pair["block"]):
                        hit_sound.play()
                        deathcount += 1
                        stamina = False  # Reset stamina status
                        lights_off = True
                        weak_grav = False
                        strong_grav = False
                        player_x, player_y = spawn_x, spawn_y
                        for pair in key_block_pairs:
                            pair["collected"] = False  # Reset the collected status for all keys
                        for pair in key_block_pairs_timed:
                            pair["collected"] = False  # Reset the collected status for all keys
                            pair["timer"] = 0  # Reset the timer for all key blocks
                        velocity_y = 0  # Reset vertical speed
                        wait_time = pygame.time.get_ticks()  # Start the wait time
                        death_text = in_game_ice.get("crushed_message", "Crushed!")

        for pair in key_block_pairs_timed:
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

        if player_x > 400:
            screen.blit(ice_robo, (ice_robo_x - camera_x, ice_robo_y - camera_y))
        else:
            screen.blit(ice_robo, (ice_robo_x, ice_robo_y))

        pygame.draw.rect(screen, (96, 96, 96), (0, 0, 300 , 130 ))
        pygame.draw.rect(screen, (96, 96, 96), (SCREEN_WIDTH // 2 - 80, 0, 160 , 70))
        pygame.draw.rect(screen, (96, 96, 96), (SCREEN_WIDTH - 250, 0, 250 , 80 ))

        levels = load_language(lang_code).get('levels', {})
        lvl_text = levels.get("lvl13", "Level 13")  # Render the level text
        rendered_lvl_text = font.render(lvl_text, True, (255, 255, 255))
        screen.blit(rendered_lvl_text, (SCREEN_WIDTH //2 - rendered_lvl_text.get_width() // 2, 20)) # Draws the level text

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(font.render(deaths_val, True, (255, 255, 255)), (20, 20))

        temp_val = in_game_ice.get("temp", "Temperature: {current_temp}").format(current_temp=current_temp)
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

        # DEATH LOGICS
        for block in moving_block:
            if block['width'] < 100:
                laser_rect = pygame.Rect(block['x'], block['y'] + block['height'] +10, block['width'], 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block['x'] + 4, block['y'] + block['height'] + 5, block['width'] - 8 , 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground and player_x != block['x']:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = in_game.get("hit_message", "Hit on the head!")
                stamina = False  # Reset stamina status
                lights_off = True
                weak_grav = False
                strong_grav = False
                if not is_mute:    
                    hit_sound.play()
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                wait_time = pygame.time.get_ticks()  # Start the wait time
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
                stamina = False  # Reset stamina status
                lights_off = True
                weak_grav = False
                strong_grav = False
                    # Trigger death logic
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                velocity_y = 0
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
                stamina = False  # Reset stamina status
                lights_off = True
                weak_grav = False
                strong_grav = False
                velocity_y = 0
                    # Trigger death logic
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()
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
                stamina = False  # Reset stamina status
                lights_off = True
                weak_grav = False
                strong_grav = False
                velocity_y = 0
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                if not is_mute:
                    death_sound.play()
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
                stamina = False  # Reset stamina status
                lights_off = True
                weak_grav = False
                strong_grav = False
                velocity_y = 0
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                if not is_mute:
                    death_sound.play()
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
                death_text = in_game.get("hit_message", "Hit on the head!")
                stamina = False
                lights_off = True
                if not is_mute:    
                    hit_sound.play()
                for pair in key_block_pairs:
                    pair["collected"] = False  # Reset the collected status for all keys
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                velocity_y = 0
                wait_time = pygame.time.get_ticks()  # Start the wait time
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
                    stamina = False  # Reset stamina status
                    lights_off = True
                    weak_grav = False
                    strong_grav = False
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    wait_time = pygame.time.get_ticks()  # Start the wait time
                    if not is_mute:
                        death_sound.play()
                    for pair in key_block_pairs:
                        pair["collected"] = False  # Reset the collected status for all keys
                    for pair in key_block_pairs_timed:
                        pair["collected"] = False  # Reset the collected status for all keys
                        pair["timer"] = 0  # Reset the timer for all key blocks
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
                    wait_time = pygame.time.get_ticks()  # Start the wait time
                    if not is_mute:
                        death_sound.play()
                    for pair in key_block_pairs:
                        pair["collected"] = False  # Reset the collected status for all keys
                    for pair in key_block_pairs_timed:
                        pair["collected"] = False  # Reset the collected status for all keys
                        pair["timer"] = 0  # Reset the timer for all key blocks
                    velocity_y = 0
                    deathcount += 1
                    stamina = False  # Reset stamina status
                    lights_off = True
                    weak_grav = False
                    strong_grav = False
                    collision_detected = True  # Set the flag to stop further checks
                    for ice in ice_blocks:
                        ice.float_height = ice.initial_height
                        ice.rect.height = int(ice.float_height)
                    break

        if player_y > 1100:
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()  # Start the wait time
            stamina = False  # Reset stamina status
            lights_off = True
            weak_grav = False
            strong_grav = False
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["timer"] = 0  # Reset the timer for all key blocks
            if not is_mute:    
                fall_sound.play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            for ice in ice_blocks:
                ice.float_height = ice.initial_height
                ice.rect.height = int(ice.float_height)

        # Player Image
        if player_x > 400:
         if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
         elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
         else:
            screen.blit(player_img, (player_x - camera_x, player_y - camera_y))
        else:
         if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x , player_y - camera_y ))  # Draw the moving block image
         elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x , player_y - camera_y))  # Draw the moving block image
         else:
            screen.blit(player_img, (player_x, player_y - camera_y))

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(font.render(death_text, True, (255, 0 ,0)), (20, 80))
            else:
                wait_time = None


        if visibility > 0:
         fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
         fade_surface.set_alpha(visibility)
         fade_surface.fill((0, 0, 0))
         screen.blit(fade_surface, (0, 0))
         if fade_time is None:
                     fade_time = pygame.time.get_ticks()
         else:
                    if pygame.time.get_ticks() - fade_time > 1:
                        visibility -= 1
                        fade_time = None

        
        pygame.display.update() 

transition_time = None
is_transitioning = False

# Handle actions based on current page
def handle_action(key):
    global current_page, pending_level, level_load_time, transition, is_transitioning, transition_time,locked_char_sound_played, locked_char_sound_time, news_times
    
    if current_page == 'main_menu':
        if key == "start":
            complete = progress["complete_levels"]
            if complete < 11:
                level_page = "levels"
            else:
                level_page = "ice_levels"
            if not is_transitioning:
                transition.start(level_page)
                transition_time = pygame.time.get_ticks()  # Start the wait time
                is_transitioning = True
                if is_transitioning and transition_time is not None:
                    if pygame.time.get_ticks() - transition_time  > 2000:
                        is_transitioning = False
                        transition_time = None
                        set_page(level_page)
                        
        elif key == "character_select":
            if not is_transitioning:
                transition.start("character_select")
                transition_time = pygame.time.get_ticks()  # Start the wait time
                is_transitioning = True
            if is_transitioning and transition_time is not None:
                if transition_time - pygame.time.get_ticks() > 2000:
                    set_page("character_select")
                    is_transitioning = False
                    transition_time = None
        elif key == "settings":
            open_settings()
            low_detail()
            progress["is_mute"] = is_mute
            save_progress(progress)
        elif key == "quit":
            if not is_transitioning:
                transition.start("quit_confirm")
                transition_time = pygame.time.get_ticks()  # Start the wait time
                is_transitioning = True
            if is_transitioning and transition_time is not None:
                if transition_time - pygame.time.get_ticks() > 2000:
                    set_page("quit_confirm")
                    is_transitioning = False
                    transition_time = None
        elif key == "language":
            if not is_transitioning:
                transition.start("language_select")
                transition_time = pygame.time.get_ticks()  # Start the wait time
                is_transitioning = True
            if is_transitioning and transition_time is not None:
                if transition_time - pygame.time.get_ticks() > 2000:
                    set_page("language_select")
                    is_transitioning = False
                    transition_time = None
        elif key == "news":
            if not is_transitioning:
                transition.start("news")
                transition_time = pygame.time.get_ticks()  # Start the wait time
                is_transitioning = True
            if is_transitioning and transition_time is not None:
                if transition_time - pygame.time.get_ticks() > 2000:
                    set_page("news")
                    is_transitioning = False
                    transition_time = None
    elif current_page == 'language_select':
        if key == "back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()  # Start the wait time
                is_transitioning = True
            if is_transitioning and transition_time is not None:
                if transition_time - pygame.time.get_ticks() > 2000:
                    set_page("main_menu")
                    is_transitioning = False
                    transition_time = None
        elif key in ["en", "fr", "es", "de", "zh_cn", "tr", "pt_br", "ru", "jp", "id", "kr", "it"]:
            change_language(key)
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()  # Start the wait time
                is_transitioning = True
            if is_transitioning and transition_time is not None:
                if transition_time - pygame.time.get_ticks() > 2000:
                    set_page("main_menu")
                    is_transitioning = False
                    transition_time = None
    elif current_page == 'levels':
        if key is None:  # Ignore clicks on locked levels
            return
        elif key == "back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()  # Start the wait time
                is_transitioning = True
            if is_transitioning and transition_time is not None:
                if transition_time - pygame.time.get_ticks() > 2000:
                    set_page("main_menu")
                    is_transitioning = False
                    transition_time = None
        elif key == "next":
            buttons.clear()
            set_page("ice_levels")
        else:  # Trigger a level's screen
            if not is_transitioning:
                transition.start(f"{key}_screen")
                transition_time = pygame.time.get_ticks()  # Start the wait time
                is_transitioning = True
            if is_transitioning and transition_time is not None:
                if transition_time - pygame.time.get_ticks() > 2000:
                    set_page(f"{key}_screen")
                    is_transitioning = False
                    transition_time = None
    elif current_page == "ice_levels":
        if key is None:  # Ignore clicks on locked levels
            return
        else:  # Trigger a level's screen
         if not key == "back":
          if not key == "lvl14":
            if not is_transitioning:
                transition.start(f"{key}_screen")
                transition_time = pygame.time.get_ticks()  # Start the wait time
                is_transitioning = True
            if is_transitioning and transition_time is not None:
                if transition_time - pygame.time.get_ticks() > 2000:
                    set_page(f"{key}_screen")
                    is_transitioning = False
                    transition_time = None
          else:
           if not is_mute:
            death_sound.play()
    elif current_page == "quit_confirm":
        if key == "yes":
            quit_game()
        elif key == "no":
            set_page("main_menu")
    elif current_page == "character_select":
        if key == "locked" and not locked_char_sound_played:
         death_sound.play()
         locked_char_sound_played = False
         locked_char_sound_time = time.time()
    elif current_page == "map":
        map()
        


# Start with main menu
set_page('main_menu')
update_locked_levels() # Update locked levels every frame!

# Global variables(only needed before amin loop)!
button_hovered_last_frame = False
last_hovered_key = None
main_menu_hover = None
wait_time = None
disk_mode = True
logo_hover = False
logo_click = False
LDM = False
news_lines = None
image_paths = None
image_surfaces = None
locked_char_sound_time = None
locked_char_sound_played = False
mapped = False
camera_x = 0
map_x = 0
if not is_mute and SCREEN_WIDTH > MIN_WIDTH or SCREEN_HEIGHT > MIN_HEIGHT:
    click_sound.play()

# Main loop
running = True
while running:
    messages = load_language(lang_code).get('messages', {})
    # Clear screen!
    screen.blit(background, (0, 0))
    mouse_pos = pygame.mouse.get_pos()

    if transition_time is not None and pygame.time.get_ticks() - transition_time > 1000:
        transition_time = None
        is_transitioning = False

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
                if current_page != "levels" or current_page != "quit_confirm":
                        if is_locked is not None:
                            for _, rect, key, is_locked in buttons:
                                if rect.collidepoint(event.pos):
                                    if key is not None and not is_mute:
                                        click_sound.play()
                                    handle_action(key)
                                    last_page_change_time = time.time()
                elif current_page == "levels":
                    for rendered, rect, key, is_locked in buttons:
                        if rect.collidepoint(event.pos):
                            if key is not None:
                                handle_action(key)  # Only load level on click!

        if current_page == "map":
            map()
            screen.blit(mappy, (map_x,0))

            keys = pygame.key.get_pressed()
            max_scroll = mappy.get_width() - SCREEN_WIDTH - 60
            if keys[pygame.K_RIGHT] and map_x > -max_scroll:
                map_x -= 24
            elif keys[pygame.K_LEFT] and map_x < 0:
                map_x += 24

        if current_page == "main_menu":

            screen.blit(logo, ((SCREEN_WIDTH // 2 - logo.get_width() // 2), 30))
            screen.blit(logo_text, logo_pos)
            screen.blit(site_text, site_pos)
            screen.blit(credit_text, credit_pos)
            screen.blit(ver_text, ver_pos)
        # Render the main menu buttons
            hovered_key = None
            for rendered, rect, key, is_locked in buttons:
                mouse_pos = pygame.mouse.get_pos()
                if studio_logo_rect.collidepoint(mouse_pos):
                    screen.blit(studio_glow, studio_glow_rect.topleft)
                    if not logo_hover:
                        hover_sound.play()
                        logo_hover = True
                    if event.type == pygame.MOUSEBUTTONDOWN and not logo_click:    
                        if not is_mute:
                            click_sound.play()    
                        webbrowser.open("https://omerarfan.github.io/lilrobowebsite/") 
                        logo_click = True
                else:
                    screen.blit(studio_logo, studio_logo_rect.topleft)
                    logo_hover = False
                    logo_click = False

                if rect.collidepoint(mouse_pos):
                    hovered_key = key
                    button_surface = pygame.Surface(rect.inflate(30, 15).size, pygame.SRCALPHA)
                    button_surface.fill((255, 255, 0, 255))  # RGBA: Hover color
                    screen.blit(button_surface, rect.inflate(30, 15).topleft)
                    pygame.draw.rect(screen, (74, 74, 74), rect.inflate(30, 15), 6)  # Border for hover effect

                    if key == "start":
                        menu_text = font.render("Play the game.", True, (255, 255, 0))
                        screen.blit(menu_text, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT - 50))
                    elif key == "character_select":
                        char_text = font.render("Select your character!", True, (255, 255, 0))
                        screen.blit(char_text, (SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 50))
                    elif key == "settings": 
                        settings_text = font.render("Turn on the audio or turn it off, depending on current mode.", True, (255, 255, 0))
                        screen.blit(settings_text, (SCREEN_WIDTH // 2 - 400, SCREEN_HEIGHT - 50))
                    elif key == "news":
                        news_text = font.render("News and updates about the game!", True, (255, 255, 0))
                        screen.blit(news_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT - 50))
                    elif key == "quit":
                        quit_text = font.render("Exit the game.", True, (255, 255, 0))
                        screen.blit(quit_text, (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT - 50))
                    elif key == "language":
                        lang_text = font.render("Select your language.", True, (255, 255, 0))
                        screen.blit(lang_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT - 50))

                    if hovered_key != last_hovered_key and not is_mute:
                        hover_sound.play()

                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((140, 140, 0, 255))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 0, 0), rect.inflate(30, 15), 6)

                screen.blit(rendered, rect)
            last_hovered_key = hovered_key

        if current_page == "character_select":
         screen.blit(plain_background, (0, 0))

    # Initialize locked sound effect and mouse position
         locked_sound_played = False
         mouse_pos = pygame.mouse.get_pos()

         messages = load_language(lang_code).get('messages', {})  # Fetch localized messages
         char_text = font.render("Select your Robo!", True, (0, 0, 0))
         screen.blit(char_text, (SCREEN_WIDTH // 2 - 100, 50))

    # Check if characters are locked
         robo_unlock = True
         icerobo_unlock = progress.get("icerobo_unlocked", False)
         evilrobo_unlock = progress.get("evilrobo_unlocked", False)
         lavarobo_unlock = progress.get("lavarobo_unlocked", False)
         greenrobo_unlock = progress.get("greenrobo_unlocked", False)
         cakebo_unlock = progress.get("cakebo_unlocked", False)

            # Draw images
         screen.blit(robot_img, robot_rect)     
         screen.blit(evilrobot_img if evilrobo_unlock else locked_img, evilrobot_rect)
         screen.blit(icerobot_img if icerobo_unlock else locked_img, icerobot_rect)
         screen.blit(lavarobot_img if lavarobo_unlock else locked_img, lavarobot_rect)
         screen.blit(greenrobot_img if greenrobo_unlock else locked_img, greenrobot_rect)
         screen.blit(cakebot_img if cakebo_unlock else locked_img, cakebot_rect)

     # Draw a highlight border around the selected character
         highlight_colors = {
          "robot": (63, 72, 204),
          "evilrobot": (128, 0, 128),
          "icerobot": (51, 254, 255),
          "lavarobot": (136, 0, 21),
          "greenrobot": (25, 195, 21),
          "cakebot": (255, 171, 204)
         }
         
         rects = {
          "robot": robot_rect,
          "evilrobot": evilrobot_rect,
          "icerobot": icerobot_rect,
          "lavarobot": lavarobot_rect,
          "greenrobot": greenrobot_rect,
          "cakebot": cakebot_rect
         }
        
         if selected_character in rects:
          pygame.draw.rect(screen, highlight_colors[selected_character], rects[selected_character].inflate(5, 5), 5)

            # --- Use MOUSEBUTTONDOWN instead of continuous mouse.get_pressed ---
         for event in pygame.event.get():
           if event.type == pygame.QUIT:
            set_page("quit_confirm")

           elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if robot_rect.collidepoint(mouse_pos):
                try_select_robo(robo_unlock, "robot", robot_rect, "placeholder", "Imagine if this actually popped up in game BRO-")
            elif evilrobot_rect.collidepoint(mouse_pos):
                try_select_robo(evilrobo_unlock, "evilrobot", evilrobot_rect, "evillocked_message", "Encounter this robot in an alternative route to unlock him!")
            elif icerobot_rect.collidepoint(mouse_pos):
                try_select_robo(icerobo_unlock, "icerobot", icerobot_rect, "icelock_message", "This robot is hiding in the mountains...")
            elif lavarobot_rect.collidepoint(mouse_pos):
                try_select_robo(lavarobo_unlock, "lavarobot", lavarobot_rect, "lavalocked_message", "This robot is coming soon!")
            elif greenrobot_rect.collidepoint(mouse_pos):
                try_select_robo(greenrobo_unlock, "greenrobot", greenrobot_rect, "greenlocked_message", "Get GOLD rank in all Green World Levels to unlock this robot!")
            elif cakebot_rect.collidepoint(mouse_pos):
                try_select_robo(cakebo_unlock, "cakebot", cakebot_rect, "cakelocked_message", "Happy 2 month anniversary!")
            elif rect.collidepoint(mouse_pos):
                set_page("main_menu")
                if not is_mute:
                    click_sound.play()

         keys = pygame.key.get_pressed()
         if keys[pygame.K_ESCAPE]:
            set_page("main_menu")

    # Display locked message for 5 seconds
         if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 5000:
             rendered_locked_text = font.render(locked_text, True, (255, 255, 0))
             screen.blit(rendered_locked_text, ((SCREEN_WIDTH // 2 - rendered_locked_text.get_width() // 2), SCREEN_HEIGHT - 700))
            else:
             wait_time = None

    # Render buttons
         for rendered, rect, key, is_locked in buttons:
            hovered = rect.collidepoint(mouse_pos)
            button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
            if hovered:
             button_surface.fill((200, 200, 250, 100))
             if not button_hovered_last_frame and not is_mute:
                hover_sound.play()
             button_hovered_last_frame = True
            else:
             button_surface.fill((153, 51, 255, 0))
             button_hovered_last_frame = False
            screen.blit(button_surface, rect.inflate(20, 10).topleft)
            screen.blit(rendered, rect)


        if current_page == "language_select":
            screen.blit(plain_background, (0, 0))
            screen.blit(heading_text, (SCREEN_WIDTH // 2 - heading_text.get_width() // 2, 50))

        if current_page == "quit_confirm":
            screen.blit(plain_background, (0, 0))
            # Render the quit confirmation text
            screen.blit(quit_text, quit_text_rect)
            screen.blit(icerobot_img, (SCREEN_WIDTH // 2 - icerobot_img.get_width() // 2, SCREEN_HEIGHT // 2 - 200))

            # Render the "Yes" and "No" buttons
            for rendered, rect, key, is_locked in buttons:
                if rect.collidepoint(mouse_pos):
                    button_surface = pygame.Surface(rect.inflate(30, 15).size, pygame.SRCALPHA)
                    button_surface.fill((255, 255, 0, 255))  # RGBA: Hover color
                    screen.blit(button_surface, rect.inflate(30, 15).topleft)
                    pygame.draw.rect(screen, (74, 74, 74), rect.inflate(30, 15), 6)
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)      
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered
                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((140, 140, 0, 255))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 0, 0), rect.inflate(30, 15), 6)
                screen.blit(rendered, rect)

            # Allow returning to the main menu with ESC
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                set_page("main_menu")

        elif current_page == "news":
            if news_lines is None or image_paths is None:
                news_lines, image_paths = fetch_news_html_and_convert()
                image_surfaces = []
                for path in image_paths:
                  print(" Loading image:", path)
                  try:
                     img = pygame.image.load(path).convert_alpha()
                     img = pygame.transform.scale(img, (250, 250))
                     image_surfaces.append(img)
                     print(" Loaded:", path)
                  except Exception as e:
                    print(" Failed to load:", path, e)

            screen.fill((20, 20, 20))

            title = font.render(current_lang.get("news", "News"), True, (255, 255, 255))
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

            y = 120

            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                set_page("main_menu")


        # Draw text
            for line in news_lines:
             rendered = font.render(line, True, (200, 200, 200))
             screen.blit(rendered, (80, y))
             y += 28

            # Draw images BELOW text
            for img in image_surfaces: # type: ignore
                screen.blit(img, (80, y))
                y += img.get_height() + 20


        elif current_page == "lvl1_screen":
            # Render the Level 1 screen
            create_lvl1_screen()

        elif current_page == "lvl2_screen":
            create_lvl2_screen()
    
        elif current_page == "lvl3_screen":
            create_lvl3_screen()

        elif current_page == "lvl4_screen":
            create_lvl4_screen()

        elif current_page == "lvl5_screen":
            create_lvl5_screen()

        elif current_page == "lvl6_screen":
            create_lvl6_screen()

        elif current_page == "lvl7_screen":
            create_lvl7_screen()

        elif current_page == "lvl8_screen":
            create_lvl8_screen()

        elif current_page == "lvl9_screen":
            create_lvl9_screen()

        elif current_page == "lvl10_screen":
            create_lvl10_screen()

        elif current_page == "lvl11_screen":
            create_lvl11_screen()

        elif current_page == "lvl12_screen":
            create_lvl12_screen()

        elif current_page == "lvl13_screen":
            create_lvl13_screen()      

        elif current_page == "levels":
            screen.blit(green_background, (0, 0))

            # Fetch the localized "Select a Level" text dynamically
            select_text = current_lang.get("level_display", "Select a Level")
            rendered_select_text = font.render(select_text, True, (255, 255, 255))
            select_text_rect = rendered_select_text.get_rect(center=(SCREEN_WIDTH // 2, 50))

            # Draw the "Select a Level" text
            screen.blit(rendered_select_text, select_text_rect)

            # Render buttons for levels

            for rendered, rect, key, is_locked in buttons:
                if rect.collidepoint(mouse_pos):
                    if key is not None:
                        # Unlocked level
                        screen.blit(greendisk_img, rect)
                    else:
                        screen.blit(lockeddisk_img, rect)
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered
            # SHow Level stats
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                for text_surface, disk_rect, key, is_locked in buttons:
                    if disk_rect.collidepoint(event.pos):
                        if key != "next" and key != "back" and not is_locked:
                            hs = progress['score'][key]
                            high_text = messages.get("hs_m", "Highscore: {hs}").format(hs=hs)
                            lvl_time_text = font.render(high_text, True, (255, 255, 0))

                            # Adjust position as needed
                            screen.blit(lvl_time_text, (SCREEN_WIDTH // 2 - lvl_time_text.get_width() // 2, SCREEN_HEIGHT - 50))
                            s = key
                            num = int(s[3:])  # Skip the first 3 characters
                            print(num)  # Output: 13
                            stars = get_stars(num, progress['score'][key])
                            if stars >= 1:
                                screen.blit(s_star_img, (SCREEN_WIDTH // 2 - 25, SCREEN_HEIGHT - 80))
                            if stars >= 2:
                                screen.blit(s_star_img, (SCREEN_WIDTH // 2 , SCREEN_HEIGHT - 80))
                            if stars == 3:
                                screen.blit(s_star_img, (SCREEN_WIDTH // 2 + 25, SCREEN_HEIGHT - 80))

                    else:    
                        if key is not None:
                            # Unlocked level
                            screen.blit(greendisk_img, rect)
                        else:
                            screen.blit(lockeddisk_img, rect)
                        text_rect = text_surface.get_rect(center=(disk_rect.x + 50, disk_rect.y + 50))
                        screen.blit(text_surface, text_rect)
            
            for text_surface, disk_rect, key, is_locked in buttons: 
                if key is not None:
                    screen.blit(greendisk_img, disk_rect)
                else:
                    screen.blit(lockeddisk_img, disk_rect)
                text_rect = text_surface.get_rect(center=(disk_rect.x + 50, disk_rect.y + 50))
                screen.blit(text_surface, text_rect)

        elif current_page == "ice_levels":
            if LDM:
                screen.fill((0, 146, 230))
            else:
                screen.blit(ice_background, (0, 0))
                        
            # Fetch the localized "Select a Level" text dynamically
            select_text = current_lang.get("level_display", "Select a Level")
            rendered_select_text = font.render(select_text, True, (0, 0, 0))
            select_text_rect = rendered_select_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            screen.blit(rendered_select_text, select_text_rect)

            if not LDM:
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
            
            for rendered, rect, key, is_locked in buttons:
                if rect.collidepoint(mouse_pos):
                    if key is not None:
                         # Unlocked level
                        screen.blit(icedisk_img, rect)
                    else:
                        screen.blit(lockeddisk_img, rect)
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered

    # Render buttons for ice world levels
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                for text_surface, disk_rect, key, is_locked in buttons:
                    if disk_rect.collidepoint(event.pos):
                        if not key == "back" and not is_locked:
                            hs = progress['score'][key]
                            high_text = messages.get("hs_m", "Highscore: {hs}").format(hs=hs)
                            lvl_time_text = font.render(high_text, True, (255, 255, 0))
                            # Adjust position as needed
                            screen.blit(lvl_time_text, (SCREEN_WIDTH // 2 - lvl_time_text.get_width() // 2, SCREEN_HEIGHT - 50))
                            s = key
                            num = int(s[3:])  # Skip the first 3 characters
                            stars = get_stars(num, progress['score'][key])
                            if stars >= 1:
                                screen.blit(s_star_img, (SCREEN_WIDTH // 2 - 25, SCREEN_HEIGHT - 80))
                            if stars >= 2:
                                screen.blit(s_star_img, (SCREEN_WIDTH // 2 , SCREEN_HEIGHT - 80))
                            if stars == 3:
                                screen.blit(s_star_img, (SCREEN_WIDTH // 2 + 25, SCREEN_HEIGHT - 80))
                        elif key == "back" and (pygame.mouse.get_pressed()[0]):
                            set_page("levels")
                    else:    
                        if key is not None:
                            # Unlocked level
                            screen.blit(icedisk_img, rect)
                        else:
                            screen.blit(lockeddisk_img, rect)
                        text_rect = text_surface.get_rect(center=(disk_rect.x + 50, disk_rect.y + 50))
                        screen.blit(text_surface, text_rect)
            
            for text_surface, disk_rect, key, is_locked in buttons: 
                if key is not None:
                    screen.blit(icedisk_img, disk_rect)
                else:
                    screen.blit(lockeddisk_img, disk_rect)
                text_rect = text_surface.get_rect(center=(disk_rect.x + 50, disk_rect.y + 50))
                screen.blit(text_surface, text_rect)

        else:
            # Render buttons for other pages
            for rendered, rect, key, is_locked in buttons:
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

        if show_greenrobo_unlocked:
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = font.render("Green Robo Unlocked!", True, (51, 255, 51))
                screen.blit(unlocked_text, (SCREEN_WIDTH // 2 - unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False
        
        if notif:
            if time.time() - notification_time < 4:  # Show for 4 seconds
                screen.blit(notification_text, (SCREEN_WIDTH // 2 - notification_text.get_width() // 2, 100))
        else:
            notif = False

        if er:
            if time.time() - notification_time < 4:  # Show for 4 seconds
                screen.blit(error_code, (SCREEN_WIDTH // 2 - error_code.get_width() // 2, 120))
        else:
            er = False
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(cursor_img, mouse_pos)

        if transition.active:
            transition.update()

        pygame.display.flip()

pygame.quit()