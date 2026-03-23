import pygame
import json
import os
import math
import sys
import time
import random
import webbrowser
import copy

from datetime import datetime, date

import level_logic
import menu_ui
import manage_data
import startup

# GAME VERSION
version = "1.3.4.2"

# Initialize audio
pygame.mixer.init()

# Initialize pygame
pygame.init()

# Initializing screen resolution
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

if sys.platform.startswith('linux'):
    os.environ['SDL_VIDEODRIVER'] = 'x11'

pygame.display.set_caption("Roboquix")
MIN_WIDTH, MIN_HEIGHT = 1250, 700

# First of all, LOAD THE DAMN BGGG
bg = pygame.image.load(manage_data.resource_path("bgs/PlainBackground.png")).convert()
bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Load and set window icon
icon = pygame.image.load(manage_data.resource_path("oimgs/icons/icon.png")).convert_alpha()
pygame.display.set_icon(icon)

def change_ambience(new_file):
    global is_mute_amb
    if not is_mute_amb:
     pygame.mixer.music.load(manage_data.resource_path(new_file))
     pygame.mixer.music.set_volume(2)  # Adjust as needed
     pygame.mixer.music.play(-1)

# Variables for handling display notifications
notif = False
er = False

pygame.mouse.set_visible(False)  # Hide the system cursor

# Initalizing Player ID
HEX = "0123456789ABCDEF"

def generate_player_id():
    roll = random.random() * 100  # 0.0 → 100.0

    if roll < 0.001:        # 0.1%
        length = 3
    elif roll < 2.1:     # next 5%
        length = 4
    elif roll < 25:                 # rest
        length = 5
    else:
        length = 6

    return "".join(random.choices(HEX, k=length))

notification_time = None

save_count = 0

is_syncing = False

