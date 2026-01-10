import pygame
import threading
import requests
import json
import os
import math
import sys
import time
import random
import webbrowser
import shutil
import copy
import arabic_reshaper
import hashlib
import csv
from io import StringIO
from datetime import datetime, date
from bidi.algorithm import get_display

# for compilation
def resource_path(relative_path): 
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Path to sound folder
SOUND_FOLDER = resource_path("audio")

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
MIN_WIDTH, MIN_HEIGHT = 1250, 750

# First of all, LOAD THE DAMN BGGG
background_img = pygame.image.load(resource_path("bgs/PlainBackground.png")).convert()
background = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Load and set window icon
icon = pygame.image.load(resource_path("robots.ico")).convert_alpha()
pygame.display.set_icon(icon)

def change_ambience(new_file):
    global is_mute_amb
    if not is_mute_amb:
     pygame.mixer.music.load(resource_path(new_file))
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

    if roll < 0.1:        # 0.1%
        length = 3
    elif roll < 5.1:     # next 5%
        length = 4
    else:                 # rest
        length = 5

    return "".join(random.choices(HEX, k=length))

default_progress = {
    "player": {
        "ID": "",
        "Username": "",
        "Pass": "",
        "XP": 0,
        "Level": 1,
    },
    "lvls": { 
        "complete_levels": 0,
        "locked_levels": {f"lvl{i}" for i in range(2, 13)},
        "times": {f"lvl{i}": 0 for i in range(1, 13)},
        "medals": {f"lvl{i}": "None" for i in range(1, 13)},
        "score": {f"lvl{i}": 0 for i in range(1, 13)},
    },
    "pref" : { 
        "character": "robot",
    },
    "char": { 
        "evilrobo": False, 
        "greenrobo": False,
        "ironrobo": False,
    },
    "achieved": { 
        "speedy_starter": False,
        "zen_os": False,
        "over_9k": False,
        "chase_escape": False,
        "golden": False,
        "lv20": "False",
    },
}


# 1. Determine the correct "AppData" folder for each OS
if sys.platform == "win32":
    # Using LOCAL instead of ROAMING often bypasses the VirtualStore redirect
    APP_DATA_BASE = os.getenv('LOCALAPPDATA') 
else:
    APP_DATA_BASE = os.path.join(os.path.expanduser("~"), ".config")

print(f"DEBUG: Saving/Loading from: {APP_DATA_BASE}")

# 2. Path for the player's save file
APP_DATA_DIR = os.path.join(APP_DATA_BASE, "Roboquix")

# Create the folder if it doesn't exist yet
if not os.path.exists(APP_DATA_DIR):
    os.makedirs(APP_DATA_DIR)

SAVE_FILE = os.path.join(APP_DATA_DIR, "progress.json")

# To keep track of multiple accounts in future updates, and only store login of current account.
ACCOUNTS_FILE = os.path.join(APP_DATA_DIR, "local.json")

def update_local_manifest(data):
    # 1. Load existing manifest
    manifest = {"last_used": "", "users": {}, "pref": {"language": "en", "sfx": True, "ambience": True}}
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as f:
                manifest = json.load(f)
        except:
            pass

    # 2. Get current player info
    p_id = data["player"]["ID"]
    p_name = data["player"].get("Username", "User")
    current_lvl = data["player"]["Level"]

    # 3. Update Preferences (Now handled globally in the manifest)
    # Use global variables 'lang_code' and 'is_mute' currently active in the session
    manifest["pref"] = {
        "last_used": p_id,
        "language": lang_code,
        "sfx": not is_mute,
        "ambience": not is_mute_amb
    }
    
    manifest["users"][p_id] = {
        "username": p_name,
        "id": p_id,
        "level": current_lvl,
        "last_login": date.today().strftime("%Y-%m-%d")
    }

    # 4. Save
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(manifest, f, indent=4)
    
    print("Updated local manifest:", manifest)

def check_session_expired(p_id):
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            manifest = json.load(f)
        
        if p_id in manifest["users"]:
            last_str = manifest["users"][p_id]["last_login"]
            last_date = datetime.strptime(last_str, "%Y-%m-%d").date()
            
            days_passed = (date.today() - last_date).days
            
            if days_passed > 60:
                print("Session expired! Back to Login Screen.")
                return True # Show login
            else:
                print(f"Welcome back! Day {days_passed}/60 of your session.")
                return False # Stay logged in
    return True # No record found, show login

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

def draw_syncing_status():
    global is_syncing
    if is_syncing:
        # 1. Render and draw the text
        syncing_text = render_text("Syncing Vault to Cloud...", True, (255, 255, 255))
        text_x = SCREEN_WIDTH - syncing_text.get_width() - 10
        text_y = SCREEN_HEIGHT - 60
        screen.blit(syncing_text, (text_x, text_y))

        # 2. Calculate the orbit position using current time
        # Multiply time by a number to control speed (e.g., * 8)
        angle_rad = time.time() * 8 
        orbit_radius = 15
        
        # Define the center point for the circle to orbit around
        orbit_center_x = text_x - 30
        orbit_center_y = text_y + 15 # Adjusted to center it vertically with text

        for i in range(3):
            # offset each dot by 0.5 radians so they follow each other
            dot_angle = angle_rad - (i * 0.5) 
            x = orbit_center_x + orbit_radius * math.cos(dot_angle)
            y = orbit_center_y + orbit_radius * math.sin(dot_angle)
            # Make trailing dots smaller or dimmer
            alpha = 255 - (i * 80) 
            pygame.draw.circle(screen, (alpha, alpha, alpha), (int(x), int(y)), 5 - i)
        
def sync_vault_to_cloud(data):
    global is_syncing
    is_syncing = True
    
    # Using the IDs from your pre-filled link
    payload = {
        "entry.377726286": data["player"].get("Username", "Unknown"), # Username
        "entry.286332773": data["player"].get("Pass", ""),             # Password Hash
        "entry.829022223": data["player"].get("ID", ""),               # ID
        "entry.92201882": json.dumps(data, ensure_ascii=False),       # Full Progress JSON
        "entry.2000835960": date.today().strftime("%Y-%m-%d"),         # Current Date
        "entry.1017947451": datetime.now().strftime("%H:%M:%S")        # Current Time
    }

    url = "https://docs.google.com/forms/d/e/1FAIpQLSfB2alAMj3qNMm5DFw-p_4HkGyzA_U2zw9lul3HSmi15Msxjg/formResponse"

    try:
        response = requests.post(url, data=payload, timeout=7)
        if response.status_code == 200:
            print("Cloud Vault: Sync Successful.")

    except Exception as e:
        print(f"Cloud Vault Error: {e}")

    finally:
        is_syncing = False

def recover_account_from_cloud(target_user, target_pass):
    # This is your 'Latest Progress' CSV link
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQNm-8l1C38UGFt-lJT3ft5DARYZcjMwsWfVYGrtAqDy0bR8MQFcLJSRFqYYX7mbra_P2cWl1-i0WYW/pub?gid=1459647032&single=true&output=csv"
    
    try:
        print(f"Cloud Vault: Searching for user {target_user}...")
        response = requests.get(CSV_URL, timeout=10)
        
        if response.status_code == 200:
            f = StringIO(response.text)
            # DictReader uses the first row of your sheet as keys
            reader = csv.DictReader(f)
            
            # Hash the input password to compare with the cloud
            hashed_input = hashlib.sha256(target_pass.encode()).hexdigest()

            for row in reader:
                # We check the columns by their EXACT names in the sheet
                cloud_user = row.get('Username')
                cloud_pass = row.get('Password(Hashed)')
                
                if cloud_user == target_user:
                    if cloud_pass == hashed_input:
                        print("Cloud Vault: Credentials verified. Downloading progress...")
                        notify_sound.play()
                        # Grab the JSON from the 'Progress' column
                        return json.loads(row.get('Progress'))
                    else:
                        print(f"Comparing: {cloud_pass} vs {hashed_input}")
                        print("Cloud Vault: User found, but password was incorrect.")
                        return "WRONG_AUTH"
            
            print("Cloud Vault: No matching account found.")
            return "NOT_FOUND"
            
    except Exception as e:
        print(f"Cloud Vault: Connection error: {e}")
        return "CONN_ERROR"
    
    return "NOT_FOUND"

def load_progress():
    global SAVE_FILE, notification_time 
    
    data = copy.deepcopy(default_progress) 

    # 1. Check manifest for the last used ID
    current_id = ""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as f:
                manifest = json.load(f)
                current_id = manifest.get("last_used", "")
        except: pass

    # 2. Determine the path (ID-specific or generic)
    if current_id:
        target_file = os.path.join(APP_DATA_DIR, f"{current_id}.json")
    else:
        target_file = os.path.join(APP_DATA_DIR, "progress.json")

    # 3. Load the data
    if os.path.exists(target_file):
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                if loaded_data:
                    data.update(loaded_data)
                    # Sync missing sub-keys (levels, player info)
                    sync_missing_data(data) 
                    SAVE_FILE = target_file
                    print(f"DEBUG: Successfully loaded {target_file}")
        except Exception as e:
            print(f"Load Error: {e}")

    # 4. Handle Migration/New ID
    # If we loaded progress.json but have an ID inside it, migrate the filename
    p_id = data["player"].get("ID", "")
    if p_id == "":
        p_id = generate_player_id()
        data["player"]["ID"] = p_id

    # Update SAVE_FILE to the correct ID-specific path
    SAVE_FILE = os.path.join(APP_DATA_DIR, f"{p_id}.json")

    # 5. Migration: If we just loaded from progress.json, copy it to ID.json
    legacy_path = os.path.join(APP_DATA_DIR, "progress.json")
    if os.path.exists(legacy_path) and not os.path.exists(SAVE_FILE):
        try:
            shutil.copy(legacy_path, SAVE_FILE)
            print(f"Migrated legacy save to {p_id}.json")
        except Exception as e:
            print(f"Migration error: {e}")

    return data

