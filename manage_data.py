import copy
import json
import os
import shutil
import time
import threading
import sys
import menu_ui
from datetime import datetime, date
import csv
import hashlib
import threading
import requests
from io import StringIO
import pygame
import acc_sys
import level_logic

pygame.font.init()

# The Global Asset Vault
manifest, lang_code = None, None
is_mute, is_mute_amb = False, False
progress = {}
sounds = {}
ui = {}
bgs = {}
assets = {}
medals = {}
disks = {}
robos = {}
fonts = {}
current_page = 'main_menu'

default_progress = {
    "player": {
        "ID": "",
        "Username": "",
        "Pass": "",
        "XP": 0,
        "Level": 1
    },
    "lvls": { 
        "complete_levels": 0,
        "locked_levels": [f"lvl{i}" for i in range(2, 13)],
        "times": {f"lvl{i}": 0 for i in range(1, 13)},
        "medals": {f"lvl{i}": "None" for i in range(1, 13)},
        "score": {f"lvl{i}": 0 for i in range(1, 13)}
    },
    "pref" : { 
        "character": "robot"
    },
    "char": { 
        "evilrobo": False, 
        "greenrobo": False,
        "ironrobo": False
    },
    "achieved": { 
        "speedy_starter": False,
        "zen_os": False,
        "over_9k": False,
        "chase_escape": False,
        "golden": False,
        "lv20": False
    }
}

save_count = 0

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

def resource_path(relative_path): 
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

with open(resource_path("data/thresholds.json"), "r", encoding="utf-8") as f:
    thresholds_data = json.load(f)
    level_thresholds = thresholds_data["level_thresholds"]
    score_thresholds = thresholds_data["score_thresholds"]

fonts = {}

def char_assets(selected_character):
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
        blink_img = pygame.image.load(resource_path(f"char/greenrobot/blinkgreenrobot.png")).convert_alpha()
        moving_img_l = pygame.image.load(resource_path(f"char/greenrobot/movegreenrobotL.png")).convert_alpha() # Resize to fit the game
        moving_img = pygame.image.load(resource_path(f"char/greenrobot/movegreenrobot.png")).convert_alpha() # Resize to fit the game
    elif selected_character == "ironrobot":
        player_img = pygame.image.load(resource_path(f"char/ironrobot/ironrobo.png")).convert_alpha()
        blink_img = pygame.image.load(resource_path(f"char/ironrobot/blinkironrobo.png")).convert_alpha()
        moving_img_l = pygame.image.load(resource_path(f"char/ironrobot/ironrobomoveL.png")).convert_alpha() # Resize to fit the game
        moving_img = pygame.image.load(resource_path(f"char/ironrobot/ironrobomove.png")).convert_alpha() # Resize to fit the game
    img_width, img_height = player_img.get_size()
    return player_img, blink_img, moving_img, moving_img_l, img_width, img_height

def change_ambience(new_file):
  if not is_mute_amb:
    pygame.mixer.music.load(resource_path(new_file))
    pygame.mixer.music.set_volume(2)  # Adjust as needed
    pygame.mixer.music.play(-1)

def update_locked_levels(progress, manifest):
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
    save_progress(progress, manifest)

def load_language(lang_code, manifest):
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

def change_language(lang, manifest, progress):
    global lang_code, last_page_change_time, current_lang, font, font_path_ch, font_path
    lang_code = lang
    last_page_change_time = time.time()  # Track the time when the language changes
    current_lang = load_language(lang_code, manifest)  # Reload the language data
    manifest["pref"]["language"] = lang_code
    update_local_manifest(progress)
    if lang_code == "zh_cn":
        font = fonts['ch']
    elif lang_code == "jp":
        font = fonts['jp']
    elif lang_code == "kr":
        font = fonts['kr']
    elif lang_code == "pk" or lang_code == "ir" or lang_code == "ar":
        font = fonts['ar']
    else:
        font = fonts['def']
    return current_lang