def draw_notifications():
    global notif, er, notification_time
    if notif:
            if time.time() - notification_time < 4:  # Show for 4 seconds
                screen.blit(notification_text, (SCREEN_WIDTH // 2 - notification_text.get_width() // 2, 100))
    else:
        notif = False

    if er:
        if notification_time is not None and time.time() - notification_time < 4:  # Show for 4 seconds
            screen.blit(error_code, (SCREEN_WIDTH // 2 - error_code.get_width() // 2, 130))
    else:
        er = False

def draw_loading_orb(text_x, text_y, show_time):
        # Calculate the orbit position using current time
        angle_rad = time.time() * 8 
        orbit_radius = 15
        
        # Define the center point for the circle to orbit around
        orbit_center_x = text_x - 30
        orbit_center_y = text_y + 15 # Adjusted to center it vertically with text

        if show_time is None:
          for i in range(3):
            # offset each dot by 0.5 radians so they follow each other
            dot_angle = angle_rad - (i * 0.5) 
            x = orbit_center_x + orbit_radius * math.cos(dot_angle)
            y = orbit_center_y + orbit_radius * math.sin(dot_angle)
            # Make trailing dots smaller or dimmer
            alpha = 255 - (i * 80) 
            pygame.draw.circle(screen, (alpha, alpha, alpha), (int(x), int(y)), 5 - i)

def draw_syncing_status():
    global sync_status, sync_finish_time, is_syncing
    if is_syncing:
        if sync_finish_time is not None:
            if time.time() - sync_finish_time > 1:
                is_syncing = False
                sync_finish_time = None
                return

        # 1. Render and draw the text
        syncing_text = menu_ui.render_text(sync_status, True, (255, 255, 255))
        text_x = SCREEN_WIDTH - syncing_text.get_width() - 10
        text_y = SCREEN_HEIGHT - 60
        screen.blit(syncing_text, (text_x, text_y))
        draw_loading_orb(text_x, text_y, sync_finish_time)

# To handle sync status message output.        
sync_status = ""
sync_finish_time = None

fonts = manage_data.init_fonts()

# Load progress at start
progress_loaded = False
language_loaded = False
sounds_loaded = False
images_loaded = False
running = False

def draw_loading_bar(stage_name, percent):
    screen.blit(bg, (0, 0))
    complete = None
    text = fonts['def'].render(f"{stage_name}", True, (255, 255, 255))
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
    screen.blit(text, text_rect)
    draw_loading_orb(text_rect.x, text_rect.y, complete)
    pygame.draw.rect(screen, (0, 0, 255), (0, SCREEN_HEIGHT - 10, (SCREEN_WIDTH / 100)*percent, 10))
    pygame.display.flip()

ps = 0
while ps < 100:
 # In the loading loop section:
 if not language_loaded:
    stage = "Loading configured settings..."
    draw_loading_bar(stage, ps)
    # NEW: Load from manifest instead of progress
    manifest, lang_code, is_mute, is_mute_amb = manage_data.init_accs()
    ps = 5
    language_loaded = True

 stage = "Checking for latest save..."
 draw_loading_bar(stage, ps)
 if not progress_loaded and language_loaded:
    progress = manage_data.load_progress(); ps = 8
    complete_levels = progress.get("complete_levels", 0); ps += 1
    progress_loaded = True

 if progress_loaded and not sounds_loaded:
  stage = "Loading sounds..."
  draw_loading_bar(stage, ps)
  sounds = startup.init_sounds()
  ps += 25
  sounds_loaded = True
  draw_loading_bar(stage, ps)

 if sounds_loaded and not images_loaded:
    # UI (Logos & Cursors)
    stage = "Loading UI assets..."
    draw_loading_bar(stage, ps)
    ui = startup.init_ui_images(SCREEN_WIDTH, SCREEN_HEIGHT)
    ps += 4

    stage = "Loading backgrounds..."
    draw_loading_bar(stage, ps)
    bgs = startup.init_bgs(SCREEN_WIDTH, SCREEN_HEIGHT)
    ps += 5

    # Medals
    stage = "Loading medals..."
    draw_loading_bar(stage, ps)
    medals = startup.init_medals()
    ps += 4

    # Disks
    stage = "Loading disks..."
    draw_loading_bar(stage, ps)
    disks = startup.init_disks()
    ps += 3

    # In-game assets (saws, teleporters, badges, checkpoints)
    stage = "Loading in-game assets..."
    draw_loading_bar(stage, ps)
    assets = startup.init_assets()
    ps += 8

    # Characters
    stage = "Loading robos..."
    draw_loading_bar(stage, ps)
    robos = startup.init_robos()
    ps += 6
    images_loaded = True

    if is_mute_amb:
        pygame.mixer.music.stop()
    else:
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play(-1)  # Loop forever
 else:
     ps = 100
     draw_loading_bar(stage, ps)
 
 pygame.display.flip()

if ps == 100:
 running = True

with open(manage_data.resource_path("data/thresholds.json"), "r", encoding="utf-8") as f:
    thresholds_data = json.load(f)
    level_thresholds = thresholds_data["level_thresholds"]
    score_thresholds = thresholds_data["score_thresholds"]
    
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

def create_achieve_screen():
    global current_lang
    buttons.clear()
    current_lang = manage_data.load_language(lang_code, manifest)
    # 1. Load the sections with fallback to the root dictionary
    # This covers both nested: current_lang["achieve"]["zen_os"] 
    # and flat: current_lang["zen_os"]
    ach_data = current_lang.get("achieve", {}) 
    header_data = current_lang.get("main_menu", {})
    back_data = current_lang.get("language_select", {})

    # 1. Render Main Header
    ach_txt = header_data.get("achievements", "Achievements")
    ach_header = menu_ui.render_text(ach_txt, True, (255, 255, 255))
    screen.blit(ach_header, (SCREEN_WIDTH // 2 - ach_header.get_width() // 2, 50))

    ach_list = [
        "zen_os",
        "zen_os_desc",
        "speedy_starter", 
        "speedy_starter_desc",
        "over_9k",
        "over_9k_desc",
        "chase_escape",
        "chase_escape_desc",
        "golden", 
        "golden_desc",
        "lv20", 
        "lv20_desc"
    ]

    y_offset = 120 
    
    count = 0

    for title_key in ach_list:
        # We try to get from ach_data first, then fallback to current_lang directly
        title_str = ach_data.get(title_key, "?")

        # Render Title
        if title_key[-5:] != "_desc":
         if progress["achieved"][title_key]:
           color = (0, 204, 0)
         else:
           color = (255, 255, 0)

        title_surf = menu_ui.render_text(title_str, True, color)
        if lang_code == "ar" or lang_code == "pk":
            x_pos = SCREEN_WIDTH - 100 - title_surf.get_width()
        else:
            x_pos = 100
        screen.blit(title_surf, (x_pos, y_offset))

        count += 1
        if count % 2 == 0:
           y_offset += 52
        else:
           y_offset += 25

    back_text = back_data.get("back", "Back")
    rendered_back = menu_ui.render_text(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
    buttons.append((rendered_back, back_rect, "back", False))

class Achievements:
    @staticmethod
    def get_notif_text(ach_key, default_name):
        # Helper to build the 'Achievement Unlocked: Name' string
        lang = manage_data.change_language(lang_code, manifest, progress)
        ach_data = lang.get("achieve", {})
        
        # Get "Achievement Unlocked:" prefix
        prefix = ach_data.get("unlock", "Achievement unlocked:")
        # Get the specific name (e.g., "Speedy Starter!")
        name = ach_data.get(ach_key, default_name)
        
        # Combine them and render
        full_string = f"{prefix} {name}"
        return menu_ui.render_text(full_string, True, (255, 255, 0))

    def lvl1speed(ctime):
        global notification_text, notification_time, notif
        unlock = progress["achieved"].get("speedy_starter", False)
        if ctime <= 4.5 and not unlock:
            progress["achieved"]["speedy_starter"] = True  
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("speedy_starter", "Speedy Starter")
            if not is_mute:
                sounds['notify'].play()
            if notification_time is None:
                notif = True
                notification_time = time.time()
    
    def perfect6(ctime, deaths):
        global notification_text, notification_time, notif
        unlock = progress["achieved"].get("zen_os", False)
        if ctime <= 30 and deaths <= 0 and not unlock:
            progress["achieved"]["zen_os"] = True
            progress["char"]["ironrobo"] = True
            manage_data.save_progress(progress)
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("zen_os", "Zenith of Six")
            if not is_mute:
                sounds['notify'].play()
            if notification_time is None:
                notif = True
                notification_time = time.time()

    def lvl90000(score):
        global notification_text, notification_time, notif
        unlock = progress["achieved"].get("over_9k", False)
        if score >= 105000 and not unlock:
            progress["achieved"]["over_9k"] = True          
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("over_9k", "It's over 9000!!")
            if not is_mute:
                sounds['notify'].play()
            if notification_time is None:
                notif = True
                notification_time = time.time()
    
    def evilchase():
        global notification_text, notification_time, notif
        unlock = progress["achieved"].get("chase_escape", False)
        if not unlock:
            progress["achieved"]["chase_escape"] = True
            progress["char"]["evilrobo"] = True
            manage_data.save_progress(progress)
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("chase_escape", "Chased and Escaped")
            if not is_mute:
                sounds['notify'].play()
            if notification_time is None:
                notif = True
                notification_time = time.time()
    
    def check_green_gold():
        global notification_text, notification_time, notif
        all_gold = all(progress["lvls"]["medals"][f"lvl{i}"] in ["Gold", "Diamond"] for i in range(1, 7))
        unlock = progress["achieved"].get("golden", False)
        if all_gold and not unlock:        
            progress["achieved"]["golden"] = True
            progress["char"]["greenrobo"] = True
            manage_data.save_progress(progress)
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("golden", "Golden!")
            if not is_mute:
                sounds['notify'].play()
            if notification_time is None:
                notif = True
                notification_time = time.time()
    
    def check_xplvl20(Level):
        global notification_text, notification_time, notif
        unlock = progress["achieved"].get("lv20", False)
        if Level >= 20 and not unlock:
            progress["achieved"]["lv20"] = True
            manage_data.save_progress(progress)
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("lv20", "XP Collector!")
            if not is_mute:
                sounds['notify'].play()
            if notification_time is None:
                notif = True
                notification_time = time.time()
        
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

        if self.direction == 1 and self.x >= -50:
            self.x = 0
            # Switch page when screen is fully covered
            pygame.event.wait(10)
            set_page(self.target_page)
            self.direction = -2  # Start sliding out

        elif self.direction == -2 and self.x >= self.screen.get_width():
            self.active = False  # Done with transition

        # Draw the image
        self.screen.blit(self.image, (self.x, 0))

transition = TransitionManager(screen, bgs['trans'])

current_lang = manage_data.change_language(lang_code, manifest, progress)
# Page states
current_page = 'main_menu'
buttons = []

def create_main_menu_buttons():

    global current_lang, buttons
    current_lang = manage_data.load_language(lang_code, manifest).get('main_menu', {})
    buttons.clear()
    button_texts = ["start", "achievements", "character_select", "settings", "quit"]

    # Center buttons vertically and horizontally
    button_spacing = 72
    start_y = (SCREEN_HEIGHT // 2) - (len(button_texts) * button_spacing // 2) + 150

    for i, key in enumerate(button_texts):
        text = current_lang[key]
        rendered = menu_ui.render_text(text, True, (255, 255, 255))
        rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * button_spacing)) 
        buttons.append((rendered, rect, key, False))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            set_page("quit_confirm")


def create_language_buttons():
    global current_lang, buttons, heading_text
    current_lang = manage_data.load_language(lang_code, manifest).get('language_select', {})
    buttons.clear()
    start = manage_data.load_language(lang_code, manifest).get('main_menu', {})

    language_options = [
        ("English", "en"),
        ("Français", "fr"),
        ("Español", "es"),
        ("Deutsch", "de"),
        ("Türkçe", "tr"),
        ("Bahasa Indonesia", "id"),
        ("Русский", "ru"),
        ("简体中文", "zh_cn"),
        ("日本語", "jp"),
        ("한국인", "kr"),
        ("اردو", "pk"),
        ("العربية", "ar"),
    ]
    buttons_per_row = 4
    spacing_x = 200
    spacing_y = 70

    # Calculate starting positions to center the grid
    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (SCREEN_WIDTH - grid_width) // 2
    start_y = (SCREEN_HEIGHT // 2) - (len(language_options) // buttons_per_row * spacing_y // 2)

    heading = start.get("language", "Change Language")
    heading_text = menu_ui.render_text(heading, True, (255 , 255, 255))

    for i, (display_name, code) in enumerate(language_options):
        text = display_name
        rendered = menu_ui.render_text(text, True, (255, 255, 255))

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
    rendered_back = menu_ui.render_text(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(SCREEN_WIDTH // 2, y + spacing_y + 40))
    buttons.append((rendered_back, back_rect, "back", False))

def worlds():
    global current_lang, buttons
    buttons.clear()
    current_lang = manage_data.load_language(lang_code, manifest).get('language_select', {})
    screen.blit(bgs['plain'], (0, 0))

    # 1. Define Positions
    # We define the center points so the image and the button hitbox align perfectly
    green_center = (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2)
    mech_center = (SCREEN_WIDTH // 2 + 250, SCREEN_HEIGHT // 2)

    # 2. Draw the Disks
    # Use the rect to blit so the image is centered on our coordinates
    green_rect = disks['green'].get_rect(center=green_center)
    mech_rect = disks['mech'].get_rect(center=mech_center)
    
    screen.blit(disks['green'], green_rect)
    screen.blit(disks['mech'], mech_rect)

    # 3. Add Disks to the Button List
    # Format: (surface/image, rect, action_key, is_locked)
    buttons.append((disks['green'], green_rect, "levels", False))
    buttons.append((disks['mech'], mech_rect, "mech_levels", False))

    # --- Back Button Logic ---
    back_text = current_lang.get("back", "Back")        
    rendered_back = menu_ui.render_text(back_text, True, (255, 255, 255))

    back_rect = pygame.Rect(0, 0, rendered_back.get_width(), rendered_back.get_height())
    back_rect.center = (SCREEN_WIDTH // 2 , SCREEN_HEIGHT - 200)

    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    # Add the back button
    buttons.append((rendered_back, back_rect, "back", False))

def green_world_buttons():
    global current_lang, buttons
    buttons.clear()

    # Store the rendered text and its position for later drawing
    global text_rect, level_key

    level_options = ["lvl1", "lvl2", "lvl3", "lvl4", "lvl5", "lvl6"]
    level_no = ["1", "2", "3", "4", "5", "6"]
    buttons_per_row = 3
    spacing_x = 160
    spacing_y = 160

    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (SCREEN_WIDTH - grid_width) // 2
    start_y = ((SCREEN_HEIGHT // 2) - ((len(level_options) // buttons_per_row) * spacing_y // 2)) + 50

    for i, level in enumerate(level_options):
        col = i % buttons_per_row
        row = i // buttons_per_row
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        is_locked = level in progress["lvls"]["locked_levels"]
        text_surface = fonts['mega'].render(level_no[i], True, (255, 255, 255))
        disk_rect = disks['green'].get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = menu_ui.render_text(back_text, True, (255, 255, 255))

    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.Rect(SCREEN_WIDTH // 2 - rendered_back.get_width() // 2, SCREEN_HEIGHT - 175, 100, 100)
    back_rect.center = (SCREEN_WIDTH // 2 , SCREEN_HEIGHT - 200)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))

    next_text = current_lang.get("next", "next")
    rendered_next = menu_ui.render_text(next_text, True, (255, 255, 255))

    next_rect = pygame.Rect(0, 0, 100, 100)
    next_rect.center = (SCREEN_WIDTH - 90, SCREEN_HEIGHT // 2)

    text_rect = rendered_next.get_rect(center=next_rect.center)
    screen.blit(rendered_next, text_rect)

def mech_world_buttons():
    global current_lang, buttons
    buttons.clear()

    # Store the rendered text and its position for later drawing
    global text_rect, level_key

    level_options = ["lvl7", "lvl8", "lvl9", "lvl10", "lvl11", "lvl12"]
    level_no = ["7", "8", "9", "10", "11", "12"]
    buttons_per_row = 3
    spacing_x = 160
    spacing_y = 160

    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (SCREEN_WIDTH - grid_width) // 2
    start_y = ((SCREEN_HEIGHT // 2) - ((len(level_options) // buttons_per_row) * spacing_y // 2)) + 50

    for i, level in enumerate(level_options):
        col = i % buttons_per_row
        row = i // buttons_per_row
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        is_locked = level in progress["lvls"]["locked_levels"]
        text_surface = fonts['mega'].render(level_no[i], True, (255, 255, 255))
        disk_rect = disks['mech'].get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = menu_ui.render_text(back_text, True, (255, 255, 255))

    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.Rect(SCREEN_WIDTH // 2 - rendered_back.get_width() // 2, SCREEN_HEIGHT - 175, 100, 100)
    back_rect.center = (SCREEN_WIDTH // 2 , SCREEN_HEIGHT - 200)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))

    next_text = current_lang.get("next", "next")
    rendered_next = menu_ui.render_text(next_text, True, (255, 255, 255))

    next_rect = pygame.Rect(0, 0, 100, 100)
    next_rect.center = (SCREEN_WIDTH - 90, SCREEN_HEIGHT // 2)

    text_rect = rendered_next.get_rect(center=next_rect.center)
    screen.blit(rendered_next, text_rect)

#def load_level(level_id):
#    global current_page, buttons
#
   # Show "Loading..." text
#    screen.fill((30, 30, 30))
#    messages = manage_data.change_language(lang_code, manifest, progress).get('messages', {})  # Reload messages with the current language
#    loading_text = messages.get("loading", "Loading...")
#    rendered_loading = menu_ui.render_text(loading_text, True, (255, 255, 255))
#    loading_rect = rendered_loading.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))  # Center dynamically
#    screen.blit(rendered_loading, loading_rect)
#    pygame.display.flip()

 #   # Short delay to let the user see the loading screen
  #  pygame.time.delay(800)  # 800 milliseconds

    # Now switch the page
   # buttons.clear()

def xp():
    # XP from scores
    scores = progress["lvls"]["score"]
    score_xp = sum(scores.values()) // 1000

    # XP from stars
    stars = 0
    for level in range(1, 13):
        score = scores.get(f"lvl{level}", 0)
        stars += get_stars(level, score)
    star_xp = stars * 20  # 50 XP per star

    # XP from achievements
    achievements = progress["achieved"]  # your achievements dict
    achievement_xp = {
     "speedy_starter": 30,
     "zen_os": 150,
     "over_9k": 150,
     "chase_escape": 25,
     "golden": 200,
     "lvl20": 0,
    }

    # Sum XP for unlocked achievements
    ach_xp = sum(xp for ach, unlocked in achievements.items() if unlocked for name, xp in achievement_xp.items() if ach == name)

    # Total XP
    total_xp = score_xp + ach_xp + star_xp
    progress["player"]["XP"] = total_xp
    def xp_needed(level):
        return int(50 * (1.1 ** (level - 1)))  # or tweak multiplier

    def calculate_level(total_xp):
        level = 1
        xp_left = total_xp
        while xp_left >= xp_needed(level):
            xp_left -= xp_needed(level)
            level += 1
        return level, xp_left

    level, xp_in_level = calculate_level(total_xp)
    progress["player"]["Level"] = level
    Achievements.check_xplvl20(level)
    return level, xp_in_level, xp_needed(level)

#Initialize default character
selected_character = progress["pref"].get("character", manage_data.default_progress["pref"]["character"])

# Get rects and position them
robot_rect = robos['robot'].get_rect(topleft=(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 50))
evilrobot_rect = robos['evilrobot'].get_rect(topleft=(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50))
greenrobot_rect = robos['greenrobot'].get_rect(topleft=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
ironrobot_rect = robos['ironrobot'].get_rect(topleft=(SCREEN_WIDTH // 2 + 150, SCREEN_HEIGHT // 2 - 50))
def character_select():
    global selected_character, set_page, current_page
    
    # Clear screen
    buttons.clear()
    current_lang = manage_data.loadlanguage(lang_code, manifest)['char_select']
    button_texts = ["back"]

    for i, key in enumerate(button_texts):
        text = current_lang[key]
        rendered = menu_ui.render_text(text, True, (255, 255, 255))
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
            elif greenrobot_rect.collidepoint(mouse_pos):
                selected_character = "greenrobot"
                set_page("main_menu")
    pygame.display.flip()


def quit_game(progress):
    draw_syncing_status()
    manage_data.sync_vault_to_cloud(progress)
    pygame.quit()
    sys.exit()

#def go_back():
#    global last_page_change_time
#    last_page_change_time = time.time()  # Track the time when going back
#    set_page('main_menu')

def update_locked_levels():
    all_levels = ["lvl2", "lvl3", "lvl4", "lvl5", "lvl6", "lvl7", "lvl8", "lvl9", "lvl10", "lvl11", "lvl12"]
    # Always start with all levels locked except lvl2 (which unlocks after lvl1 is completed)
    locked = set(all_levels)
    score = progress["lvls"].get("score", {})

    # Unlock levels if the previous level's time is not 0
    for i, lvl in enumerate(all_levels):
        prev_lvl = f"lvl{i+1}"
        if score.get(prev_lvl, 0) != 0:
            locked.discard(lvl)  # Unlock this level

    progress["lvls"]["locked_levels"] = list(locked)
    manage_data.save_progress(progress)

def settings_menu():
    global current_lang, buttons
    # 1. Load language (only once per page change is better, but this works)
    current_lang = manage_data.load_language(lang_code, manifest).get('settings', {})
    setting_lang = manage_data.load_language(lang_code, manifest).get('main_menu', {})
    buttons.clear()
    screen.blit(bgs['plain'], (0, 0))

    # 2. Match these keys EXACTLY to handle_action
    # format: (Display Text, Internal Key)
    button_data = [
        (current_lang["About"], "About"),
        (current_lang["Audio"], "Audio"),
        (current_lang["Account"], "Account"),
        (setting_lang["language"], "Language"),
        (current_lang["Back"], "Back")
    ]

    heading = setting_lang.get("settings", "Settings")
    heading_text = menu_ui.render_text(heading, True, (255 , 255, 255))
    screen.blit(heading_text, (SCREEN_WIDTH // 2 - heading_text.get_width() // 2, 200))

    button_spacing = 72
    start_y = (SCREEN_HEIGHT // 2) - (len(button_data) * button_spacing // 2) + 150

    for i, (display_text, internal_key) in enumerate(button_data):
        rendered = menu_ui.render_text(display_text, True, (255, 255, 255))
        rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * button_spacing)) 
        # Store the internal_key so handle_action knows what was clicked
        buttons.append((rendered, rect, internal_key, False))

    # Mouse pos for hover effects
    mouse_pos = pygame.mouse.get_pos()
    
    for rendered, rect, key, _ in buttons:
        if rect.collidepoint(mouse_pos):
            # Add a small glow for hover feedback
            pygame.draw.rect(screen, (0, 213, 0), rect.inflate(20, 10), 2)
        screen.blit(rendered, rect)

def about_menu():
    global buttons, version
    buttons.clear()
    screen.blit(bgs['plain'], (0, 0))
    settings_lang = manage_data.load_language(lang_code, manifest).get('settings', {})

    title = settings_lang.get("About", "About")
    title_rendered = menu_ui.render_text(title, True, (255, 255, 255))
    screen.blit(title_rendered, (SCREEN_WIDTH // 2 - title_rendered.get_width() // 2, 100))

    site = settings_lang.get("site_credit", "Sound effects used from pixabay.com and edited using Audacity")
    site_text = menu_ui.render_text(site, True, (255, 255, 255))
    site_pos = ((SCREEN_WIDTH // 2 - site_text.get_width() // 2), 200)

    logo = settings_lang.get("logo_credit", "Logo and Backgrounds made with canva.com")
    logo_text = menu_ui.render_text(logo, True, (255, 255, 255))
    logo_pos = ((SCREEN_WIDTH // 2- logo_text.get_width() // 2), 240)

    credit = settings_lang.get("credit_credit", "Made by Omer Arfan")
    credit_text = menu_ui.render_text(credit, True, (255, 255, 255))
    credit_pos = ((SCREEN_WIDTH // 2 - credit_text.get_width() // 2), 280)

    ver = settings_lang.get("version_credit", "Game Version: {version}").format(version=version)
    ver_text = menu_ui.render_text(ver, True, (255, 255, 255))
    ver_pos = ((SCREEN_WIDTH // 2 - ver_text.get_width() // 2), 320)

    thx = settings_lang.get("thanks", "Thank you for playing! You are amazing!")
    thx_text = menu_ui.render_text(thx, True, (0, 255, 0))
    thx_pos = ((SCREEN_WIDTH // 2 - thx_text.get_width() // 2), 400)

    bugs = settings_lang.get("bugs", "If you find any bugs, please report them on the GitHub repository.")
    bugs_text = menu_ui.render_text(bugs, True, (242, 123, 32))
    bugs_pos = ((SCREEN_WIDTH // 2 - bugs_text.get_width() // 2), 440)

    sorry = settings_lang.get("sorry", "Sorry for any inconvenience caused by bugs.")
    sorry_text = menu_ui.render_text(sorry, True, (242, 123, 32))
    sorry_pos = ((SCREEN_WIDTH // 2 - sorry_text.get_width() // 2), 480)

    screen.blit(logo_text, logo_pos)
    screen.blit(site_text, site_pos)
    screen.blit(credit_text, credit_pos)
    screen.blit(ver_text, ver_pos)
    screen.blit(thx_text, thx_pos)
    screen.blit(bugs_text, bugs_pos)
    screen.blit(sorry_text, sorry_pos)

    support_text = settings_lang.get("support", "Support / Report Bugs")
    support_rendered = menu_ui.render_text(support_text, True, (255, 255, 255))
    support_rect = support_rendered.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 122))
    buttons.append((support_rendered, support_rect, "Support", False))

    back_text = settings_lang.get("Back", "Back")
    rendered = menu_ui.render_text(back_text, True, (255, 255, 255))
    rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
    buttons.append((rendered, rect, "Back", False))

def audio_settings_menu():
    global buttons
    buttons.clear()
    screen.blit(bgs['plain'], (0, 0))
    settings_lang = manage_data.load_language(lang_code, manifest).get('settings', {})

    # 1. Draw Title
    title_str = settings_lang.get("Audio", "Audio")
    title_txt = menu_ui.render_text(title_str, True, (255, 255, 255))
    screen.blit(title_txt, (SCREEN_WIDTH // 2 - title_txt.get_width() // 2, 200))
    
    # 2. Sound Buttons (SFX)
    sound_label = settings_lang.get("Sound", "Sound")
    if is_mute:
        # Fetches "Unmute {setting}" and replaces {setting} with "Sound"
        sfx_text_str = settings_lang.get("Unmute", "Unmute {setting}").format(setting=sound_label)
    else:
        # Fetches "Mute {setting}" and replaces {setting} with "Sound"
        sfx_text_str = settings_lang.get("Mute", "Mute {setting}").format(setting=sound_label)
    
    renderedsfx = menu_ui.render_text(sfx_text_str, True, (255, 255, 255))
    rectsfx = renderedsfx.get_rect(center=(SCREEN_WIDTH // 2, 350))
    buttons.append((renderedsfx, rectsfx, "SFX", False)) # Keeping "SFX" as the internal ID for your click handler

    # 3. Ambience Buttons
    amb_label = settings_lang.get("Ambience", "Ambience")
    if is_mute_amb:
        amb_text_str = settings_lang.get("Unmute", "Unmute {setting}").format(setting=amb_label)
    else:
        amb_text_str = settings_lang.get("Mute", "Mute {setting}").format(setting=amb_label)
    
    renderedamb = menu_ui.render_text(amb_text_str, True, (255, 255, 255))
    rectamb = renderedamb.get_rect(center=(SCREEN_WIDTH // 2, 450))
    buttons.append((renderedamb, rectamb, "Ambience", False))

    # 4. Back Button
    back_txt = settings_lang.get("Back", "Back")
    renderedback = menu_ui.render_text(back_txt, True, (255, 255, 255))
    rectback = renderedback.get_rect(center=(SCREEN_WIDTH // 2, 550))
    buttons.append((renderedback, rectback, "Back", False))
    
    # Blit everything to the screen
    screen.blit(renderedsfx, rectsfx)
    screen.blit(renderedamb, rectamb)
    screen.blit(renderedback, rectback)

def muting_sfx():
    global is_mute
    is_mute = not is_mute
    # Save directly to manifest (pass 'progress' so it can see player ID/Level)
    manage_data.update_local_manifest(progress)

def muting_amb():
    global is_mute_amb
    # Toggle the state
    is_mute_amb = not is_mute_amb
    
    # Apply the change to the mixer
    if is_mute_amb:
        pygame.mixer.music.stop()
    else:
        # If your game has a specific music file, trigger it here
        pygame.mixer.music.play(-1) 
        pass
        
    # Save directly to manifest
    manage_data.update_local_manifest(progress)


def update_xp_ui():
    global level, xp_needed, xp_total, XP_text, XP_text2

    level, xp_needed, xp_total = xp()

    if level < 20:
        color = (255, 255, 255)
        XP_text = fonts['mega'].render(str(level), True, color)
        XP_text2 = menu_ui.render_text(f"{xp_needed}/{xp_total}", True, color)
    else:
        color = (225, 212, 31)
        XP_text = fonts['mega'].render(str(level), True, color)
        max_txt = manage_data.load_language(lang_code, manifest).get('messages', {}).get("max_level", "MAX LEVEL!")
        XP_text2 = menu_ui.render_text(max_txt, True, color)    

# Central page switcher
def set_page(page):
    global current_page, current_lang  # Explicitly mark current_page and current_lang as global
    current_page = page

    # Reload the current language data for the new page
    if page == 'main_menu':
        update_xp_ui() # Update XP display when returning to main menu, especially in case of different users.
        current_lang = manage_data.load_language(lang_code, manifest).get('main_menu', {})
        create_main_menu_buttons()
    elif page == "achievements":
        create_achieve_screen()
    elif page == 'character_select':
        character_select()
    elif page == 'language_select':
        current_lang = manage_data.load_language(lang_code, manifest).get('language_select', {})
        create_language_buttons()
    elif page == "worlds":
        worlds()
    elif page == "settings":
        settings_menu()
    elif page == "About":
        about_menu()
    elif page == "Audio":
        audio_settings_menu()
    elif page == "Account":
        create_account_selector()
    elif page == "login_screen":
        show_login_screen()
    elif page == 'levels':
        current_lang = manage_data.load_language(lang_code, manifest).get('levels', {})
        green_world_buttons()
        change_ambience("audio/amb/greenambience.wav")
    elif page == 'mech_levels':
        current_lang = manage_data.load_language(lang_code, manifest).get('levels', {})
        mech_world_buttons()
        change_ambience("audio/amb/mechambience.wav")
    elif page == 'quit_confirm':
        current_lang = manage_data.load_language(lang_code, manifest).get('messages', {})
        create_quit_confirm_buttons()
    elif page == 'lvl1_screen':  # New page for Level 1
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl1_screen()
    elif page == 'lvl2_screen':  # New page for Level 2
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl2_screen()
    elif page == 'lvl3_screen':  # New page for Level 3
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl3_screen()
    elif page == 'lvl4_screen':  # New page for Level 4
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl4_screen()
    elif page == 'lvl5_screen':  # New page for Level 5
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl5_screen()
    elif page == 'lvl6_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl6_screen()
    elif page == 'lvl7_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl7_screen()
    elif page == 'lvl8_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl8_screen()
    elif page == 'lvl9_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl9_screen()
    elif page == 'lvl10_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl10_screen()
    elif page == 'lvl11_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl11_screen()
    elif page == 'lvl12_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        create_lvl12_screen()

def try_select_robo(unlock_flag, char_key, rect, locked_msg_key, fallback_msg):
    if rect.collidepoint(pygame.mouse.get_pos()):
        global wait_time, selected_character, locked_char_sound_time, locked_char_sound_played
        charsel = manage_data.load_language(lang_code, manifest).get('char_select', {})

        if unlock_flag:
            selected_character = char_key
            progress["pref"]["character"] = selected_character
            manage_data.save_progress(progress)
            if not is_mute:
                sounds['click'].play()
        else:
            handle_action("locked")
            if not locked_char_sound_played or time.time() - locked_char_sound_time > 1.5: # type: ignore
                if not is_mute:
                    sounds['death'].play()
                locked_char_sound_time = time.time()
                locked_char_sound_played = True
            if wait_time is None:
                wait_time = pygame.time.get_ticks()
            global locked_text
            locked_text = charsel.get(locked_msg_key, fallback_msg)

def create_quit_confirm_buttons():
    global current_lang, buttons, quit_text, quit_text_rect
    buttons.clear()

    # Get the quit confirmation text from the current language
    messages = manage_data.load_language(lang_code, manifest).get('messages', {})
    confirm_quit = messages.get("confirm_quit", "Are you sure you want to quit?")

    # Store the quit confirmation text for rendering in the main loop
    quit_text = menu_ui.render_text(confirm_quit, True, (255, 255, 255))
    quit_text_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 25))

    # Create "Yes" button
    yes_text = messages.get("yes", "Yes")
    rendered_yes = menu_ui.render_text(yes_text, True, (255, 255, 255))
    yes_rect = rendered_yes.get_rect(center=(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50))
    buttons.append((rendered_yes, yes_rect, "yes", False))

    # Create "No" button
    no_text = messages.get("no", "No")
    rendered_no = menu_ui.render_text(no_text, True, (255, 255, 255))
    no_rect = rendered_no.get_rect(center=(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 + 50))
    buttons.append((rendered_no, no_rect, "no", False))

    pygame.display.flip()  # Update the display to show the quit confirmation screen

def score_calc():
    global current_time, medal, deathcount, score
    global base_score, medal_score, death_score, time_score
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
    global score, display_score, new_hs, hs, stareffects, stars, medal
    global base_score, medal_score, death_score, time_score
    messages = manage_data.load_language(lang_code, manifest).get('messages', {})
    display_score = 0
    star1_p, star2_p, star3_p = False, False, False
    star_time = time.time()
    running = True
    notified = False
    clock = pygame.time.Clock()
    star_channel = pygame.mixer.Channel(2)
    lvl_comp = messages.get("lvl_comp", "Level Complete!")
    old_xp = progress["player"].get("XP", 0)
    rendered_lvl_comp = menu_ui.render_text(lvl_comp, True, (255, 255, 255))
    while running:
        screen.blit(bgs['end'], (0, 0))
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.blit(rendered_lvl_comp, (SCREEN_WIDTH // 2 - rendered_lvl_comp.get_width() // 2, 50))

        # Animate score
        
        if display_score < score:
          if not is_mute:
            sounds['hover'].play()
          display_score += max(5, (score // 71))
        if stars >= 1 and (time.time() - star_time > 0.5):
                screen.blit(assets['star'], (SCREEN_WIDTH // 2 - 231, 110))
                if not star1_p:
                 for _ in range(40):  # Add some particles at star position
                    stareffects.append(StarParticles(SCREEN_WIDTH // 2 - 230 + assets['star'].get_width() // 2, 110 + assets['star'].get_height() // 2)) 
                 if not is_mute:
                  star_channel.play(sounds['star1'])
                star1_p = True
        if stars >= 2 and (time.time() - star_time > 1.5):
                screen.blit(assets['star'], (SCREEN_WIDTH // 2 - 76, 110))
                if not star2_p and star1_p: 
                    for _ in range(40):  # Add some particles at star position
                     stareffects.append(StarParticles(SCREEN_WIDTH // 2 - 75 + assets['star'].get_width() // 2, 110 + assets['star'].get_height() // 2))  
                    if not is_mute:
                     star_channel.play(sounds['star2'])
                    star2_p = True
        if stars >= 3 and (time.time() - star_time  >  2.5):
                screen.blit(assets['star'], (SCREEN_WIDTH // 2 + 79, 110)) 
                if  not star3_p and star2_p: 
                    for _ in range(40):  # Add some particles at star position
                      stareffects.append(StarParticles(SCREEN_WIDTH // 2 + 80 + assets['star'].get_width() // 2, 110 + assets['star'].get_height() // 2)) 
                    if not is_mute:
                     star_channel.play(sounds['star3'])
                    star3_p = True
        if medal != "None":
            screen.blit(medals[medal], (SCREEN_WIDTH // 2 - 200, 300 - medals[medal].get_height() // 2))

        for particle in stareffects[:]:
         particle.update()
         particle.draw(screen)
         if particle.life <= 0:
            stareffects.remove(particle)
        
        if display_score > score:
            display_score = score
        
        score_text = fonts['mega'].render(str(display_score), True, (255, 255, 255))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 300 - score_text.get_height() // 2))

        # Check for XP gained
        xp()
        new_xp = progress["player"].get("XP", 0)
        gain = new_xp - old_xp
        if time.time() - star_time > 3.2:
            xp_text = messages.get("xp_gained", "XP Gained: +{gain}").format(gain=gain)
            xp_render = menu_ui.render_text(xp_text, True, (0, 188, 255))
            screen.blit(xp_render, (SCREEN_WIDTH // 2 - xp_render.get_width() // 2, 350))

        global base_score, medal_score, death_score, time_score

        # Show Breakdown
        if score > 500: 
         if time.time() - star_time > 4:
            break_text = messages.get("breakdown", "BREAKDOWN")
            break_render = menu_ui.render_text(break_text, True, (158, 158, 158))
            screen.blit(break_render, (SCREEN_WIDTH // 2 - break_render.get_width() // 2, 400))
         if time.time() - star_time > 4.2:
            base_text = messages.get("base_score", "Base Score: {bs}").format(bs=base_score)
            base_render = menu_ui.render_text(base_text, True, (158, 158, 158))
            screen.blit(base_render, (SCREEN_WIDTH // 2 - base_render.get_width() // 2, 440))
         if time.time() - star_time > 4.4:
            medal_text = messages.get("medal_score", "Medal score: {ms}").format(ms=-medal_score)
            medal_render = menu_ui.render_text(medal_text, True, (158, 158, 158))
            screen.blit(medal_render, (SCREEN_WIDTH // 2 - medal_render.get_width() // 2, 480))
         if time.time() - star_time > 4.6:   
            death_text = messages.get("death_score", "Death Penalty: {ds}").format(ds=-death_score)
            death_render = menu_ui.render_text(death_text, True, (158, 158, 158))
            screen.blit(death_render, (SCREEN_WIDTH // 2 - death_render.get_width() // 2, 520))
         if time.time() - star_time > 4.8:
            time_text = messages.get("time_score", "Time Penalty: {ts}").format(ts=-time_score)
            time_render = menu_ui.render_text(time_text, True, (158, 158, 158))
            screen.blit(time_render, (SCREEN_WIDTH // 2 - time_render.get_width() // 2, 560))
        else:
            if time.time() - star_time > 4:
             low_text = messages.get("lowest", "Lowest possible score!")
             low_render = menu_ui.render_text(low_text, True, (255, 0, 0))
             screen.blit(low_render, (SCREEN_WIDTH // 2 - low_render.get_width() // 2, 500))
             if time_score > death_score:
                 reason_text = messages.get("time_reason", "You took too long to")
                 reason_text_2 = messages.get("time_reason_2", "complete the level.")
             else:
                 reason_text = messages.get("death_reason", "You died too many times!")
                 reason_text_2 = messages.get("death_reason_2", "")
             reason_render = menu_ui.render_text(reason_text, True, (255, 0, 0))
             screen.blit(reason_render, (SCREEN_WIDTH // 2 - reason_render.get_width() // 2, 540))
             reason_render_2 = menu_ui.render_text(reason_text_2, True, (255, 0, 0))
             screen.blit(reason_render_2, (SCREEN_WIDTH // 2 - reason_render_2.get_width() // 2, 580))

        if time.time() - star_time > 5.5:  # Show for 3.5 seconds
                if new_hs:
                    hs_text = messages.get("new_hs", "New High Score!")
                    new_hs_text = menu_ui.render_text(hs_text, True, (255, 215, 0))
                    screen.blit(new_hs_text, (SCREEN_WIDTH // 2 - new_hs_text.get_width() // 2, 610))
                    if not is_mute and not notified:
                        sounds['hscore'].play()
                        notified = True
                else:
                    high_text = messages.get("hs_m", "Highscore: {hs}").format(hs=hs)
                    hs_text = menu_ui.render_text(high_text, True, (158, 158, 158))
                    screen.blit(hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 610))
        
        next_left = int(8 - (time.time() - star_time))
        if time.time() - star_time > 9 or keys[pygame.K_SPACE]:
                running = False
        else: 
            # Instead of hardcoded text:
            press_text = messages.get("press_space", "Press the spacebar to")
            p_render = menu_ui.render_text(press_text, True, (158, 158, 158))
            screen.blit(p_render, (SCREEN_WIDTH // 2 - p_render.get_width() // 2, SCREEN_HEIGHT - 60))
            wait_text = messages.get("continue_wait", "continue or wait for {next_left}").format(next_left=next_left)
            w_render = menu_ui.render_text(wait_text, True, (158, 158, 158))
            screen.blit(w_render, (SCREEN_WIDTH // 2 - w_render.get_width() // 2, SCREEN_HEIGHT - 35))

        draw_notifications()
        draw_syncing_status()
        pygame.display.update()
        clock.tick(60)

def char_assets():
    global selected_character, player_img, blink_img, moving_img, moving_img_l, img_width, img_height
    selected_character = progress["pref"].get("character", manage_data.default_progress["pref"]["character"])
    # Load player image
    if selected_character == "robot": 
        player_img = pygame.image.load(manage_data.resource_path(f"char/robot/robot.png")).convert_alpha()
        blink_img = pygame.image.load(manage_data.resource_path(f"char/robot/blinkrobot.png")).convert_alpha()
        moving_img_l = pygame.image.load(manage_data.resource_path(f"char/robot/smilerobotL.png")).convert_alpha() # Resize to fit the game
        moving_img = pygame.image.load(manage_data.resource_path(f"char/robot/smilerobot.png")).convert_alpha() # Resize to fit the game
    elif selected_character == "evilrobot":
        player_img = pygame.image.load(manage_data.resource_path(f"char/evilrobot/evilrobot.png")).convert_alpha()
        blink_img = pygame.image.load(manage_data.resource_path(f"char/evilrobot/blinkevilrobot.png")).convert_alpha()
        moving_img_l = pygame.image.load(manage_data.resource_path(f"char/evilrobot/movevilrobotL.png")).convert_alpha() # Resize to fit the game
        moving_img = pygame.image.load(manage_data.resource_path(f"char/evilrobot/movevilrobot.png")).convert_alpha() # Resize to fit the game
    elif selected_character == "greenrobot":
        player_img = pygame.image.load(manage_data.resource_path(f"char/greenrobot/greenrobot.png")).convert_alpha()
        blink_img = pygame.image.load(manage_data.resource_path(f"char/greenrobot/blinkgreenrobot.png")).convert_alpha()
        moving_img_l = pygame.image.load(manage_data.resource_path(f"char/greenrobot/movegreenrobotL.png")).convert_alpha() # Resize to fit the game
        moving_img = pygame.image.load(manage_data.resource_path(f"char/greenrobot/movegreenrobot.png")).convert_alpha() # Resize to fit the game
    elif selected_character == "ironrobot":
        player_img = pygame.image.load(manage_data.resource_path(f"char/ironrobot/ironrobo.png")).convert_alpha()
        blink_img = pygame.image.load(manage_data.resource_path(f"char/ironrobot/blinkironrobo.png")).convert_alpha()
        moving_img_l = pygame.image.load(manage_data.resource_path(f"char/ironrobot/ironrobomoveL.png")).convert_alpha() # Resize to fit the game
        moving_img = pygame.image.load(manage_data.resource_path(f"char/ironrobot/ironrobomove.png")).convert_alpha() # Resize to fit the game
    img_width, img_height = player_img.get_size()

# For saw images
saw_cache = {}

ctime = None # global only for resetting

def resetting():
    global ctime
    if ctime is None:
        ctime = pygame.time.get_ticks()

# ALgorithm for logic stuff when level is completed
def fin_lvl_logic(lvl):
            global medal, hs, stars, new_hs
            if progress["lvls"]["complete_levels"] < lvl:
                progress["lvls"]["complete_levels"] = lvl

            if not is_mute:
                sounds['warp'].play()

            if current_time < progress["lvls"]["times"][f"lvl{lvl}"] or progress["lvls"]["times"][f"lvl{lvl}"] == 0:
                progress["lvls"]["times"][f"lvl{lvl}"] = round(current_time, 2)
            
            if progress["lvls"]["score"][f"lvl{lvl}"] < 100000:
                progress["lvls"]["medals"][f"lvl{lvl}"] = get_medal(lvl, progress["lvls"]["times"][f"lvl{lvl}"])
            else:
                progress["lvls"]["medals"][f"lvl{lvl}"] = "Diamond"

            medal = get_medal(lvl, current_time)
            if medal == "Gold" and deathcount == 0:
                medal = "Diamond"
                progress["lvls"]["medals"][f"lvl{lvl}"] = medal
            score_calc()
            if progress["lvls"]["score"][f"lvl{lvl}"] < score or progress["lvls"]["score"][f"lvl{lvl}"] == 0:
                progress["lvls"]["score"][f"lvl{lvl}"] = score
                new_hs = True
            if not new_hs:
                hs = progress["lvls"]["score"][f"lvl{lvl}"]
            update_locked_levels()
            stars = get_stars(lvl, score)


def create_lvl1_screen():
    global player_img, screen, complete_levels, is_mute, is_transitioning, transition_time, current_time, medal, deathcount, score
    global new_hs, hs, stars, ctime
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    global x, y, camera_x, camera_y, player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text,spawn_x, spawn_y,  player_rect, on_ground
    char_assets()
    new_hs = False

    buttons.clear()
    screen.blit(bgs['green'], (0, 0))
    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

    wait_time = None
    death_text = None
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
        [(2650, 250), (2700, 200), (2750, 250)],
    ]

    exit_portal = pygame.Rect(2780, 60, 140, 180)
    clock = pygame.time.Clock()

    # Render the texts
    warning_text = in_game.get("warning_message", "Watch out for spikes!")
    rendered_warning_text = menu_ui.render_text(warning_text, True, (255, 0, 0))  # Render the warning text

    up_text = in_game.get("up_message", "Press UP to Jump!")
    rendered_up_text = menu_ui.render_text(up_text, True, (0, 0, 0))  # Render the up text

    exit_text = in_game.get("exit_message", "Exit Portal! Come here to win!")
    rendered_exit_text = menu_ui.render_text(exit_text, True, (0, 73, 0))  # Render the exit text

    moving_text = in_game.get("moving_message", "Not all blocks stay still...")
    rendered_moving_text = menu_ui.render_text(moving_text, True, (128, 0, 128))  # Render the moving text

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text

    pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

    level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)
    
    screen.blit(rendered_up_text, (700 - camera_x, 200 - camera_y))  # Draws the rendered up text
    screen.blit(rendered_warning_text, (1900 - camera_x, 150 - camera_y))  # Draws the rendered warning text
    screen.blit(rendered_moving_text, (1350 - camera_x, 170 - camera_y))  # Draws the rendered moving text
    screen.blit(rendered_exit_text, (2400 - camera_x, 300 - camera_y))  # Draws the rendered exit text

    for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

    draw_notifications()
    draw_syncing_status()

    if transition.x <= -transition.image.get_width():
       while running:
        clock.tick_busy_loop(60)
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
                sounds['jump'].play()
        

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                sounds['move'].play()
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
            death_text = rendered_fall_text
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['fall'].play()
            velocity_y = 0
            deathcount += 1

        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(1)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.lvl1speed(current_time)
            Achievements.check_green_gold()

            manage_data.save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl2_screen')

        # Drawing
        screen.blit(bgs['green'], (0, 0))

        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))
    
        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)

        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            velocity_y = 0
            deathcount += 1

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

        level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)

        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        # Inside the game loop:
        screen.blit(rendered_up_text, (700 - camera_x, 200 - camera_y))  # Draws the rendered up text
        screen.blit(rendered_warning_text, (1900 - camera_x, 150 - camera_y))  # Draws the rendered warning text
        screen.blit(rendered_moving_text, (1350 - camera_x, 170 - camera_y))  # Draws the rendered moving text
        screen.blit(rendered_exit_text, (2400 - camera_x, 300 - camera_y))  # Draws the rendered exit text


        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(1, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)

        if keys[pygame.K_r]:
            resetting()
            if  time.time() - ctime > 3:
                ctime = None
                start_time = time.time()
                current_time = 0
                spawn_x, spawn_y = 600, 200
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                velocity_y = 0
                deathcount = 0
            else:
                countdown = max(0, 3 - round(time.time() - ctime, 2))
                reset_text = menu_ui.render_text(f"Resetting the level in {countdown:.2f}", True, (255, 0, 0))
                screen.blit(reset_text, (SCREEN_WIDTH // 2 - 200 , 300))             
        else:
            ctime = None

        level_logic.death_message(screen, death_text, wait_time, duration=2500)

        draw_notifications()
        draw_syncing_status()

        pygame.display.update()    

def create_lvl2_screen():
    global player_img, screen, complete_levels, is_mute, selected_character, wait_time, transition_time, is_transitioning, current_time, medal, deathcount, score
    global new_hs, hs, stars, ctime
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    global x, y, camera_x, camera_y, spawn_x, spawn_y,  player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground
    char_assets()
    new_hs = False

    screen.blit(bgs['green'], (0, 0))
    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

    wait_time = None
    death_text = None
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

    exit_portal = pygame.Rect(4330, 460, 140, 180)
    clock = pygame.time.Clock()
    
    # Render the texts
    jump_message = in_game.get("jump_message", "Use orange blocks to jump high distances!")
    rendered_jump_text = menu_ui.render_text(jump_message, True, (255, 128, 0))  # Render the jump text

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text

    if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))



    pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

    for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (jump_block.x - camera_x, jump_block.y - camera_y, jump_block.width, jump_block.height))

    level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)

            # Inside the game loop:
    screen.blit(rendered_jump_text, (900 - camera_x, 500 - camera_y))  # Draws the rendered up text

    draw_notifications()
    draw_syncing_status()

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
                sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                sounds['move'].play()
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
                death_text = rendered_fall_text
                if not is_mute:
                    sounds['fall'].play()
                wait_time = pygame.time.get_ticks()
                player_x, player_y = spawn_x, spawn_y
                velocity_y = 0
                deathcount += 1

        # Exit portal
        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(2)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

            manage_data.save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl3_screen')    

        # Drawing
        screen.blit(bgs['green'], (0, 0))

        if player_rect.colliderect(flag) and not checkpoint_reached:
            checkpoint_reached = True
            spawn_x, spawn_y = 2150, 620  # Store checkpoint position
            if not is_mute:
                sounds['checkpoint'].play()
            
        if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 
        
        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, is_mute, sounds['bounce'], False, False)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            velocity_y = 0
            deathcount += 1
        
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

        level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        screen.blit(rendered_jump_text, (900 - camera_x, 500 - camera_y))  # Draws the rendered up text

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(2, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)

        if keys[pygame.K_r]:
            resetting()
            if  time.time() - ctime > 3:
                ctime = None
                start_time = time.time()
                current_time = 0
                spawn_x, spawn_y = 150, 500
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                velocity_y = 0
                deathcount = 0
            else:
                countdown = max(0, 3 - round(time.time() - ctime, 2))
                reset_text = menu_ui.render_text(f"Resetting the level in {countdown:.2f}", True, (255, 0, 0))
                screen.blit(reset_text, (SCREEN_WIDTH // 2 - 200 , 300))             
        else:
            ctime = None
        
        level_logic.death_message(screen, death_text, wait_time, duration=2500)

        draw_notifications()
        draw_syncing_status()

        pygame.display.update()    

def create_lvl3_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    global x, y, camera_x, camera_y, spawn_x, spawn_y,  player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground
    char_assets()
    new_hs = False
    screen.blit(bgs['green'], (0, 0))
    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

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
            "key": (250, 175, 30, (255, 255, 0)),
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
        pygame.Rect(1220, -425, 360, 50),
    ]

    jump_blocks = [
        pygame.Rect(950, 700, 100, 50), # Jump blocks to help the character go up and then fall down
        pygame.Rect(2300, 751, 100, 100),
        pygame.Rect(2600, 285, 120, 100),
    ]

    spikes = [
    [(900, 350), (950, 400), (1000, 350)],
    [(1000, 350), (1050, 400), (1100, 350)],
    [(2000, 750), (2050, 700), (2100, 750)],
    ]

    exit_portal = pygame.Rect(430, -350, 140, 180)
    clock = pygame.time.Clock()

    saw_text = in_game.get("saws_message", "Saws are also dangerous!")
    rendered_saw_text = menu_ui.render_text(saw_text, True, (255, 0, 0))  # Render the saw text

    key_text = in_game.get("key_message", "Grab the coin and open the block!")
    rendered_key_text = menu_ui.render_text(key_text, True, (255, 255, 0))  # Render the key text

    # Drawing
    screen.blit(bgs['green'], (0, 0))

    screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
        # Draw all saws first
    for x, y, r, color in saws:
            saw_ig_img = pygame.transform.scale(assets['saw'], (int(r*2), int(r*2)))
            screen.blit(saw_ig_img, (int(x - r - camera_x), int(y - r - camera_y)))

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

    level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)

    # Draw the texts
    screen.blit(rendered_saw_text, (int(550 - camera_x), int(600 - camera_y)))  # Draws the rendered up text
    screen.blit(rendered_key_text, (int(2500 - camera_x), int(200 - camera_y)))  # Draws the rendered up text

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text

    draw_notifications()
    draw_syncing_status()

    if transition.x <= -transition.image.get_width():
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
                sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                sounds['move'].play()
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

        if player_y > 1100:
                death_text = rendered_fall_text
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    sounds['fall'].play()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                velocity_y = 0
                deathcount += 1

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 200, 100  # Store checkpoint position
            if not is_mute:
                sounds['checkpoint'].play()
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not is_mute:
                sounds['checkpoint'].play()
            spawn_x, spawn_y = 2100, -400  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(3)
            level_complete()    
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

            manage_data.save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl4_screen')

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
        screen.blit(bgs['green'], (0, 0))

        if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
        # Draw all saws first

        level_logic.draw_saws(screen, saws, assets['saw'], camera_x, camera_y, saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.handle_key_blocks(screen, sounds['open'], key_block_pairs, is_mute, on_ground, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y)

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)

        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                key_block_pairs[0]["collected"] = False  # Reset key block status
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, is_mute, sounds['bounce'], False, False)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            velocity_y = 0
            deathcount += 1
        
        level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        # Draw the texts
        screen.blit(rendered_saw_text, (int(550 - camera_x), int(600 - camera_y)))  # Draws the rendered up text
        screen.blit(rendered_key_text, (int(2500 - camera_x), int(200 - camera_y)))  # Draws the rendered up text

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(3, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)

        draw_notifications()
        draw_syncing_status()

        pygame.display.update()    

def create_lvl4_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    global x, y, camera_x, camera_y, spawn_x, spawn_y,  player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(bgs['green'], (0, 0))
    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

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
    saw_angle = 0

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
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 90, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 180, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 270, 'speed': 2, "block": 1},
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
    exit_portal = pygame.Rect(4870, 265, 140, 180)
    clock = pygame.time.Clock()

    # Drawing
    screen.blit(bgs['green'], (0, 0))

    screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
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
            scale_factor = (rotating_saw['r'] * 2.5) / assets['saw'].get_width()
            rotated_saw = pygame.transform.rotozoom(assets['saw'], saw_angle, scale_factor)
            rect = rotated_saw.get_rect(center=(int(x - camera_x), int(y - camera_y)))
            screen.blit(rotated_saw, rect)

    for x, y, r, color in saws:
        scale_factor = (r * 2.5) / assets['saw'].get_width()
        rotated_saw = pygame.transform.rotozoom(assets['saw'], saw_angle, scale_factor)
        rect = rotated_saw.get_rect(center=(int(x - camera_x), int(y - camera_y)))
        screen.blit(rotated_saw, rect)

        # Draw all lasers first
    for laser in lasers:
        pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for jump_block in jump_blocks:
        pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text
        
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


    level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)

    draw_notifications()
    draw_syncing_status()
    
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
                sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                sounds['move'].play()
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

        if player_y > 1100:
            death_text = rendered_fall_text
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Saw collision detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 1500, 500  # Store checkpoint position
            if not is_mute:
                sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not is_mute:
                sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3150, 100  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(4)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

            manage_data.save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl5_screen') 

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
        screen.blit(bgs['green'], (0, 0))

        if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        if level_logic.handle_rotating_saws(screen, rotating_saws, blocks, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False
        
        level_logic.draw_saws(screen, saws, assets['saw'], camera_x, camera_y, saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.handle_key_blocks(screen, sounds['open'], key_block_pairs, is_mute, on_ground, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y)

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)

        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                key_block_pairs[0]["collected"] = False  # Reset key block status
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

        # Draw all lasers first
        for laser in lasers:
            pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))

        # Then check for collision with lasers
        for laser in lasers:
            # Check if the player collides with the laser
            if player_rect.colliderect(laser):
                # Trigger death logic
                player_x, player_y = spawn_x, spawn_y
                death_text = menu_ui.render_text(in_game.get("laser_message", "Lasered!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not is_mute:
                    sounds['laser'].play()
                velocity_y = 0
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, is_mute, sounds['bounce'], False, False)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            velocity_y = 0
            deathcount += 1
        
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


        level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(4, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        draw_notifications()
        draw_syncing_status()
        pygame.display.update()   

def create_lvl5_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    global x, y, camera_x, camera_y, spawn_x, spawn_y,  player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(bgs['green'], (0, 0))
    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

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
    saw_angle = 0

    # Draw flag
    flag = pygame.Rect(2100, -150, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(3450, -450, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 2100, -150
    flag_2_x, flag_2_y = 3450, -450

    key_block_pairs = [
        {
            "key": (4250, -900, 30, (255, 255, 0)),
            "block": pygame.Rect(1300, -250, 200, 250),
            "collected": False
        },
    ]

    walls = [        
        pygame.Rect(2700, -310, 50, 91),
        pygame.Rect(2880, -310, 50, 140)
        ]

    blocks = [
        pygame.Rect(-50, 650, 860, 100),
        pygame.Rect(920, 510, 100, 100),
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
        {'r': 100, 'speed': 6, 'cx': 1250, 'cy': 200, 'max': 700, 'min': 200},
    ]

    moving_saws_x = [
        {'r': 100, 'speed': 8, 'cx': 2400, 'cy': -500, 'max': 3300, 'min': 2400},
    ]

    saws = [
        (500, 630, 80,(255, 0, 0)),  # (x, y, radius, color)
        (2000, -360, 80,(255, 0, 0)),  # (x, y, radius, color)
        (2400, -360, 80,(255, 0, 0)),  # (x, y, radius, color)
    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 180, 'speed': 2, "block": 1},
    ]


    jump_blocks = [
        pygame.Rect(2200, 751, 100, 100),
        pygame.Rect(2570, 400, 100, 100),
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
        [(3900, -20), (3950, 30), (4000, -20)],
        [(3900, -320), (3950, -270), (4000, -320)],
        [(3900, -620), (3950, -570), (4000, -620)],
        [(4200, -120), (4250, -70), (4300, -120)],
        [(4200, -420), (4250, -370), (4300, -420)],
        [(4500, -20), (4550, 30), (4600, -20)],
        [(4500, -320), (4550, -270), (4600, -320)],
        [(4500, -620), (4550, -570), (4600, -620)],
        [(4800, -720), (4850, -670), (4900, -720)],
        [(4800, -420), (4850, -370), (4900, -420)],
        [(4800, -120), (4850, -70), (4900, -120)],
    ]

    exit_portal = pygame.Rect(1360, 20, 140, 180)
    clock = pygame.time.Clock()

    
    # Render the texts
    screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
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
            scale_factor = (rotating_saw['r'] * 2.5) / assets['saw'].get_width()
            rotated_saw = pygame.transform.rotozoom(assets['saw'], saw_angle, scale_factor)
            rect = rotated_saw.get_rect(center=(int(x - camera_x), int(y - camera_y)))
            screen.blit(rotated_saw, rect)
    
    for x, y, r, color in saws:
        scale_factor = (r * 2.5) / assets['saw'].get_width()
        rotated_saw = pygame.transform.rotozoom(assets['saw'], saw_angle, scale_factor)
        rect = rotated_saw.get_rect(center=(int(x - camera_x), int(y - camera_y)))
        screen.blit(rotated_saw, rect)

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

    level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text
    
    draw_notifications()
    draw_syncing_status()
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
                sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                sounds['move'].play()
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

        for block in walls:
            if player_rect.colliderect(block):
                # Horizontal collision (left or right side of the block)
                if player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        if player_y > 1100:
            death_text = rendered_fall_text
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Saw collision detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2050, -200  # Store checkpoint position
            if not is_mute:
                sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not is_mute:
                sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3450, -550  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(5)
            level_complete()

            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

            manage_data.save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl6_screen')

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
        screen.blit(bgs['green'], (0, 0))

        if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        if level_logic.handle_rotating_saws(screen, rotating_saws, blocks, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False

        level_logic.draw_saws(screen, saws, assets['saw'], camera_x, camera_y, saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.handle_key_blocks(screen, sounds['open'], key_block_pairs, is_mute, on_ground, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y)
        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

        for block in walls:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, is_mute, sounds['bounce'], False, False)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            velocity_y = 0
            deathcount += 1

        level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)
       
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(5, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)
        
        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        
        draw_notifications()
        draw_syncing_status()
        pygame.display.update()   

def create_lvl6_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, current_time, medal, deathcount, score
    start_time = time.time()
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    global x, y, camera_x, camera_y, spawn_x, spawn_y,  player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(bgs['green'], (0, 0))

    wait_time = None
    death_text = None
    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

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
    saw_angle = 0

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

    lasers = [
        pygame.Rect(5870, 180, 15, 350),
    ]

    blocks = [
        pygame.Rect(-200, 700, 1200, 100),
        pygame.Rect(800, 400, 100, 100),
        pygame.Rect(1400, 400, 100, 100),
        pygame.Rect(1700, 400, 100, 100),
        pygame.Rect(2000, 400, 100, 100),
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
        (5000, 550, 100, (255, 0, 0)),
        (5400, 550, 100, (255, 0, 0)),

    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 120, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 240, 'speed': 2, "block": 1},
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

    exit_portal = pygame.Rect(5630, 340, 140, 180)
    clock = pygame.time.Clock()


    screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
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
            scale_factor = (rotating_saw['r'] * 2.5) / assets['saw'].get_width()
            rotated_saw = pygame.transform.rotozoom(assets['saw'], saw_angle, scale_factor)
            rect = rotated_saw.get_rect(center=(int(x - camera_x), int(y - camera_y)))
            screen.blit(rotated_saw, rect)

    for x, y, r, color in saws:
            angle = (pygame.time.get_ticks() // 3) % 360
            saw_ig_img = assets['saw']
            curr_w, curr_h = saw_ig_img.get_size()
            center_x = x - camera_x
            center_y = y - camera_y
            draw_x = center_x - (curr_w / 2)
            draw_y = center_y - (curr_h / 2)
            screen.blit(saw_ig_img, (draw_x, draw_y))

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

    level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text

    draw_notifications()
    draw_syncing_status()
    if transition.x <= -transition.image.get_width():
      while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        if wait_time is None:
            val = random.random()

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
                sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                sounds['move'].play()
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

        if player_y > 1100:
            death_text = rendered_fall_text
            wait_time = pygame.time.get_ticks()
            if not is_mute and val > 0.35: # type: ignore
                sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Saw collision detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2400, 350  # Store checkpoint position
            if not is_mute:
                sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not is_mute:
                sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3150, 400  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(6)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()
            Achievements.perfect6(current_time, deathcount)
            manage_data.save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('worlds')

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
        screen.blit(bgs['green'], (0, 0))

        if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        if level_logic.handle_rotating_saws(screen, rotating_saws, blocks, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0

        level_logic.draw_saws(screen, saws, assets['saw'], camera_x, camera_y, saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.handle_key_blocks(screen, sounds['open'], key_block_pairs, is_mute, on_ground, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y)

        for laser in lasers:
            pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))

        for laser in lasers:
            # Check if the player collides with the laser
            if player_rect.colliderect(laser):
                # Trigger death logic
                death_text = menu_ui.render_text(in_game.get("laser_message", "Lasered!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not is_mute and val > 0.35:
                    sounds['laser'].play()
                player_x, player_y = spawn_x, spawn_y # type: ignore
                deathcount += 1
                velocity_y = 0
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key
        
        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, is_mute, sounds['bounce'], False, False)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            velocity_y = 0
            deathcount += 1

        level_logic.draw_portal(screen, assets['exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(6, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                if val > 0.3:
                    screen.blit(death_text, (20, 50))
                else:
                    if not guide:
                        sounds['hscore'].play()
                        guide = True
                    
                    if val < 0.15:
                        screen.blit(menu_ui.render_text('"The strong is not the one who overcomes the people by his strength, but the strong is', True, (255, 255, 0)), (20, 50))
                        screen.blit(menu_ui.render_text('the one who controls himself while in anger." (Bukhari 6114)', True, (255, 255, 0)), (20, 80)) 
                    else:
                        screen.blit(menu_ui.render_text('"Indeed, with hardship comes ease." (Quran 94:6)', True, (255, 255, 0)), (20, 50))
            
            else:
                wait_time = None
                val = None

        draw_notifications()
        draw_syncing_status()
        pygame.display.update()   

def create_lvl7_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, current_time, medal, deathcount, score
    start_time = time.time()
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(bgs['mech'], (0, 0))

    wait_time = None
    death_text = None
    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

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
    saw_angle = 0

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
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 3, 'block': 0},
        {'r': 40, 'orbit_radius': 230, 'angle': 120, 'speed': 3, 'block': 0},
        {'r': 40, 'orbit_radius': 230, 'angle': 240, 'speed': 3, 'block': 0},
        {'r': 60, 'orbit_radius': 500, 'angle': 60, 'speed': 2, 'block': 0},
        {'r': 60, 'orbit_radius': 500, 'angle': 180, 'speed': 2, 'block': 0},
        {'r': 60, 'orbit_radius': 500, 'angle': 300, 'speed': 2, 'block': 0},
        {'r': 80, 'orbit_radius': 900, 'angle': 0, 'speed': 1, 'block': 0},
        {'r': 80, 'orbit_radius': 900, 'angle': 120, 'speed': 1, 'block': 0},
        {'r': 80, 'orbit_radius': 900, 'angle': 240, 'speed': 1, 'block': 0},
    ]

    spikes = [
    [(3400, 500), (3450, 450), (3500, 500)],
    [(4100, 500), (4150, 450), (4200, 500)],
    ]

    exit_portal = pygame.Rect(1960, -1320, 140, 180)
    clock = pygame.time.Clock()

    teleporters = [
        {
            "entry": pygame.Rect(5150, 300, 140, 180),
            "exit": pygame.Rect(100, -1400, 50, 50),
            "color": (0, 196, 255)
        }
    ]

    screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for rotating_saw in rotating_saws:
            rad = math.radians(rotating_saw['angle'])

            orbit_center_x = blocks[0].centerx
            orbit_center_y = blocks[0].centery
            x = orbit_center_x + rotating_saw['orbit_radius'] * math.cos(rad)
            y = orbit_center_y + rotating_saw['orbit_radius'] * math.sin(rad)

            angle = (pygame.time.get_ticks() // 3) % 360
            saw_ig_img = assets['saw']
            curr_w, curr_h = saw_ig_img.get_size()
            center_x = x - camera_x
            center_y = y - camera_y
            draw_x = center_x - (curr_w / 2)
            draw_y = center_y - (curr_h / 2)
            screen.blit(saw_ig_img, (draw_x, draw_y))

    for x, y, r, color in saws:
            angle = (pygame.time.get_ticks() // 3) % 360
            saw_ig_img = assets['saw']
            curr_w, curr_h = saw_ig_img.get_size()
            center_x = x - camera_x
            center_y = y - camera_y
            draw_x = center_x - (curr_w / 2)
            draw_y = center_y - (curr_h / 2)
            screen.blit(saw_ig_img, (draw_x, draw_y))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    level_logic.draw_portal(screen, assets['mech_exit'], exit_portal, camera_x, camera_y)
    
    portal_text = menu_ui.render_text(in_game.get("portal_message", "These blue portals teleport you! But to good places... mostly!"), True, (0, 102, 204))

    draw_notifications()
    draw_syncing_status()
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
                set_page("mech_levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not is_mute:
                sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                sounds['move'].play()
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

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

        # Checkpoint Logic
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2600, 250  # Store checkpoint position
            if not is_mute:
                sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 150, -1500  # Checkpoint position
            if not is_mute:
                sounds['checkpoint'].play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(7)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

            manage_data.save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl8_screen')

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
        screen.blit(bgs['mech'], (0, 0))

        if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        if level_logic.handle_rotating_saws(screen, rotating_saws, blocks, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0

        for teleporter in teleporters:
            # Draw the entry rectangle
            level_logic.draw_portal(screen, assets['teleport'], teleporter["entry"], camera_x, camera_y)
            # Draw the exit rectangle
            level_logic.draw_portal(screen, assets['teleport_exit'], teleporter["exit"], camera_x, camera_y)

           # Check if the player collides with the entry rectangle
            if player_rect.colliderect(teleporter["entry"]):
                # Teleport the player to the exit rectangle
                if not is_mute:
                    sounds['warp'].play()
                player_x, player_y = teleporter["exit"].x, teleporter["exit"].y
        
        level_logic.draw_saws(screen, saws, assets['saw'], camera_x, camera_y, saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

        level_logic.draw_portal(screen, assets['mech_exit'], exit_portal, camera_x, camera_y)
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)          

        screen.blit(portal_text, (4400 - camera_x, 300 - camera_y))

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(7, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        draw_notifications()
        draw_syncing_status()
        pygame.display.update()   

def create_lvl8_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()

    new_hs = False
    buttons.clear()
    screen.blit(bgs['mech'], (0, 0))

    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

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
    saw_angle = 0

    # Draw flag
    flag = pygame.Rect(8700, -320, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(10000, -320, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 8700, -320
    flag_2_x, flag_2_y = 10000, -320

    blocks = [
        pygame.Rect(0, 400, 100, 100),
        pygame.Rect(460, 650, 540, 50),
        pygame.Rect(1200, 200, 1050, 50),
        pygame.Rect(8200, -200, 6000, 400),
        pygame.Rect(9000, -750, 50, 600),
        pygame.Rect(9600, -750, 50, 600),
        pygame.Rect(10000, -1650, 2000, 500),
        pygame.Rect(10000, -1650, 100, 1220),
        pygame.Rect(10750, -360, 600, 170),
    ]
    
    jump_blocks = [
        pygame.Rect(1100, 600, 100, 100),
        pygame.Rect(11000, -460, 100, 100),
    ]

    moving_saws = [
        {'r': 60, 'speed': 11, 'cx': 350, 'cy': 200, 'max': 800, 'min': 0},
    ]

    moving_saws_x = [
        {'r': 130, 'speed':19, 'cx': 11000, 'cy': -950, 'max': 11300, 'min': 10700}
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
    [(10100, -1150), (10150, -1100), (10200, -1150)],
    [(10200, -1150), (10250, -1100), (10300, -1150)],
    [(10300, -1150), (10350, -1100), (10400, -1150)],
    [(10400, -1150), (10450, -1100), (10500, -1150)],
    [(10500, -1150), (10550, -1100), (10600, -1150)],
    [(10600, -1150), (10650, -1100), (10700, -1150)],
    [(10700, -1150), (10750, -1100), (10800, -1150)],
    [(10800, -1150), (10850, -1100), (10900, -1150)],
    [(10900, -1150), (10950, -1100), (11000, -1150)],
    [(11000, -1150), (11050, -1100), (11100, -1150)],
    [(11100, -1150), (11150, -1100), (11200, -1150)],
    [(11200, -1150), (11250, -1100), (11300, -1150)],
    [(11300, -1150), (11350, -1100), (11400, -1150)],
    ]

    exit_portal = pygame.Rect(10980, -1050, 140, 180)
    clock = pygame.time.Clock()

    gravity_weakers = [
        (8700, -350, 30, (0, 102, 204)),
    ]

    teleporters = [
        {
            "entry": pygame.Rect(2090, 0, 140, 180),
            "exit": pygame.Rect(8300, -400, 100, 100),
            "color": (0, 196, 255)
        }
    ]

    screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for x, y, r, color in saws:
            angle = (pygame.time.get_ticks() // 3) % 360
            saw_ig_img = assets['saw']
            curr_w, curr_h = saw_ig_img.get_size()
            center_x = x - camera_x
            center_y = y - camera_y
            draw_x = center_x - (curr_w / 2)
            draw_y = center_y - (curr_h / 2)
            screen.blit(saw_ig_img, (draw_x, draw_y))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    level_logic.draw_portal(screen, assets['mech_exit'], exit_portal, camera_x, camera_y)

    button1_text = in_game.get("button1_message", "Blue buttons, upon activation, will make you jump higher!")
    button1_text = menu_ui.render_text(button1_text, True, (0, 102, 204))

    clarify_text = in_game.get("clarify_message", "Until you reach a checkpoint, of course!")
    clarify_text = menu_ui.render_text(clarify_text, True, (0, 102, 204))

    mock_text = in_game.get("mock_message", "Wrong way my guy nothing to see here...")
    mock_text = menu_ui.render_text(mock_text, True, (255, 0, 0))

    draw_notifications()
    draw_syncing_status()
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
                set_page("mech_levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if weak_grav:
                velocity_y = -weak_jump_strength
            else:
                velocity_y = -jump_strength
            if not is_mute:
                sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                sounds['move'].play()
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

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            weak_grav = False # Reset weak gravity status
            if not is_mute:
                sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

        # Checkpoint Logic
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            weak_grav = False # Reset weak gravity status
            spawn_x, spawn_y = 8680, -500  # Store checkpoint position
            if not is_mute:
                sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            weak_grav = False # Reset weak gravity status
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 10000, -350  # Checkpoint position
            if not is_mute:
                sounds['checkpoint'].play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(8)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

            manage_data.save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl9_screen')

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
        screen.blit(bgs['mech'], (0, 0))

        if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))

        # Handle Moving Saws
        for teleporter in teleporters:
            # Draw the entry rectangle
            level_logic.draw_portal(screen, assets['teleport'], teleporter["entry"], camera_x, camera_y)
            # Draw the exit rectangle
            level_logic.draw_portal(screen, assets['teleport_exit'], teleporter["exit"], camera_x, camera_y)

           # Check if the player collides with the entry rectangle
            if player_rect.colliderect(teleporter["entry"]):
                # Teleport the player to the exit rectangle
                if not is_mute:
                    sounds['warp'].play()
                player_x, player_y = teleporter["exit"].x, teleporter["exit"].y

        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0

        level_logic.draw_saws(screen, saws, assets['saw'], camera_x, camera_y, saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, is_mute, sounds['bounce'], False, weak_grav)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

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
                    sounds['button'].play()
                weak_grav = True


        level_logic.draw_portal(screen, assets['mech_exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        screen.blit(button1_text, (8400 - camera_x, -150 - camera_y))
        screen.blit(clarify_text, (9800 - camera_x, -150 - camera_y))
        screen.blit(mock_text, (13200 - camera_x, -300 - camera_y))

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(8, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        draw_notifications()
        draw_syncing_status()
        pygame.display.update()   

def create_lvl9_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(bgs['mech'], (0, 0))
    
    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

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
    saw_angle = 0

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
        pygame.Rect(1600, 600, 300, 100),
        pygame.Rect(2050, 500, 100, 100),
        pygame.Rect(2300, 400, 600, 100),
        pygame.Rect(2800, -300, 100, 500),
        pygame.Rect(3200, 200, 100, 530),
        pygame.Rect(2900, -600, 1100, 100),
        pygame.Rect(3500, 200, 2030, 100),
        pygame.Rect(3550, 650, 2280, 100)
    ]

    walls = [
        pygame.Rect(3500, 220, 100, 830)
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

    exit_portal = pygame.Rect(3325, 420, 140, 180)
    clock = pygame.time.Clock()

    gravity_strongers = [
        (300, 50, 30, (204, 102, 204)),
    ]

    gravity_weakers = [
        (2550, 350, 30, (0, 102, 204)),
    ]

    moving_block = pygame.Rect(4450, 30, 100, 20)
    moving_direction1 = 1
    moving_speed = 5
    moving_limit_left1 = 4050
    moving_limit_right1 = 5600

    screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for x, y, r, color in gravity_strongers:
            # Draw the button as a circle
                pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    level_logic.draw_portal(screen, assets['mech_exit'], exit_portal, camera_x, camera_y)
    
    draw_notifications()
    draw_syncing_status()

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
                set_page("mech_levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if strong_grav:
                velocity_y = -strong_jump_strength
            elif weak_grav:
                velocity_y = -weak_grav_strength
            else:
                velocity_y = -jump_strength
            if not is_mute:
                sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                sounds['move'].play()
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

        for block in walls:
            if player_rect.colliderect(block):
                # Horizontal collision (left or right side of the block)
                if player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            key_block_pairs[0]["collected"] = False  # Reset key block status
            strong_grav = False # Reset strong gravity status
            weak_grav = False # Reset weak gravity status
            if not is_mute:    
                sounds['fall'].play()
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
                sounds['checkpoint'].play()
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
                sounds['checkpoint'].play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(9)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.lvl90000(score)
            Achievements.check_green_gold()

            manage_data.save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl10_screen')

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
        screen.blit(bgs['mech'], (0, 0))

        if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.handle_key_blocks(screen, sounds['open'], key_block_pairs, is_mute, on_ground, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y)

        for block in walls:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, is_mute, sounds['bounce'], strong_grav, weak_grav)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

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
                    sounds['button'].play()
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
                    sounds['button'].play()
                weak_grav = True
                strong_grav = False

        level_logic.draw_portal(screen, assets['mech_exit'], exit_portal, camera_x, camera_y)
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        button2_text = in_game.get("button2_message", "Lavender buttons, upon activation, will make you jump lower!")
        screen.blit(menu_ui.render_text(button2_text, True, (204, 102, 204)), (100 - camera_x, 100 - camera_y))

        clarify2_text = in_game.get("clarify_message2", "They also affect your jumps on jump blocks!")
        screen.blit(menu_ui.render_text(clarify2_text, True, (204, 102, 204)), (1000 - camera_x, 450 - camera_y))

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(9, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)
        
        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        draw_notifications()
        draw_syncing_status()
        pygame.display.update() 

def create_lvl10_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, current_time, medal, deathcount, score
    global new_hs, hs, stars
    new_hs = False
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    buttons.clear()
    screen.blit(bgs['mech'], (0, 0))

    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y =  0, 250
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
    saw_angle = 0

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
        pygame.Rect(1920, 400, 100, 100),
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


    rotating_saws = [
        {'r': 40, 'orbit_radius': 300, 'angle': 0, 'speed': 3, 'block': 0},
    ]

    lights = [
        {
            "button": pygame.Rect(400, 380, 50, 50),
            "block": pygame.Rect(1300, 0, 200, 400),
        }
    ]

    exit_portal = pygame.Rect(5960, 280, 140, 180)
    clock = pygame.time.Clock()

    gravity_strongers = [
        (5050, 420, 30, (204, 102, 204)),
    ]

    moving_block = pygame.Rect(2200, 300, 100, 20)
    moving_direction1 = 1
    moving_speed = 5
    moving_limit_left1 = 2200
    moving_limit_right1 = 2800

    screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))

    for rotating_saw in rotating_saws:
    # Update angle
            rad = math.radians(rotating_saw['angle'])

    # Orbit around block center
            orbit_center_x = blocks[0].centerx
            orbit_center_y = blocks[0].centery
            x = orbit_center_x + rotating_saw['orbit_radius'] * math.cos(rad)
            y = orbit_center_y + rotating_saw['orbit_radius'] * math.sin(rad)

    # Draw the saw
            scale_factor = (rotating_saw['r'] * 2.5) / assets['saw'].get_width()
            rotated_saw = pygame.transform.rotozoom(assets['saw'], saw_angle, scale_factor)
            rect = rotated_saw.get_rect(center=(int(x - camera_x), int(y - camera_y)))
            screen.blit(rotated_saw, rect)

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for x, y, r, color in saws:
            angle = (pygame.time.get_ticks() // 3) % 360
            saw_ig_img = assets['saw']
            curr_w, curr_h = saw_ig_img.get_size()
            center_x = x - camera_x
            center_y = y - camera_y
            draw_x = center_x - (curr_w / 2)
            draw_y = center_y - (curr_h / 2)
            screen.blit(saw_ig_img, (draw_x, draw_y))

    
    draw_notifications()
    draw_syncing_status()

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
            spawn_x, spawn_y = 0, 250
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("mech_levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if strong_grav:
                velocity_y = -strong_jump_strength
            elif weak_grav:
                velocity_y = -weak_grav_strength
            else:
                velocity_y = -jump_strength
            if not is_mute:
                sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += move_speed

            if on_ground and not was_moving and not is_mute:
                sounds['move'].play()
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

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            lights_off = True
            strong_grav = False # Reset strong gravity status
            if not is_mute:    
                sounds['fall'].play()
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
                sounds['checkpoint'].play()
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
                sounds['checkpoint'].play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(10)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

            manage_data.save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl11_screen')

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
        screen.blit(bgs['mech'], (0, 0))

        if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))

# Saw collision detection and drawing
        if level_logic.handle_rotating_saws(screen, rotating_saws, blocks, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, is_mute, sounds['bounce'], strong_grav, weak_grav)
        level_logic.draw_saws(screen, saws, assets['saw'], camera_x, camera_y, saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

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
                    sounds['button'].play()
                strong_grav = True
                weak_grav = False

        level_logic.draw_portal(screen, assets['mech_exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        button2_text = in_game.get("button3_message", "Purple buttons, upon activation, will turn out almost all the lights!")
        screen.blit(menu_ui.render_text(button2_text, True, (104, 102, 204)), (100 - camera_x, 300 - camera_y))

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        player_x, player_y, velocity_y, on_ground, player_rect, lights_off = level_logic.handle_light_blocks(screen, lights, on_ground, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, lights_off, SCREEN_WIDTH, SCREEN_HEIGHT, is_mute, sounds['button'])

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(10, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        draw_notifications()
        draw_syncing_status()
        pygame.display.update() 

def create_lvl11_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(bgs['mech'], (0, 0))

    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

    wait_time = None
    death_text = None
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
    evilrobo_mascot = pygame.image.load(manage_data.resource_path(f"char/evilrobot/evilrobot.png")).convert_alpha()
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

    blocks = [
        pygame.Rect(-600, 525, 2850, 50),
        pygame.Rect(1065, 200, 70, 375),
        pygame.Rect(1625, -200, 100, 590),
        pygame.Rect(1625, 50, 150, 50),
        pygame.Rect(2200, 400, 150, 50),
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
        {'r': 200, 'speed': 21, 'cx': 3000, 'cy': 0, 'max': 5920, "min": 2700},
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

    lights = [
        {
        "button": pygame.Rect(2350, -425, 50, 50),
        "block": pygame.Rect(3050, -200, 120, 400)
        }
    ]

    exit_portal = pygame.Rect(6600, 250, 140, 180)
    clock = pygame.time.Clock()

    speedsters = [
        (-100, 400, 30, (51, 255, 51)),
        (2450, -400, 30, (51, 255, 51)),
    ]
    
    for x, y, r, color in saws:
            angle = (pygame.time.get_ticks() // 3) % 360
            saw_ig_img = assets['saw']
            curr_w, curr_h = saw_ig_img.get_size()
            center_x = x - camera_x
            center_y = y - camera_y
            draw_x = center_x - (curr_w / 2)
            draw_y = center_y - (curr_h / 2)
            screen.blit(saw_ig_img, (draw_x, draw_y))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [((x - camera_x),( y - camera_y)) for x, y in spike])

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    draw_notifications()
    draw_syncing_status()

    button4_text = in_game.get("button4_message", "Green buttons, upon activation, will give you a massive speed boost!")
    rendered_button4_text = menu_ui.render_text(button4_text, True, (51, 255, 51))

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
            evilrobo_phase = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("mech_levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if strong_grav:
                velocity_y = -strong_jump_strength
            elif weak_grav:
                velocity_y = -weak_grav_strength
            else:
                velocity_y = -jump_strength
            if not is_mute:
                sounds['jump'].play()

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
                sounds['move'].play()
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

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            evilrobo_phase = 0
            epos_x, epos_y = espawn_x, espawn_y
            lights_off = True
            stamina = False
            wait_time = pygame.time.get_ticks()
            if not is_mute:    
                sounds['fall'].play()
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
                sounds['checkpoint'].play()
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
                sounds['checkpoint'].play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(11)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

            manage_data.save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('lvl12_screen')    

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
        screen.blit(bgs['mech'], (0, 0))

        if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0

        if level_logic.handle_rushing_saws(screen, rushing_saws, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, is_mute, sounds['bounce'], strong_grav, weak_grav)
        level_logic.draw_saws(screen, saws, assets['saw'], camera_x, camera_y, saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

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
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                evilrobo_phase = 0
                epos_x, epos_y = espawn_x, espawn_y
                stamina = False
                wait_time = pygame.time.get_ticks()
                lights_off = True
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1

        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

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
                    sounds['button'].play()
                strong_grav = False
                stamina = True
                weak_grav = False

        level_logic.draw_portal(screen, assets['mech_exit'], exit_portal, camera_x, camera_y)
        # Player Image
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        # Boss Trigger Area

        if player_x > suspicious_x and player_y < -300 and lights_off:
            screen.blit(evilrobo_mascot, ((epos_x - camera_x), (epos_y - camera_y)))

            if evilrobo_phase == 0 and player_x < trigger_x:
                sus_message = menu_ui.render_text("Huh? Is there anyone there?", True, (255, 20, 12))
                screen.blit(sus_message, (4800 - camera_x, -450 - camera_y))
            else:
                if evilrobo_phase < 1:
                    evilrobo_phase = 1  # Prevents repeating

        if evilrobo_phase == 1 and player_y < -300 and lights_off:
            holup_message = menu_ui.render_text("HEY! Get away from here!", True, (185, 0, 0))
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
                confused_text = menu_ui.render_text("WHERE DID HE GO????", True, (82, 0, 0))
                screen.blit(confused_text, ((epos_x - camera_x), (epos_y - camera_y - 40)))
                if not unlock:
                    unlock = True
                    unlock_time = pygame.time.get_ticks()
            epos_x -= 12

        if epos_x < 2150:
            evilrobo_phase = 2

        if unlock and unlock_time is not None:
            Achievements.evilchase()
            unlock_time = None

        evilrobo_rect = pygame.Rect(int(epos_x), int(epos_y), evilrobo_mascot.get_width(), evilrobo_mascot.get_height())
        
        if player_rect.colliderect(evilrobo_rect) and lights_off:
            evilrobo_phase = 0
            velocity_y = 0
            epos_x, epos_y = espawn_x, espawn_y
            player_x, player_y = spawn_x, spawn_y
            screen.fill((255, 255, 255))
            stamina = False
            if not is_mute:
                sounds['hit'].play()
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
                if not is_mute:
                    sounds['hit'].play()

        screen.blit(rendered_button4_text, (-320 - camera_x, 300 - camera_y))

        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)
        
        player_x, player_y, velocity_y, on_ground, player_rect, lights_off = level_logic.handle_light_blocks(screen, lights, on_ground, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, lights_off, SCREEN_WIDTH, SCREEN_HEIGHT, is_mute, sounds['button'])

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(11, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        draw_notifications()
        draw_syncing_status()
        pygame.display.update()

def create_lvl12_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(bgs['mech'], (0, 0))

    in_game = manage_data.load_language(lang_code, manifest).get('in_game', {})

    wait_time = None
    death_text = None
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

    # Other settings
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    lights_off = True
    saw_angle = 0

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
        pygame.Rect(2300, 200, 150, 100),
        pygame.Rect(2600, 20, 200, 100),
        pygame.Rect(4500, 750, 600, 200),
    ]

    jump_blocks = [
        pygame.Rect(3000, 250, 100, 100),
        pygame.Rect(4300, 550, 100, 100),
    ]

    moving_saws = [ 
        {'r': 70, 'speed': 4, 'cx': 800, 'cy': 0, 'max': 500, 'min': -100},
        {'r': 70, 'speed': 5, 'cx': 1400, 'cy': 300, 'max': 600, 'min': 0},
    ]

    moving_saws_x = [
        {'r': 95, 'speed': 6, 'cx': 3350, 'cy': -50, 'min': 3300, 'max': 3900},
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

    exit_portal = pygame.Rect(4080, -910, 140, 180)
    clock = pygame.time.Clock()

    draw_notifications()
    draw_syncing_status()

    timed_coin_text_2 = in_game.get("timed_coin_message_2", "time. Run before they close again, or at worst, crush you...")
    rendered_timed_text_2 = menu_ui.render_text(timed_coin_text_2, True, (255, 128, 0))

    timed_coin_text = in_game.get("timed_coin_message", "Orange coins are timed! They open blocks for a limited")
    rendered_timed_text = menu_ui.render_text(timed_coin_text, True, (255, 128, 0))

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
            weak_grav = False
            strong_grav = False
            checkpoint_reached = False  # Reset checkpoint status
            spawn_x, spawn_y = 100, 0
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["timer"] = 0  # Reset the timer for all key blocks

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                set_page("mech_levels")

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if strong_grav:
                velocity_y = -strong_jump_strength
            elif weak_grav:
                velocity_y = -weak_grav_strength
            else:
                velocity_y = -jump_strength
            if not is_mute:
                sounds['jump'].play()

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
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if stamina:
                    velocity_x = stamina_speed
                    player_x += velocity_x
                else:
                    velocity_x = move_speed
                    player_x += velocity_x

            if on_ground and not was_moving and not is_mute:
                sounds['move'].play()
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
                sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag

        # Exit portal
        if player_rect.colliderect(exit_portal):
            fin_lvl_logic(12)
            level_complete()
            manage_data.save_progress(progress)  # Save progress to JSON file
           
            # Check if all medals from lvl1 to lvl12 are "Gold"
            Achievements.check_green_gold()
            
            running = False
            set_page('main_menu')    

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(bgs['mech'], (0, 0))

        if checkpoint_reached:
            screen.blit(assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, assets['saw'], camera_x, camera_y, saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not is_mute: sounds['death'].play()
            velocity_y = 0

        level_logic.draw_saws(screen, saws, assets['saw'], camera_x, camera_y, saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, is_mute, sounds['bounce'], strong_grav, weak_grav)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not is_mute:    
                    sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

        level_logic.draw_portal(screen, assets['mech_exit'], exit_portal, camera_x, camera_y)

        screen.blit(rendered_timed_text, (0 - camera_x, -80 - camera_y))
        
        screen.blit(rendered_timed_text_2, (-20 - camera_x, -30 - camera_y))
        
        for pair in key_block_pairs_timed:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]

            key_rect = pygame.Rect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)

            if player_rect.colliderect(key_rect):
                if not pair["collected"]:
                    pair["locked_time"] = pygame.time.get_ticks()
                    pair["collected"] = True
                    if not is_mute:
                        sounds['open'].play()

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
                        if not is_mute:
                         sounds['hit'].play()
                        deathcount += 1
                        stamina = False  # Reset stamina status
                        lights_off = True
                        weak_grav = False
                        strong_grav = False
                        player_x, player_y = spawn_x, spawn_y
                        for pair in key_block_pairs_timed:
                            pair["collected"] = False  # Reset the collected status for all keys
                            pair["timer"] = 0  # Reset the timer for all key blocks
                        velocity_y = 0  # Reset vertical speed
                        wait_time = pygame.time.get_ticks()  # Start the wait time
                        death_text = menu_ui.render_text(in_game.get("crushed_message", "Crushed!"), True, (255, 0, 0))

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
                    sounds['button'].play()
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
                    sounds['button'].play()
                weak_grav = True
                strong_grav = False

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, SCREEN_WIDTH, SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = get_medal(12, current_time)
        level_logic.draw_medals(screen, medal, deathcount, medals, timer_text.get_width(), SCREEN_WIDTH)

        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not is_mute:
                sounds['death'].play()
            velocity_y = 0
            deathcount += 1

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()  # Start the wait time
            weak_grav = False
            strong_grav = False
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["timer"] = 0  # Reset the timer for all key blocks
            if not is_mute:    
                sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

        # Player Image
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        draw_notifications()
        draw_syncing_status()
        pygame.display.update() 

transition_time = None
is_transitioning = False

# Handle actions based on current page
def handle_action(key):
    global progress, current_page, pending_level, level_load_time, transition, is_transitioning, transition_time,locked_char_sound_played, locked_char_sound_time, manifest
    
    global pending_page
    if current_page == 'main_menu':
        if key == "start":
            if not is_transitioning:
                transition.start("worlds")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "worlds"
        elif key == "achievements":
            if not is_transitioning:
                transition.start("achievements")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "achievements"
        elif key == "character_select":
            if not is_transitioning:
                transition.start("character_select")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "character_select"
        elif key == "settings":
            if not is_transitioning:
                transition.start("settings")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "settings"
        elif key == "quit":
            if not is_transitioning:
                transition.start("quit_confirm")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "quit_confirm"
    elif current_page == "achievements":
        if key == "back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
    elif current_page == "settings":
        if key == "Back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
        if key == "About": # Note: Ensure capitalization matches your button_texts
            if not is_transitioning:
                transition.start("About")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "About"
        if key == "Audio": # Note: Ensure capitalization matches your button_texts
            if not is_transitioning:
                transition.start("Audio")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "Audio"
        if key == "Account": # Note: Ensure capitalization matches your button_texts
            if not is_transitioning:
                transition.start("Account")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "Account"
        if key == "Language":
            if not is_transitioning:
                transition.start("language_select")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "language_select"
    elif current_page == "About":
        if key == "Back":
            if not is_transitioning:
                transition.start("settings")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "settings"
        if key == "Support":
            webbrowser.open("https://github.com/OmerArfan/platformer02/blob/main/gameinfo/Support.md")
    elif current_page == "Audio":
        if key == "Back":
            if not is_transitioning:
                transition.start("settings")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "settings"
        elif key == "SFX":
            muting_sfx()
        elif key == "Ambience":
            muting_amb()
    elif current_page == "Account":
        if key == "new_account":
            # Go to your existing login/ID generation screen
            if not is_transitioning:
                transition.start("login_screen") 
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "login_screen"
        elif key and key.startswith("load_user_"):
            # Extract ID from the key string
            selected_id = key.replace("load_user_", "")
            # Update manifest to set 'last_used' so load_progress knows which one to grab
            if os.path.exists(ACCOUNTS_FILE):
                with open(ACCOUNTS_FILE, "r") as f:
                    manifest = json.load(f)
                manifest["last_used"] = selected_id
                with open(ACCOUNTS_FILE, "w") as f:
                    json.dump(manifest, f, indent=4)
            # Load the data and move to main menu
            progress = manage_data.load_progress(ACCOUNTS_FILE, APP_DATA_DIR, manage_data.manage_data.default_progress, generate_player_id, manage_data.fetch_cloud_data_by_id)
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
    elif current_page == 'worlds':
        if key == "back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
        elif key == "levels":
            if not is_transitioning:
                transition.start("levels")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "levels"
        elif key == "mech_levels":
            if not is_transitioning:
                transition.start("mech_levels")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "mech_levels"
    elif current_page == 'language_select':
        if key == "back":
            if not is_transitioning:
                transition.start("settings")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "settings"
        elif key in ["en", "fr", "es", "de", "zh_cn", "tr", "ru", "jp", "id", "kr", "ar", "pk"]:
            if not is_transitioning:
                manage_data.change_language(key, manifest, progress)
                global lang_code
                lang_code = key
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
    elif current_page == 'levels' or current_page == 'mech_levels':
        if key is None:  # Ignore clicks on locked levels
            return
        elif key == "back":
            if not is_transitioning:
                transition.start("worlds")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "worlds"
        else:  # Trigger a level's screen
            if not is_transitioning:
                transition.start(f"{key}_screen")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = f"{key}_screen"
    elif current_page == "quit_confirm":
        if key == "yes":
            quit_game(progress)
        elif key == "no":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
    elif current_page == "character_select":
        if key == "locked" and not locked_char_sound_played and not is_mute:
            sounds['death'].play()
            locked_char_sound_played = False
            locked_char_sound_time = time.time()
        if key == "back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"

# Start with main menu
set_page('main_menu')
update_locked_levels() # Update locked levels every frame!

# Global variables(only needed before main loop)!
button_hovered_last_frame = False
last_hovered_key = None
main_menu_hover = None
wait_time = None
logo_hover = False
logo_click = False
image_paths = None
image_surfaces = None
locked_char_sound_time = None
locked_char_sound_played = False

## ACCOUNTS LOGIC

username = ""
user_pass = ""
input_mode = "ID"  # Toggle between typing ID or Password
session_timeout = 3600 * 24 * 60
last_login = 0

def hash_password(password):
    # Convert the string to bytes, then create a SHA-256 hash
    return hashlib.sha256(password.encode()).hexdigest()

def show_login_screen():
    global username, user_pass, input_mode, login_done, progress, buttons, er, notification_text, notification_time, notif, error_code
    settings = manage_data.load_language(lang_code, manifest).get('settings', {})
    login_done = False
    status_msg = ""
    status_color = (180, 180, 180)
    if transition.x <= -transition.image.get_width():
       while not login_done:
        screen.blit(bgs['plain'], (0, 0))
        # 1. Header
        id_title_text = settings.get("login_header", "LOGIN / REGISTER")
        id_title = menu_ui.render_text(id_title_text, True, (255, 255, 255))
        screen.blit(id_title, (SCREEN_WIDTH // 2 - id_title.get_width() // 2, 80))

        # 2. Instructions
        instr_txt = settings.get("login_instr1", "Enter your username and password to access your account, or create a new one.")
        instr = menu_ui.render_text(instr_txt, True, (255, 255, 255))
        screen.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2 , 200))
        
        instr_txt2 = settings.get("login_instr2", "If the account does not exist, a new account will be created for you.")
        instr2 = menu_ui.render_text(instr_txt2, True, (255, 255, 255))
        screen.blit(instr2, (SCREEN_WIDTH // 2 - instr2.get_width() // 2 , 230))

        instr_txt3 = settings.get("login_instr3", "Press TAB to switch between inputting Password and Username. To return, press ESC.")
        instr3 = menu_ui.render_text(instr_txt3, True, (255, 255, 255))
        screen.blit(instr3, (SCREEN_WIDTH // 2 - instr3.get_width() // 2 , 260))
        
        instr_txt4 = settings.get("case_warning", "Usernames and Passwords are case sensitive!")
        instr4 = menu_ui.render_text(instr_txt4, True, (255, 255, 255))
        screen.blit(instr4, (SCREEN_WIDTH // 2 - instr4.get_width() // 2 , 290))

        # 3. Status Message (Errors, Success, etc.)
        if status_msg:
            s_surf = menu_ui.render_text(status_msg, True, status_color)
            screen.blit(s_surf, (SCREEN_WIDTH // 2 - s_surf.get_width() // 2, 350))

        # 4. Inputs
        # USERNAME
        u_color = (255, 255, 255) if input_mode == "USER" else (80, 80, 80)
        u_text = settings.get("username_label", "Username") # Just gets the word
        u_surf = menu_ui.render_text(f"{u_text}: {username}", True, u_color) # Stick them together here
        screen.blit(u_surf, (SCREEN_WIDTH // 2 - u_surf.get_width() // 2, 400))

        # PASSWORD
        p_color = (255, 255, 255) if input_mode == "PASS" else (80, 80, 80) 
        p_text = settings.get("password_label", "Password") # Just gets the word
        stars = "*" * len(user_pass)
        p_surf = menu_ui.render_text(f"{p_text}: {stars}", True, p_color) # Stick them together here
        screen.blit(p_surf, (SCREEN_WIDTH // 2 - p_surf.get_width() // 2, 450))
        
        # Submit button
        submit_txt = settings.get("submit_prompt", "Press ENTER to Continue")
        submit_surf = menu_ui.render_text(submit_txt, True, (0, 255, 0))
        screen.blit(submit_surf, (SCREEN_WIDTH // 2 - submit_surf.get_width() // 2, 550))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                login_done = True
                set_page("quit_confirm")

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    input_mode = "PASS" if input_mode == "USER" else "USER"
                
                if event.key == pygame.K_ESCAPE:
                    login_done = True
                    set_page("Account")

                elif event.key == pygame.K_RETURN:
                    if len(username) > 2 and len(user_pass) > 3:
                        status_msg = settings.get("checking_vault", "Checking Cloud Vault...")
                        status_color = (255, 255, 0)
                        pygame.display.update()
                        result = manage_data.recover_account_from_cloud(username, user_pass)
        # Access the notification globals
                        global notif, notification_text, notification_time, er
                        if isinstance(result, dict):
            # [SCENARIO 1] SUCCESS
                         progress = result
                         manage_data.save_progress(progress)
            
            # TRIGGER NOTIFICATION
                         login_success_text = settings.get("login_success", "Login Successful!")
                         notification_text = menu_ui.render_text(login_success_text, True, (0, 255, 0))
                         notification_time = time.time()
                         notif = True
                         login_done = True
                         if not is_mute: sounds['notify'].play()
                         set_page("Account") # Explicitly set the page back
                         return

                        elif result == "CONN_ERROR":
                            if not is_mute: 
                                sounds['hit'].play()
                            conn_error_text = settings.get("conn_error", "Connection Error: Cloud Vault is unreachable.")
                            notification_text = menu_ui.render_text(conn_error_text, True, (255, 0, 0))
                            notif = True
                            notification_time = time.time()
                            set_page("main_menu")
                            return
                        
                        elif result == "WRONG_AUTH":
            # [SCENARIO 2] WRONG PASS
                         status_msg = settings.get("wrong_pass", "Incorrect Password.")
                         status_color = (255, 50, 50)
                         if not is_mute: sounds['death'].play()
            
                        else:
                         # CASE: Username doesn't exist in cloud. This is a signup.
                            guest_id_to_promote = None
                            
                            # Check the local manifest for a Guest (Username: "")
                            if os.path.exists(ACCOUNTS_FILE):
                                try:
                                    with open(ACCOUNTS_FILE, "r") as f:
                                        manifest = json.load(f)
                                        users_list = manifest.get("users", {})
                                        
                                        # We look specifically for the empty string ""
                                        for p_id, user_info in users_list.items():
                                            if user_info.get("username") == "":
                                                guest_id_to_promote = p_id
                                                break
                                except Exception as e:
                                    er = True
                                    error_code = f"Manifest Read Error: {e}"
                                    if not is_mute:
                                        sounds['hit'].play()
                                    notification_time = time.time()

                            # 2. Assign the ID
                            if guest_id_to_promote:
                                # PROMOTE the guest ID to this new username
                                progress["player"]["ID"] = guest_id_to_promote
                                print(f"Migrating Guest ID {guest_id_to_promote} to {username}")
                            else:
                                # No guest found, create a brand new ID
                                # Initialize with DEFAULT STATS for a new user
                                progress = copy.deepcopy(manage_data.default_progress)
                                progress["player"]["ID"] = generate_player_id()
                                print(f"No guest found. Generated new ID: {progress['player']['ID']}")

                            # 3. Update the credentials
                            progress["player"]["Username"] = username
                            progress["player"]["Pass"] = hash_password(user_pass)

                            # 4. Save and Sync
                            # This will create/update the row in your Google Sheet using the selected ID
                            manage_data.save_progress(progress)
                            threading.Thread(target=manage_data.sync_vaukt, args=(progress,), daemon=True).start()
                            login_done = True
                            if not is_mute: sounds['notify'].play()
                            notification_txt = settings.get("account_created", "Account Created and Logged In!")
                            notification_text = menu_ui.render_text(notification_txt, True, (0, 255, 0))
                            notif = True
                            notification_time = time.time()
                            set_page("main_menu")
                            return        
                    else:
                        if not is_mute:
                            sounds['death'].play()
                        status_msg = settings.get("too_short", "Username or Password too short.")
                        status_color = (255, 50, 50)
                
                elif event.key == pygame.K_BACKSPACE:
                    if input_mode == "USER": username = username[:-1]
                    else: user_pass = user_pass[:-1]
                
                else:
                    if event.unicode.isalnum() or event.unicode in " _-":
                        if input_mode == "USER" and len(username) < 15:
                            username += event.unicode
                        elif input_mode == "PASS" and len(user_pass) < 20:
                            user_pass += event.unicode
        
        draw_notifications()
        draw_syncing_status()

        pygame.display.flip()
    pygame.display.update()

def create_account_selector():
    global buttons
    buttons.clear()
    settings = manage_data.load_language(lang_code, manifest).get('settings', {})

    # 1. Load manifest
    manifest = {"users": {}}
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as f:
                manifest = json.load(f)
        except: pass
    
    accounts = list(manifest.get("users", {}).items())
    
    # --- LAYOUT CONSTANTS ---
    COLUMN_WIDTH = 300
    START_Y = 200
    MAX_Y = SCREEN_HEIGHT - 150
    SPACING_Y = 72
    
    # Calculate how many columns we actually have
    num_accounts = len(accounts) + 1  # +1 for the "New Player" button
    items_per_col = (MAX_Y - START_Y) // SPACING_Y
    num_cols = (num_accounts // items_per_col) + 1
    
    # Calculate the starting X so the WHOLE group is centered
    # Total width is (number of columns * width), then we find the center
    total_group_width = num_cols * COLUMN_WIDTH
    start_x = (SCREEN_WIDTH // 2) - (total_group_width // 2) + (COLUMN_WIDTH // 2)

    current_x = start_x
    current_y = START_Y

    # 2. Render Account Buttons
    for p_id, info in accounts:
        name_str = info.get("username", "Unknown")
        rendered_name = menu_ui.render_text(name_str, True, (255, 255, 255))

        # Check if we need to wrap to a new column
        if current_y >= MAX_Y:
            current_y = START_Y
            current_x += COLUMN_WIDTH
            
        # Left-aligning looks better in columns:
        # We use current_x as the anchor for the left side of the text
        rect = rendered_name.get_rect(topleft=(current_x - 100, current_y))

        buttons.append((rendered_name, rect, f"load_user_{p_id}", False))
        current_y += SPACING_Y

    # 3. "New Player" Button (Follows the same grid logic)
    if current_y > MAX_Y:
        current_y = START_Y
        current_x += COLUMN_WIDTH

    new_txt = settings.get("new_acc", "+ NEW PLAYER")
    new_txt_rendered = menu_ui.render_text(new_txt, True, (0, 255, 200)) # Highlighted color
    new_rect = new_txt_rendered.get_rect(topleft=(current_x - 100, current_y))
    buttons.append((new_txt_rendered, new_rect, "new_account", False))

if not is_mute and SCREEN_WIDTH > MIN_WIDTH and SCREEN_HEIGHT > MIN_HEIGHT:
    sounds['click'].play()

# Info

# First define current XP outside the loop
level, xp_needed, xp_total = xp()
if level < 20:
    color = (255, 255, 255)
else:
    color = (225, 212, 31)

XP_text = fonts['mega'].render(f"{level}", True, color)
if level < 20:
    XP_text2 = menu_ui.render_text(f"{xp_needed}/{xp_total}", True, color)
else:
    max_txt = manage_data.load_language(lang_code, manifest).get('messages', {}).get("max_level", "MAX LEVEL!")
    XP_text2 = menu_ui.render_text(max_txt, True, color)

while running:
    # This is in the main loop, unlike the other texts, because it needs to update if the player changes!
    ID_text = menu_ui.render_text(f"ID: {progress['player']['ID']}", True, (255, 255, 255))
    ID_pos = (SCREEN_WIDTH - (ID_text.get_width() + 10), 0)

    messages = manage_data.load_language(lang_code, manifest).get('messages', {})
    # Clear screen!
    screen.blit(bgs['plain'], (0, 0))
    mouse_pos = pygame.mouse.get_pos()

    if transition_time is not None and pygame.time.get_ticks() - transition_time > 1000:
        transition_time = None
        is_transitioning = False

    # Handle transition timer and page change
    if is_transitioning and transition_time is not None and pending_page is not None:
        if transition.x >= 0:
            # Then recheck if XP has been added or not.
            level, xp_needed, xp_total = xp()
            if level < 20:
                color = (255, 255, 255)
            else:
                color = (225, 212, 31)

            XP_text = fonts['mega'].render(f"{level}", True, color)
            if level < 20:
                XP_text2 = menu_ui.render_text(f"{xp_needed}/{xp_total}", True, color)
            else:
                max_txt = manage_data.load_language(lang_code, manifest).get('messages', {}).get("max_level", "MAX LEVEL!")
                XP_text2 = menu_ui.render_text(max_txt, True, color)
                # Then let transition loop play as normal
            is_transitioning = False
            current_pending = pending_page
            transition_time = None
            pending_page = None
            set_page(current_pending)

    XP_pos2 = (SCREEN_WIDTH - (XP_text2.get_width() + 10), 50)
    XP_pos = (SCREEN_WIDTH - (XP_text.get_width() + XP_text2.get_width() + 30), 30)
    xp_center_x = XP_pos[0] + (XP_text.get_width() / 2)
    badge_x = xp_center_x - (assets['badge'].get_width() / 2)
    badge_pos = (badge_x, 32)

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
            screen.blit(robos['evilrobot'], (SCREEN_WIDTH // 2 - robos['evilrobot'].get_width() // 2, SCREEN_HEIGHT // 2 - 200))

            # Render the text
            messages = manage_data.load_language(lang_code, manifest).get('messages', {})
            deny_text = messages.get("deny_message", "Access denied!")
            rendered_deny_text = menu_ui.render_text(deny_text, True, (255, 100, 100))
            error_text = messages.get("error_message","Your screen resolution is too small! Increase the screen")
            rendered_error_text = menu_ui.render_text(error_text, True, (255, 255, 255))
            error_text2 = messages.get("error_message2", "resolution in your system settings.")
            rendered_error_text2 = menu_ui.render_text(error_text2, True, (255, 255, 255))
            countdown_text = messages.get("countdown_message", "Closing in {countdown} second(s)...").format(countdown=countdown)
            rendered_countdown_text = menu_ui.render_text(countdown_text, True, (255, 100, 100))

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
        # Collect events ONCE per frame
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                set_page("quit_confirm")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Only process clicks if enough time has passed since last page change
                if current_page not in ["levels", "mech_levels", "worlds"]:
                    for _, rect, key, is_locked in buttons:
                        if rect.collidepoint(event.pos):
                            if key is not None and not is_mute:
                                sounds['click'].play()
                            handle_action(key)
                            last_page_change_time = time.time()
                elif current_page in ["levels", "mech_levels", "worlds"]:
                    for rendered, rect, key, is_locked in buttons:
                        if rect.collidepoint(event.pos):
                            if key is not None and not is_mute:
                                sounds['click'].play()
                            handle_action(key)  # Only load level on click!
                    
        if current_page == "main_menu":
            screen.blit(ui['logo'], ((SCREEN_WIDTH // 2 - ui['logo'].get_width() // 2), -20))
            screen.blit(bgs['lilrobopeek'], ((SCREEN_WIDTH - bgs['lilrobopeek'].get_width()), (SCREEN_HEIGHT - bgs['lilrobopeek'].get_height())))
            screen.blit(ID_text, ID_pos)
            if level < 20:
                screen.blit(assets['badge'], badge_pos)
            else:
                screen.blit(assets['max_badge'], badge_pos)
            screen.blit(XP_text, XP_pos)
            screen.blit(XP_text2, XP_pos2)
        # Render the main menu buttons
            hovered_key = None
            for rendered, rect, key, is_locked in buttons:
                mouse_pos = pygame.mouse.get_pos()
                if ui['studio_logo_rect'].collidepoint(mouse_pos):
                    screen.blit(ui['studio_glow'], ui['studio_glow_rect'].topleft)
                    if not logo_hover:
                        if not is_mute:
                            sounds['hover'].play()
                        logo_hover = True
                    if event.type == pygame.MOUSEBUTTONDOWN and not logo_click:    
                        if not is_mute:
                            sounds['click'].play()    
                        webbrowser.open("https://omerarfan.github.io/lilrobowebsite/") 
                        logo_click = True
                else:
                    screen.blit(ui['studio_logo'], ui['studio_logo_rect'].topleft)
                    logo_hover = False
                    logo_click = False

                if rect.collidepoint(mouse_pos):
                    hovered_key = key
                    if hovered_key != last_hovered_key and not is_mute:
                        sounds['hover'].play()

                screen.blit(rendered, rect)
            last_hovered_key = hovered_key

        if current_page == "achievements":
            create_achieve_screen()

        if current_page == "character_select":
         screen.blit(bgs['plain'], (0, 0))

         # Initialize locked sound effect and mouse position
         locked_sound_played = False
         mouse_pos = pygame.mouse.get_pos()

         messages = manage_data.load_language(lang_code, manifest).get('messages', {})  # Fetch localized messages
         header_txt = manage_data.load_language(lang_code, manifest).get('main_menu', {})
         char_sel = header_txt.get("character_select", "Character Select")
         char_text = menu_ui.render_text(char_sel, True, (255, 255, 255))
         screen.blit(char_text, (SCREEN_WIDTH // 2 - 100, 50))

         # Check if characters are locked
         robo_unlock = True
         evilrobo_unlock = progress["char"].get("evilrobo", False)
         greenrobo_unlock = progress["char"].get("greenrobo", False)
         ironrobo_unlock = progress["char"].get("ironrobo", False)
         # Get currently selected character
         selected_character = progress["pref"].get("character", manage_data.default_progress["pref"]["character"])
         # Draw images
         screen.blit(robos['robot'], robot_rect)     
         screen.blit(robos['evilrobot'] if evilrobo_unlock else robos['locked'], evilrobot_rect)
         screen.blit(robos['greenrobot'] if greenrobo_unlock else robos['locked'], greenrobot_rect)
         screen.blit(robos['ironrobot'] if ironrobo_unlock else robos['locked'], ironrobot_rect)
         # Draw a highlight border around the selected character
         highlight_colors = {
          "robot": (63, 72, 204),
          "evilrobot": (128, 0, 128),
          "greenrobot": (25, 195, 21),
          "ironrobot": (64, 64, 64),
         }
         
         rects = {
          "robot": robot_rect,
          "evilrobot": evilrobot_rect,
          "greenrobot": greenrobot_rect,
          "ironrobot": ironrobot_rect,
         }
        
         if selected_character in rects:
          pygame.draw.rect(screen, highlight_colors[selected_character], rects[selected_character].inflate(5, 5), 5)

            # --- Use MOUSEBUTTONDOWN instead of continuous mouse.get_pressed ---
         for event in events:
           if event.type == pygame.QUIT:
            set_page("quit_confirm")

           elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if robot_rect.collidepoint(mouse_pos):
                try_select_robo(robo_unlock, "robot", robot_rect, "placeholder", "Imagine if this actually popped up in game BRO-")
            elif evilrobot_rect.collidepoint(mouse_pos):
                try_select_robo(evilrobo_unlock, "evilrobot", evilrobot_rect, "evillocked_message", "Encounter this robot in an alternative route to unlock him!")
            elif greenrobot_rect.collidepoint(mouse_pos):
                try_select_robo(greenrobo_unlock, "greenrobot", greenrobot_rect, "greenlocked_message", "Get GOLD rank in all Green World Levels to unlock this robot!")
            elif ironrobot_rect.collidepoint(mouse_pos):
                try_select_robo(ironrobo_unlock, "ironrobot", ironrobot_rect, "ironlocked_message", "Unlock the Zenith Of Six achievement to get this character!")
            elif rect.collidepoint(mouse_pos):
                handle_action(key)

         keys = pygame.key.get_pressed()
         if keys[pygame.K_ESCAPE]:
            set_page("main_menu")

    # Display locked message for 5 seconds
         if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 5000:
             rendered_locked_text = menu_ui.render_text(locked_text, True, (255, 255, 0))
             screen.blit(rendered_locked_text, ((SCREEN_WIDTH // 2 - rendered_locked_text.get_width() // 2), 100))
            else:
             wait_time = None

        if current_page == "language_select":
            screen.blit(bgs['plain'], (0, 0))
            screen.blit(heading_text, (SCREEN_WIDTH // 2 - heading_text.get_width() // 2, 50))

        if current_page == "quit_confirm":
            screen.blit(bgs['plain'], (0, 0))
            # Render the quit confirmation text
            screen.blit(quit_text, quit_text_rect)
            screen.blit(robos['greenrobot_moving'], (SCREEN_WIDTH // 2 - robos['robot'].get_width() // 2, SCREEN_HEIGHT // 2 - 200))
            button_hovered_last_frame = menu_ui.draw_buttons(screen, buttons, sounds['hover'], is_mute, mouse_pos, button_hovered_last_frame)

            # Allow returning to the main menu with ESC
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                set_page("main_menu")

        elif current_page == "lvl1_screen":
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
        
        elif current_page == "levels" or current_page == "mech_levels":
            if current_page == "levels":
                screen.blit(bgs['green'], (0, 0))
                disk_img = disks['green']
            else:
                screen.blit(bgs['mech'], (0, 0))
                disk_img = disks['mech']
            # Fetch the localized "Select a Level" text dynamically
            select_text = current_lang.get("level_display", "Select a Level")
            rendered_select_text = menu_ui.render_text(select_text, True, (255, 255, 255))
            select_text_rect = rendered_select_text.get_rect(center=(SCREEN_WIDTH // 2, 50))

            # Draw the "Select a Level" text
            screen.blit(rendered_select_text, select_text_rect)

            # Render buttons for levels

            for rendered, rect, key, is_locked in buttons:
                if rect.collidepoint(mouse_pos):
                    if key is not None:
                        # Unlocked level
                        screen.blit(disk_img, rect)
                    else:
                        screen.blit(disks['locked'], rect)
                    button_hovered_last_frame = menu_ui.hover_effect(screen, rect, sounds['hover'], is_mute, button_hovered_last_frame)
            # Show Level stats - check current mouse position every frame
            for text_surface, disk_rect, key, is_locked in buttons:
                if disk_rect.collidepoint(mouse_pos):
                    if key != "next" and key != "back" and not is_locked:
                        hs = progress["lvls"]['score'][key]
                        high_text = messages.get("hs_m", "Highscore: {hs}").format(hs=hs)
                        lvl_score_text = menu_ui.render_text(high_text, True, (255, 255, 0))

                        # Adjust position as needed
                        screen.blit(lvl_score_text, (SCREEN_WIDTH // 2 - lvl_score_text.get_width() // 2, SCREEN_HEIGHT - 50))
                        s = key
                        num = int(s[3:])  # Skip the first 3 characters
                        medals = progress["lvls"]['medals'][key]
                        if medals != "None":
                            screen.blit(medals[medals], (SCREEN_WIDTH // 2 - medals[medals].get_width() // 2 - 210, SCREEN_HEIGHT - 80))
                        stars = get_stars(num, progress["lvls"]['score'][key])
                        if stars >= 1:
                            screen.blit(assets['star'], (SCREEN_WIDTH // 2 - 25, SCREEN_HEIGHT - 80))
                        if stars >= 2:
                            screen.blit(assets['star'], (SCREEN_WIDTH // 2 , SCREEN_HEIGHT - 80))
                        if stars == 3:
                            screen.blit(assets['star'], (SCREEN_WIDTH // 2 + 25, SCREEN_HEIGHT - 80))
            
            for text_surface, disk_rect, key, is_locked in buttons: 
                if key is not None:
                    screen.blit(disk_img, disk_rect)
                else:
                    screen.blit(disks['locked'], disk_rect)
                text_rect = text_surface.get_rect(center=(disk_rect.x + 50, disk_rect.y + 50))
                screen.blit(text_surface, text_rect)

        elif current_page == "settings":
            screen.blit(bgs['plain'], (0, 0))
            settings_menu()
            button_hovered_last_frame = menu_ui.draw_buttons(screen, buttons, sounds['hover'], is_mute, mouse_pos, button_hovered_last_frame)

        elif current_page == "About":   
            about_menu()
            button_hovered_last_frame = menu_ui.draw_buttons(screen, buttons, sounds['hover'], is_mute, mouse_pos, button_hovered_last_frame)
            
        elif current_page == "Audio":
            screen.blit(bgs['plain'], (0, 0))
            audio_settings_menu()
            button_hovered_last_frame = menu_ui.draw_buttons(screen, buttons, sounds['hover'], is_mute, mouse_pos, button_hovered_last_frame)

        elif current_page == "Account":
            screen.blit(bgs['plain'], (0, 0))
            settings = manage_data.change_language(lang_code, manifest, progress).get('settings', {})  # Fetch localized messages
            # 1. Draw the Title Manually Here

            title_text = settings.get("select", "SELECT PROFILE")
            title = menu_ui.render_text(title_text, True, (255, 255, 255))
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

            # 2. Draw the Buttons (Using the standard button loop)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, buttons, sounds['hover'], is_mute, mouse_pos, button_hovered_last_frame)

        elif current_page == "login_screen":
            show_login_screen()
        
        else:
            button_hovered_last_frame = menu_ui.draw_buttons(screen, buttons, sounds['hover'], is_mute, mouse_pos, button_hovered_last_frame)
        
        draw_notifications()

        draw_syncing_status()
        
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(ui['cursor'], mouse_pos)

        if transition.active:
            transition.update()
        
        pygame.display.flip()

pygame.quit()