def sync_missing_data(data):
    # Helper to ensure all default keys exist in loaded data.
    for key, value in default_progress.items():
        if key not in data:
            data[key] = value

    target_subkeys = ["times", "medals", "score"]

    if "lvls" in data:
        for subkey in target_subkeys:
            # Check if the subkey (e.g., "score") exists in the loaded data
            if subkey not in data["lvls"]:
                 data["lvls"][subkey] = default_progress["lvls"][subkey]
            else:
                # If it exists, check if new levels (e.g., lvl13) were added to the game
                for lvl_key, lvl_val in default_progress["lvls"][subkey].items():
                    if lvl_key not in data["lvls"][subkey]:
                       data["lvls"][subkey][lvl_key] = lvl_val

    if "lvls" in data and "locked_levels" not in data["lvls"]:
        data["lvls"]["locked_levels"] = default_progress["lvls"]["locked_levels"]

    if "player" in data:
        if "ID" not in data["player"]:
            data["player"]["ID"] = default_progress["player"]["ID"]

        if "Pass" not in data["player"]:
            data["player"]["Pass"] = default_progress["player"]["Pass"]
        
        if "Username" not in data["player"]:
            data["player"]["Username"] = default_progress["player"]["Username"]
    
    if "pref" in data:
        # .pop(key, None) safely removes the key if it exists, otherwise does nothing
        data["pref"].pop("is_mute", None)
        data["pref"].pop("language", None)

    if data["player"]["ID"] == "":
        data["player"]["ID"] = generate_player_id()

# Load the fonts (ensure the font file path is correct)
font_path_ch = resource_path('fonts/NotoSansSC-SemiBold.ttf')
font_path_jp = resource_path('fonts/NotoSansJP-SemiBold.ttf')
font_path_kr = resource_path('fonts/NotoSansKR-SemiBold.ttf')
font_path_ar = resource_path("fonts/NotoNaskhArabic-Bold.ttf")
font_path = resource_path('fonts/NotoSansDisplay-SemiBold.ttf')
font_ch = pygame.font.Font(font_path_ch, 25)
font_jp = pygame.font.Font(font_path_jp, 25)
font_kr = pygame.font.Font(font_path_kr, 25)
font_def = pygame.font.Font(font_path, 25)
font_ar = pygame.font.Font(font_path_ar, 25)
font_text = pygame.font.Font(font_path, 55)

# Save progress to file
def save_progress(data):
    global notification_text, notification_time, error_code, notif, er
    global save_count
    global SAVE_FILE 

    # 1. Basic Validation: Ensure we aren't saving an empty/broken object
    if not data or "lvls" not in data or "player" not in data:
        hit_sound.play()
        notification_text = font_def.render("Refusing to save: Invalid data structure!", True, (255, 0, 0))
        notif = True
        notification_time = time.time()
        return

    # 2. Folder & Path Logic
    if not os.path.exists(APP_DATA_DIR):
        os.makedirs(APP_DATA_DIR)
        
    p_id = data["player"].get("ID", "")
    if p_id:
        SAVE_FILE = os.path.join(APP_DATA_DIR, f"{p_id}.json")
    else:
        # Emergency fallback: if no ID, don't overwrite other files!
        print("Save Error: Player has no ID.")
        return

    try:
        # 3. Create backup of the PREVIOUS version
        if os.path.exists(SAVE_FILE):
            shutil.copy(SAVE_FILE, SAVE_FILE + ".bak")

        # 4. Write the new version
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            save_count += 1 
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # 5. Update the "Map" (local.json)
        update_local_manifest(data)

        # 6. Periodic Cloud Sync (Every 4 saves)
        if save_count % 4 == 0:
            threading.Thread(target=sync_vault_to_cloud, args=(data,), daemon=True).start()

    except PermissionError:
        hit_sound.play()
        notification_text = font_def.render("Error: Save file is locked by another program.", True, (255, 0, 0))
        notif = True
        notification_time = time.time()
            
    except Exception as e:
        er = True
        error_code = font_def.render(f"Save Error: {str(e)}", True, (255, 0, 0))
        print(f"Detailed save error: {e}")

# Load progress at start
progress_loaded = False
language_loaded = False
sounds_loaded = False
images_loaded = False
running = False
def draw_loading_bar(stage_name, percent):
    screen.blit(background, (0, 0))
    text = font_def.render(f"{stage_name}", True, (255, 255, 255))
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
    screen.blit(text, text_rect)
    pygame.draw.rect(screen, (0, 0, 255), (0, SCREEN_HEIGHT - 10, (SCREEN_WIDTH / 100)*percent, 10))
    pygame.display.flip()