def load_progress():
    global SAVE_FILE
    
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
        except Exception as e:
            print(f"Main save corrupted, trying backup: {e}")
            # TRY THE BACKUP
            backup_file = target_file + ".bak"
            if os.path.exists(backup_file):
                try:
                    with open(backup_file, "r", encoding="utf-8") as f:
                        loaded_data = json.load(f)
                        print("DEBUG: Successfully recovered from backup!")
                except:
                    loaded_data = None
            else:
                loaded_data = None

        if loaded_data:
            data.update(loaded_data)
            sync_missing_data(data) 
            SAVE_FILE = target_file

    # 4. Handle Migration/New ID
    # If we loaded progress.json but have an ID inside it, migrate the filename
    p_id = data["player"].get("ID", "")
    if p_id == "" and not os.path.exists(os.path.join(APP_DATA_DIR, "progress.json")):
        p_id = acc_sys.generate_player_id()
        data["player"]["ID"] = p_id

    # Update SAVE_FILE to the correct ID-specific path
    SAVE_FILE = os.path.join(APP_DATA_DIR, f"{p_id}.json")

    # 5. Migration: If we just loaded from progress.json, copy it to ID.json
    legacy_path = os.path.join(APP_DATA_DIR, "progress.json")
    if os.path.exists(legacy_path) and not os.path.exists(SAVE_FILE):
        try:
            shutil.copy(legacy_path, SAVE_FILE)
            os.remove(legacy_path) # <--- DELETE the old one so it's gone for good!
            print(f"Migrated and cleaned up legacy save.")
        except Exception as e:
            print(f"Migration error: {e}")

    local_xp = data.get("player", {}).get("XP", 0)
    p_id = data["player"].get("ID")

    if p_id:
        print(f"Checking cloud for ID: {p_id}...")
        cloud_data = fetch_cloud_data_by_id(p_id)
        
        if cloud_data:
            cloud_xp = cloud_data.get("player", {}).get("XP", 0)
            if cloud_xp > local_xp:
                print(f"Cloud is ahead! ({cloud_xp} XP). Updating local save...")
                data = cloud_data
                # Update the physical file so we don't have to fetch again next time
                save_progress(data) 
            else:
                print(f"Local save is the latest version ({local_xp} XP).")

    return data

# Save progress to file
def save_progress(data, manifest):
    global notification_text,error_code, notif, er
    global save_count
    global SAVE_FILE 

    # If manifest not provided, load it locally
    if manifest is None:
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except:
            manifest = {"last_used": "", "users": {}, "pref": {"language": "en", "sfx": True, "ambience": True}}

    # 1. Basic Validation: Ensure we aren't saving an empty/broken object
    if not data or "lvls" not in data or "player" not in data:
        if not is_mute:
           sounds['hit'].play()
        notification_text = menu_ui.render_text("Refusing to save: Invalid data structure!", True, (255, 0, 0))
        notif = True
        menu_ui.notification_time = time.time()
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
            threading.Thread(target=sync_vault_to_cloud, args=(data, manifest), daemon=True).start()

    except PermissionError:
       # if not is_mute:
        #    hit_sound.play()
        notification_text = menu_ui.render_text("Error: Save file is locked by another program.", True, (255, 0, 0))
        notif = True
        menu_ui.notification_time = time.time()
            
    except Exception as e:
        er = True
        error_code = menu_ui.render_text(f"Save Error: {str(e)}", True, (255, 0, 0))
       # if not is_mute:
        #   hit_sound.play()
        menu_ui.notification_time = time.time()
        print(f"Detailed save error: {e}")

