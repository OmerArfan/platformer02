import sys
import webbrowser

import pygame
import arabic_reshaper
import time
from bidi.algorithm import get_display
import cleobo.data.manage_data as manage_data
import math
import cleobo.ui.state as state
import random
import re
from cleobo.levels.logic.entities import LevelManager

from cleobo.ui.text_sprite import TextSprite

# Pre-compile the regex outside the function so it only happens once!
RE_LANG = re.compile(r'([\u0590-\u06FF]|[\u4e00-\u9fff]|[\u3040-\u30FF]|[\uAC00-\uD7A3])')

manage_data.text_cache = {}
buttons = []

# To handle notifications
notif_time = None
er_time = None
notif = False
er = False

# Related to online saving
save_count = 0
is_syncing = False      
sync_status = ""
sync_finish_time = None

# Global sprite group for UI text
ui_text_sprites = pygame.sprite.Group()

def render_text(text, Boolean, color, bigfont=False):
    # 1. FASTER FONT PICKING
    # We check if there's any non-default char in one go
    match = RE_LANG.search(text)
    font_key = 'def'
    display_text = text
    cache_key = (text, color, bigfont)
    
    if cache_key in manage_data.text_cache:
        return manage_data.text_cache[cache_key]

    if bigfont:
        font_key = 'mega'
    elif match:
        char = match.group(0)
        if '\u0590' <= char <= '\u06FF':
            display_text = get_display(arabic_reshaper.reshape(text))
            font_key = 'ar'
        elif '\u4e00' <= char <= '\u9fff': font_key = 'ch'
        elif '\u3040' <= char <= '\u30FF': font_key = 'jp'
        elif '\uAC00' <= char <= '\uD7A3': font_key = 'kr'

    font_to_use = manage_data.fonts[font_key]

    # We avoid creating a 'combined_surf' manually.
    thickness = 1
    
    font_to_use.outline = thickness
    # This surface is automatically sized correctly by pygame-ce
    surf = font_to_use.render(display_text, True, (0, 0, 0)) 
    
    font_to_use.outline = 0
    main_text = font_to_use.render(display_text, True, color)
    
    # Blit directly onto the 'surf' we already have
    surf.blit(main_text, (thickness, thickness))
    
    return surf

def draw_buttons(screen, mouse_pos, button_hovered_last_frame):
    for rendered, rect, key, is_locked in buttons:
        if rect.collidepoint(mouse_pos):
            button_suface(screen, rect)
            button_hovered_last_frame = hover_effect(screen, rect, button_hovered_last_frame)
        else:
            button_suface(screen, rect)
        screen.blit(rendered, rect)
    return button_hovered_last_frame

def button_suface(screen, rect):
    if (manage_data.now.day >= 29 and manage_data.now.month == 4) or (manage_data.now.day <= 13 and manage_data.now.month == 5):
        button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
        button_surface.fill((175, 0, 202, 255))
        screen.blit(button_surface, rect.inflate(20, 10).topleft)
        pygame.draw.rect(screen, (255, 0, 252), rect.inflate(30, 15), 6)
    else:
        button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
        button_surface.fill((8, 81, 179, 255))
        screen.blit(button_surface, rect.inflate(20, 10).topleft)
        pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)

def hover_effect(screen, rect, button_hovered_last_frame):
    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
    hovered = rect.collidepoint(pygame.mouse.get_pos())
    if hovered and not button_hovered_last_frame and not manage_data.is_mute:
        manage_data.sounds['hover'].play()
    button_hovered_last_frame = hovered
    return button_hovered_last_frame