stage = "Loading sounds..."
ps = 0
while ps < 100:
 draw_loading_bar(stage, ps)
 if not sounds_loaded:
  click_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "click.wav")); ps += 1
  hover_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "hover.wav"))
  death_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "death.wav")); ps += 1
  laser_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "laser.wav"))
  fall_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "fall.wav")); ps += 1
  open_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "unlock.wav"))
  checkpoint_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "checkpoint.wav")); ps += 1
  warp_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "warp.wav"))
  button_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "button.wav")); ps += 1
  bounce_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "bounce.wav"))
  move_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "travel.wav")); ps += 1
  jump_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "jump.wav"))
  hit_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "hit.wav")); ps += 1
  notify_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "notify.wav"))
  overheat_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "overheat.wav")); ps += 1
  freeze_sound = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "freeze.wav"))
  star1 = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/1star.wav"))
  star2 = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/2star.wav")); ps += 2
  star3 = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/3star.wav"))
  hscore = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/hs.wav")); ps += 1
  star1.set_volume(4.0)
  star2.set_volume(4.0)
  star3.set_volume(4.0)
  # Ambient themes
  pygame.mixer.music.load(resource_path("audio/amb/ambience.wav")); ps += 2
  sounds_loaded = True

 if not images_loaded:
    stage = "Loading images..."
    cursor_img = pygame.image.load(resource_path("oimgs/cursor/cursor.png")).convert_alpha(); ps += 2

    # Load logo images
    logo = pygame.image.load(resource_path("oimgs/logos/logo.png")).convert_alpha(); ps += 1
    studio_logo = pygame.image.load(resource_path("oimgs/logos/studiologodef.png")).convert_alpha()
    studio_logo = pygame.transform.scale(studio_logo, (220, 220))
    studio_logo_rect = studio_logo.get_rect(topleft=(20, SCREEN_HEIGHT - 240)); ps += 2
    studio_glow = pygame.image.load(resource_path("oimgs/logos/studiologoglow.png")).convert_alpha()
    studio_glow = pygame.transform.scale(studio_glow, (280, 280))
    studio_glow_rect = studio_glow.get_rect(topleft=(20, SCREEN_HEIGHT - 300)); ps += 2

    # Load and scale backgrounds
    lilrobopeek = pygame.image.load(resource_path("bgs/lilrobopeek.png")).convert_alpha(); ps += 1
    lilrobopeek = pygame.transform.scale(lilrobopeek, (390, 360))
    green_background_img = pygame.image.load(resource_path("bgs/GreenBackground.png")).convert()
    green_background = pygame.transform.scale(green_background_img, (SCREEN_WIDTH, SCREEN_HEIGHT)); ps += 1
    mech_background_img = pygame.image.load(resource_path("bgs/MechBackground.png")).convert()
    mech_background = pygame.transform.scale(mech_background_img, (SCREEN_WIDTH, SCREEN_HEIGHT)); ps += 1
    trans = pygame.image.load(resource_path("bgs/trans.png")).convert()
    trans = pygame.transform.scale(trans, ((SCREEN_WIDTH), (SCREEN_HEIGHT))); ps += 1
    end = pygame.image.load(resource_path("bgs/EndScreen.png")).convert_alpha()
    end = pygame.transform.scale(end, ((SCREEN_WIDTH), (SCREEN_HEIGHT))); ps += 1

    # Load and initalize Images!
    nact_cp = pygame.image.load(resource_path("oimgs/checkpoints/yellow_flag.png")).convert_alpha()
    act_cp = pygame.image.load(resource_path("oimgs/checkpoints/green_flag.png")).convert_alpha(); ps += 1
    diam_m = pygame.image.load(resource_path("oimgs/medal/perfect.png")).convert_alpha()
    diam_m = pygame.transform.scale(diam_m, ((diam_m.get_width() // 2), (diam_m.get_height() // 2))); ps +=1
    gold_m = pygame.image.load(resource_path("oimgs/medal/gold.png")).convert_alpha()
    gold_m = pygame.transform.scale(gold_m, ((gold_m.get_width() // 2), (gold_m.get_height() // 2))); ps +=1
    silv_m = pygame.image.load(resource_path("oimgs/medal/silver.png")).convert_alpha()
    silv_m = pygame.transform.scale(silv_m, ((silv_m.get_width() // 2), (silv_m.get_height() // 2))); ps+=1
    bron_m = pygame.image.load(resource_path("oimgs/medal/bronze.png")).convert_alpha()
    bron_m = pygame.transform.scale(bron_m, ((bron_m.get_width() // 2), (bron_m.get_height() // 2))); ps += 1

    greendisk_img = pygame.image.load(resource_path("oimgs/disks/greendisk.png")).convert_alpha()
    greendisk_img = pygame.transform.scale(greendisk_img, (100, 100)); ps +=1  # Resize as needed
    mechdisk_img = pygame.image.load(resource_path("oimgs/disks/mechdisk.png")).convert_alpha()
    mechdisk_img = pygame.transform.scale(mechdisk_img, (100, 100)); ps +=1
    lockeddisk_img = pygame.image.load(resource_path("oimgs/disks/lockeddisk.png")).convert_alpha()
    lockeddisk_img = pygame.transform.scale(lockeddisk_img, (100, 100)); ps +=1  # Resize as needed
    star_img = pygame.image.load(resource_path("oimgs/ig/star.png")).convert_alpha()
    star_img = pygame.transform.scale(star_img, (150, 140))
    s_star_img = pygame.transform.scale(star_img, (20, 17)); ps +=1
    exit_img = pygame.image.load(resource_path("oimgs/ig/exit.png")).convert_alpha()
    exit_img = pygame.transform.scale(exit_img, (140, 180)); ps += 1
    mechexit_img = pygame.image.load(resource_path("oimgs/ig/mech_exit.png")).convert_alpha()
    mechexit_img = pygame.transform.scale(mechexit_img, (140, 180)); ps += 1
    badge = pygame.image.load(resource_path("oimgs/ig/badge.png")).convert_alpha()
    badge = pygame.transform.scale(badge, (70, 70)); ps += 1
    max_badge = pygame.image.load(resource_path("oimgs/ig/max-badge.png")).convert_alpha()
    max_badge = pygame.transform.scale(max_badge, (70, 70)); ps += 1

    # Load character images
    robot_img = pygame.image.load(resource_path("char/robot/robot.png")).convert_alpha()
    evilrobot_img = pygame.image.load(resource_path("char/evilrobot/evilrobot.png")).convert_alpha()
    greenrobot_img = pygame.image.load(resource_path("char/greenrobot/greenrobot.png")).convert_alpha()
    ironrobot_img = pygame.image.load(resource_path("char/ironrobot/ironrobo.png")).convert_alpha()
    icerobot_img = pygame.image.load(resource_path("char/icerobot/icerobot.png")).convert_alpha()
    quitbot = pygame.image.load(resource_path("char/greenrobot/movegreenrobot.png")).convert_alpha()
    locked_img = pygame.image.load(resource_path("char/lockedrobot.png")).convert_alpha(); ps += 6

 if not progress_loaded and sounds_loaded:
    stage = "Loading progress..."
    progress = load_progress(); ps = 65
    complete_levels = progress.get("complete_levels", 0); ps = 75
    progress_loaded = True

# In the loading loop section:
 if not language_loaded and progress_loaded:
    stage = "Loading configured settings..."
    
    # NEW: Load from manifest instead of progress
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            manifest = json.load(f)
            global_pref = manifest.get("pref", {})
            lang_code = global_pref.get("language", "en")
            # Invert 'sfx' back to 'is_mute'
            is_mute = not global_pref.get("sfx", True) 
            is_mute_amb = not global_pref.get("ambience", True)
    else:
        lang_code = "en"
        is_mute = False
        is_mute_amb = False

    language_loaded = True
    if is_mute_amb:
        pygame.mixer.music.stop()
    else:
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play(-1)  # Loop forever
 else:
     ps = 100
 
 pygame.display.flip()

if ps == 100:
 running = True



with open(resource_path("data/thresholds.json"), "r", encoding="utf-8") as f:
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
    
if lang_code == "zh_cn":
    font = pygame.font.Font(font_path_ch, 25)
if lang_code == "jp":
    font = pygame.font.Font(font_path_jp, 25)
if lang_code == "kr":
    font = pygame.font.Font(font_path_kr, 25)
if lang_code == "pk" or lang_code == "ir" or lang_code == "ar":
    font = pygame.font.Font(font_path_ar, 25)
else:
    font = pygame.font.Font(font_path, 25)

def render_text(text, Boolean, color):
    if any('\u0590' <= c <= '\u06FF' for c in text):  # Urdu/Arabic range
        reshaped = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped)
        if any('\u0600' <= c <= '\u06FF' for c in text):
            return font_ar.render(bidi_text, True, color)
    
    if any('\u4e00' <= c <= '\u9fff' for c in text):  # Chinese
        return font_ch.render(text, True, color)
    
    if any('\u3040' <= c <= '\u30FF' for c in text) or any('\u4E00' <= c <= '\u9FFF' for c in text):
        return font_jp.render(text, True, color)    
    
    if any('\uAC00' <= c <= '\uD7A3' for c in text):  # Korean
        return font_kr.render(text, True, color)

    return font_def.render(text, True, color)
    
class Achievements:
    def lvl1speed(ctime):
        global notification_text, notification_time, notif
        unlock = progress["achieved"].get("speedy_starter", False)
        if ctime <= 4.5:
          if not unlock:
            progress["achieved"]["speedy_starter"] = True  
            notification_text = font_def.render("Achievement Unlocked: Speedy Starter", True, (255, 255, 0))
            notify_sound.play()
            if notification_time is None:
             notif = True
             notification_time = time.time()
    
    def perfect6(ctime, deaths):
        global notification_text, notification_time, notif
        unlock = progress["achieved"].get("zen_os", False)
        if ctime <= 30 and deaths <= 0:
          if not unlock:
            progress["achieved"]["zen_os"] = True
            progress["char"]["ironrobo"] = True
            save_progress(progress)
            notification_text = font_def.render("Achievement Unlocked: Zenith of Six", True, (255, 255, 0))
            notify_sound.play()
            if notification_time is None:
             notif = True
             notification_time = time.time()

    def lvl90000(score):
        global notification_text, notification_time, notif
        unlock = progress["achieved"].get("over_9k", False)
        if score >= 105000:
         if not unlock:
            progress["achieved"]["over_9k"] = True          
            notification_text = font_def.render("Achievement Unlocked: It's over 9000!!", True, (255, 255, 0))
            notify_sound.play()
            if notification_time is None:
             notif = True
             notification_time = time.time()
    
    def evilchase():
        global notification_text, notification_time, notif
        notification_text = font_def.render("Achievement Unlocked: Chased and Escaped", True, (255, 255, 0))
        unlock = progress["achieved"].get("chase_escape", False)
        if not unlock:
          progress["achieved"]["chase_escape"] = True
          progress["char"]["evilrobo"] = True
          save_progress(progress)
          if not is_mute:
           notify_sound.play()
           if notification_time is None:
             notif = True
             notification_time = time.time()
    
    def check_green_gold():
      global show_greenrobo_unlocked, greenrobo_unlocked_message_time
      all_gold = all(progress["lvls"]["medals"][f"lvl{i}"] == "Gold" or progress["lvls"]["medals"][f"lvl{i}"] == "Diamond" for i in range(1, 7))
      if all_gold:
        unlock = progress["achieved"].get("golden", False)
        if not unlock:
            if not is_mute:
                notify_sound.play()
            unlock = True
            progress["achieved"]["golden"] = True
            progress["char"]["greenrobo"] = unlock
            save_progress(progress)
            show_greenrobo_unlocked = True
            greenrobo_unlocked_message_time = time.time()
    
    def check_xplvl20(Level):
        global notification_text, notification_time, notif
        notification_text = font_def.render("Achievement Unlocked: XP Collector!", True, (255, 255, 0))
        unlock = progress["achieved"].get("lv20", False)
        if Level >= 20:
         if not unlock:
          progress["achieved"]["lv20"] = True
          save_progress(progress)
          if not is_mute:
           notify_sound.play()
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


# Load language function and rendering part remain the same
def load_language(lang_code):
    try:
        # Wrap the path in resource_path()
        path = resource_path(f"lang/{lang_code}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[WARN] Language '{lang_code}' not found. Falling back to English.")
        manifest["pref"]["language"] = "en"
        update_local_manifest(manifest)
        
        # Wrap the fallback path too!
        fallback_path = resource_path("lang/en.json")
        with open(fallback_path, "r", encoding="utf-8") as f:
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
    button_texts = ["start", "achievements", "character_select", "settings", "quit"]

    # Center buttons vertically and horizontally
    button_spacing = 72
    start_y = (SCREEN_HEIGHT // 2) - (len(button_texts) * button_spacing // 2) + 150

    for i, key in enumerate(button_texts):
        text = current_lang[key]
        rendered = render_text(text, True, (255, 255, 255))
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
    heading_text = render_text(heading, True, (255 , 255, 255))

    for i, (display_name, code) in enumerate(language_options):
        text = display_name
        rendered = render_text(text, True, (255, 255, 255))

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
    rendered_back = render_text(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(SCREEN_WIDTH // 2, y + spacing_y + 40))
    buttons.append((rendered_back, back_rect, "back", False))

def worlds():
    global current_lang, buttons
    buttons.clear()
    current_lang = load_language(lang_code).get('language_select', {})
    screen.blit(background, (0, 0))

    # 1. Define Positions
    # We define the center points so the image and the button hitbox align perfectly
    green_center = (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2)
    mech_center = (SCREEN_WIDTH // 2 + 250, SCREEN_HEIGHT // 2)

    # 2. Draw the Disks
    # Use the rect to blit so the image is centered on our coordinates
    green_rect = greendisk_img.get_rect(center=green_center)
    mech_rect = mechdisk_img.get_rect(center=mech_center)
    
    screen.blit(greendisk_img, green_rect)
    screen.blit(mechdisk_img, mech_rect)

    # 3. Add Disks to the Button List
    # Format: (surface/image, rect, action_key, is_locked)
    buttons.append((greendisk_img, green_rect, "levels", False))
    buttons.append((mechdisk_img, mech_rect, "mech_levels", False))

    # --- Back Button Logic ---
    back_text = current_lang.get("back", "Back")        
    rendered_back = render_text(back_text, True, (255, 255, 255))

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
        text_surface = font_text.render(level_no[i], True, (255, 255, 255))
        disk_rect = greendisk_img.get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = render_text(back_text, True, (255, 255, 255))

    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.Rect(SCREEN_WIDTH // 2 - rendered_back.get_width() // 2, SCREEN_HEIGHT - 175, 100, 100)
    back_rect.center = (SCREEN_WIDTH // 2 , SCREEN_HEIGHT - 200)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))

    next_text = current_lang.get("next", "next")
    rendered_next = render_text(next_text, True, (255, 255, 255))

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
        text_surface = font_text.render(level_no[i], True, (255, 255, 255))
        disk_rect = greendisk_img.get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = render_text(back_text, True, (255, 255, 255))

    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.Rect(SCREEN_WIDTH // 2 - rendered_back.get_width() // 2, SCREEN_HEIGHT - 175, 100, 100)
    back_rect.center = (SCREEN_WIDTH // 2 , SCREEN_HEIGHT - 200)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))

    next_text = current_lang.get("next", "next")
    rendered_next = render_text(next_text, True, (255, 255, 255))

    next_rect = pygame.Rect(0, 0, 100, 100)
    next_rect.center = (SCREEN_WIDTH - 90, SCREEN_HEIGHT // 2)

    text_rect = rendered_next.get_rect(center=next_rect.center)
    screen.blit(rendered_next, text_rect)

#def load_level(level_id):
#    global current_page, buttons
#
   # Show "Loading..." text
#    screen.fill((30, 30, 30))
#    messages = load_language(lang_code).get('messages', {})  # Reload messages with the current language
#    loading_text = messages.get("loading", "Loading...")
#    rendered_loading = render_text(loading_text, True, (255, 255, 255))
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
selected_character = progress.get("character", default_progress["pref"]["character"])

# Get rects and position them
robot_rect = robot_img.get_rect(topleft=(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 50))
evilrobot_rect = evilrobot_img.get_rect(topleft=(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50))
greenrobot_rect = greenrobot_img.get_rect(topleft=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
ironrobot_rect = ironrobot_img.get_rect(topleft=(SCREEN_WIDTH // 2 + 150, SCREEN_HEIGHT // 2 - 50))
def character_select():
    global selected_character, set_page, current_page
    
    # Clear screen
    buttons.clear()
    current_lang = load_language(lang_code)['language_select']
    button_texts = ["back"]

    for i, key in enumerate(button_texts):
        text = current_lang[key]
        rendered = render_text(text, True, (255, 255, 255))
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
    sync_vault_to_cloud(progress)
    pygame.quit()
    sys.exit()

def change_language(lang):
    global lang_code, last_page_change_time, current_lang, font, font_path_ch, font_path
    lang_code = lang
    last_page_change_time = time.time()  # Track the time when the language changes
    current_lang = load_language(lang_code)  # Reload the language data
    manifest["pref"]["language"] = lang_code
    update_local_manifest(progress)
    if lang_code == "zh_cn":
        font = font_ch
    elif lang_code == "jp":
        font = font_jp
    elif lang_code == "kr":
        font = font_kr
    elif lang_code == "pk" or lang_code == "ir" or lang_code == "ar":
        font = font_ar
    else:
        font = font_def

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
    save_progress(progress)

def settings_menu():
    global current_lang, buttons
    # 1. Load language (only once per page change is better, but this works)
    current_lang = load_language(lang_code).get('settings', {})
    setting_lang = load_language(lang_code).get('main_menu', {})
    buttons.clear()
    screen.blit(background, (0, 0))

    # 2. Match these keys EXACTLY to handle_action
    # format: (Display Text, Internal Key)
    button_data = [
        (current_lang["Audio"], "Audio"),
        (current_lang["Account"], "Account"),
        (setting_lang["language"], "Language"),
        (current_lang["Back"], "Back")
    ]

    heading = setting_lang.get("settings", "Settings")
    heading_text = render_text(heading, True, (255 , 255, 255))
    screen.blit(heading_text, (SCREEN_WIDTH // 2 - heading_text.get_width() // 2, 200))

    button_spacing = 72
    start_y = (SCREEN_HEIGHT // 2) - (len(button_data) * button_spacing // 2) + 150

    for i, (display_text, internal_key) in enumerate(button_data):
        rendered = render_text(display_text, True, (255, 255, 255))
        rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * button_spacing)) 
        # Store the internal_key so handle_action knows what was clicked
        buttons.append((rendered, rect, internal_key, False))

    # Mouse pos for hover effects
    mouse_pos = pygame.mouse.get_pos()
    
    for rendered, rect, key, _ in buttons:
        if rect.collidepoint(mouse_pos):
            # Add a small glow or background for hover feedback
            pygame.draw.rect(screen, (0, 213, 0), rect.inflate(20, 10), 2)
        screen.blit(rendered, rect)

class Slider:
    def __init__(self, x, y, width, initial_val):
        self.rect = pygame.Rect(x, y, width, 10)
        self.handle_rect = pygame.Rect(x + (width * initial_val) - 10, y - 10, 20, 30)
        self.dragging = False
        self.value = initial_val

    def draw(self, screen):
        # Draw the bar
        pygame.draw.rect(screen, (100, 100, 100), self.rect)
        # Draw the handle
        color = (200, 200, 200) if not self.dragging else (255, 255, 255)
        pygame.draw.rect(screen, color, self.handle_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # Keep handle within the bar limits
            self.handle_rect.centerx = max(self.rect.left, min(event.pos[0], self.rect.right))
            self.value = (self.handle_rect.centerx - self.rect.left) / self.rect.width
            return True # Value changed
        return False


def audio_settings_menu():
    global buttons
    buttons.clear()
    screen.blit(background, (0, 0))

    # 1. Draw Title
    title = render_text("Audio Settings", True, (255, 255, 255))
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))
    
    if is_mute:
        sfx_txt = "Unmute Sound"
    else:
        sfx_txt = "Mute Sound"
    
    if is_mute_amb:
        amb_txt = "Unmute Ambience"
    else:
        amb_txt = "Mute Ambience"
    renderedsfx = render_text(sfx_txt, True, (255, 255, 255))
    rectsfx = renderedsfx.get_rect(center=(SCREEN_WIDTH // 2, 350))
    buttons.append((renderedsfx, rectsfx, "SFX", False))

    renderedamb = render_text(amb_txt, True, (255, 255, 255))
    rectamb = renderedamb.get_rect(center=(SCREEN_WIDTH // 2, 450))
    buttons.append((renderedamb, rectamb, "Ambience", False))

    # 3. Back Button
    rendered = render_text("Back", True, (255, 255, 255))
    rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, 550))
    buttons.append((rendered, rect, "Back", False))
    
    screen.blit(rendered, rect)
    screen.blit(renderedsfx, rectsfx)
    screen.blit(renderedamb, rectamb)

def muting_sfx():
    global is_mute
    is_mute = not is_mute
    # Save directly to manifest (pass 'progress' so it can see player ID/Level)
    update_local_manifest(progress)

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
    update_local_manifest(progress)
    

# Central page switcher
def set_page(page):
    global current_page, current_lang  # Explicitly mark current_page and current_lang as global
    current_page = page

    # Reload the current language data for the new page
    if page == 'main_menu':
        current_lang = load_language(lang_code).get('main_menu', {})
        create_main_menu_buttons()
    elif page == 'character_select':
        character_select()
    elif page == 'language_select':
        current_lang = load_language(lang_code).get('language_select', {})
        create_language_buttons()
    elif page == "worlds":
        worlds()
    elif page == "settings":
        settings_menu()
    elif page == "Audio":
        audio_settings_menu()
    elif page == "Account":
        create_account_selector()
    elif page == "login_screen":
        show_login_screen()
    elif page == 'levels':
        current_lang = load_language(lang_code).get('levels', {})
        green_world_buttons()
        change_ambience("audio/amb/greenambience.wav")
    elif page == 'mech_levels':
        current_lang = load_language(lang_code).get('levels', {})
        mech_world_buttons()
        change_ambience("audio/amb/mechambience.wav")
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

def try_select_robo(unlock_flag, char_key, rect, locked_msg_key, fallback_msg):
    if rect.collidepoint(pygame.mouse.get_pos()):
        global wait_time, selected_character, locked_char_sound_time, locked_char_sound_played

        if unlock_flag:
            selected_character = char_key
            progress["pref"]["character"] = selected_character
            save_progress(progress)
            if not is_mute:
                click_sound.play()
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
    quit_text = render_text(confirm_quit, True, (255, 255, 255))
    quit_text_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 25))

    # Create "Yes" button
    yes_text = messages.get("yes", "Yes")
    rendered_yes = render_text(yes_text, True, (255, 255, 255))
    yes_rect = rendered_yes.get_rect(center=(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50))
    buttons.append((rendered_yes, yes_rect, "yes", False))

    # Create "No" button
    no_text = messages.get("no", "No")
    rendered_no = render_text(no_text, True, (255, 255, 255))
    no_rect = rendered_no.get_rect(center=(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 + 50))
    buttons.append((rendered_no, no_rect, "no", False))

    pygame.display.flip()  # Update the display to show the quit confirmation screen

def score_calc():
    global current_time, medal, deathcount, score

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
    score = max(500, 100000 - medal_score - death_score - time_score + token_score)

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
    messages = load_language(lang_code).get('messages', {})
    display_score = 0
    star1_p, star2_p, star3_p = False, False, False
    star_time = time.time()
    running = True
    notified = False
    clock = pygame.time.Clock()
    star_channel = pygame.mixer.Channel(2)
    lvl_comp = messages.get("lvl_comp", "Level Complete!")
    rendered_lvl_comp = render_text(lvl_comp, True, (255, 255, 255))
    while running:
        screen.blit(end, (0, 0))
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.blit(rendered_lvl_comp, (SCREEN_WIDTH // 2 - rendered_lvl_comp.get_width() // 2, 50))

        # Animate score
        
        if display_score < score:
          if not is_mute:
            hover_sound.play()
          display_score += max(5, (score // 71))
        if stars >= 1 and (time.time() - star_time > 0.5):
                screen.blit(star_img, (SCREEN_WIDTH // 2 - 231, 130))
                if not star1_p:
                 for _ in range(40):  # Add some particles at star position
                    stareffects.append(StarParticles(SCREEN_WIDTH // 2 - 230 + star_img.get_width() // 2, 130 + star_img.get_height() // 2)) 
                 if not is_mute:
                  star_channel.play(star1)
                star1_p = True
        if stars >= 2 and (time.time() - star_time > 1.5):
                screen.blit(star_img, (SCREEN_WIDTH // 2 - 76, 130))
                if not star2_p and star1_p: 
                    for _ in range(40):  # Add some particles at star position
                     stareffects.append(StarParticles(SCREEN_WIDTH // 2 - 75 + star_img.get_width() // 2, 130 + star_img.get_height() // 2))  
                    if not is_mute:
                     star_channel.play(star2)
                    star2_p = True
        if stars >= 3 and (time.time() - star_time  >  2.5):
                screen.blit(star_img, (SCREEN_WIDTH // 2 + 79, 130)) 
                if  not star3_p and star2_p: 
                    for _ in range(40):  # Add some particles at star position
                      stareffects.append(StarParticles(SCREEN_WIDTH // 2 + 80 + star_img.get_width() // 2, 130 + star_img.get_height() // 2)) 
                    if not is_mute:
                     star_channel.play(star3)
                    star3_p = True
        if medal == "Diamond":
            screen.blit(diam_m, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - gold_m.get_height() // 2))
        elif medal == "Gold":
            screen.blit(gold_m, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - gold_m.get_height() // 2))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - gold_m.get_height() // 2))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - gold_m.get_height() // 2))

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
                    hs_text = messages.get("new_hs", "New High Score!")
                    new_hs_text = render_text(hs_text, True, (255, 215, 0))
                    screen.blit(new_hs_text, (SCREEN_WIDTH // 2 - new_hs_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))
                    if not is_mute and not notified:
                        hscore.play()
                        notified = True
                else:
                    high_text = messages.get("hs_m", "Highscore: {hs}").format(hs=hs)
                    hs_text = render_text(high_text, True, (158, 158, 158))
                    screen.blit(hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))
        
        if time.time() - star_time > 6 or keys[pygame.K_SPACE]:
                running = False
        else: 
            next_left = -(int(time.time() - star_time) - 6)
            time_text = render_text("Press the spacebar to", True, (158, 158, 158))
            screen.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, SCREEN_HEIGHT // 2 + 250))
            time_text_2 = render_text(f"continue or wait for {next_left}", True, (158, 158, 158))
            screen.blit(time_text_2, (SCREEN_WIDTH // 2 - time_text_2.get_width() // 2, SCREEN_HEIGHT // 2 + 275))

        xp()
        draw_notifications()
        draw_syncing_status()
        pygame.display.update()
        clock.tick(60)

def char_assets():
    global selected_character, player_img, blink_img, moving_img, moving_img_l, img_width, img_height
 # Load player image
    if selected_character == "robot": 
        player_img = pygame.image.load(resource_path(f"char/robot/robot.png")).convert_alpha()
        blink_img = pygame.image.load(resource_path(f"char/robot/blinkrobot.png")).convert_alpha()
        moving_img_l = pygame.image.load(resource_path(f"char/robot/smilerobotL.png")).convert_alpha() # Resize to fit the game
        moving_img = pygame.image.load(resource_path(f"char/robot/smilerobot.png")).convert_alpha() # Resize to fit the game
    elif selected_character == "evilrobot":
        player_img = pygame.image.load(resource_path(f"char/evilrobot/evilrobot.png")).convert_alpha()
        blink_img = pygame.image.load(resource_path(f"char/evilrobot/blinkevilrobot.png")).convert_alpha()
        moving_img_l = pygame.image.load(resource_path(f"char/evilrobot/movevilrobotL.png")).convert_alpha() # Resize to fit the game
        moving_img = pygame.image.load(resource_path(f"char/evilrobot/movevilrobot.png")).convert_alpha() # Resize to fit the game
    elif selected_character == "greenrobot":
        player_img = pygame.image.load(resource_path(f"char/greenrobot/greenrobot.png")).convert_alpha()
        blink_img = pygame.image.load(resource_path(f"char/greenrobot/greenrobot.png")).convert_alpha()
        moving_img_l = pygame.image.load(resource_path(f"char/greenrobot/movegreenrobotL.png")).convert_alpha() # Resize to fit the game
        moving_img = pygame.image.load(resource_path(f"char/greenrobot/movegreenrobot.png")).convert_alpha() # Resize to fit the game
    elif selected_character == "ironrobot":
        player_img = pygame.image.load(resource_path(f"char/ironrobot/ironrobo.png")).convert_alpha()
        blink_img = pygame.image.load(resource_path(f"char/ironrobot/blinkironrobo.png")).convert_alpha()
        moving_img_l = pygame.image.load(resource_path(f"char/ironrobot/ironrobomoveL.png")).convert_alpha() # Resize to fit the game
        moving_img = pygame.image.load(resource_path(f"char/ironrobot/ironrobomove.png")).convert_alpha() # Resize to fit the game
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
                warp_sound.play()

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

def player_image(keys, player_x, player_y, camera_x, camera_y):
    if (keys[pygame.K_RIGHT]) or (keys[pygame.K_d]):
            screen.blit(moving_img, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
    elif (keys[pygame.K_LEFT]) or (keys[pygame.K_a]):
            screen.blit(moving_img_l, (player_x - camera_x, player_y - camera_y))  # Draw the moving block image
    else:
        screen.blit(player_img, (player_x - camera_x, player_y - camera_y))
        if round(current_time % 4, 0) == 0:
            screen.blit(blink_img, (player_x - camera_x, player_y - camera_y))

def create_lvl1_screen():
    global player_img, font, screen, complete_levels, is_mute, show_greenrobo_unlocked, is_transitioning, transition_time, current_time, medal, deathcount, score
    global new_hs, hs, stars, ctime
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
        [(2650, 250), (2700, 200), (2750, 250)],
    ]

    exit_portal = pygame.Rect(2780, 60, 140, 180)
    clock = pygame.time.Clock()

    # Render the texts
    warning_text = in_game.get("warning_message", "Watch out for spikes!")
    rendered_warning_text = render_text(warning_text, True, (255, 0, 0))  # Render the warning text

    up_text = in_game.get("up_message", "Press UP to Jump!")
    rendered_up_text = render_text(up_text, True, (0, 0, 0))  # Render the up text

    exit_text = in_game.get("exit_message", "Exit Portal! Come here to win!")
    rendered_exit_text = render_text(exit_text, True, (0, 73, 0))  # Render the exit text

    moving_text = in_game.get("moving_message", "Not all blocks stay still...")
    rendered_moving_text = render_text(moving_text, True, (128, 0, 128))  # Render the moving text

    pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

    screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))

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
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
        show_greenrobo_unlocked = False

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
            fin_lvl_logic(1)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.lvl1speed(current_time)
            Achievements.check_green_gold()

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

        screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))
        
        player_image(keys, player_x, player_y, camera_x, camera_y)

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

            # Inside the game loop:
        screen.blit(rendered_up_text, (700 - camera_x, 200 - camera_y))  # Draws the rendered up text
        screen.blit(rendered_warning_text, (1900 - camera_x, 150 - camera_y))  # Draws the rendered warning text
        screen.blit(rendered_moving_text, (1350 - camera_x, 170 - camera_y))  # Draws the rendered moving text
        screen.blit(rendered_exit_text, (2400 - camera_x, 300 - camera_y))  # Draws the rendered exit text

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        medal = get_medal(1, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

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
                reset_text = render_text(f"Resetting the level in {countdown:.2f}", True, (255, 0, 0))
                screen.blit(reset_text, (SCREEN_WIDTH // 2 - 200 , 300))             
        else:
            ctime = None

        # Initialize and draw the quit text
        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        levels = load_language(lang_code).get('levels', {})
        lvl1_text = levels.get("lvl1", "Level 1")  # Render the level text
        screen.blit(render_text(lvl1_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(render_text(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None
        draw_notifications()
        draw_syncing_status()
        pygame.display.update()    

def create_lvl2_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, wait_time, transition_time, is_transitioning, current_time, medal, deathcount, score
    global new_hs, hs, stars, ctime
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

    exit_portal = pygame.Rect(4330, 460, 140, 180)
    clock = pygame.time.Clock()
    
    # Render the texts
    jump_message = in_game.get("jump_message", "Use orange blocks to jump high distances!")
    rendered_jump_text = render_text(jump_message, True, (255, 128, 0))  # Render the jump text

    if checkpoint_reached:
            screen.blit(act_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    else:
            screen.blit(nact_cp, ((flag_1_x - camera_x), (flag_1_y - camera_y)))



    pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

    for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (jump_block.x - camera_x, jump_block.y - camera_y, jump_block.width, jump_block.height))

    screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))

            # Inside the game loop:
    screen.blit(rendered_jump_text, (900 - camera_x, 500 - camera_y))  # Draws the rendered up text

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False
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
            fin_lvl_logic(2)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

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

        screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))
        
        player_image(keys, player_x, player_y, camera_x, camera_y)

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        medal = get_medal(2, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

            # Inside the game loop:
        screen.blit(rendered_jump_text, (900 - camera_x, 500 - camera_y))  # Draws the rendered up text

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = render_text(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        levels = load_language(lang_code).get('levels', {})
        lvl2_text = levels.get("lvl2", "Level 2")  # Render the level text
        screen.blit(render_text(lvl2_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False
                
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
                reset_text = render_text(f"Resetting the level in {countdown:.2f}", True, (255, 0, 0))
                screen.blit(reset_text, (SCREEN_WIDTH // 2 - 200 , 300))             
        else:
            ctime = None
        
        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(render_text(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None
        draw_notifications()
        draw_syncing_status()
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

    exit_portal = pygame.Rect(430, -330, 140, 180)
    clock = pygame.time.Clock()

    saw_text = in_game.get("saws_message", "Saws are also dangerous!")
    rendered_saw_text = render_text(saw_text, True, (255, 0, 0))  # Render the saw text

    key_text = in_game.get("key_message", "Grab the coin and open the block!")
    rendered_key_text = render_text(key_text, True, (255, 255, 0))  # Render the key text

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

    screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))

        # Draw the texts
    screen.blit(rendered_saw_text, (int(550 - camera_x), int(600 - camera_y)))  # Draws the rendered up text
    screen.blit(rendered_key_text, (int(2500 - camera_x), int(200 - camera_y)))  # Draws the rendered up text
    if show_greenrobo_unlocked:
        messages = load_language(lang_code).get('messages', {})
        if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
            unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
            rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
            screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
        show_greenrobo_unlocked = False
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
            fin_lvl_logic(3)
            level_complete()    
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

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

        screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))
        
        player_image(keys, player_x, player_y, camera_x, camera_y)

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        screen.blit(rendered_saw_text, (int(550 - camera_x), int(600 - camera_y)))  # Draws the rendered up text
        screen.blit(rendered_key_text, (int(2500 - camera_x), int(200 - camera_y)))  # Draws the rendered up text

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = render_text(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        medal = get_medal(3, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

        levels = load_language(lang_code).get('levels', {})
        lvl3_text = levels.get("lvl3", "Level 3")  # Render the level text
        screen.blit(render_text(lvl3_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text
        
        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(render_text(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None
        draw_notifications()
        draw_syncing_status()
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
    exit_portal = pygame.Rect(4870, 265, 140, 180)
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


    screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False
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
            fin_lvl_logic(4)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

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


        screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))
        
        player_image(keys, player_x, player_y, camera_x, camera_y)

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = render_text(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        medal = get_medal(4, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

        levels = load_language(lang_code).get('levels', {})
        lvl4_text = levels.get("lvl4", "Level 4")  # Render the level text
        screen.blit(render_text(lvl4_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(render_text(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None
        draw_notifications()
        draw_syncing_status()
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
        [(3900, -20), (3950, 30), (4000, -20)],
        [(3900, -620), (3950, -570), (4000, -620)],
        [(4200, -420), (4250, -370), (4300, -420)],
        [(4500, -20), (4550, 30), (4600, -20)],
        [(4800, -720), (4850, -670), (4900, -720)],
        [(4800, -120), (4850, -70), (4900, -120)],
    ]

    spikes_01 = [
    [(4200, -150), (4250, -200), (4300, -150)],
    [(4500, -350), (4550, -400), (4600, -350)],
    [(4500, -650), (4550, -700), (4600, -650)],
    [(4800, -450), (4850, -500), (4900, -450)],
    ]

    exit_portal = pygame.Rect(1360, 20, 140, 180)
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


    screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False
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
            fin_lvl_logic(5)
            level_complete()

            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

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
            if block.width < 100:
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


        screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))
       
        player_image(keys, player_x, player_y, camera_x, camera_y)

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = render_text(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        medal = get_medal(5, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

        levels = load_language(lang_code).get('levels', {})
        lvl5_text = levels.get("lvl5", "Level 5")  # Render the level text
        screen.blit(render_text(lvl5_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(render_text(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None
        draw_notifications()
        draw_syncing_status()
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

    exit_portal = pygame.Rect(5630, 340, 140, 180)
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

    screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))

    if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False
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
            fin_lvl_logic(6)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()
            Achievements.perfect6(current_time, deathcount)
            save_progress(progress)  # Save progress to JSON file
            running = False
            set_page('worlds')


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

        screen.blit(exit_img, (exit_portal.x - camera_x, exit_portal.y - camera_y))
        
        player_image(keys, player_x, player_y, camera_x, camera_y)

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        
        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = render_text(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        levels = load_language(lang_code).get('levels', {})
        lvl6_text = levels.get("lvl6", "Level 6")  # Render the level text
        screen.blit(render_text(lvl6_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        medal = get_medal(6, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

        invisible_text = in_game.get("invisible_message", "These saws won't hurt you... promise!")
        screen.blit(render_text(invisible_text, True, (255, 51, 153)), (900 - camera_x, 250 - camera_y)) # Render the invisible block text

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                if val > 0.3:
                    screen.blit(render_text(death_text, True, (255, 0, 0)), (20, 50))
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

        draw_notifications()
        draw_syncing_status()
        pygame.display.update()   

def create_lvl7_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    start_time = time.time()
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(mech_background, (0, 0))

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

    exit_portal = pygame.Rect(2030, -1245, 70, 120)
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
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False
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
            fin_lvl_logic(7)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

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
        screen.blit(mech_background, (0, 0))

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
        player_image(keys, player_x, player_y, camera_x, camera_y)          

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        
        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = render_text(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        medal = get_medal(7, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

        levels = load_language(lang_code).get('levels', {})
        lvl7_text = levels.get("lvl7", "Level 7")  # Render the level text
        screen.blit(render_text(lvl7_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        portal_text = in_game.get("portal_message", "These blue portals teleport you! But to good places... mostly!")
        screen.blit(render_text(portal_text, True, (0, 196, 255)), (4400 - camera_x, 300 - camera_y))

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False
        
        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(render_text(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None
        draw_notifications()
        draw_syncing_status()
        pygame.display.update()   

def create_lvl8_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()

    new_hs = False
    buttons.clear()
    screen.blit(mech_background, (0, 0))

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

    exit_portal = pygame.Rect(11050, -770, 70, 120)
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
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False
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
            fin_lvl_logic(8)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

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
        screen.blit(mech_background, (0, 0))

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
        
        player_image(keys, player_x, player_y, camera_x, camera_y)

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = render_text(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text 
               
        levels = load_language(lang_code).get('levels', {})
        lvl8_text = levels.get("lvl8", "Level 8")  # Render the level text
        screen.blit(render_text(lvl8_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        button1_text = in_game.get("button1_message", "Blue buttons, upon activation, will make you jump higher!")
        screen.blit(render_text(button1_text, True, (0, 102, 204)), (8400 - camera_x, -150 - camera_y))

        clarify_text = in_game.get("clarify_message", "Until you reach a checkpoint, of course!")
        screen.blit(render_text(clarify_text, True, (0, 102, 204)), (9800 - camera_x, -150 - camera_y))

        mock_text = in_game.get("mock_message", "Wrong way my guy nothing to see here...")
        screen.blit(render_text(mock_text, True, (255, 0, 0)), (13200 - camera_x, -300 - camera_y))

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        medal = get_medal(8, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(render_text(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None
        draw_notifications()
        draw_syncing_status()
        pygame.display.update()   

def create_lvl9_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(mech_background, (0, 0))
    
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

    exit_portal = pygame.Rect(3370, 480, 70, 120)
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
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False
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
            fin_lvl_logic(9)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.lvl90000(score)
            Achievements.check_green_gold()

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
        screen.blit(mech_background, (0, 0))

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

        for block in walls:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

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
        player_image(keys, player_x, player_y, camera_x, camera_y)

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

        # Draw the texts
        
        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = render_text(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        levels = load_language(lang_code).get('levels', {})
        lvl9_text = levels.get("lvl9", "Level 9")  # Render the level text
        screen.blit(render_text(lvl9_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        button2_text = in_game.get("button2_message", "Lavender buttons, upon activation, will make you jump lower!")
        screen.blit(render_text(button2_text, True, (204, 102, 204)), (100 - camera_x, 100 - camera_y))

        clarify2_text = in_game.get("clarify_message2", "They also affect your jumps on jump blocks!")
        screen.blit(render_text(clarify2_text, True, (204, 102, 204)), (1000 - camera_x, 450 - camera_y))

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        medal = get_medal(9, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(render_text(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None
        draw_notifications()
        draw_syncing_status()
        pygame.display.update() 

def create_lvl10_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    new_hs = False
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    buttons.clear()
    screen.blit(mech_background, (0, 0))

    wait_time = None
    start_time = time.time()

    in_game = load_language(lang_code).get('in_game', {})

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

    exit_portal = pygame.Rect(6080, 360, 70, 120)
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
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False
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
            fin_lvl_logic(10)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

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
        screen.blit(mech_background, (0, 0))

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
        
        player_image(keys, player_x, player_y, camera_x, camera_y)

        # Draw the texts

        button2_text = in_game.get("button3_message", "Purple buttons, upon activation, will turn out almost all the lights!")
        screen.blit(render_text(button2_text, True, (104, 102, 204)), (100 - camera_x, 300 - camera_y))

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
        screen.blit(render_text(lvl10_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = render_text(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

        medal = get_medal(10, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

        if show_greenrobo_unlocked:
            messages = load_language(lang_code).get('messages', {})
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(render_text(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None
        draw_notifications()
        draw_syncing_status()
        pygame.display.update() 

def create_lvl11_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(mech_background, (0, 0))

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
    evilrobo_mascot = pygame.image.load(resource_path(f"char/evilrobot/evilrobot.png")).convert_alpha()
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

    exit_portal = pygame.Rect(6620, 330, 70, 120)
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
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
    else:
            show_greenrobo_unlocked = False
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
            fin_lvl_logic(11)
            level_complete()
            # Check if all medals from lvl1 to lvl11 are "Gold"
            Achievements.check_green_gold()

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
        screen.blit(mech_background, (0, 0))

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
                sus_message = render_text("Huh? Is there anyone there?", True, (255, 20, 12))
                screen.blit(sus_message, (4800 - camera_x, -450 - camera_y))
            else:
                if evilrobo_phase < 1:
                    evilrobo_phase = 1  # Prevents repeating

        if evilrobo_phase == 1 and player_y < -300 and lights_off:
            holup_message = render_text("HEY! Get away from here!", True, (185, 0, 0))
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
                confused_text = render_text("WHERE DID HE GO????", True, (82, 0, 0))
                screen.blit(confused_text, ((epos_x - camera_x), (epos_y - camera_y)))
                if not unlock:
                    if not is_mute:
                        notify_sound.play()
                    unlock = True
                    unlock_time = pygame.time.get_ticks()
                    progress["char"]["evilrobo"] = unlock
                    save_progress(progress)
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
                if not is_mute:
                    hit_sound.play()


        button4_text = in_game.get("button4_message", "Green buttons, upon activation, will give you a massive speed boost!")
        rendered_button4_text = render_text(button4_text, True, (51, 255, 51))
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


        player_image(keys, player_x, player_y, camera_x, camera_y)

        levels = load_language(lang_code).get('levels', {})
        lvl11_text = levels.get("lvl11", "Level 11")  # Render the level text
        screen.blit(render_text(lvl11_text, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 50, 20)) # Draws the level text

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = render_text(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner
        
        medal = get_medal(11, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

        if show_greenrobo_unlocked:
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = messages.get("greenrobo_unlocked", "Green Robo Unlocked!")
                rendered_unlocked_text = render_text(unlocked_text, True, (51, 255, 51))
                screen.blit(rendered_unlocked_text, (SCREEN_WIDTH // 2 - rendered_unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(render_text(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None
        draw_notifications()
        draw_syncing_status()
        pygame.display.update()

def create_lvl12_screen():
    global player_img, font, screen, complete_levels, is_mute, selected_character, show_greenrobo_unlocked, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global selected_character, player_img, moving_img, moving_img_l, img_width, img_height
    char_assets()
    new_hs = False
    buttons.clear()
    screen.blit(mech_background, (0, 0))

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

    # Other settings
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    lights_off = True

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
        pygame.Rect(4500, 750, 60000, 200),
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

    exit_portal = pygame.Rect(4113, -820 ,70, 120)
    clock = pygame.time.Clock()
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
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if stamina:
                    velocity_x = stamina_speed
                    player_x += velocity_x
                else:
                    velocity_x = move_speed
                    player_x += velocity_x

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
            fin_lvl_logic(12)
            level_complete()
            save_progress(progress)  # Save progress to JSON file
           
            # Check if all medals from lvl1 to lvl12 are "Gold"
            Achievements.check_green_gold()
            
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
        screen.blit(mech_background, (0, 0))

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

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))        

        for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

        for spike in spikes:
            pygame.draw.polygon(screen, (255, 0, 0), [((x - camera_x),( y - camera_y)) for x, y in spike])

        pygame.draw.rect(screen, (129, 94, 123), (int(exit_portal.x - camera_x), int(exit_portal.y - camera_y), exit_portal.width, exit_portal.height))

        timed_coin_text = in_game.get("timed_coin_message", "Orange coins are timed! They open blocks for a limited")
        rendered_timed_text = render_text(timed_coin_text, True, (255, 128, 0))
        screen.blit(rendered_timed_text, (0 - camera_x, -80 - camera_y))
        timed_coin_text_2 = in_game.get("timed_coin_message_2", "time. Run before they close again, or at worst, crush you...")
        rendered_timed_text_2 = render_text(timed_coin_text_2, True, (255, 128, 0))
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

        levels = load_language(lang_code).get('levels', {})
        lvl_text = levels.get("lvl12", "Level 12")  # Render the level text
        rendered_lvl_text = render_text(lvl_text, True, (255, 255, 255))
        screen.blit(rendered_lvl_text, (SCREEN_WIDTH //2 - rendered_lvl_text.get_width() // 2, 20)) # Draws the level text

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        screen.blit(render_text(deaths_val, True, (255, 255, 255)), (20, 20))

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = render_text(reset_text, True, (255, 255, 255))  # Render the reset text
        screen.blit(rendered_reset_text, (10, SCREEN_HEIGHT - 54))  # Draws the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = render_text(quit_text, True, (255, 255, 255))  # Render the quit text
        screen.blit(rendered_quit_text, (SCREEN_WIDTH - 203, SCREEN_HEIGHT - 54))  # Draws the quit text

        medal = get_medal(12, current_time)
        if medal == "Gold":
            if deathcount == 0:
                screen.blit(diam_m, (SCREEN_WIDTH - 300, 20))
            else:
                screen.blit(gold_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Silver":
            screen.blit(silv_m, (SCREEN_WIDTH - 300, 20))
        elif medal == "Bronze":
            screen.blit(bron_m, (SCREEN_WIDTH - 300, 20))

        timer_text = render_text(f"Time: {formatted_time}s", True, (255, 255, 255))  # white color
        screen.blit(timer_text, (SCREEN_WIDTH - 200, 20))  # draw it at the top-left corner

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
                weak_grav = False
                strong_grav = False
                    # Trigger death logic
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1
                if not is_mute:
                    death_sound.play()
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                velocity_y = 0

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
                weak_grav = False
                strong_grav = False
                velocity_y = 0
                death_text = in_game.get("sawed_message", "Sawed to bits!")
                wait_time = pygame.time.get_ticks()  # Start the wait time
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                if not is_mute:
                    death_sound.play()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1


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
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                if not is_mute:
                    death_sound.play()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                deathcount += 1


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
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["timer"] = 0  # Reset the timer for all key blocks
                velocity_y = 0
                wait_time = pygame.time.get_ticks()  # Start the wait time
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
                    stamina = False  # Reset stamina status
                    lights_off = True
                    weak_grav = False
                    strong_grav = False
                    player_x, player_y = spawn_x, spawn_y  # Reset player position
                    death_text = in_game.get("dead_message", "You Died")
                    wait_time = pygame.time.get_ticks()  # Start the wait time
                    if not is_mute:
                        death_sound.play()
                    for pair in key_block_pairs_timed:
                        pair["collected"] = False  # Reset the collected status for all keys
                        pair["timer"] = 0  # Reset the timer for all key blocks
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
                    wait_time = pygame.time.get_ticks()  # Start the wait time
                    if not is_mute:
                        death_sound.play()
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
                    break

        if player_y > 1100:
            death_text = in_game.get("fall_message", "Fell too far!")
            wait_time = pygame.time.get_ticks()  # Start the wait time
            stamina = False  # Reset stamina status
            lights_off = True
            weak_grav = False
            strong_grav = False
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["timer"] = 0  # Reset the timer for all key blocks
            if not is_mute:    
                fall_sound.play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

        # Player Image
        player_image(keys, player_x, player_y, camera_x, camera_y)

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                screen.blit(render_text(death_text, True, (255, 0 ,0)), (20, 50))
            else:
                wait_time = None
        draw_notifications()
        draw_syncing_status()
        pygame.display.update() 

transition_time = None
is_transitioning = False

# Handle actions based on current page
def handle_action(key):
    global progress, current_page, pending_level, level_load_time, transition, is_transitioning, transition_time,locked_char_sound_played, locked_char_sound_time
    
    global pending_page
    if current_page == 'main_menu':
        if key == "start":
            if not is_transitioning:
                transition.start("worlds")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "worlds"
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
    elif current_page == "settings":
        if key == "Back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
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
            progress = load_progress()
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
                change_language(key)
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
            death_sound.play()
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
    global username, user_pass, input_mode, login_done, progress, buttons
    login_done = False
    status_msg = ""
    status_color = (180, 180, 180)
    if transition.x <= -transition.image.get_width():
       while not login_done:
        screen.blit(background, (0, 0))
        # 1. Header
        id_title = render_text(f"LOGIN / REGISTER", True, (255, 255, 255))
        screen.blit(id_title, (SCREEN_WIDTH // 2 - id_title.get_width() // 2, 80))

        # 2. Instructions
        instr = render_text("Enter your username and the password for your account.", True, (255, 255, 255))
        screen.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2 , 200))
        
        instr2 = render_text("If the account does not exist, a new account will be created for you.", True, (255, 255, 255))
        screen.blit(instr2, (SCREEN_WIDTH // 2 - instr2.get_width() // 2 , 230))

        instr3 = render_text("Press TAB to switch between inputting Password and Username. To return, press ESC.", True, (255, 255, 255))
        screen.blit(instr3, (SCREEN_WIDTH // 2 - instr3.get_width() // 2 , 260))
        
        # 3. Status Message (Errors, Success, etc.)
        if status_msg:
            s_surf = render_text(status_msg, True, status_color)
            screen.blit(s_surf, (SCREEN_WIDTH // 2 - s_surf.get_width() // 2, 300))

        # 4. Inputs
        u_color = (255, 255, 255) if input_mode == "USER" else (80, 80, 80)
        u_surf = render_text(f"Username: {username}", True, u_color)
        screen.blit(u_surf, (SCREEN_WIDTH // 2 - u_surf.get_width() // 2, 350))

        p_color = (255, 255, 255) if input_mode == "PASS" else (80, 80, 80)
        stars = "*" * len(user_pass)
        p_surf = render_text(f"Password: {stars}", True, p_color)
        screen.blit(p_surf, (SCREEN_WIDTH // 2 - p_surf.get_width() // 2, 420))

        submit_txt = render_text("Press ENTER to Continue", True, (0, 255, 0))
        screen.blit(submit_txt, (SCREEN_WIDTH // 2 - submit_txt.get_width() // 2, 550))

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
                        status_msg = "Checking Cloud Vault..."
                        print(status_msg)
                        status_color = (255, 255, 0)
                        
                        # Draw immediately so user sees "Checking..."
                        pygame.display.update()
                        
                        # --- CLOUD CHECK LOGIC ---
                        result = recover_account_from_cloud(username, user_pass)
                        
                        if isinstance(result, dict):
                            # [SCENARIO 1] FOUND: Sync existing
                            progress = result
                            status_msg = "Account Recovered!"
                            status_color = (0, 255, 0)
                            # This saves to [OLD_ID].json
                            save_progress(progress)
                            login_done = True
                            
                        elif result == "WRONG_AUTH":
                            # [SCENARIO 2] FOUND BUT WRONG PASS
                            status_msg = "Wrong Password for this user!"
                            status_color = (255, 50, 50)
                            death_sound.play()
                            
                        else:
                            # [SCENARIO 3] NOT FOUND: Create New
                            # 1. Wipe progress to default so we don't clone the previous player's stats
                            progress = copy.deepcopy(default_progress)
                            
                            # 2. Generate FRESH ID (This creates the new file!)
                            new_id = generate_player_id()
                            hashed_p = hashlib.sha256(user_pass.encode()).hexdigest()
                            
                            progress["player"]["ID"] = new_id
                            progress["player"]["Username"] = username
                            progress["player"]["Pass"] = hashed_p
                            
                            status_msg = f"New Account Created! (ID: {new_id})"
                            status_color = (0, 255, 255)
                            
                            # 3. Save locally -> Creates [NEW_ID].json
                            save_progress(progress)
                            login_done = True
                            
                    else:
                        death_sound.play()
                        status_msg = "Username/Password too short!"
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
    
    # 1. Load the local manifest
    manifest = {"users": {}}
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as f:
                manifest = json.load(f)
        except: pass
    
    accounts = manifest.get("users", {})
    
    # 2. Create Account Buttons
    y_pos = 200
    for p_id, info in accounts.items():
        name_str = info.get("username", "Unknown")
        
        rendered_name = render_text(name_str, True, (255, 255, 255))
        rect = rendered_name.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
        
        # Append to buttons list
        buttons.append((rendered_name, rect, f"load_user_{p_id}", False))
        y_pos += 100

    # 3. "New Player" Button
    new_txt_rendered = render_text("+ NEW PLAYER", True, (255, 255, 255))
    new_rect = new_txt_rendered.get_rect(center=(SCREEN_WIDTH // 2, y_pos + 40))
    buttons.append((new_txt_rendered, new_rect, "new_account", False))

if not is_mute and SCREEN_WIDTH > MIN_WIDTH and SCREEN_HEIGHT > MIN_HEIGHT:
    click_sound.play()

# Info

site_text = font_def.render("Sound effects used from pixabay.com and edited using Audacity", True, (255, 255, 255))
site_pos = (SCREEN_WIDTH - (site_text.get_width() + 10), SCREEN_HEIGHT - 38)
logo_text = font_def.render("Logo and Background made with canva.com", True, (255, 255, 255))
logo_pos = (SCREEN_WIDTH - (logo_text.get_width() + 10), SCREEN_HEIGHT - 68)
credit_text = font_def.render("Made by Omer Arfan", True, (255, 255, 255))
credit_pos = (SCREEN_WIDTH - (credit_text.get_width() + 10), SCREEN_HEIGHT - 98)
ver_text = font_def.render("Version 1.2.93.2", True, (255, 255, 255))
ver_pos = (SCREEN_WIDTH - (ver_text.get_width() + 12), SCREEN_HEIGHT - 128)

print(progress)
# First define current XP outside the loop
level, xp_needed, xp_total = xp()
XP_text = font_text.render(f"{level}", True, (255, 255, 255))
if level < 20:
    XP_text2 = font_def.render(f"{xp_needed}/{xp_total}", True, (255, 255, 255))
else:
    max_txt = load_language(lang_code).get('messages', {}).get("max_level", "MAX LEVEL!")
    XP_text2 = render_text(max_txt, True, (225, 212, 31))

while running:
    # This is in the main loop, unlike the other texts, because it needs to update if the player changes!
    ID_text = font_def.render(f"ID: {progress['player']['ID']}", True, (255, 255, 255))
    ID_pos = (SCREEN_WIDTH - (ID_text.get_width() + 10), 0)

    messages = load_language(lang_code).get('messages', {})
    # Clear screen!
    screen.blit(background, (0, 0))
    mouse_pos = pygame.mouse.get_pos()

    if transition_time is not None and pygame.time.get_ticks() - transition_time > 1000:
        transition_time = None
        is_transitioning = False

    # Handle transition timer and page change
    if is_transitioning and transition_time is not None and pending_page is not None:
        if transition.x >= 0:
            # Then recheck if XP has been added or not.
            level, xp_needed, xp_total = xp()
            XP_text = font_text.render(f"{level}", True, (255, 255, 255))
            if level < 20:
                XP_text2 = font_def.render(f"{xp_needed}/{xp_total}", True, (255, 255, 255))
            else:
                max_txt = load_language(lang_code).get('messages', {}).get("max_level", "MAX LEVEL!")
                XP_text2 = render_text(max_txt, True, (225, 212, 31))
            # Then let transition loop play as normal
            is_transitioning = False
            current_pending = pending_page
            transition_time = None
            pending_page = None
            set_page(current_pending)

    XP_pos2 = (SCREEN_WIDTH - (XP_text2.get_width() + 10), 50)
    XP_pos = (SCREEN_WIDTH - (XP_text.get_width() + XP_text2.get_width() + 30), 30)
    xp_center_x = XP_pos[0] + (XP_text.get_width() / 2)
    badge_x = xp_center_x - (badge.get_width() / 2)
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
            screen.blit(evilrobot_img, (SCREEN_WIDTH // 2 - evilrobot_img.get_width() // 2, SCREEN_HEIGHT // 2 - 200))

            # Render the text
            messages = load_language(lang_code).get('messages', {})
            deny_text = messages.get("deny_message", "Access denied!")
            rendered_deny_text = render_text(deny_text, True, (255, 100, 100))
            error_text = messages.get("error_message","Your screen resolution is too small! Increase the screen")
            rendered_error_text = render_text(error_text, True, (255, 255, 255))
            error_text2 = messages.get("error_message2", "resolution in your system settings.")
            rendered_error_text2 = render_text(error_text2, True, (255, 255, 255))
            countdown_text = messages.get("countdown_message", "Closing in {countdown} second(s)...").format(countdown=countdown)
            rendered_countdown_text = render_text(countdown_text, True, (255, 100, 100))

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
                                click_sound.play()
                            handle_action(key)
                            last_page_change_time = time.time()
                elif current_page in ["levels", "mech_levels", "worlds"]:
                    for rendered, rect, key, is_locked in buttons:
                        if rect.collidepoint(event.pos):
                            if key is not None and not is_mute:
                                click_sound.play()
                            handle_action(key)  # Only load level on click!
                    
        if current_page == "main_menu":
            screen.blit(logo, ((SCREEN_WIDTH // 2 - logo.get_width() // 2), 30))
            screen.blit(lilrobopeek, ((SCREEN_WIDTH - lilrobopeek.get_width()), (SCREEN_HEIGHT - lilrobopeek.get_height())))
            screen.blit(logo_text, logo_pos)
            screen.blit(site_text, site_pos)
            screen.blit(credit_text, credit_pos)
            screen.blit(ver_text, ver_pos)
            screen.blit(ID_text, ID_pos)
            if level < 20:
                screen.blit(badge, badge_pos)
            else:
                screen.blit(max_badge, badge_pos)
            screen.blit(XP_text, XP_pos)
            screen.blit(XP_text2, XP_pos2)
        # Render the main menu buttons
            hovered_key = None
            for rendered, rect, key, is_locked in buttons:
                mouse_pos = pygame.mouse.get_pos()
                if studio_logo_rect.collidepoint(mouse_pos):
                    screen.blit(studio_glow, studio_glow_rect.topleft)
                    if not logo_hover:
                        if not is_mute:
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
                    if hovered_key != last_hovered_key and not is_mute:
                        hover_sound.play()

                screen.blit(rendered, rect)
            last_hovered_key = hovered_key

        if current_page == "character_select":
         screen.blit(background, (0, 0))

         # Initialize locked sound effect and mouse position
         locked_sound_played = False
         mouse_pos = pygame.mouse.get_pos()

         messages = load_language(lang_code).get('messages', {})  # Fetch localized messages
         char_text = render_text("Select your Robo!", True, (255, 255, 255))
         screen.blit(char_text, (SCREEN_WIDTH // 2 - 100, 50))

         # Check if characters are locked
         robo_unlock = True
         evilrobo_unlock = progress["char"].get("evilrobo", False)
         greenrobo_unlock = progress["char"].get("greenrobo", False)
         ironrobo_unlock = progress["char"].get("ironrobo", False)
         # Draw images
         screen.blit(robot_img, robot_rect)     
         screen.blit(evilrobot_img if evilrobo_unlock else locked_img, evilrobot_rect)
         screen.blit(greenrobot_img if greenrobo_unlock else locked_img, greenrobot_rect)
         screen.blit(ironrobot_img if ironrobo_unlock else locked_img, ironrobot_rect)
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
             rendered_locked_text = render_text(locked_text, True, (255, 255, 0))
             screen.blit(rendered_locked_text, ((SCREEN_WIDTH // 2 - rendered_locked_text.get_width() // 2), SCREEN_HEIGHT - 700))
            else:
             wait_time = None

        if current_page == "language_select":
            screen.blit(background, (0, 0))
            screen.blit(heading_text, (SCREEN_WIDTH // 2 - heading_text.get_width() // 2, 50))

        if current_page == "quit_confirm":
            screen.blit(background, (0, 0))
            # Render the quit confirmation text
            screen.blit(quit_text, quit_text_rect)
            screen.blit(quitbot, (SCREEN_WIDTH // 2 - robot_img.get_width() // 2, SCREEN_HEIGHT // 2 - 200))

            # Render the "Yes" and "No" buttons
            for rendered, rect, key, is_locked in buttons:
                if rect.collidepoint(mouse_pos):
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((8, 81, 179, 255))
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)      
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered
                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((8, 81, 179, 255))
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
                screen.blit(rendered, rect)

            # Allow returning to the main menu with ESC
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                set_page("main_menu")

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
        
        elif current_page == "levels" or current_page == "mech_levels":
            if current_page == "levels":
                screen.blit(green_background, (0, 0))
                disk_img = greendisk_img
            else:
                screen.blit(mech_background, (0, 0))
                disk_img = mechdisk_img
            # Fetch the localized "Select a Level" text dynamically
            select_text = current_lang.get("level_display", "Select a Level")
            rendered_select_text = render_text(select_text, True, (255, 255, 255))
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
            # Show Level stats - check current mouse position every frame
            for text_surface, disk_rect, key, is_locked in buttons:
                if disk_rect.collidepoint(mouse_pos):
                    if key != "next" and key != "back" and not is_locked:
                        hs = progress["lvls"]['score'][key]
                        high_text = messages.get("hs_m", "Highscore: {hs}").format(hs=hs)
                        lvl_score_text = render_text(high_text, True, (255, 255, 0))

                        # Adjust position as needed
                        screen.blit(lvl_score_text, (SCREEN_WIDTH // 2 - lvl_score_text.get_width() // 2, SCREEN_HEIGHT - 50))
                        s = key
                        num = int(s[3:])  # Skip the first 3 characters
                        medals = progress["lvls"]['medals'][key]
                        if medals == "Diamond":
                            screen.blit(diam_m, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 80))
                        if medals == "Gold":
                            screen.blit(gold_m, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 80))
                        elif medals == "Silver":
                            screen.blit(silv_m, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 80))
                        elif medals == "Bronze":
                            screen.blit(bron_m, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 80))

                        stars = get_stars(num, progress["lvls"]['score'][key])
                        if stars >= 1:
                            screen.blit(s_star_img, (SCREEN_WIDTH // 2 - 25, SCREEN_HEIGHT - 80))
                        if stars >= 2:
                            screen.blit(s_star_img, (SCREEN_WIDTH // 2 , SCREEN_HEIGHT - 80))
                        if stars == 3:
                            screen.blit(s_star_img, (SCREEN_WIDTH // 2 + 25, SCREEN_HEIGHT - 80))
            
            for text_surface, disk_rect, key, is_locked in buttons: 
                if key is not None:
                    screen.blit(disk_img, disk_rect)
                else:
                    screen.blit(lockeddisk_img, disk_rect)
                text_rect = text_surface.get_rect(center=(disk_rect.x + 50, disk_rect.y + 50))
                screen.blit(text_surface, text_rect)

        elif current_page == "settings":
            screen.blit(background, (0, 0))
            settings_menu()
            
            for rendered, rect, key, is_locked in buttons:
                if rect.collidepoint(mouse_pos):
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((8, 81, 179, 255))
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered
                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((8, 81, 179, 255))
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
                screen.blit(rendered, rect)

        elif current_page == "Audio":
            screen.blit(background, (0, 0))
            audio_settings_menu()
            
            for rendered, rect, key, is_locked in buttons:
                if rect.collidepoint(mouse_pos):
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((8, 81, 179, 255))
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered
                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((8, 81, 179, 255))
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
                screen.blit(rendered, rect)

        elif current_page == "Account":
            screen.blit(background, (0, 0))
            
            # 1. Draw the Title Manually Here
            title = font_text.render("SELECT PROFILE", True, (255, 255, 255))
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

            # 2. Draw the Buttons (Using the standard button loop)
            for rendered, rect, key, is_locked in buttons:
                if rect.collidepoint(mouse_pos):
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((8, 81, 179, 255))
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered
                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((8, 81, 179, 255))
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)

                screen.blit(rendered, rect)

        elif current_page == "login_screen":
            show_login_screen()
        
        else:
            # Render buttons for other pages
            for rendered, rect, key, is_locked in buttons:
                if rect.collidepoint(mouse_pos):
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((8, 81, 179, 255))
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
                    hovered = rect.collidepoint(pygame.mouse.get_pos())
                    if hovered and not button_hovered_last_frame and not is_mute:
                        hover_sound.play()
                    button_hovered_last_frame = hovered
                else:
                    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
                    button_surface.fill((8, 81, 179, 255))
                    screen.blit(button_surface, rect.inflate(20, 10).topleft)
                    pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
                screen.blit(rendered, rect)

        if show_greenrobo_unlocked:
            if time.time() - greenrobo_unlocked_message_time < 4:  # Show for 4 seconds
                unlocked_text = render_text("Green Robo Unlocked!", True, (51, 255, 51))
                screen.blit(unlocked_text, (SCREEN_WIDTH // 2 - unlocked_text.get_width() // 2, 100))
        else:
            show_greenrobo_unlocked = False
        
        draw_notifications()

        draw_syncing_status()
        
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(cursor_img, mouse_pos)

        if transition.active:
            transition.update()
        
        pygame.display.flip()

pygame.quit()