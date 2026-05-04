import pygame
import cleobo.data.manage_data as manage_data
import os
import json
from datetime import datetime
import traceback

manage_data.now = datetime.now()

# Path to sound folder
SOUND_FOLDER = manage_data.resource_path("assets/sound")
IMAGES_FOLDER = manage_data.resource_path("assets/imgs")
FONTS_FOLDER = manage_data.resource_path("assets/fonts")

# Initializing Game and Engine Version
manage_data.version = "1.3.9.0471"
manage_data.kernel = "0.2.0.0017"
manage_data.power = pygame.image.load(os.path.join(IMAGES_FOLDER, "logos/power.png"))

def verify_asset_exists(path, asset_name):
    """Verify asset file exists before loading"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing asset: {asset_name} at {path}")
    return path

def init_sounds():
  sound = {}
  try:
    sound_files = {
      'click': "ui/click.wav",
      'hover': "ui/hover.wav",
      'death': "game/death.wav",
      'laser': "game/laser.wav",
      'fall': "game/fall.wav",
      'open': "game/unlock.wav",
      'checkpoint': "game/checkpoint.wav",
      'warp': "game/warp.wav",
      'button': "game/button.wav",
      'bounce': "game/bounce.wav",
      'move': "game/travel.wav",
      'jump': "game/jump.wav",
      'hit': "game/hit.wav",
      'notify': "ui/notify.wav",
      'overheat': "game/overheat.wav",
      'freeze': "game/freeze.wav",
      'star1': "stars/1star.wav",
      'star2': "stars/2star.wav",
      'star3': "stars/3star.wav",
      'hscore': "stars/hs.wav"
    }
    for name, file in sound_files.items():
      path = os.path.join(SOUND_FOLDER, file)
      verify_asset_exists(path, f"sound/{name}")
      sound[name] = pygame.mixer.Sound(path)
    
    sound['star1'].set_volume(4.0)
    sound['star2'].set_volume(4.0)
    sound['star3'].set_volume(4.0)
    
    # Ambient themes
    ambience_path = manage_data.resource_path(os.path.join(SOUND_FOLDER, "amb/main.ogg"))
    verify_asset_exists(ambience_path, "ambience")
    pygame.mixer.music.load(ambience_path)
    return sound
  except Exception as e:
    print(f"ERROR loading sounds: {e}")
    traceback.print_exc()
    raise

def init_ui_images(SCREEN_WIDTH, SCREEN_HEIGHT):
    # Logo & Cursors Dictionary
    try:
        ui = {}
        ui_files = {
            'cursor': ("cursor/cursor.png", False),
            'logo': ("logos/logo.png", False),
            'studio_logo': ("logos/studiologodef.png", False),
            'studio_glow': ("logos/studiologoglow.png", False),
        }
        
        for name, (file_path, _) in ui_files.items():
            full_path = os.path.join(IMAGES_FOLDER, file_path)
            verify_asset_exists(full_path, f"UI image/{name}")
            ui[name] = pygame.image.load(full_path).convert_alpha()
        
        ui['studio_logo'] = pygame.transform.scale(ui['studio_logo'], (220, 220))
        ui['studio_glow'] = pygame.transform.scale(ui['studio_glow'], (280, 280))
        ui['logo'] = pygame.transform.rotate(ui['logo'], 5)
        ui['studio_logo_rect'] = ui['studio_logo'].get_rect(topleft=(20, SCREEN_HEIGHT - 240))
        ui['studio_glow_rect'] = ui['studio_glow'].get_rect(topleft=(20, SCREEN_HEIGHT - 300))
        
        return ui
    except Exception as e:
        print(f"ERROR loading UI images: {e}")
        traceback.print_exc()
        raise

def init_bgs(SCREEN_WIDTH, SCREEN_HEIGHT):
    # Backgrounds Dictionary
    try:
        # Check for events
        if manage_data.now.day == 29 and manage_data.now.month == 4:
            peek_path = "bgs/anipeek.png"
            plain_path = "bgs/AniBackground.png"
        else:
            peek_path = "bgs/lilrobopeek.png"
            plain_path = "bgs/PlainBackground.png"
        
        backgrounds = {}
        bg_files = {
            'lilrobopeek': (peek_path, (390, 360), True),
            'plain': (plain_path, (SCREEN_WIDTH, SCREEN_HEIGHT), False),
            'green': ("bgs/GreenBackground.png", (SCREEN_WIDTH, SCREEN_HEIGHT), False),
            'mech': ("bgs/MechBackground.png", (SCREEN_WIDTH, SCREEN_HEIGHT), False),
            'trans_left': ("bgs/trans_left.png", ((SCREEN_WIDTH // 2 + 20), SCREEN_HEIGHT), False),
            'trans_right': ("bgs/trans_right.png", ((SCREEN_WIDTH // 2 + 20), SCREEN_HEIGHT), False),
            'end': ("bgs/EndScreen.png", (SCREEN_WIDTH, SCREEN_HEIGHT), True),
        }
        
        for name, (file_path, size, use_alpha) in bg_files.items():
            full_path = manage_data.resource_path(os.path.join(IMAGES_FOLDER, file_path))
            verify_asset_exists(full_path, f"{name}")
            img = pygame.image.load(full_path).convert_alpha() if use_alpha else pygame.image.load(full_path).convert()
            backgrounds[name] = pygame.transform.scale(img, size)
        
        return backgrounds
    except Exception as e:
        print(f"ERROR loading backgrounds: {e}")
        traceback.print_exc()
        raise

def init_medals():
    # Medals Dictionary
    try:
        medals = {}
        medal_files = ['medal/perfect.png', 'medal/gold.png', 'medal/silver.png', 'medal/bronze.png']
        medal_names = ['Diamond', 'Gold', 'Silver', 'Bronze']
        
        for medal_name, file_name in zip(medal_names, medal_files):
            full_path = manage_data.resource_path(os.path.join(IMAGES_FOLDER, file_name))
            verify_asset_exists(full_path, f"{medal_name}")
            img = pygame.image.load(full_path).convert_alpha()
            medals[medal_name] = pygame.transform.scale(
                img,
                (img.get_width() // 2, img.get_height() // 2)
            )
        
        return medals
    except Exception as e:
        print(f"ERROR loading medals: {e}")
        traceback.print_exc()
        raise

def init_disks():
    # Disks Dictionary
    try:
        disks = {}
        disk_files = {
            'green': ("disks/greendisk.png", (100, 100)),
            'mech': ("disks/mechdisk.png", (100, 100)),
            'greenpack': ("disks/greenpack.png", (220, 220)),
            'mechpack': ("disks/mechpack.png", (220, 220)),
            'locked': ("disks/lockeddisk.png", (100, 100)),
        }
        
        for name, (file_path, size) in disk_files.items():
            full_path = manage_data.resource_path(os.path.join(IMAGES_FOLDER, file_path))
            verify_asset_exists(full_path, f"{name}")
            img = pygame.image.load(full_path).convert_alpha()
            disks[name] = pygame.transform.scale(img, size)
        
        return disks
    except Exception as e:
        print(f"ERROR loading disks: {e}")
        traceback.print_exc()
        raise

def init_other_assets():
    # In-game assets (saws, teleporters, badges, checkpoints)
    try:
        assets = {}
        asset_files = {
            'star': ("ui/star.png", (150, 140)),
            'exit': ("portal/exit.png", (140, 180)),
            'mech_exit': ("portal/mech_exit.png", (140, 180)),
            'teleport': ("portal/teleport.png", (140, 180)),
            'teleport_exit': ("portal/teleport_2.png", (100, 100)),
            'badge': ("ui/badge.png", (80, 80)),
            'max_badge': ("ui/max-badge.png", (80, 80)),
            'saw': ("ingame/saw.png", None),
            'cpoint_inact': ("ingame/flags/yellow_flag.png", None),
            'cpoint_act': ("ingame/flags/green_flag.png", None),
        }
        
        for name, (file_path, size) in asset_files.items():
            full_path = manage_data.resource_path(os.path.join(IMAGES_FOLDER, file_path))
            verify_asset_exists(full_path, f"{name}")
            img = pygame.image.load(full_path).convert_alpha()
            assets[name] = pygame.transform.scale(img, size) if size else img
        
        assets['star_small'] = pygame.transform.scale(assets['star'], (20, 17))
        assets['star_normal'] = pygame.transform.scale(assets['star'], (100, 93))
        return assets
    except Exception as e:
        print(f"ERROR loading assets: {e}")
        traceback.print_exc()
        raise

def init_robos():
    # Characters Dictionary
    try:
        robos = {}
        robo_files = {
            'robot': "char/robot/robot.png",
            'evilrobot': "char/evilrobot/evilrobot.png",
            'greenrobot': "char/greenrobot/greenrobot.png",
            'ironrobot': "char/ironrobot/ironrobo.png",
            'cakebot': "char/cakebot/cakebot.png",
            'greenrobot_moving': "char/greenrobot/movegreenrobot.png",
            'locked': "char/lockedrobot.png",
        }
        
        for name, file_path in robo_files.items():
            full_path = manage_data.resource_path(os.path.join(IMAGES_FOLDER, file_path))
            verify_asset_exists(full_path, f"{name}")
            robos[name] = pygame.image.load(full_path).convert_alpha()
        
        return robos
    except Exception as e:
        print(f"ERROR loading robots: {e}")
        traceback.print_exc()
        raise

def init_accs():
    if os.path.exists(manage_data.ACCOUNTS_FILE):
        with open(manage_data.ACCOUNTS_FILE, "r") as f:
            manifest = json.load(f)
            global_pref = manifest.get("pref", {})
            lang_code = global_pref.get("language", "en")
            # Invert 'sfx' back to 'is_mute'
            is_mute = not global_pref.get("sfx", True) 
            is_mute_amb = not global_pref.get("ambience", True)
    else:
        # Create default manifest and save it
        manifest = {"last_used": "", "users": {}, "pref": {"language": "en", "sfx": True, "ambience": True}, "other": {"last_news_count": 7}}
        lang_code = "en"
        is_mute = False
        is_mute_amb = False
        
        # Ensure the directory exists and save the default manifest
        if not os.path.exists(manage_data.APP_DATA_DIR):
            os.makedirs(manage_data.APP_DATA_DIR)
        try:
            with open(manage_data.ACCOUNTS_FILE, "w") as f:
                json.dump(manifest, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not create manifest file: {e}")
    
    return manifest, lang_code, is_mute, is_mute_amb

def init_fonts():
    global fonts
    try:
        font_files = {
            'ch': ('SimplifiedChinese.ttf', 25),
            'jp': ('Japanese.ttf', 25),
            'kr': ('Korean.ttf', 25),
            'ar': ('NaskhArabic.ttf', 25),
            'def': ('DefaultFont.ttf', 25),
            'mega': ('DefaultFont.ttf', 55),
        }
        
        fonts = {}
        for name, (file_path, size) in font_files.items():
            full_path = manage_data.resource_path(os.path.join(FONTS_FOLDER, file_path))
            verify_asset_exists(full_path, f"{name}")
            fonts[name] = pygame.font.Font(full_path, size)
        
        return fonts
    except Exception as e:
        print(f"ERROR loading fonts: {e}")
        traceback.print_exc()
        raise

def verify_initialization(manage_data):
    """Check that all critical assets loaded properly"""
    checks = [
        ('sounds', manage_data.sounds, ['click', 'jump', 'death']),
        ('fonts', manage_data.fonts, ['def', 'mega']),
        ('ui', manage_data.ui, ['cursor', 'logo']),
        ('bgs', manage_data.bgs, ['plain']),
        ('assets', manage_data.assets, ['star', 'exit']),
        ('robos', manage_data.robos, ['robot']),
    ]
    
    for asset_group, asset_dict, required_keys in checks:
        if not asset_dict:
            raise RuntimeError(f"Failed to initialize {asset_group}")
        for key in required_keys:
            if key not in asset_dict:
                raise RuntimeError(f"Missing {asset_group}: {key}")
    
    print("✓ All assets verified successfully!")

def load_game_generator(SCREEN_WIDTH, SCREEN_HEIGHT):
    manage_data.fonts = init_fonts()
    yield "Loading settings...", 6
    manage_data.manifest, manage_data.lang_code, manage_data.is_mute, manage_data.is_mute_amb = init_accs()
    
    yield "Checking for latest save...", 10
    manage_data.progress = manage_data.load_progress()
    # Ensure new users are registered in the manifest immediately
    manage_data.update_local_manifest(manage_data.progress)
    
    yield "Loading sounds...", 19
    manage_data.sounds = init_sounds()
    
    yield "Loading textures...", 41
    manage_data.ui = init_ui_images(SCREEN_WIDTH, SCREEN_HEIGHT)
    manage_data.bgs = init_bgs(SCREEN_WIDTH, SCREEN_HEIGHT)
    manage_data.assets = init_other_assets()
    manage_data.disks = init_disks()
    manage_data.medals = init_medals()
    
    yield "Calibrating Robots...", 92
    manage_data.robos = init_robos()
    
    yield "Systems Ready!", 100
    verify_initialization(manage_data)
    return True # Just a signal that we finished