def update_local_manifest(data):
    global er, error_code, is_mute, manifest
    
    # Store the current last_news_count before reloading
    previous_news_count = manifest.get("other", {}).get("last_news_count", 0) if manifest else 0
    
    # 1. Load existing manifest
    manifest = {"last_used": "", "users": {}, "pref": {"language": "en", "sfx": True, "ambience": True}, "other": {"last_news_count": 0}}
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as f:
                manifest = json.load(f)
        except:
            try:
              # I fmain is corrupted check backup.
              with open(ACCOUNTS_FILE + ".bak", "r") as f:
                manifest = json.load(f)
              # Fixing the main file if it is corrupted.
              with open(ACCOUNTS_FILE, "w") as f_fix:
                    json.dump(manifest, f_fix, indent=4)
            except:
                pass

    # 2. Get current player info
    p_id = data["player"]["ID"]
    p_name = data["player"].get("Username", "User")
    current_lvl = data["player"]["Level"]

    # 3. Update Preferences
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

    if "other" not in manifest:
        manifest["other"] = {"last_news_count": 0}
    
    # Preserve the last_news_count that was set in-memory (don't overwrite with stale disk value)
    manifest["other"]["last_news_count"] = previous_news_count

    # 4. Save with Backup
    try:
        # Create the backup of the OLD version before we save the NEW one
        if os.path.exists(ACCOUNTS_FILE):
            shutil.copy2(ACCOUNTS_FILE, ACCOUNTS_FILE + ".bak")
        
        # Open with "w" to truncate (clear) the file
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump(manifest, f, indent=4)
            f.flush()            # Push data from Python to the OS
            os.fsync(f.fileno()) # Push data from the OS to the actual Hard Drive

    except Exception as e:
        #if not is_mute: hit_sound.play()
        error_code = menu_ui.render_text(f"Local manifest error: {e}", True, (255, 0, 0))
        er = True
        menu_ui.notification_time = time.time()
        print(f"Error during manifest save: {e}")

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
        data["player"]["ID"] = acc_sys.generate_player_id()


def sync_vault_to_cloud(data, manifest):
    global is_syncing, sync_status, sync_finish_time
    is_syncing = True
    settings = load_language(lang_code, manifest)['settings']
    sync_status = settings.get("sync_stat1", "Syncing Vault to Cloud...")

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
            sync_status = settings.get("sync_stat3", "Success!")

    except Exception as e:
        sync_status = settings.get("sync_stat2", "Failed!")

    finally:
        sync_finish_time = time.time()

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
                        #if not is_mute:
                         #   notify_sound.play()
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

def fetch_cloud_data_by_id(target_id):
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQNm-8l1C38UGFt-lJT3ft5DARYZcjMwsWfVYGrtAqDy0bR8MQFcLJSRFqYYX7mbra_P2cWl1-i0WYW/pub?gid=1459647032&single=true&output=csv"
    try:
        # Short timeout so the loading screen doesn't hang if internet is slow
        response = requests.get(CSV_URL, timeout=5)
        if response.status_code == 200:
            f = StringIO(response.text)
            reader = csv.DictReader(f)
            for row in reader:
                # Parse the progress string into a dictionary
                cloud_json = json.loads(row.get('Progress'))
                # Check if the ID inside that JSON matches our local ID
                if cloud_json.get("player", {}).get("ID") == target_id:
                    return cloud_json
                
    except Exception as e:
        print(f"Silent Sync Error: {e}")
        
    return None

def xp():
    global progress
    # XP from scores
    scores = progress["lvls"]["score"]
    score_xp = sum(scores.values()) // 1000

    # XP from stars
    stars = 0
    for level in range(1, 13):
        score = scores.get(f"lvl{level}", 0)
        stars += level_logic.get_stars(level, score)
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

def update_xp_ui():
    global progress, lang_code, manifest
    level, xp_needed, xp_total = xp(progress, Achievements)

    if level < 20:
        color = (255, 255, 255)
        XP_text = fonts['mega'].render(str(level), True, color)
        XP_text2 = menu_ui.render_text(f"{xp_needed}/{xp_total}", True, color)
    else:
        color = (225, 212, 31)
        XP_text = fonts['mega'].render(str(level), True, color)
        max_txt = load_language(lang_code, manifest).get('messages', {}).get("max_level", "MAX LEVEL!")
        XP_text2 = menu_ui.render_text(max_txt, True, color)   

    return XP_text, XP_text2

