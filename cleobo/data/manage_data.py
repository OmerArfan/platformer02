import copy
import json
import os
import shutil
import time
import threading
import sys
from datetime import datetime, date
import csv
import hashlib
import threading
import requests
from io import StringIO
import pygame

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
        "green": {
            "1": {f"lvl{i}": {"locked": True, "score": 0, "medal": "None", "time": 0} for i in range(1, 5)}
        },
        "ship": {
            "1": {f"lvl{i}": {"locked": True, "score": 0, "medal": "None", "time": 0} for i in range(1, 5)}
        },
        "mech": {
            "1": {f"lvl{i}": {"locked": True, "score": 0, "medal": "None", "time": 0} for i in range(1, 7)}
        },
    },
    "pref" : { 
        "character": "robot"
    },
    "char": { 
        "evilrobo": False, 
        "greenrobo": False,
        "ironrobo": False,
        "cakebot": False
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

def thresholds(world, thr):
    with open(resource_path(f"assets/data/thresholds/{world}.json"), "r", encoding="utf-8") as f:
        thresh_data = json.load(f)
        return thresh_data[thr]

fonts = {}
saw_cache = {}

def change_ambience(new_file):
  if not is_mute_amb:
    pygame.mixer.music.load(resource_path(f"assets/sound/amb/{new_file}.ogg"))
    pygame.mixer.music.set_volume(1)  # Adjust as needed
    pygame.mixer.music.play(-1)

def get_ordered_levels(progress):
    """Traverse the actual structure and discover levels—no hardcoding."""
    ordered = []
    
    for world in sorted(progress['lvls'].keys()):
        world_data = progress['lvls'][world]
        
        if not isinstance(world_data, dict):
            continue
            
        for subsection in sorted(world_data.keys(), key=lambda x: int(x) if x.isdigit() else x):
            subsection_data = world_data[subsection]
            
            if not isinstance(subsection_data, dict):
                continue
            
            level_keys = [k for k in subsection_data.keys() if k.startswith('lvl')]
            level_keys.sort(key=lambda x: int(x.replace('lvl', '')))
            
            for level_key in level_keys:
                ordered.append((world, subsection, level_key))
    
    return ordered

def update_locked_levels(progress, manifest):
    """Smart unlock system with zero hardcoding."""
    ordered_levels = get_ordered_levels(progress)  # ✅ Discovers from structure
    
    if not ordered_levels:
        return
    
    # First level always unlocked
    first_world, first_subsection, first_level = ordered_levels[0]
    progress['lvls'][first_world][first_subsection][first_level]['locked'] = False
    
    # Unlock subsequent levels based on previous completion
    for i in range(1, len(ordered_levels)):
        world, subsection, level_key = ordered_levels[i]
        prev_world, prev_subsection, prev_level_key = ordered_levels[i - 1]
        
        prev_level_data = progress['lvls'][prev_world][prev_subsection][prev_level_key]
        
        if prev_level_data.get('score', 0) != 0:  # ✅ Uses new structure
            progress['lvls'][world][subsection][level_key]['locked'] = False
        else:
            progress['lvls'][world][subsection][level_key]['locked'] = True

    # Additional rule: if the LAST level of the FIRST subsection of a world is completed
    # (score > 0), then the FIRST level of the FIRST subsection of the next world
    # should be unlocked. Also unlock if that next level already has score>0.
    worlds = sorted(progress['lvls'].keys(), key=lambda x: x)
    for idx in range(len(worlds) - 1):
        cur_world = worlds[idx]
        next_world = worlds[idx + 1]

        # get first subsection names (sorted numerically when possible)
        cur_subsecs = sorted(progress['lvls'][cur_world].keys(), key=lambda x: int(x) if x.isdigit() else x)
        next_subsecs = sorted(progress['lvls'][next_world].keys(), key=lambda x: int(x) if x.isdigit() else x)

        if not cur_subsecs or not next_subsecs:
            continue

        cur_first_sub = cur_subsecs[0]
        next_first_sub = next_subsecs[0]

        cur_levels = [k for k in progress['lvls'][cur_world][cur_first_sub].keys() if k.startswith('lvl')]
        if not cur_levels:
            continue

        # determine the last level key in current world's first subsection
        cur_levels_sorted = sorted(cur_levels, key=lambda k: int(k.replace('lvl', '')))
        cur_last_key = cur_levels_sorted[-1]
        cur_last_score = progress['lvls'][cur_world][cur_first_sub].get(cur_last_key, {}).get('score', 0)

        # determine the first level key in next world's first subsection
        next_levels = [k for k in progress['lvls'][next_world][next_first_sub].keys() if k.startswith('lvl')]
        if not next_levels:
            continue
        next_levels_sorted = sorted(next_levels, key=lambda k: int(k.replace('lvl', '')))
        next_first_key = next_levels_sorted[0]
        next_first_score = progress['lvls'][next_world][next_first_sub].get(next_first_key, {}).get('score', 0)

        if cur_last_score > 0 or next_first_score > 0:
            progress['lvls'][next_world][next_first_sub][next_first_key]['locked'] = False
        
    save_progress(progress, manifest)

def get_level_info(progress, world, subsection, level_key):
    """Helper to check level status from UI code."""
    try:
        level_data = progress['lvls'][world][subsection][level_key]
        return {
            'locked': level_data.get('locked', True),
            'completed': level_data.get('score', 0) != 0,
            'score': level_data.get('score', 0),
            'medal': level_data.get('medal', 'None'),
            'time': level_data.get('time', 0)
        }
    except KeyError:
        return None

def migrate_old_progress(progress):
    """Handle any old format inconsistencies."""
    for world in progress.get('lvls', {}).values():
        for subsection in world.values():
            if isinstance(subsection, dict):
                for level_key in subsection.keys():
                    if level_key.startswith('lvl'):
                        level = subsection[level_key]
                        level.setdefault('locked', True)
                        level.setdefault('score', 0)
                        level.setdefault('medal', 'None')
                        level.setdefault('time', 0)
    
    if 'lvls' in progress:
        progress['lvls'].pop('score', None)
        progress['lvls'].pop('medals', None)
        progress['lvls'].pop('times', None)
        progress['lvls'].pop('complete_levels', None)
        progress['lvls'].pop('locked_levels', None)
    
    return progress

def load_language():
    global manifest
    try:
        # Wrap the path in resource_path()
        path = resource_path(f"assets/lang/{lang_code}.json")
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
    current_lang = load_language()  # Reload the language data
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

import cleobo.data.acc_sys as acc_sys

def load_progress():
    global SAVE_FILE, selected_character
    
    data = copy.deepcopy(default_progress)
    manifest = None  # Initialize to None so it's always defined

    # 1. Check manifest for the last used ID
    current_id = ""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as f:
                manifest = json.load(f)
                current_id = manifest["pref"].get("last_used", "")
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
                save_progress(data, manifest) 
            else:
                print(f"Local save is the latest version ({local_xp} XP).")

    selected_character = data["pref"].get("character", default_progress["pref"]["character"])
    
    if now.day == 29 and now.month == 4:
        data['char']['cakebot'] = True
    
    # Ensure new players have their save file created immediately
    if not os.path.exists(SAVE_FILE):
        save_progress(data, manifest)
        
    return data

import cleobo.ui.menu_ui as menu_ui

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
            threading.Thread(target=sync_vault_to_cloud, args=(data,), daemon=True).start()

    except PermissionError:
        if not is_mute:
            sounds['death'].play()
        notification_text = menu_ui.render_text("Error: Save file is locked by another program.", True, (255, 0, 0))
        notif = True
        menu_ui.notification_time = time.time()
            
    except Exception as e:
        menu_ui.er = True
        menu_ui.error_code = menu_ui.render_text(f"Save Error: {str(e)}", True, (255, 0, 0))
        if not is_mute:
           sounds['hit'].play()
        menu_ui.notification_time = time.time()
        print(f"Detailed save error: {e}")

def update_local_manifest(data):
    global is_mute, manifest
    
    # Store the current last_news_count before reloading
    previous_news_count = manifest.get("other", {}).get("last_news_count", 7) if manifest else 7
    
    # 1. Load existing manifest
    manifest = {"last_used": "", "users": {}, "pref": {"language": "en", "sfx": True, "ambience": True}, "other": {"last_news_count": 8}}
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as f:
                manifest = json.load(f)
        except:
            try:
              # If main is corrupted check backup.
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
        manifest["other"] = {"last_news_count": 8}
    
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
        if not is_mute: sounds['death'].play()
        menu_ui.error_code = menu_ui.render_text(f"Local manifest error: {e}", True, (255, 0, 0))
        menu_ui.er = True
        menu_ui.notification_time = time.time()
        print(f"Error during manifest save: {e}")

def sync_missing_data(data):
    
    # 1. Ensure top-level keys exist (player, achieved, etc.)
    for key, value in default_progress.items():
        if key not in data:
            data[key] = copy.deepcopy(value)
 
    # 2. Sync lvls with new hierarchical structure (world → subsection → level)
    if "lvls" in data:
        # Iterate through default worlds
        for world_name, world_data in default_progress["lvls"].items():
            if world_name not in data["lvls"]:
                # Entire world is missing, add it with all subsections and levels
                data["lvls"][world_name] = copy.deepcopy(world_data)
            else:
                # World exists, now sync subsections within this world
                for subsection_name, subsection_data in world_data.items():
                    if subsection_name not in data["lvls"][world_name]:
                        # Subsection is missing, add it with all its levels
                        data["lvls"][world_name][subsection_name] = copy.deepcopy(subsection_data)
                    else:
                        # Subsection exists, now sync individual levels
                        for level_key, level_data in subsection_data.items():
                            if level_key not in data["lvls"][world_name][subsection_name]:
                                # Level is missing, add it
                                data["lvls"][world_name][subsection_name][level_key] = copy.deepcopy(level_data)
                            else:
                                # Level exists, ensure all required fields are present
                                existing_level = data["lvls"][world_name][subsection_name][level_key]
                                for field in ['locked', 'score', 'medal', 'time']:
                                    if field not in existing_level:
                                        existing_level[field] = level_data[field]
        
        # 3. Remove old flat structure keys for backward compatibility
        # These were used in the old system and should not exist in new system
        old_flat_keys = ['score', 'medals', 'times']
        for old_key in old_flat_keys:
            if old_key in data['lvls']:
             for i in range (1,13):
                if i <= 6:
                    world = "green"
                    lv = i
                else:
                    world = "mech"
                    lv = i - 6

                if old_key == "medals":
                    new_key = "medal"
                elif old_key == "times":
                    new_key = "time"
                else:
                    new_key = old_key

                data["lvls"][world]['1'][f'lvl{lv}'][new_key] = data['lvls'][old_key][f'lvl{i}']

             data["lvls"].pop(old_key, None)
            data['lvls'].pop('complete_levels', None)
            data['lvls'].pop('locked_levels', None)
        
        # Level 1 of green world should always be unlocked
        if "green" in data["lvls"] and "1" in data["lvls"]["green"]:
            if "lvl1" in data["lvls"]["green"]["1"]:
                data["lvls"]["green"]["1"]["lvl1"]["locked"] = False
        
        # If a level IS completed (score > 0), unlock the next level
        for world_name in data["lvls"]:
            for subsection_name in data["lvls"][world_name]:
                levels = data["lvls"][world_name][subsection_name]
                level_nums = sorted([int(k.replace('lvl', '')) for k in levels.keys() if k.startswith('lvl')])
                
                for idx, level_num in enumerate(level_nums):
                    current_level = levels[f'lvl{level_num}']
                    # If current level is completed (score > 0), unlock the next level
                    if current_level.get('score', 0) > 0 and idx + 1 < len(level_nums):
                        next_level_num = level_nums[idx + 1]
                        levels[f'lvl{next_level_num}']['locked'] = False
    
    green_world_1 = data["lvls"]["green"].get("1", {})
    ship_world_1 = data["lvls"]["ship"].get("1", {})

    # Count only actual level keys (lvl1, lvl2, ...) to decide when to migrate
    lvl_keys = [k for k in green_world_1.keys() if k.startswith('lvl')]
    if len(lvl_keys) == 6:
        ship_world_1["lvl1"] = green_world_1["lvl3"].copy()
        ship_world_1["lvl2"] = green_world_1["lvl4"].copy()
        ship_world_1["lvl3"] = green_world_1["lvl5"].copy()
        ship_world_1["lvl4"] = green_world_1["lvl6"].copy()
    
        # Except make lvl3 unlocked, and lvl4 locked
        if green_world_1['lvl2']['score'] == 0:
            lv3_lock_status = True
        else:
            lv3_lock_status = False

        green_world_1["lvl3"] = {
            "locked": lv3_lock_status,
            "score": 0,
            "medal": "None",
            "time": 0
        }
        
        green_world_1["lvl4"] = {
            "locked": True,
            "score": 0,
            "medal": "None",
            "time": 0
        }
        
        # ---- REMOVE LVL 5 AND LVL 6 FROM GREEN ----
        green_world_1.pop("lvl5", None)
        green_world_1.pop("lvl6", None)     
        
    update_locked_levels(data, manifest)

def sync_vault_to_cloud(data):
    global is_syncing, sync_status, sync_finish_time
    is_syncing = True
    settings = load_language()['settings']
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
                        if not is_mute:
                           sounds['notify'].play()
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

def get_all_cloud_ids():
    """Fetch all player IDs from the cloud vault to check for collisions."""
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQNm-8l1C38UGFt-lJT3ft5DARYZcjMwsWfVYGrtAqDy0bR8MQFcLJSRFqYYX7mbra_P2cWl1-i0WYW/pub?gid=1459647032&single=true&output=csv"
    cloud_ids = set()
    
    try:
        response = requests.get(CSV_URL, timeout=10)
        if response.status_code == 200:
            f = StringIO(response.text)
            reader = csv.DictReader(f)
            for row in reader:
                player_id = row.get('ID')
                if player_id and player_id.strip():  # Only add non-empty IDs
                    cloud_ids.add(player_id.strip())
    except Exception as e:
        print(f"Error fetching cloud IDs: {e}")
    
    return cloud_ids

import cleobo.data.achievements as achieve

def xp():
    from cleobo.levels.logic.entities import LevelManager

    global progress
    
    # XP from scores - collect all scores from the new hierarchical structure
    total_score = 0
    level_scores = {}  # Map of level_num -> score for star calculation
    
    for world_name in progress["lvls"]:
        for subsection_name in progress["lvls"][world_name]:
            for level_key in progress["lvls"][world_name][subsection_name]:
                level_data = progress["lvls"][world_name][subsection_name][level_key]
                score = level_data.get('score', 0)
                total_score += score
                
                # Extract level number for star calculation
                if level_key.startswith('lvl'):
                    level_num = int(level_key.replace('lvl', ''))
                    level_scores[level_num] = score
    
    score_xp = total_score // 1000

    # XP from stars
    stars = 0
    for world in default_progress['lvls']:
      for level in world:
        level_num = int(level_key.replace('lvl', ''))
        score = level_scores.get(level_num, 0)
        stars += LevelManager.get_stars(level_num, world, score)
      star_xp = stars * 20  # 20 XP per star

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
        if level <= 5:
            return 50
        elif level <= 10:
            return 70
        elif level <= 15:
            return 110
        elif level <= 20:
            return 170
        else: # Buffer
            return 250

    def calculate_level(total_xp):
        level = 1
        xp_left = total_xp
        while xp_left >= xp_needed(level):
            xp_left -= xp_needed(level)
            level += 1
        return level, xp_left

    level, xp_in_level = calculate_level(total_xp)
    progress["player"]["Level"] = level
    if level > 20:
        level = 20
    achieve.check_xplvl20(level)
    return level, xp_in_level, xp_needed(level)

def update_xp_ui():
    global progress, lang_code, manifest
    level, xp_needed, xp_total = xp(progress, achieve)

    if level < 20:
        color = (255, 255, 255)
        XP_text = fonts['mega'].render(str(level), True, color)
        XP_text2 = menu_ui.render_text(f"{xp_needed}/{xp_total}", True, color)
    else:
        color = (225, 212, 31)
        XP_text = fonts['mega'].render(str(level), True, color)
        max_txt = load_language().get('messages', {}).get("max_level", "MAX LEVEL!")
        XP_text2 = menu_ui.render_text(max_txt, True, color)   

    return XP_text, XP_text2

def check_for_new_gamenews(return_count):
    url = "https://omerarfan.github.io/lilrobowebsite/gamestuff.html"
    try:
        # 3 second timeout so the game doesn't hang if offline
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            online_count = response.text.count('<a href="gamenews')
            
            # Get the count from our manifest
            local_count = manifest.get("other", {}).get("last_news_count", 7)
            if local_count < 8:
                local_count = 8  # Default to 7 if not set, since we started counting from last update
            
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