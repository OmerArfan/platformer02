import pygame
import manage_data
import os

# Path to sound folder
SOUND_FOLDER = manage_data.resource_path("audio")

def init_sounds():
  sound = {
    'click': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "click.wav")),
    'hover': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "hover.wav")),
    'death': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "death.wav")),
    'laser': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "laser.wav")),
    'fall': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "fall.wav")),
    'open': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "unlock.wav")),
    'checkpoint': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "checkpoint.wav")),
    'warp': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "warp.wav")),
    'button': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "button.wav")),
    'bounce': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "bounce.wav")),
    'move': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "travel.wav")),
    'jump': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "jump.wav")),
    'hit': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "hit.wav")),
    'notify': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "notify.wav")),
    'overheat': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "overheat.wav")),
    'freeze': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "freeze.wav")),
    'star1': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/1star.wav")),
    'star2': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/2star.wav")),
    'star3': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/3star.wav")),
    'hscore': pygame.mixer.Sound(os.path.join(SOUND_FOLDER, "stars/hs.wav"))
  }
  sound['star1'].set_volume(4.0)
  sound['star2'].set_volume(4.0)
  sound['star3'].set_volume(4.0)
  # Ambient themes
  pygame.mixer.music.load(manage_data.resource_path("audio/amb/ambience.wav"))
  return sound

def init_ui_images(SCREEN_WIDTH, SCREEN_HEIGHT):
    # Logo & Cursors Dictionary
    ui = {
        'cursor': pygame.image.load(manage_data.resource_path("oimgs/cursor/cursor.png")).convert_alpha(),
        'logo': pygame.image.load(manage_data.resource_path("oimgs/logos/logo.png")).convert_alpha(),
        'studio_logo': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/logos/studiologodef.png")).convert_alpha(),
            (220, 220)
        ),
        'studio_glow': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/logos/studiologoglow.png")).convert_alpha(),
            (280, 280)
        ),
    }
    ui['logo'] = pygame.transform.rotate(ui['logo'], 5)
    ui['studio_logo_rect'] = ui['studio_logo'].get_rect(topleft=(20, SCREEN_HEIGHT - 240))
    ui['studio_glow_rect'] = ui['studio_glow'].get_rect(topleft=(20, SCREEN_HEIGHT - 300))

    return ui

def init_bgs(SCREEN_WIDTH, SCREEN_HEIGHT):
    # Backgrounds Dictionary
    backgrounds = {
        'lilrobopeek': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("bgs/lilrobopeek.png")).convert_alpha(),
            (390, 360)
        ),
        'plain': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("bgs/PlainBackground.png")).convert(),
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        ),
        'green': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("bgs/GreenBackground.png")).convert(),
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        ),
        'mech': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("bgs/MechBackground.png")).convert(),
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        ),
        'trans_left': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("bgs/trans_left.png")).convert(),
            ((SCREEN_WIDTH // 2 + 20), (SCREEN_HEIGHT))
        ),
        'trans_right': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("bgs/trans_right.png")).convert(),
            ((SCREEN_WIDTH // 2 + 20), (SCREEN_HEIGHT))
        ),
        'end': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("bgs/EndScreen.png")).convert_alpha(),
            ((SCREEN_WIDTH), (SCREEN_HEIGHT))
        ),
    }

    return backgrounds

def init_medals():
    # Medals Dictionary
    medals = {
        'Diamond': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/medal/perfect.png")).convert_alpha(),
            (pygame.image.load(manage_data.resource_path("oimgs/medal/perfect.png")).convert_alpha().get_width() // 2,
             pygame.image.load(manage_data.resource_path("oimgs/medal/perfect.png")).convert_alpha().get_height() // 2)
        ),
        'Gold': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/medal/gold.png")).convert_alpha(),
            (pygame.image.load(manage_data.resource_path("oimgs/medal/gold.png")).convert_alpha().get_width() // 2,
             pygame.image.load(manage_data.resource_path("oimgs/medal/gold.png")).convert_alpha().get_height() // 2)
        ),
        'Silver': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/medal/silver.png")).convert_alpha(),
            (pygame.image.load(manage_data.resource_path("oimgs/medal/silver.png")).convert_alpha().get_width() // 2,
             pygame.image.load(manage_data.resource_path("oimgs/medal/silver.png")).convert_alpha().get_height() // 2)
        ),
        'Bronze': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/medal/bronze.png")).convert_alpha(),
            (pygame.image.load(manage_data.resource_path("oimgs/medal/bronze.png")).convert_alpha().get_width() // 2,
             pygame.image.load(manage_data.resource_path("oimgs/medal/bronze.png")).convert_alpha().get_height() // 2)
        ),
    }
    return medals

def init_disks():
    # Disks Dictionary
    disks = {
        'green': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/disks/greendisk.png")).convert_alpha(),
            (100, 100)
        ),
        'mech': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/disks/mechdisk.png")).convert_alpha(),
            (100, 100)
        ),
        'locked': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/disks/lockeddisk.png")).convert_alpha(),
            (100, 100)
        ),
    }

    return disks

def init_assets():
    # In-game assets (saws, teleporters, badges, checkpoints)
    assets = {
        'star': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/ig/star.png")).convert_alpha(),
            (150, 140)
        ),
        'star_small': None,  # Will be set below
        'exit': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/portal/exit.png")).convert_alpha(),
            (140, 180)
        ),
        'mech_exit': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/portal/mech_exit.png")).convert_alpha(),
            (140, 180)
        ),
        'teleport': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/portal/teleport.png")).convert_alpha(),
            (140, 180)
        ),
        'teleport_exit': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/portal/teleport_2.png")).convert_alpha(),
            (100, 100)
        ),
        'badge': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/ig/badge.png")).convert_alpha(),
            (70, 70)
        ),
        'max_badge': pygame.transform.scale(
            pygame.image.load(manage_data.resource_path("oimgs/ig/max-badge.png")).convert_alpha(),
            (70, 70)
        ),
        'saw': pygame.image.load(manage_data.resource_path("oimgs/ig/saw.png")).convert_alpha(),
        'cpoint_inact': pygame.image.load(manage_data.resource_path("oimgs/checkpoints/yellow_flag.png")).convert_alpha(),
        'cpoint_act': pygame.image.load(manage_data.resource_path("oimgs/checkpoints/green_flag.png")).convert_alpha(),
    }
    assets['star_small'] = pygame.transform.scale(assets['star'], (20, 17))
    
    return assets

def init_robos():
    # Characters Dictionary
    robos = {
        'robot': pygame.image.load(manage_data.resource_path("char/robot/robot.png")).convert_alpha(),
        'evilrobot': pygame.image.load(manage_data.resource_path("char/evilrobot/evilrobot.png")).convert_alpha(),
        'greenrobot': pygame.image.load(manage_data.resource_path("char/greenrobot/greenrobot.png")).convert_alpha(),
        'ironrobot': pygame.image.load(manage_data.resource_path("char/ironrobot/ironrobo.png")).convert_alpha(),
        'icerobot': pygame.image.load(manage_data.resource_path("char/icerobot/icerobot.png")).convert_alpha(),
        'greenrobot_moving': pygame.image.load(manage_data.resource_path("char/greenrobot/movegreenrobot.png")).convert_alpha(),
        'locked': pygame.image.load(manage_data.resource_path("char/lockedrobot.png")).convert_alpha(),
    }
    
    return robos