class Achievements:
    @staticmethod
    def get_notif_text(ach_key, default_name):
        # Helper to build the 'Achievement Unlocked: Name' string
        lang = change_language(lang_code, manifest, progress)
        ach_data = lang.get("achieve", {})
        
        # Get "Achievement Unlocked:" prefix
        prefix = ach_data.get("unlock", "Achievement unlocked:")
        # Get the specific name (e.g., "Speedy Starter!")
        name = ach_data.get(ach_key, default_name)
        
        # Combine them and render
        full_string = f"{prefix} {name}"
        return menu_ui.render_text(full_string, True, (255, 255, 0))

    def lvl1speed(ctime):
        unlock = progress["achieved"].get("speedy_starter", False)
        if ctime <= 4.5 and not unlock:
            progress["achieved"]["speedy_starter"] = True  
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("speedy_starter", "Speedy Starter")
            if not is_mute:
                sounds['notify'].play()
            if menu_ui.notification_time is None:
                notif = True
                menu_ui.notification_time = time.time()
    
    def perfect6(ctime, deaths):
        global notification_text
        unlock = progress["achieved"].get("zen_os", False)
        if ctime <= 30 and deaths <= 0 and not unlock:
            progress["achieved"]["zen_os"] = True
            progress["char"]["ironrobo"] = True
            save_progress(progress, manifest)
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("zen_os", "Zenith of Six")
            if not is_mute:
                sounds['notify'].play()
            if menu_ui.notification_time is None:
                notif = True
                menu_ui.notification_time = time.time()

    def lvl90000(score):
        global notification_text
        unlock = progress["achieved"].get("over_9k", False)
        if score >= 105000 and not unlock:
            progress["achieved"]["over_9k"] = True          
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("over_9k", "It's over 9000!!")
            if not is_mute:
                sounds['notify'].play()
            if menu_ui.notification_time is None:
                notif = True
                menu_ui.notification_time = time.time()
    
    def evilchase():
        global notification_text
        unlock = progress["achieved"].get("chase_escape", False)
        if not unlock:
            progress["achieved"]["chase_escape"] = True
            progress["char"]["evilrobo"] = True
            save_progress(progress, manifest)
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("chase_escape", "Chased and Escaped")
            if not is_mute:
                sounds['notify'].play()
            if menu_ui.notification_time is None:
                notif = True
                menu_ui.notification_time = time.time()
    
    def check_green_gold():
        global notification_text
        all_gold = all(progress["lvls"]["medals"][f"lvl{i}"] in ["Gold", "Diamond"] for i in range(1, 7))
        unlock = progress["achieved"].get("golden", False)
        if all_gold and not unlock:        
            progress["achieved"]["golden"] = True
            progress["char"]["greenrobo"] = True
            save_progress(progress, manifest)
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("golden", "Golden!")
            if not is_mute:
                sounds['notify'].play()
            if menu_ui.notification_time is None:
                notif = True
                menu_ui.notification_time = time.time()
    
    def check_xplvl20(Level):
        global notification_text
        unlock = progress["achieved"].get("lv20", False)
        if Level >= 20 and not unlock:
            progress["achieved"]["lv20"] = True
            save_progress(progress, manifest)
            # LOCALIZED HERE
            notification_text = Achievements.get_notif_text("lv20", "XP Collector!")
            if not is_mute:
                sounds['notify'].play()
            if menu_ui.notification_time is None:
                notif = True
                menu_ui.notification_time = time.time()

import state

def try_select_robo(unlock_flag, char_key, rect, locked_msg_key, fallback_msg, transition):
    if rect.collidepoint(pygame.mouse.get_pos()):
        global selected_character
        charsel = load_language(lang_code, manifest).get('char_select', {})

        if unlock_flag:
            selected_character = char_key
            progress["pref"]["character"] = selected_character
            save_progress(progress, manifest)
            if not is_mute:
                sounds['click'].play()
        else:
            state.handle_action("locked", transition, current_page)  # Trigger the locked transition effect
            if not state.locked_char_sound_played or time.time() - state.locked_char_sound_time > 1.5: # type: ignore
                if not is_mute:
                    sounds['death'].play()
                state.locked_char_sound_time = time.time()
                state.locked_char_sound_played = True
            if state.wait_time is None:
                state.wait_time = pygame.time.get_ticks()
            global locked_text
            locked_text = charsel.get(locked_msg_key, fallback_msg)

def check_for_new_gamenews(return_count):
    url = "https://omerarfan.github.io/lilrobowebsite/gamestuff.html"
    try:
        # 3 second timeout so the game doesn't hang if offline
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            online_count = response.text.count('<a href="gamenews')
            
            # Get the count from our manifest
            local_count = manifest.get("other", {}).get("last_news_count", 0)
            
            # If online has more, we have new news!
            if online_count > local_count:
                print(local_count, online_count)
                if return_count:
                    return online_count
                else:
                    return True
            
    except Exception as e:
        print(f"News check failed: {e}")
    
    if return_count:
        return manifest["other"]["last_news_count"]
    else:
        return False