def draw_notifs(screen):
    global notif, er, notif_time, er_time, notification_text, error_code
    if notif:
        if notif_time is not None and time.time() - notif_time < 4:  # Show for 4 seconds
            screen.blit(notification_text, (manage_data.SCREEN_WIDTH // 2 - notification_text.get_width() // 2, 100))
        else:
            notif = False
            notif_time = None

    if er:
        if er_time is not None and time.time() - er_time < 4:  # Show for 4 seconds
            screen.blit(error_code, (manage_data.SCREEN_WIDTH // 2 - error_code.get_width() // 2, 130))
        else:
            er = False
            er_time = None

buttons = []

def draw_loading_bar(screen, stage_name, percent):
    text = render_text(f"{stage_name} ({percent}%)", True, (255, 255, 255))
    text_rect = text.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 60))
    screen.blit(text, text_rect)
    pygame.draw.rect(screen, (0, 0, 255), (0, manage_data.SCREEN_HEIGHT - 10, (manage_data.SCREEN_WIDTH / 100)*percent, 10))
    pygame.display.flip()

def draw_loading_orb(screen, text_x, text_y, show_time):
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

def draw_syncing_status(screen):
    global is_syncing, sync_status, sync_finish_time
    if is_syncing:
        if sync_finish_time is not None:
            if time.time() - sync_finish_time > 1:
                is_syncing = False
                sync_finish_time = None
                return

        syncing_text = render_text(sync_status, True, (255, 255, 255))
        text_x = manage_data.SCREEN_WIDTH - syncing_text.get_width() - 10
        text_y = manage_data.SCREEN_HEIGHT - 60
        screen.blit(syncing_text, (text_x, text_y))
        draw_loading_orb(screen, text_x, text_y, sync_finish_time)

reblit_txt = True
last_lang = None  # Track language changes
prev_ID = None # Track Account changes

def create_achieve_screen(screen):
    global current_lang, ui_text_sprites, reblit_txt, last_lang, prev_ID
    buttons.clear()
    
    screen.blit(manage_data.bgs['plain'], (0, 0))  # Draw background
    
    # Detect language change
    if manage_data.lang_code != last_lang or manage_data.progress['player']['ID'] != prev_ID:
        reblit_txt = True
        last_lang = manage_data.lang_code
        prev_ID = manage_data.progress['player']['ID']
    
    current_lang = manage_data.load_language()
    ach_data = current_lang.get("achieve", {}) 
    header_data = current_lang.get("main_menu", {})
    back_data = current_lang.get("language_select", {})

    # 1. Render Main Header (as TextSprite)
    ach_txt = header_data.get("achievements", "Achievements")
    header = TextSprite(ach_txt, 
                       x=manage_data.SCREEN_WIDTH // 2, 
                       y=50, 
                       color=(255, 255, 255),
                       center_x=True
                       )
    
    if reblit_txt:
        ui_text_sprites.empty()  # Clear previous sprites
        ui_text_sprites.add(header)

        ach_list = [
            "zen_os", 
            "zen_os_desc",
            "speedy_starter", 
            "speedy_starter_desc",
            "over_9k",
            "over_9k_desc",
            "termvel",
            "termvel_desc",
            "golden", 
            "golden_desc",
            "mech_eng", 
            "mech_eng_desc",
            "captain",
            "captain_desc",
            "lv20", 
            "lv20_desc",
            "chase_escape", 
            "removed",
        ]

        y_offset = 120 
        count = 0

        for title_key in ach_list:
            title_str = ach_data.get(title_key, "?")

            # Render Title (as TextSprite)
            # Only treat non-description/metadata keys as achievements
            if title_key[-5:] != "_desc" and title_key not in ("removed", "secret"):
                if manage_data.progress.get("achieved", {}).get(title_key, False):
                    color = (0, 204, 0)
                else:
                    color = (255, 255, 0)
            
            # Create sprite first with a temporary position
            title = TextSprite(title_str, x=100, y=y_offset, color=color)
            
            # Now adjust position based on language
            if manage_data.lang_code == "ar" or manage_data.lang_code == "pk":
                # For RTL languages, subtract the width from right edge
                x_pos = manage_data.SCREEN_WIDTH - title.get_width() - 100
                title.set_position(x_pos, y_offset)
            
            ui_text_sprites.add(title)

            count += 1
            if count % 2 == 0:
                y_offset += 52
            else:
                y_offset += 25
    
        reblit_txt = False

    # Draw all text sprites
    ui_text_sprites.update()
    ui_text_sprites.draw(screen)
    
    # Back button (still using old button system for now)
    back_text = back_data.get("back", "Back")
    rendered_back = render_text(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 100))
    buttons.append((rendered_back, back_rect, "back", False))

def init_profile_vars():
    global gold_medals, diamond_medals, total_stars, ulock_ach, total_ach
    
    gold_medals, diamond_medals, total_stars, ulock_ach, total_ach = 0, 0, 0, 0, 0

    for wk, world in (manage_data.progress['lvls'].items() if isinstance(manage_data.progress.get('lvls'), dict) else enumerate(manage_data.progress.get('lvls', []))):
        if isinstance(world, dict):
            levels = world.get("1") if "1" in world else None
            if levels is None:
                levels = next((v for v in world.values() if isinstance(v, list)), [])
        else:
            levels = world
        if isinstance(levels, dict):
            # keep keys so we can extract level number (e.g. 'lvl1')
            iter_levels = levels.items()
        elif isinstance(levels, list):
            iter_levels = levels
        else:
            iter_levels = []

        # iter_levels is either an iterable of (lvlkey, lvl_dict) or a list of lvl_dict
        if isinstance(iter_levels, list):
            for lvl in iter_levels:
                if not isinstance(lvl, dict):
                    continue
                medal = lvl.get('medal')
                if medal == "Gold" or medal == "Diamond":
                    gold_medals += 1
                    if medal == "Diamond":
                        diamond_medals += 1
                score = lvl.get('score', 0)
                # LevelManager expects a level number or id; we don't have the key here — skip number parsing
                level_star = LevelManager.get_stars(lvl, wk, score)
                total_stars += level_star
        else:
            for lvlkey, lvl in iter_levels:
                if not isinstance(lvl, dict):
                    continue
                medal = lvl.get('medal')
                if medal == "Gold" or medal == "Diamond":
                    gold_medals += 1
                    if medal == "Diamond":
                        diamond_medals += 1
                score = lvl.get('score', 0)
                lvl_no = lvlkey.replace("lvl", "")
                level_star = LevelManager.get_stars(lvl_no, wk, score)
                total_stars += level_star

    for ach in manage_data.progress['achieved']:
        if manage_data.progress["achieved"][ach]:
            ulock_ach += 1
        total_ach += 1


def draw_profile(screen):
    global current_lang, buttons
    buttons.clear()
    screen.blit(manage_data.bgs['plain'], (0, 0))
    # initialize profile counters (gold/diamond/stars/achievements)
    init_profile_vars()
    current_lang = manage_data.load_language().get('main_menu', {})
    settings = manage_data.load_language().get('settings', {})
    profile_text = current_lang.get("profile", "Profile")
    rendered_profile = render_text(profile_text, True, (255, 255, 255))
    screen.blit(rendered_profile, (manage_data.SCREEN_WIDTH // 2 - rendered_profile.get_width() // 2, 50))
    
    current_lang = manage_data.load_language()
    back_data = current_lang.get("language_select", {})

    level, xp_needed, xp_total = xp.xp()

    if level < 5:
        color = (255, 255, 255)
        XP_text2 = render_text(f"{xp_needed}/{xp_total}", True, color)
        badge = manage_data.badges['tier1']
        bar = 400*(xp_needed/xp_total)
    elif level < 10:
        color = (255, 255, 255)
        XP_text2 = render_text(f"{xp_needed}/{xp_total}", True, color)
        badge = manage_data.badges['tier2']
        bar = 400*(xp_needed/xp_total)
    elif level < 15:
        color = (255, 255, 255)
        XP_text2 = render_text(f"{xp_needed}/{xp_total}", True, color)
        badge = manage_data.badges['tier3']
        bar = 400*(xp_needed/xp_total)
    elif level < 20:
        color = (255, 255, 255)
        XP_text2 = render_text(f"{xp_needed}/{xp_total}", True, color)
        badge = manage_data.badges['tier4']
        bar = 400*(xp_needed/xp_total)
    elif level <= 25:
        if level < 25:
            color = (255, 255, 255)
            XP_text2 = render_text(f"{xp_needed}/{xp_total}", True, color)
            bar = 400*(xp_needed/xp_total)
        else:
            max_txt = manage_data.load_language().get('messages', {}).get("max_level", "MAX LEVEL!")
            color = (225, 212, 31)
            XP_text2 = render_text(max_txt, True, color)
            bar = 400
        badge = manage_data.badges['tier5']

    player_txt = settings.get("username_label", "Player")
    player_text = render_text(f"{player_txt}: {manage_data.progress['player']['Username']}", True, (255, 255, 255))
    player_pos = (manage_data.SCREEN_WIDTH // 2 - (player_text.get_width() // 2), 100)

    ID_text = render_text(f"ID: {manage_data.progress['player']['ID']}", True, (255, 255, 255))
    ID_pos = (manage_data.SCREEN_WIDTH // 2 - (ID_text.get_width() // 2), 150)

    XP_text = render_text(f"{level}", True, color, bigfont=True)
    XP_pos2 = (manage_data.SCREEN_WIDTH // 2 - (XP_text2.get_width() - 100), 205)
    XP_pos = (manage_data.SCREEN_WIDTH // 2 - (XP_text.get_width() + XP_text2.get_width() + 30), 200)

    xp_center_x = XP_pos[0] + (XP_text.get_width() / 2)
    badge_x = xp_center_x - (badge.get_width() // 2)
    badge_pos = (badge_x, 185)

    ach_txt = current_lang.get("main_menu", {}).get("achievements", "Achievements")
    ach_text = render_text(f"{ach_txt}: {ulock_ach}/{total_ach}", True, (255, 255, 255))
    ach_pos = (manage_data.SCREEN_WIDTH // 2 - (ach_text.get_width() // 2), 310)

    screen.blit(manage_data.medals['Gold'], (manage_data.SCREEN_WIDTH // 2 - 350, 370))
    screen.blit(manage_data.medals['Diamond'], (manage_data.SCREEN_WIDTH // 2 - 50, 370))
    screen.blit(manage_data.assets['star_normal'], (manage_data.SCREEN_WIDTH // 2 + 250, 345))
    screen.blit(render_text(f"{gold_medals}", True, (255, 255, 255), bigfont=True), (manage_data.SCREEN_WIDTH // 2 - 280, 365))
    screen.blit(render_text(f"{diamond_medals}", True, (255, 255, 255), bigfont=True), (manage_data.SCREEN_WIDTH // 2 + 20, 365))
    screen.blit(render_text(f"{total_stars}", True, (255, 255, 255), bigfont=True), (manage_data.SCREEN_WIDTH // 2 + 340, 365))

    screen.blit(badge, badge_pos)
    screen.blit(XP_text, XP_pos)
    screen.blit(XP_text2, XP_pos2)
    screen.blit(ID_text, ID_pos)
    screen.blit(player_text, player_pos)
    screen.blit(ach_text, ach_pos)
    pygame.draw.rect(screen, color, (XP_pos2[0] - 80, 240, bar, 25))
    pygame.draw.rect(screen, color, (XP_pos2[0] - 80, 240, 400, 25), 2)

    back_text = back_data.get("back", "Back")
    rendered_back = render_text(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 100))
    buttons.append((rendered_back, back_rect, "back", False))
    
def draw_main_menu(screen, event, ui_states):
    # 1. Draw static backgrounds/logo
    screen.blit(manage_data.ui['logo'], ((manage_data.SCREEN_WIDTH // 2 - manage_data.ui['logo'].get_width() // 2), -20))
    screen.blit(manage_data.bgs['lilrobopeek'], ((manage_data.SCREEN_WIDTH - manage_data.bgs['lilrobopeek'].get_width()), (manage_data.SCREEN_HEIGHT - manage_data.bgs['lilrobopeek'].get_height())))

    mouse_pos = pygame.mouse.get_pos()
    hovered_key = None

    # 2. Studio Logo Logic (Website link + Glow)
    if manage_data.ui['studio_logo_rect'].collidepoint(mouse_pos):
        screen.blit(manage_data.ui['studio_glow'], manage_data.ui['studio_glow_rect'].topleft)
        if not ui_states['logo_hover'] and not manage_data.is_mute:
            manage_data.sounds['hover'].play()
        ui_states['logo_hover'] = True
        
        if event.type == pygame.MOUSEBUTTONDOWN and not ui_states['logo_click']:
            if not manage_data.is_mute: manage_data.sounds['click'].play()
            webbrowser.open("https://omerarfan.github.io/lilrobowebsite/") 
            ui_states['logo_click'] = True
            ui_states['new_news'] = False
            # Update news manifest
            manage_data.manifest["other"]["last_news_count"] = manage_data.check_for_new_gamenews(True)
            manage_data.update_local_manifest(manage_data.progress)
    else:
        screen.blit(manage_data.ui['studio_logo'], manage_data.ui['studio_logo_rect'].topleft)
        ui_states['logo_hover'] = False
        ui_states['logo_click'] = False

    # 3. News Notification
    if ui_states['new_news']:
        screen.blit(new_txt(), (20, manage_data.SCREEN_HEIGHT - 50))

    # 4. Buttons Loop
    for rendered, rect, key, is_locked in buttons:
        if rect.collidepoint(mouse_pos):
            hovered_key = key
            if hovered_key != ui_states['last_hovered'] and not manage_data.is_mute:
                manage_data.sounds['hover'].play()
        screen.blit(rendered, rect)

    ui_states['last_hovered'] = hovered_key
    return ui_states

def create_main_menu_buttons():
    global current_lang, buttons
    current_lang = manage_data.load_language().get('main_menu', {})
    buttons.clear()
    button_texts = ["start", "achievements", "character_select", "settings", "profile", "quit"]

    # Center buttons vertically and horizontally
    button_spacing = 72 
    start_y = (manage_data.SCREEN_HEIGHT // 2) - (len(button_texts) * button_spacing // 2) + 150

    for i, key in enumerate(button_texts):
        text = current_lang[key]
        rendered = render_text(text, True, (255, 255, 255))
        rect = rendered.get_rect(center=(manage_data.SCREEN_WIDTH // 2, start_y + i * button_spacing)) 
        buttons.append((rendered, rect, key, False))

def create_language_buttons(screen):
    global current_lang, buttons
    current_lang = manage_data.load_language().get('language_select', {})
    buttons.clear()
    start = manage_data.load_language().get('main_menu', {})

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
    start_x = (manage_data.SCREEN_WIDTH - grid_width) // 2
    start_y = (manage_data.SCREEN_HEIGHT // 2) - (len(language_options) // buttons_per_row * spacing_y // 2)

    heading = start.get("language", "Change Language")
    heading_text = render_text(heading, True, (255 , 255, 255))
    screen.blit(heading_text, (manage_data.SCREEN_WIDTH // 2 - heading_text.get_width() // 2, 50))

    for i, (display_name, code) in enumerate(language_options):
        text = display_name
        rendered = render_text(text, True, (255, 255, 255))

        col = i % buttons_per_row
        row = i // buttons_per_row

        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        rect = rendered.get_rect(center=(x, y))
        buttons.append((rendered, rect, code, False))

    # Add a "Back" button at the bottom center
    back_text = current_lang.get("back", "Back")
    rendered_back = render_text(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(manage_data.SCREEN_WIDTH // 2, y + spacing_y + 40))
    buttons.append((rendered_back, back_rect, "back", False))

def draw_world_stats(screen, world_name, world_key, world_rect):
    # Helper function to render world name, medals, and stars on a world button.
    # Calculate medals and stars
    medals = 0
    stars = 0
    
    if world_key == "mech":
        num_levels = 6 
    else:
        num_levels = 4
    for i in range(1, num_levels + 1):
        medal = manage_data.progress["lvls"][world_key]["1"][f"lvl{i}"]["medal"]
        if medal == "Gold" or medal == "Diamond":
            medals += 1
        
        score = manage_data.progress["lvls"][world_key]["1"][f"lvl{i}"]["score"]
        stars += LevelManager.get_stars(i, world_key, score)

    # Render text
    title = render_text(world_name, True, (255, 255, 255))
    medals_text = render_text(f"{medals}", True, (255, 255, 0), bigfont=True)
    stars_text = render_text(f"{stars}", True, (255, 255, 0), bigfont=True)

    # Position text
    title_pos = (world_rect.centerx - title.get_width() // 2, world_rect.centery - 180)
    medals_pos = (world_rect.centerx - medals_text.get_width() // 2 - 35, world_rect.centery + 150)
    gold_medal_img_pos = (world_rect.centerx - medals_text.get_width() // 2 - 130, world_rect.centery + 155)
    diam_medal_img_pos = (world_rect.centerx - medals_text.get_width() // 2 - 110, world_rect.centery + 155)
    star_img_pos = (world_rect.centerx - stars_text.get_width() // 2 + 5, world_rect.centery + 140)
    stars_pos = (world_rect.centerx - stars_text.get_width() // 2 + 105, world_rect.centery + 150)

    # Draw everything
    screen.blit(title, title_pos)
    screen.blit(manage_data.medals['Gold'], gold_medal_img_pos)
    screen.blit(manage_data.medals['Diamond'], diam_medal_img_pos)
    screen.blit(manage_data.assets['star_normal'], star_img_pos)
    screen.blit(medals_text, medals_pos)
    screen.blit(stars_text, stars_pos)

def worlds(screen):
    global current_lang, buttons
    buttons.clear()
    current_lang = manage_data.load_language().get('levels', {})

    green_txt = current_lang.get("green", "Green")
    ship_txt = current_lang.get("ship", "Ship")
    mech_txt = current_lang.get("mech", "Mech")
    desert_txt = current_lang.get("desert", "Desert")

    green_center = (manage_data.SCREEN_WIDTH // 2 - 560, manage_data.SCREEN_HEIGHT // 2 - 70)
    ship_center = (manage_data.SCREEN_WIDTH // 2 - 185, manage_data.SCREEN_HEIGHT // 2 - 70)
    mech_center = (manage_data.SCREEN_WIDTH // 2 + 190, manage_data.SCREEN_HEIGHT // 2 - 70)
    desert_center = (manage_data.SCREEN_WIDTH // 2 + 565, manage_data.SCREEN_HEIGHT // 2 - 70)
    
    mech_rect = manage_data.disks['mechpack'].get_rect(center=mech_center)
    green_rect = manage_data.disks['greenpack'].get_rect(center=green_center)
    ship_rect = manage_data.disks['shippack'].get_rect(center=ship_center)
    desert_rect = manage_data.disks['desertpack'].get_rect(center=desert_center)

    screen.blit(manage_data.disks['mechpack'], mech_rect)
    screen.blit(manage_data.disks['greenpack'], green_rect)
    screen.blit(manage_data.disks['shippack'], ship_rect)
    screen.blit(manage_data.disks['desertpack'], desert_rect)

    # Draw stats for both worlds
    draw_world_stats(screen, green_txt, "green", green_rect)
    draw_world_stats(screen, ship_txt, "ship", ship_rect)
    draw_world_stats(screen, mech_txt, "mech", mech_rect)
    draw_world_stats(screen, desert_txt, "desert", desert_rect)
    
    buttons.append((manage_data.disks['greenpack'], green_rect, "levels", False))
    buttons.append((manage_data.disks['mechpack'], mech_rect, "mech_levels", False))
    buttons.append((manage_data.disks['shippack'], ship_rect, "ship_levels", False))
    buttons.append((manage_data.disks['desertpack'], desert_rect, "desert_levels", False))

    world_text = current_lang.get("worlds", "Select World")        
    rendered_world_txt = render_text(world_text, True, (255, 255, 255))

    # --- Back Button Logic ---
    back_text = current_lang.get("back", "Back")        
    rendered_back = render_text(back_text, True, (255, 255, 255))

    back_rect = pygame.FRect(0, 0, rendered_back.get_width(), rendered_back.get_height())
    back_rect.center = (manage_data.SCREEN_WIDTH // 2 , manage_data.SCREEN_HEIGHT - 200)

    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_world_txt, (manage_data.SCREEN_WIDTH // 2 - rendered_world_txt.get_width() // 2, 50))
    screen.blit(rendered_back, text_rect)

    # Add the back button
    buttons.append((rendered_back, back_rect, "back", False))

def green_world_buttons(screen):
    global current_lang, buttons, text_rect
    buttons.clear()
    
    parts = manage_data.current_page.split("_")
    subsection = parts[1]
    
    level_options = ["lvl1", "lvl2", "lvl3", "lvl4"]
    level_no = ["1", "2", "3", "4"]
    buttons_per_row = 2
    spacing_x = 180
    spacing_y = 180

    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (manage_data.SCREEN_WIDTH - grid_width) // 2
    start_y = ((manage_data.SCREEN_HEIGHT // 2) - ((len(level_options) // buttons_per_row) * spacing_y // 2)) + 50

    for i, level in enumerate(level_options):
        col = i % buttons_per_row
        row = i // buttons_per_row
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        is_locked = manage_data.progress["lvls"]["green"][subsection][level]['locked']
        text_surface = render_text(level_no[i], True, (255, 255, 255), bigfont=True)
        disk_rect = manage_data.disks['green'].get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = render_text(back_text, True, (255, 255, 255))

    prev_text = current_lang.get("prev", "Previous")
    rendered_prev = render_text(prev_text, True, (255, 255, 255))

    next_text = current_lang.get("next", "Next")
    rendered_next = render_text(next_text, True, (255, 255, 255))

    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_back.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    back_rect.center = (manage_data.SCREEN_WIDTH // 2 , manage_data.SCREEN_HEIGHT - 200)

    prev_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_prev.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    prev_rect.center = (manage_data.SCREEN_WIDTH // 2 - 150, manage_data.SCREEN_HEIGHT - 200)

    next_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_next.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    next_rect.center = (manage_data.SCREEN_WIDTH // 2 + 150, manage_data.SCREEN_HEIGHT - 200)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    prev_txt_rect = rendered_prev.get_rect(center=prev_rect.center)
    screen.blit(rendered_prev, prev_txt_rect)

    next_txt_rect = rendered_next.get_rect(center=next_rect.center)
    screen.blit(rendered_next, next_txt_rect)

    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))
    buttons.append((rendered_prev, prev_rect, "previous", True))
    buttons.append((rendered_next, next_rect, "next", True))

def ship_world_buttons(screen):
    global text_rect, current_lang, buttons
    buttons.clear()

    level_options = ["lvl1", "lvl2", "lvl3", "lvl4"]
    level_no = ["1", "2", "3", "4"]
    buttons_per_row = 2
    spacing_x = 180
    spacing_y = 180

    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (manage_data.SCREEN_WIDTH - grid_width) // 2
    start_y = ((manage_data.SCREEN_HEIGHT // 2) - ((len(level_options) // buttons_per_row) * spacing_y // 2)) + 50

    for i, level in enumerate(level_options):
        col = i % buttons_per_row
        row = i // buttons_per_row
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        is_locked = manage_data.progress["lvls"]["ship"]["1"][level]['locked']
        text_surface = render_text(level_no[i], True, (255, 255, 255), bigfont=True)
        disk_rect = manage_data.disks['mech'].get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = render_text(back_text, True, (255, 255, 255))

    prev_text = current_lang.get("prev", "Previous")
    rendered_prev = render_text(prev_text, True, (255, 255, 255))

    next_text = current_lang.get("next", "Next")
    rendered_next = render_text(next_text, True, (255, 255, 255))

    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_back.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    back_rect.center = (manage_data.SCREEN_WIDTH // 2 , manage_data.SCREEN_HEIGHT - 200)

    prev_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_prev.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    prev_rect.center = (manage_data.SCREEN_WIDTH // 2 - 150, manage_data.SCREEN_HEIGHT - 200)

    next_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_next.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    next_rect.center = (manage_data.SCREEN_WIDTH // 2 + 150, manage_data.SCREEN_HEIGHT - 200)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    prev_txt_rect = rendered_prev.get_rect(center=prev_rect.center)
    screen.blit(rendered_prev, prev_txt_rect)

    next_txt_rect = rendered_next.get_rect(center=next_rect.center)
    screen.blit(rendered_next, next_txt_rect)
    
    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))
    buttons.append((rendered_prev, prev_rect, "previous", True))
    buttons.append((rendered_next, next_rect, "next", True))

def mech_world_buttons(screen):
    global text_rect, current_lang, buttons
    buttons.clear()

    level_options = ["lvl1", "lvl2", "lvl3", "lvl4", "lvl5", "lvl6"]
    level_no = ["1", "2", "3", "4", "5", "6"]
    buttons_per_row = 3
    spacing_x = 180
    spacing_y = 180

    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (manage_data.SCREEN_WIDTH - grid_width) // 2
    start_y = ((manage_data.SCREEN_HEIGHT // 2) - ((len(level_options) // buttons_per_row) * spacing_y // 2)) + 50

    for i, level in enumerate(level_options):
        col = i % buttons_per_row
        row = i // buttons_per_row
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        is_locked = manage_data.progress["lvls"]["mech"]["1"][level]['locked']
        text_surface = render_text(level_no[i], True, (255, 255, 255), bigfont=True)
        disk_rect = manage_data.disks['mech'].get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = render_text(back_text, True, (255, 255, 255))

    prev_text = current_lang.get("prev", "Previous")
    rendered_prev = render_text(prev_text, True, (255, 255, 255))

    next_text = current_lang.get("next", "Next")
    rendered_next = render_text(next_text, True, (255, 255, 255))

    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_back.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    back_rect.center = (manage_data.SCREEN_WIDTH // 2 , manage_data.SCREEN_HEIGHT - 200)

    prev_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_prev.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    prev_rect.center = (manage_data.SCREEN_WIDTH // 2 - 150, manage_data.SCREEN_HEIGHT - 200)

    next_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_next.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    next_rect.center = (manage_data.SCREEN_WIDTH // 2 + 150, manage_data.SCREEN_HEIGHT - 200)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    prev_txt_rect = rendered_prev.get_rect(center=prev_rect.center)
    screen.blit(rendered_prev, prev_txt_rect)

    next_txt_rect = rendered_next.get_rect(center=next_rect.center)
    screen.blit(rendered_next, next_txt_rect)
    
    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))
    buttons.append((rendered_prev, prev_rect, "previous", True))
    buttons.append((rendered_next, next_rect, "next", True))

def desert_world_buttons(screen):
    global text_rect, current_lang, buttons
    buttons.clear()

    level_options = ["lvl1", "lvl2", "lvl3", "lvl4"]
    level_no = ["1", "2", "3", "4"]
    buttons_per_row = 2
    spacing_x = 180
    spacing_y = 180

    grid_width = (buttons_per_row - 1) * spacing_x
    start_x = (manage_data.SCREEN_WIDTH - grid_width) // 2
    start_y = ((manage_data.SCREEN_HEIGHT // 2) - ((len(level_options) // buttons_per_row) * spacing_y // 2)) + 50

    for i, level in enumerate(level_options):
        col = i % buttons_per_row
        row = i // buttons_per_row
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        is_locked = manage_data.progress["lvls"]["desert"]["1"][level]['locked']
        text_surface = render_text(level_no[i], True, (255, 255, 255), bigfont=True)
        disk_rect = manage_data.disks['mech'].get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = render_text(back_text, True, (255, 255, 255))

    prev_text = current_lang.get("prev", "Previous")
    rendered_prev = render_text(prev_text, True, (255, 255, 255))

    next_text = current_lang.get("next", "Next")
    rendered_next = render_text(next_text, True, (255, 255, 255))

    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_back.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    back_rect.center = (manage_data.SCREEN_WIDTH // 2 , manage_data.SCREEN_HEIGHT - 200)

    prev_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_prev.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    prev_rect.center = (manage_data.SCREEN_WIDTH // 2 - 150, manage_data.SCREEN_HEIGHT - 200)

    next_rect = pygame.FRect(manage_data.SCREEN_WIDTH // 2 - rendered_next.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 110, 110)
    next_rect.center = (manage_data.SCREEN_WIDTH // 2 + 150, manage_data.SCREEN_HEIGHT - 200)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    prev_txt_rect = rendered_prev.get_rect(center=prev_rect.center)
    screen.blit(rendered_prev, prev_txt_rect)

    next_txt_rect = rendered_next.get_rect(center=next_rect.center)
    screen.blit(rendered_next, next_txt_rect)
    
    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))
    buttons.append((rendered_prev, prev_rect, "previous", True))
    buttons.append((rendered_next, next_rect, "next", True))

def draw_level_select(screen, mouse_pos, current_page, current_lang, messages, button_hovered_last_frame):
    # 1. Dynamic Setup
    parts = manage_data.current_page.split("_")
    world_type = parts[0]
    screen.blit(manage_data.bgs[world_type], (0, 0))
    disk_img = manage_data.disks[world_type]
    current_lang = manage_data.load_language().get('levels', {})

    # 2. Header
    title = render_text(current_lang.get("level_display", "Select Level"), True, (255, 255, 255))
    screen.blit(title, title.get_rect(center=(manage_data.SCREEN_WIDTH // 2, 50)))

    # 3. The Unified Loop
    for text_surf, rect, key, is_locked in buttons:
        is_hovered = rect.collidepoint(mouse_pos)
        
        # Draw Disk & Text
        img = disk_img if key and not is_locked else manage_data.disks['locked']
        screen.blit(img, rect)
        screen.blit(text_surf, text_surf.get_rect(center=rect.center))

        if is_hovered:
            # Hover logic
            button_hovered_last_frame = hover_effect(screen, rect, button_hovered_last_frame)
            
            # Metadata (Score/Stars) - Only for level buttons
            if key is not None:
              if key.startswith("lvl") and not is_locked:
                score = manage_data.progress["lvls"][world_type]["1"][key]['score']
                
                # Highscore
                hs_txt = render_text(messages.get("hs_m", "HS: {hs}").format(hs=score), True, (255, 255, 0))
                screen.blit(hs_txt, (manage_data.SCREEN_WIDTH//2 - hs_txt.get_width()//2, manage_data.SCREEN_HEIGHT - 50))
                
                # Medals & Stars
                medal = manage_data.progress["lvls"][world_type]["1"][key]['medal']
                if medal != "None":
                    screen.blit(manage_data.medals[medal], (manage_data.SCREEN_WIDTH // 2 - 250, manage_data.SCREEN_HEIGHT - 80))
                
                stars = LevelManager.get_stars(int(key[3:]), world_type, score)
                for i in range(stars):
                    screen.blit(manage_data.assets['star_small'], (manage_data.SCREEN_WIDTH // 2 + (i-1)*35, manage_data.SCREEN_HEIGHT - 80))
                    
    return button_hovered_last_frame

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

from cleobo.data import xp

def level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars):
    messages = manage_data.load_language().get('messages', {})
    display_score = 0
    star1_p, star2_p, star3_p = False, False, False
    star_time = time.time()
    running = True
    notified = False
    clock = pygame.time.Clock()
    star_channel = pygame.mixer.Channel(2)
    lvl_comp = messages.get("lvl_comp", "Level Complete!")
    old_xp = manage_data.progress["player"].get("XP", 0)
    rendered_lvl_comp = render_text(lvl_comp, True, (255, 255, 255))

    BG = pygame.Surface((manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT))
    BG.fill((40, 40, 40)) # A dark grey color
    BG.set_alpha(25)     # Adjust this to change how "locked" it looks
    while running:
        screen.blit(BG, (0, 0))
        screen.blit(manage_data.bgs['end'], (manage_data.SCREEN_WIDTH // 2 - manage_data.bgs['end'].get_width() // 2, 0))
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.blit(rendered_lvl_comp, (manage_data.SCREEN_WIDTH // 2 - rendered_lvl_comp.get_width() // 2, 50))

        # Animate score
        
        if display_score < score:
          if not manage_data.is_mute:
            manage_data.sounds['hover'].play()
          display_score += max(5, (score // 71))

        if stars >= 1 and (time.time() - star_time > 0.5):
                screen.blit(manage_data.assets['star'], (manage_data.SCREEN_WIDTH // 2 - 231, 110))
                if not star1_p:
                 for _ in range(40):  # Add some particles at star position
                    stareffects.append(StarParticles(manage_data.SCREEN_WIDTH // 2 - 230 + manage_data.assets['star'].get_width() // 2, 110 + manage_data.assets['star'].get_height() // 2)) 
                 if not manage_data.is_mute:
                  star_channel.play(manage_data.sounds['star1'])
                star1_p = True

        if stars >= 2 and (time.time() - star_time > 1.5):
                screen.blit(manage_data.assets['star'], (manage_data.SCREEN_WIDTH // 2 - 76, 110))
                if not star2_p and star1_p: 
                    for _ in range(40):  # Add some particles at star position
                     stareffects.append(StarParticles(manage_data.SCREEN_WIDTH // 2 - 75 + manage_data.assets['star'].get_width() // 2, 110 + manage_data.assets['star'].get_height() // 2))  
                    if not manage_data.is_mute:
                     star_channel.play(manage_data.sounds['star2'])
                    star2_p = True

        if stars >= 3 and (time.time() - star_time  >  2.5):
                screen.blit(manage_data.assets['star'], (manage_data.SCREEN_WIDTH // 2 + 79, 110)) 
                if  not star3_p and star2_p: 
                    for _ in range(40):  # Add some particles at star position
                      stareffects.append(StarParticles(manage_data.SCREEN_WIDTH // 2 + 80 + manage_data.assets['star'].get_width() // 2, 110 + manage_data.assets['star'].get_height() // 2)) 
                    if not manage_data.is_mute:
                     star_channel.play(manage_data.sounds['star3'])
                    star3_p = True

        if medal == "Gold" and death_score == 0:
            medal = "Diamond"

        if medal is not None and medal != "None":
            if medal in manage_data.medals:
                screen.blit(manage_data.medals[medal], (manage_data.SCREEN_WIDTH // 2 - 200, 300 - manage_data.medals[medal].get_height() // 2))

        for particle in stareffects[:]:
         particle.update()
         particle.draw(screen)
         if particle.life <= 0:
            stareffects.remove(particle)
        
        if display_score > score:
            display_score = score
        
        score_text = render_text(str(display_score), True, (255, 255, 255), bigfont=True)
        screen.blit(score_text, (manage_data.SCREEN_WIDTH // 2 - score_text.get_width() // 2, 300 - score_text.get_height() // 2))

        # Check for XP gained
        xp.xp()
        new_xp = manage_data.progress["player"].get("XP", 0)
        gain = new_xp - old_xp
        if time.time() - star_time > 3.2:
            xp_text = messages.get("xp_gained", "XP Gained: +{gain}").format(gain=gain)
            xp_render = render_text(xp_text, True, (0, 188, 255))
            screen.blit(xp_render, (manage_data.SCREEN_WIDTH // 2 - xp_render.get_width() // 2, 350))

        # Show Breakdown
        if score > 500: 
         if time.time() - star_time > 4:
            break_text = messages.get("breakdown", "BREAKDOWN")
            break_render = render_text(break_text, True, (158, 158, 158))
            screen.blit(break_render, (manage_data.SCREEN_WIDTH // 2 - break_render.get_width() // 2, 400))
         if time.time() - star_time > 4.2:
            base_text = messages.get("base_score", "Base Score: {bs}").format(bs=base_score)
            base_render = render_text(base_text, True, (158, 158, 158))
            screen.blit(base_render, (manage_data.SCREEN_WIDTH // 2 - base_render.get_width() // 2, 440))
         if time.time() - star_time > 4.4:
            medal_text = messages.get("medal_score", "Medal score: {ms}").format(ms=-medal_score)
            medal_render = render_text(medal_text, True, (158, 158, 158))
            screen.blit(medal_render, (manage_data.SCREEN_WIDTH // 2 - medal_render.get_width() // 2, 480))
         if time.time() - star_time > 4.6:   
            death_text = messages.get("death_score", "Death Penalty: {ds}").format(ds=-death_score)
            death_render = render_text(death_text, True, (158, 158, 158))
            screen.blit(death_render, (manage_data.SCREEN_WIDTH // 2 - death_render.get_width() // 2, 520))
         if time.time() - star_time > 4.8:
            time_text = messages.get("time_score", "Time Penalty: {ts}").format(ts=-time_score)
            time_render = render_text(time_text, True, (158, 158, 158))
            screen.blit(time_render, (manage_data.SCREEN_WIDTH // 2 - time_render.get_width() // 2, 560))
        else:
            if time.time() - star_time > 4:
             low_text = messages.get("lowest", "Lowest possible score!")
             low_render = render_text(low_text, True, (255, 0, 0))
             screen.blit(low_render, (manage_data.SCREEN_WIDTH // 2 - low_render.get_width() // 2, 450))
             if time_score > death_score:
                 reason_text = messages.get("time_reason", "You took too long to")
                 reason_text_2 = messages.get("time_reason_2", "complete the level.")
             else:
                 reason_text = messages.get("death_reason", "You died too many times!")
                 reason_text_2 = messages.get("death_reason_2", "")
             reason_render = render_text(reason_text, True, (255, 0, 0))
             screen.blit(reason_render, (manage_data.SCREEN_WIDTH // 2 - reason_render.get_width() // 2, 490))
             reason_render_2 = render_text(reason_text_2, True, (255, 0, 0))
             screen.blit(reason_render_2, (manage_data.SCREEN_WIDTH // 2 - reason_render_2.get_width() // 2, 530))

        if time.time() - star_time > 5.5:  # Show for 3.5 seconds
                if new_hs:
                    hs_text = messages.get("new_hs", "New High Score!")
                    new_hs_text = render_text(hs_text, True, (255, 215, 0))
                    screen.blit(new_hs_text, (manage_data.SCREEN_WIDTH // 2 - new_hs_text.get_width() // 2, 610))
                    if not manage_data.is_mute and not notified:
                        manage_data.sounds['hscore'].play()
                        notified = True
                else:
                    high_text = messages.get("hs_m", "Highscore: {hs}").format(hs=hs)
                    hs_text = render_text(high_text, True, (158, 158, 158))
                    screen.blit(hs_text, (manage_data.SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 610))
        
        next_left = int(8 - (time.time() - star_time))
        if time.time() - star_time > 9 or keys[pygame.K_SPACE]:
                running = False
        else: 
            # Instead of hardcoded text:
            press_text = messages.get("press_space", "Press the spacebar to")
            p_render = render_text(press_text, True, (158, 158, 158))
            screen.blit(p_render, (manage_data.SCREEN_WIDTH // 2 - p_render.get_width() // 2, manage_data.SCREEN_HEIGHT - 135))
            wait_text = messages.get("continue_wait", "continue or wait for {next_left}").format(next_left=next_left)
            w_render = render_text(wait_text, True, (158, 158, 158))
            screen.blit(w_render, (manage_data.SCREEN_WIDTH // 2 - w_render.get_width() // 2, manage_data.SCREEN_HEIGHT - 100))

        draw_notifs(screen)
        draw_syncing_status(screen)
        pygame.display.update()
        clock.tick(60)

def draw_character_select(screen, mouse_pos, events, transition, rect, key):
    global buttons
    buttons.clear()

    mouse_pos = pygame.mouse.get_pos()
    header_txt = manage_data.load_language().get('main_menu', {})

    char_sel = header_txt.get("character_select", "Character Select")
    char_text = render_text(char_sel, True, (255, 255, 255))
    screen.blit(char_text, (manage_data.SCREEN_WIDTH // 2 - char_text.get_width() // 2, 50))

    rarities = manage_data.load_language().get('char_select', {})

    back_text = rarities.get("back", "Back")
    rendered_back = render_text(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 50))
    buttons.append((rendered_back, back_rect, "back", False))

    common = render_text(rarities.get("common", "Common"), True, (0, 249, 41))
    rare = render_text(rarities.get("rare", "Rare"), True, (0, 196, 255))
    epic = render_text(rarities.get("epic", "Epic"), True, (102, 0, 255))
    legi = render_text(rarities.get("legi", "Legendary"), True, (255, 154, 0))

    screen.blit(common, (manage_data.SCREEN_WIDTH // 2 - common.get_width() // 2, 130))
    screen.blit(rare, (manage_data.SCREEN_WIDTH // 2 - rare.get_width() // 2, 300))
    screen.blit(epic, (manage_data.SCREEN_WIDTH // 2 - epic.get_width() // 2, 470))
    screen.blit(legi, (manage_data.SCREEN_WIDTH // 2 - legi.get_width() // 2, 640))

    manage_data.unlocked_robos = {
        'robot': True,
        'sunnyrobot': manage_data.progress["char"].get("sunnyrobo", False),
        'evilrobot': manage_data.progress["char"].get("evilrobo", False),
        'greenrobot': manage_data.progress["char"].get("greenrobo", False),
        'ironrobot': manage_data.progress["char"].get("ironrobo", False),
        'cakebot': manage_data.progress["char"].get("cakebot", False),
        'vectorbot': manage_data.progress["char"].get("vectorbot", False),
        'piratebot': manage_data.progress["char"].get("piratebot", False),
        'cashrobot': manage_data.progress["char"].get("cashrobo", False)
    }
        
    selected_character = manage_data.progress["pref"].get("character", manage_data.default_progress["pref"]["character"])
        
    LOCKED_FILTER = pygame.Surface((100, 100))
    LOCKED_FILTER.fill((40, 40, 40)) # A dark grey color
    LOCKED_FILTER.set_alpha(210)     # Adjust this to change how "locked" it looks      

    for robo_name in ['robot', 'evilrobot', 'greenrobot', 'ironrobot', 'cakebot', 'vectorbot', 'piratebot', 'sunnyrobot', 'cashrobot']:
        rect = manage_data.robo_rects[robo_name]  
        if manage_data.unlocked_robos[robo_name]:
            screen.blit(manage_data.robos[robo_name], rect)
        else:
            screen.blit(manage_data.robos[robo_name], rect)
            screen.blit(LOCKED_FILTER, rect)
        
    # Draw a highlight border around the selected character
    highlight_colors = {
        "robot": (63, 72, 204),
        'sunnyrobot': (189, 82, 10),
        "evilrobot": (128, 0, 128),
        "greenrobot": (25, 195, 21),
        "ironrobot": (64, 64, 64),
        "cakebot": (255, 171, 204),
        "vectorbot": (25, 46, 222),
        "piratebot": (56, 30, 10),
        "cashrobot": (2, 214, 1),
        }
    
    if selected_character in manage_data.robo_rects:
        pygame.draw.rect(screen, highlight_colors[selected_character], manage_data.robo_rects[selected_character].inflate(5, 5), 5)

        # Display locked message if one exists
    if hasattr(state, 'locked_message') and state.locked_message is not None:
            screen.blit(state.locked_message, (manage_data.SCREEN_WIDTH // 2 - state.locked_message.get_width() // 2, 90))

    for event in events:
        if event.type == pygame.QUIT:
            state.set_page(screen, "quit_confirm", transition)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if manage_data.robo_rects['robot'].collidepoint(mouse_pos):
                try_select_robo(manage_data.unlocked_robos['robot'], "robot", manage_data.robo_rects['robot'], "placeholder", "Imagine if this actually popped up in game BRO-", transition)
            elif manage_data.robo_rects['evilrobot'].collidepoint(mouse_pos):
                try_select_robo(manage_data.unlocked_robos['evilrobot'], "evilrobot", manage_data.robo_rects['evilrobot'], "evilrobo", "Encounter this robot in an alternative route to unlock him!", transition)
            elif manage_data.robo_rects['greenrobot'].collidepoint(mouse_pos):
                try_select_robo(manage_data.unlocked_robos['greenrobot'], "greenrobot", manage_data.robo_rects['greenrobot'], "greenrobo", "Get GOLD rank in all Green World Levels to unlock this robot!", transition)
            elif manage_data.robo_rects['ironrobot'].collidepoint(mouse_pos):
                try_select_robo(manage_data.unlocked_robos['ironrobot'], "ironrobot", manage_data.robo_rects['ironrobot'], "ironrobo", "Unlock the Zenith Of Six achievement to get this character!", transition)
            elif manage_data.robo_rects['cakebot'].collidepoint(mouse_pos):
                try_select_robo(manage_data.unlocked_robos['cakebot'], "cakebot", manage_data.robo_rects['cakebot'], "cakebot", "This Robo will be available every April 29!", transition)
            elif manage_data.robo_rects['vectorbot'].collidepoint(mouse_pos):
                try_select_robo(manage_data.unlocked_robos['vectorbot'], "vectorbot", manage_data.robo_rects['vectorbot'], "vectorbot", "Unlock the Mechanical Engineer achievement to get this robo!", transition)
            elif manage_data.robo_rects['piratebot'].collidepoint(mouse_pos):
                try_select_robo(manage_data.unlocked_robos['piratebot'], "piratebot", manage_data.robo_rects['piratebot'], "piratebot", "Become the Captain of the Ship to get this robo!", transition)
            elif manage_data.robo_rects['sunnyrobot'].collidepoint(mouse_pos):
                try_select_robo(manage_data.unlocked_robos['sunnyrobot'], "sunnyrobot", manage_data.robo_rects['sunnyrobot'], "sunnyrobot", "Get the speedy starter achievement to unlock this robo!", transition)            
            elif manage_data.robo_rects['cashrobot'].collidepoint(mouse_pos):
                try_select_robo(manage_data.unlocked_robos['cashrobot'], "cashrobot", manage_data.robo_rects['cashrobot'], "cashrobot", "Get the XP Collector achievement to unlock this robo!", transition)            
            elif rect.collidepoint(mouse_pos):
                state.handle_action(key, transition, manage_data.current_page)

def try_select_robo(unlock_flag, char_key, rect, locked_msg_key, fallback_msg, transition):
    if rect.collidepoint(pygame.mouse.get_pos()):
        global selected_character
        charsel = manage_data.load_language().get('char_select', {})

        if unlock_flag:
            selected_character = char_key
            manage_data.progress["pref"]["character"] = selected_character
            manage_data.selected_character = selected_character
            manage_data.save_progress(manage_data.progress, manage_data.manifest)
            if not manage_data.is_mute:
                manage_data.sounds['click'].play()
        else:
            state.handle_action("locked", transition, manage_data.current_page)  # Trigger the locked transition effect
            if not state.locked_char_sound_played or time.time() - state.locked_char_sound_time > 1.5: # type: ignore
                if not manage_data.is_mute:
                    manage_data.sounds['death'].play()
                state.locked_char_sound_time = time.time()
                state.locked_char_sound_played = True
            if state.wait_time is None:
                state.wait_time = pygame.time.get_ticks()
            locked_text = charsel.get(locked_msg_key, fallback_msg)
            state.locked_message = render_text(locked_text, True, (255, 255, 0))

def settings_menu(screen):
    global current_lang, buttons
    # 1. Load language (only once per page change is better, but this works)
    current_lang = manage_data.load_language().get('settings', {})
    setting_lang = manage_data.load_language().get('main_menu', {})
    buttons.clear()
    screen.blit(manage_data.bgs['plain'], (0, 0))

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
    heading_text = render_text(heading, True, (255 , 255, 255))
    screen.blit(heading_text, (manage_data.SCREEN_WIDTH // 2 - heading_text.get_width() // 2, 200))

    button_spacing = 72
    start_y = (manage_data.SCREEN_HEIGHT // 2) - (len(button_data) * button_spacing // 2) + 150

    for i, (display_text, internal_key) in enumerate(button_data):
        rendered = render_text(display_text, True, (255, 255, 255))
        rect = rendered.get_rect(center=(manage_data.SCREEN_WIDTH // 2, start_y + i * button_spacing)) 
        # Store the internal_key so handle_action knows what was clicked
        buttons.append((rendered, rect, internal_key, False))

    # Mouse pos for hover effects
    mouse_pos = pygame.mouse.get_pos()
    
    for rendered, rect, key, _ in buttons:
        if rect.collidepoint(mouse_pos):
            # Add a small glow for hover feedback
            pygame.draw.rect(screen, (0, 213, 0), rect.inflate(20, 10), 2)
        screen.blit(rendered, rect)

def about_menu(screen):
    global buttons
    buttons.clear()
    screen.blit(manage_data.bgs['plain'], (0, 0))
    settings_lang = manage_data.load_language().get('settings', {})

    title = settings_lang.get("About", "About")
    title_rendered = render_text(title, True, (255, 255, 255))
    screen.blit(title_rendered, (manage_data.SCREEN_WIDTH // 2 - title_rendered.get_width() // 2, 50))

    site = settings_lang.get("site_credit", "Sound effects used from pixabay.com and edited using Audacity")
    site_text = render_text(site, True, (255, 255, 255))
    site_pos = ((manage_data.SCREEN_WIDTH // 2 - site_text.get_width() // 2), 150)

    logo = settings_lang.get("logo_credit", "Logo and Backgrounds made with canva.com")
    logo_text = render_text(logo, True, (255, 255, 255))
    logo_pos = ((manage_data.SCREEN_WIDTH // 2- logo_text.get_width() // 2), 190)

    credit = settings_lang.get("credit_credit", "Made by Omer Arfan")
    credit_text = render_text(credit, True, (255, 255, 255))
    credit_pos = ((manage_data.SCREEN_WIDTH // 2 - credit_text.get_width() // 2), 230)

    ver = settings_lang.get("version_credit", "Game Version: {version}").format(version=manage_data.version)
    ver_text = render_text(ver, True, (255, 255, 255))
    ver_pos = ((manage_data.SCREEN_WIDTH // 2 - ver_text.get_width() // 2), 270)

    ker = settings_lang.get("kernel_credit", "Cleobo Version: {kernel}").format(kernel=manage_data.kernel)
    ker_text = render_text(ker, True, (255, 255, 255))
    ker_pos = ((manage_data.SCREEN_WIDTH // 2 - ker_text.get_width() // 2), 310)

    # License rendering
    lic = settings_lang.get("license_credit", "Licensed under GNU GPL v3.0")
    lic_text = render_text(lic, True, (255, 255, 255))
    lic_pos = ((manage_data.SCREEN_WIDTH // 2 - lic_text.get_width() // 2), 350)

    thx = settings_lang.get("thanks", "Thank you for playing! You are amazing!")
    thx_text = render_text(thx, True, (0, 255, 0))
    thx_pos = ((manage_data.SCREEN_WIDTH // 2 - thx_text.get_width() // 2), 430)

    bugs = settings_lang.get("bugs", "If you find any bugs, please report them on the GitHub repository.")
    bugs_text = render_text(bugs, True, (242, 123, 32))
    bugs_pos = ((manage_data.SCREEN_WIDTH // 2 - bugs_text.get_width() // 2), 470)

    sorry = settings_lang.get("sorry", "Sorry for any inconvenience caused by bugs.")
    sorry_text = render_text(sorry, True, (242, 123, 32))
    sorry_pos = ((manage_data.SCREEN_WIDTH // 2 - sorry_text.get_width() // 2), 510)

    screen.blit(logo_text, logo_pos)
    screen.blit(site_text, site_pos)
    screen.blit(credit_text, credit_pos)
    screen.blit(ver_text, ver_pos)
    screen.blit(ker_text, ker_pos)
    screen.blit(lic_text, lic_pos)
    screen.blit(thx_text, thx_pos)
    screen.blit(bugs_text, bugs_pos)
    screen.blit(sorry_text, sorry_pos)

    license_btn_text = settings_lang.get("view_license", "View License")
    license_btn_rendered = render_text(license_btn_text, True, (255, 255, 255))
    license_btn_rect = license_btn_rendered.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 194))
    buttons.append((license_btn_rendered, license_btn_rect, "License", False))

    support_text = settings_lang.get("support", "Support / Report Bugs")
    support_rendered = render_text(support_text, True, (255, 255, 255))
    support_rect = support_rendered.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 122))
    buttons.append((support_rendered, support_rect, "Support", False))

    back_text = settings_lang.get("Back", "Back")
    rendered = render_text(back_text, True, (255, 255, 255))
    rect = rendered.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 50))
    buttons.append((rendered, rect, "Back", False))

def audio_settings_menu(screen):
    global buttons
    buttons.clear()
    screen.blit(manage_data.bgs['plain'], (0, 0))
    settings_lang = manage_data.load_language().get('settings', {})

    # 1. Draw Title
    title_str = settings_lang.get("Audio", "Audio")
    title_txt = render_text(title_str, True, (255, 255, 255))
    screen.blit(title_txt, (manage_data.SCREEN_WIDTH // 2 - title_txt.get_width() // 2, 200))
    
    # 2. Sound Buttons (SFX)
    sound_label = settings_lang.get("Sound", "Sound")
    if manage_data.is_mute:
        # Fetches "Unmute {setting}" and replaces {setting} with "Sound"
        sfx_text_str = settings_lang.get("Unmute", "Unmute {setting}").format(setting=sound_label)
    else:
        # Fetches "Mute {setting}" and replaces {setting} with "Sound"
        sfx_text_str = settings_lang.get("Mute", "Mute {setting}").format(setting=sound_label)
    
    renderedsfx = render_text(sfx_text_str, True, (255, 255, 255))
    rectsfx = renderedsfx.get_rect(center=(manage_data.SCREEN_WIDTH // 2, 350))
    buttons.append((renderedsfx, rectsfx, "SFX", False)) # Keeping "SFX" as the internal ID for your click handler

    # 3. Ambience Buttons
    amb_label = settings_lang.get("Ambience", "Ambience")
    if manage_data.is_mute_amb:
        amb_text_str = settings_lang.get("Unmute", "Unmute {setting}").format(setting=amb_label)
    else:
        amb_text_str = settings_lang.get("Mute", "Mute {setting}").format(setting=amb_label)
    
    renderedamb = render_text(amb_text_str, True, (255, 255, 255))
    rectamb = renderedamb.get_rect(center=(manage_data.SCREEN_WIDTH // 2, 450))
    buttons.append((renderedamb, rectamb, "Ambience", False))

    # 4. Back Button
    back_txt = settings_lang.get("Back", "Back")
    renderedback = render_text(back_txt, True, (255, 255, 255))
    rectback = renderedback.get_rect(center=(manage_data.SCREEN_WIDTH // 2, 550))
    buttons.append((renderedback, rectback, "Back", False))
    
    # Blit everything to the screen
    screen.blit(renderedsfx, rectsfx)
    screen.blit(renderedamb, rectamb)
    screen.blit(renderedback, rectback)


def create_quit_confirm_buttons():
    global current_lang, buttons
    buttons.clear()

    # Get the quit confirmation text from the current language
    messages = manage_data.load_language().get('messages', {})
    confirm_quit = messages.get("confirm_quit", "Are you sure you want to quit?")

    # Store the quit confirmation text for rendering in the main loop
    quit_text = render_text(confirm_quit, True, (255, 255, 255))
    quit_text_rect = quit_text.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT // 2 - 25))

    # Create "Yes" button
    yes_text = messages.get("yes", "Yes")
    rendered_yes = render_text(yes_text, True, (255, 255, 255))
    yes_rect = rendered_yes.get_rect(center=(manage_data.SCREEN_WIDTH // 2 - 100, manage_data.SCREEN_HEIGHT // 2 + 50))
    buttons.append((rendered_yes, yes_rect, "yes", False))

    # Create "No" button
    no_text = messages.get("no", "No")
    rendered_no = render_text(no_text, True, (255, 255, 255))
    no_rect = rendered_no.get_rect(center=(manage_data.SCREEN_WIDTH // 2 + 100, manage_data.SCREEN_HEIGHT // 2 + 50))
    buttons.append((rendered_no, no_rect, "no", False))

    return quit_text, quit_text_rect

def new_txt():
    current_lang = manage_data.load_language().get('main_menu', {})
    new_txt = render_text(current_lang.get("new", "Update Available!"), True, (225, 212, 31))
    return new_txt

# Inside py (or similar)
def show_resolution_limit(screen):
    countdown = 5
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()

    while countdown > 0:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        elapsed = (pygame.time.get_ticks() - start_time) // 1000
        countdown = 5 - elapsed
        
        screen.fill((0, 0, 0))
        
        # Center the evil robot
        robo_x = manage_data.SCREEN_WIDTH // 2 - manage_data.robos['evilrobot'].get_width() // 2
        robo_y = manage_data.SCREEN_HEIGHT // 2 - 200
        screen.blit(manage_data.robos['evilrobot'], (robo_x, robo_y))

        # Fetch localized messages
        messages = manage_data.load_language().get('messages', {})
        
        # Render texts using your existing render_text logic
        texts = [
            (messages.get("deny_message", "Access denied!"), (255, 100, 100), -280),
            (messages.get("error_message", "Your screen resolution is too small!"), (255, 255, 255), -40),
            (messages.get("error_message2", "Increase the resolution in system settings."), (255, 255, 255), 0),
            (messages.get("countdown_message", "Closing in {countdown} seconds...").format(countdown=countdown), (255, 100, 100), 50)
        ]

        for text_str, color, offset in texts:
            rendered = render_text(text_str, True, color)
            screen.blit(rendered, (manage_data.SCREEN_WIDTH // 2 - rendered.get_width() // 2, manage_data.SCREEN_HEIGHT // 2 + offset))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()