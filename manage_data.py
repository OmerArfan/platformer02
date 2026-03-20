import copy
import json
import os
import shutil
import time
import threading
import sys
import menu_ui
from datetime import date
import csv
import hashlib
import threading
import requests
from io import StringIO
import pygame

pygame.font.init()

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

fonts = {}

def init_accs():
    global lang_code, is_mute, is_mute_amb
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
    return manifest, lang_code, is_mute, is_mute_amb

def init_fonts():
    global fonts
    font_path_ch = resource_path('fonts/NotoSansSC-SemiBold.ttf')
    font_path_jp = resource_path('fonts/NotoSansJP-SemiBold.ttf')
    font_path_kr = resource_path('fonts/NotoSansKR-SemiBold.ttf')
    font_path_ar = resource_path("fonts/NotoNaskhArabic-Bold.ttf")
    font_path = resource_path('fonts/NotoSansDisplay-SemiBold.ttf')
    fonts = {
        'ch': pygame.font.Font(font_path_ch, 25),
        'jp': pygame.font.Font(font_path_jp, 25),
        'kr': pygame.font.Font(font_path_kr, 25),
        'def': pygame.font.Font(font_path, 25),
        'ar': pygame.font.Font(font_path_ar, 25),
        'mega': pygame.font.Font(font_path, 55)
    }
    return fonts

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
    return font

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
        p_id = generate_player_id()
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
def save_progress(data):
    global notification_text, notification_time, error_code, notif, er
    global save_count
    global SAVE_FILE 

    # 1. Basic Validation: Ensure we aren't saving an empty/broken object
    if not data or "lvls" not in data or "player" not in data:
        if not is_mute:
            hit_sound.play()
        notification_text = menu_ui.render_text("Refusing to save: Invalid data structure!", True, (255, 0, 0))
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
        if not is_mute:
            hit_sound.play()
        notification_text = menu_ui.render_text("Error: Save file is locked by another program.", True, (255, 0, 0))
        notif = True
        notification_time = time.time()
            
    except Exception as e:
        er = True
        error_code = menu_ui.render_text(f"Save Error: {str(e)}", True, (255, 0, 0))
        #if not is_mute:
         #   hit_sound.play()
        notification_time = time.time()
        print(f"Detailed save error: {e}")

def update_local_manifest(data):
    global er, error_code, is_mute, notification_time
    # 1. Load existing manifest
    manifest = {"last_used": "", "users": {}, "pref": {"language": "en", "sfx": True, "ambience": True}}
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
        if not is_mute: hit_sound.play()
        error_code = menu_ui.render_text(f"Local manifest error: {e}", True, (255, 0, 0))
        er = True
        notification_time = time.time()
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
        data["player"]["ID"] = generate_player_id()


def sync_vault_to_cloud(data):
    global is_syncing, sync_status, sync_finish_time
    is_syncing = True
    settings = load_language(lang_code)['settings']
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
                        if not is_mute:
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