import pygame
import arabic_reshaper
import time
from bidi.algorithm import get_display
import level_logic
import manage_data
import math
import state

def render_text(text, Boolean, color):
    # 1. PICK THE FONT (Your existing Unicode Logic)
    font_to_use = manage_data.fonts['def'] # Default
    display_text = text

    if any('\u0590' <= c <= '\u06FF' for c in text):  # Urdu/Arabic range
        reshaped = arabic_reshaper.reshape(text)
        display_text = get_display(reshaped)
        font_to_use = manage_data.fonts['ar']
    elif any('\u4e00' <= c <= '\u9fff' for c in text):  # Chinese
        font_to_use = manage_data.fonts['ch']
    elif any('\u3040' <= c <= '\u30FF' for c in text): # Japanese
        font_to_use = manage_data.fonts['jp']   
    elif any('\uAC00' <= c <= '\uD7A3' for c in text):  # Korean
        font_to_use = manage_data.fonts['kr']

    # 2. RENDER THE SHADOW (For Readability on Green/Mech BGs)
    shadow_color = (0, 0, 0)
    shadow_surf = font_to_use.render(display_text, True, shadow_color)
    
    # 3. RENDER MAIN TEXT
    main_surf = font_to_use.render(display_text, True, color)
    
    # 4. COMBINE INTO ONE SURFACE
    w = max(1, main_surf.get_width() + 2)
    h = max(1, main_surf.get_height() + 1)
    combined_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    combined_surf.blit(shadow_surf, (1, 1)) # The offset shadow
    combined_surf.blit(main_surf, (0, 0))   # The original text
    
    return combined_surf

def draw_buttons(screen, buttons, hover_sound, is_mute, mouse_pos, button_hovered_last_frame):
    for rendered, rect, key, is_locked in buttons:
        if rect.collidepoint(mouse_pos):
            button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
            button_surface.fill((8, 81, 179, 255))
            screen.blit(button_surface, rect.inflate(20, 10).topleft)
            pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
            button_hovered_last_frame = hover_effect(screen, rect, hover_sound, is_mute, button_hovered_last_frame)
        else:
            button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
            button_surface.fill((8, 81, 179, 255))
            screen.blit(button_surface, rect.inflate(20, 10).topleft)
            pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
        screen.blit(rendered, rect)
    return button_hovered_last_frame

def hover_effect(screen, rect, hover_sound, is_mute, button_hovered_last_frame):
    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
    hovered = rect.collidepoint(pygame.mouse.get_pos())
    if hovered and not button_hovered_last_frame and not is_mute:
        hover_sound.play()
    button_hovered_last_frame = hovered
    return button_hovered_last_frame

def draw_notifs(screen):
    global notif, er, notification_time, notification_text, error_code
    if notif:
            if time.time() - notification_time < 4:  # Show for 4 seconds
                screen.blit(notification_text, (manage_data.SCREEN_WIDTH // 2 - notification_text.get_width() // 2, 100))
    else:
        notif = False

    if er:
        if notification_time is not None and time.time() - notification_time < 4:  # Show for 4 seconds
            screen.blit(error_code, (manage_data.SCREEN_WIDTH // 2 - error_code.get_width() // 2, 130))
    else:
        er = False

buttons = []

def draw_loading_bar(screen, bg, stage_name, percent):
    screen.blit(bg, (0, 0))
    complete = None
    text = manage_data.fonts['def'].render(f"{stage_name}", True, (255, 255, 255))
    text_rect = text.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 60))
    screen.blit(text, text_rect)
    draw_loading_orb(screen, text_rect.x, text_rect.y, complete)
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

def create_achieve_screen(screen, lang_code, manifest, progress):
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
    ach_header = render_text(ach_txt, True, (255, 255, 255))
    screen.blit(ach_header, (manage_data.SCREEN_WIDTH // 2 - ach_header.get_width() // 2, 50))

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

        title_surf = render_text(title_str, True, color)
        if lang_code == "ar" or lang_code == "pk":
            x_pos = manage_data.SCREEN_WIDTH - 100 - title_surf.get_width()
        else:
            x_pos = 100
        screen.blit(title_surf, (x_pos, y_offset))

        count += 1
        if count % 2 == 0:
           y_offset += 52
        else:
           y_offset += 25

    back_text = back_data.get("back", "Back")
    rendered_back = render_text(back_text, True, (255, 255, 255))
    back_rect = rendered_back.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 100))
    buttons.append((rendered_back, back_rect, "back", False))

def create_main_menu_buttons(screen, lang_code, manifest, progress):

    global current_lang, buttons
    current_lang = manage_data.load_language(lang_code, manifest).get('main_menu', {})
    buttons.clear()
    button_texts = ["start", "achievements", "character_select", "settings", "quit"]

    # Center buttons vertically and horizontally
    button_spacing = 72 
    start_y = (manage_data.SCREEN_HEIGHT // 2) - (len(button_texts) * button_spacing // 2) + 150

    for i, key in enumerate(button_texts):
        text = current_lang[key]
        rendered = render_text(text, True, (255, 255, 255))
        rect = rendered.get_rect(center=(manage_data.SCREEN_WIDTH // 2, start_y + i * button_spacing)) 
        buttons.append((rendered, rect, key, False))


def create_language_buttons(screen, lang_code, manifest, progress):
    global current_lang, buttons
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

def worlds(screen, lang_code, manifest, progress, bgs, disks):
    global current_lang, buttons
    buttons.clear()
    current_lang = manage_data.load_language(lang_code, manifest).get('language_select', {})
    screen.blit(bgs['plain'], (0, 0))

    # 1. Define Positions
    # We define the center points so the image and the button hitbox align perfectly
    green_center = (manage_data.SCREEN_WIDTH // 2 - 250, manage_data.SCREEN_HEIGHT // 2)
    mech_center = (manage_data.SCREEN_WIDTH // 2 + 250, manage_data.SCREEN_HEIGHT // 2)

    # 2. Draw the Disks
    # Use the rect to blit so the image is centered on our coordinates
    mech_rect = disks['mechpack'].get_rect(center=mech_center)
    green_rect = disks['greenpack'].get_rect(center=green_center)
    
    screen.blit(disks['mechpack'], mech_rect)
    screen.blit(disks['greenpack'], green_rect)

    # 3. Add Disks to the Button List
    # Format: (surface/image, rect, action_key, is_locked)
    buttons.append((disks['greenpack'], green_rect, "levels", False))
    buttons.append((disks['mechpack'], mech_rect, "mech_levels", False))

    # --- Back Button Logic ---
    back_text = current_lang.get("back", "Back")        
    rendered_back = render_text(back_text, True, (255, 255, 255))

    back_rect = pygame.Rect(0, 0, rendered_back.get_width(), rendered_back.get_height())
    back_rect.center = (manage_data.SCREEN_WIDTH // 2 , manage_data.SCREEN_HEIGHT - 200)

    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    # Add the back button
    buttons.append((rendered_back, back_rect, "back", False))

def green_world_buttons(screen, lang_code, manifest, progress, bgs, disks):
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
    start_x = (manage_data.SCREEN_WIDTH - grid_width) // 2
    start_y = ((manage_data.SCREEN_HEIGHT // 2) - ((len(level_options) // buttons_per_row) * spacing_y // 2)) + 50

    for i, level in enumerate(level_options):
        col = i % buttons_per_row
        row = i // buttons_per_row
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        is_locked = level in progress["lvls"]["locked_levels"]
        text_surface = manage_data.fonts['mega'].render(level_no[i], True, (255, 255, 255))
        disk_rect = disks['green'].get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = render_text(back_text, True, (255, 255, 255))

    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.Rect(manage_data.SCREEN_WIDTH // 2 - rendered_back.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 100, 100)
    back_rect.center = (manage_data.SCREEN_WIDTH // 2 , manage_data.SCREEN_HEIGHT - 200)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))

    next_text = current_lang.get("next", "next")
    rendered_next = render_text(next_text, True, (255, 255, 255))

    next_rect = pygame.Rect(0, 0, 100, 100)
    next_rect.center = (manage_data.SCREEN_WIDTH - 90, manage_data.SCREEN_HEIGHT // 2)

    text_rect = rendered_next.get_rect(center=next_rect.center)
    screen.blit(rendered_next, text_rect)

def mech_world_buttons(screen, lang_code, manifest, progress, bgs, disks):
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
    start_x = (manage_data.SCREEN_WIDTH - grid_width) // 2
    start_y = ((manage_data.SCREEN_HEIGHT // 2) - ((len(level_options) // buttons_per_row) * spacing_y // 2)) + 50

    for i, level in enumerate(level_options):
        col = i % buttons_per_row
        row = i // buttons_per_row
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y

        is_locked = level in progress["lvls"]["locked_levels"]
        text_surface = manage_data.fonts['mega'].render(level_no[i], True, (255, 255, 255))
        disk_rect = disks['mech'].get_rect(center=(x, y))
        buttons.append((text_surface, disk_rect, level if not is_locked else None, is_locked))

    # Get the text
    back_text = current_lang.get("back", "Back")        
    rendered_back = render_text(back_text, True, (255, 255, 255))

    # Create a fixed 100x100 hitbox centered at the right location
    back_rect = pygame.Rect(manage_data.SCREEN_WIDTH // 2 - rendered_back.get_width() // 2, manage_data.SCREEN_HEIGHT - 175, 100, 100)
    back_rect.center = (manage_data.SCREEN_WIDTH // 2 , manage_data.SCREEN_HEIGHT - 200)

    # Then during draw phase: center the text inside that fixed rect
    text_rect = rendered_back.get_rect(center=back_rect.center)
    screen.blit(rendered_back, text_rect)

    # Add the button
    buttons.append((rendered_back, back_rect, "back", False))

    next_text = current_lang.get("next", "next")
    rendered_next = render_text(next_text, True, (255, 255, 255))

def draw_level_select(screen, mouse_pos, current_page, current_lang, messages, button_hovered_last_frame):
    # 1. Dynamic Setup
    world_type = 'green' if current_page == "levels" else 'mech'
    screen.blit(manage_data.bgs[world_type], (0, 0))
    disk_img = manage_data.disks[world_type]
    
    # 2. Header
    title = render_text(current_lang.get("level_display", "Select"), True, (255, 255, 255))
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
            button_hovered_last_frame = hover_effect(screen, rect, manage_data.sounds['hover'], manage_data.is_mute, button_hovered_last_frame)
            
            # Metadata (Score/Stars) - Only for level buttons
            if key.startswith("lvl") and not is_locked:
                score = manage_data.progress["lvls"]['score'][key]
                
                # Highscore
                hs_txt = render_text(messages.get("hs_m", "HS: {hs}").format(hs=score), True, (255, 255, 0))
                screen.blit(hs_txt, (manage_data.SCREEN_WIDTH//2 - hs_txt.get_width()//2, manage_data.SCREEN_HEIGHT - 50))
                
                # Medals & Stars
                medal = manage_data.progress["lvls"]['medals'][key]
                if medal != "None":
                    screen.blit(manage_data.medals[medal], (manage_data.SCREEN_WIDTH // 2 - 250, manage_data.SCREEN_HEIGHT - 80))
                
                stars = level_logic.get_stars(int(key[3:]), score)
                for i in range(stars):
                    screen.blit(manage_data.assets['star_small'], (manage_data.SCREEN_WIDTH // 2 + (i-1)*25, manage_data.SCREEN_HEIGHT - 80))
                    
    return button_hovered_last_frame

def draw_character_select(screen, mouse_pos, events, transition, rect, key):
         screen.blit(manage_data.bgs['plain'], (0, 0))

         locked_sound_played = False
         mouse_pos = pygame.mouse.get_pos()

         messages = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('messages', {})  # Fetch localized messages
         header_txt = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('main_menu', {})
         char_sel = header_txt.get("character_select", "Character Select")
         char_text = render_text(char_sel, True, (255, 255, 255))
         screen.blit(char_text, (manage_data.SCREEN_WIDTH // 2 - 100, 50))

         manage_data.unlocked_robos = {
            'robot': True,
            'evilrobot': manage_data.progress["char"].get("evilrobo", False),
            'greenrobot': manage_data.progress["char"].get("greenrobo", False),
            'ironrobot': manage_data.progress["char"].get("ironrobo", False)
         }
         
         selected_character = manage_data.progress["pref"].get("character", manage_data.default_progress["pref"]["character"])
         
         screen.blit(manage_data.robos['robot'], manage_data.robo_rects['robot'])     
         screen.blit(manage_data.robos['evilrobot'] if manage_data.unlocked_robos['evilrobot'] else manage_data.robos['locked'], manage_data.robo_rects['evilrobot'])
         screen.blit(manage_data.robos['greenrobot'] if manage_data.unlocked_robos['greenrobot'] else manage_data.robos['locked'], manage_data.robo_rects['greenrobot'])
         screen.blit(manage_data.robos['ironrobot'] if manage_data.unlocked_robos['ironrobot'] else manage_data.robos['locked'], manage_data.robo_rects['ironrobot'])
         # Draw a highlight border around the selected character
         highlight_colors = {
          "robot": (63, 72, 204),
          "evilrobot": (128, 0, 128),
          "greenrobot": (25, 195, 21),
          "ironrobot": (64, 64, 64),
         }
        
         if selected_character in manage_data.robo_rects:
          pygame.draw.rect(screen, highlight_colors[selected_character], manage_data.robo_rects[selected_character].inflate(5, 5), 5)

         for event in events:
           if event.type == pygame.QUIT:
            state.set_page(screen, "quit_confirm", manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.Achievements, manage_data.bgs, manage_data.disks, manage_data.version, manage_data.is_mute, manage_data.is_mute_amb, transition)

           elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if manage_data.robo_rects['robot'].collidepoint(mouse_pos):
                manage_data.try_select_robo(manage_data.unlocked_robos['robot'], "robot", manage_data.robo_rects['robot'], "placeholder", "Imagine if this actually popped up in game BRO-", transition)
            elif manage_data.robo_rects['evilrobot'].collidepoint(mouse_pos):
                manage_data.try_select_robo(manage_data.unlocked_robos['evilrobot'], "evilrobot", manage_data.robo_rects['evilrobot'], "evillocked_message", "Encounter this robot in an alternative route to unlock him!", transition)
            elif manage_data.robo_rects['greenrobot'].collidepoint(mouse_pos):
                manage_data.try_select_robo(manage_data.unlocked_robos['greenrobot'], "greenrobot", manage_data.robo_rects['greenrobot'], "greenlocked_message", "Get GOLD rank in all Green World Levels to unlock this robot!", transition)
            elif manage_data.robo_rects['ironrobot'].collidepoint(mouse_pos):
                manage_data.try_select_robo(manage_data.unlocked_robos['ironrobot'], "ironrobot", manage_data.robo_rects['ironrobot'], "ironlocked_message", "Unlock the Zenith Of Six achievement to get this character!", transition)
            elif rect.collidepoint(mouse_pos):
                state.handle_action(key, transition, manage_data.current_page)

def character_select(lang_code, manifest):
    
    # Clear screen
    buttons.clear()
    current_lang = manage_data.load_language(lang_code, manifest)['char_select']
    button_texts = ["back"]

    for i, key in enumerate(button_texts):
        text = current_lang[key]
        rendered = render_text(text, True, (255, 255, 255))
        rect = rendered.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 100)) 
        buttons.append((rendered, rect, key, False))
   
    pygame.display.flip()

def settings_menu(screen, lang_code, manifest, bgs):
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

def about_menu(screen, lang_code, manifest, bgs, version):
    global buttons
    buttons.clear()
    screen.blit(bgs['plain'], (0, 0))
    settings_lang = manage_data.load_language(lang_code, manifest).get('settings', {})

    title = settings_lang.get("About", "About")
    title_rendered = render_text(title, True, (255, 255, 255))
    screen.blit(title_rendered, (manage_data.SCREEN_WIDTH // 2 - title_rendered.get_width() // 2, 100))

    site = settings_lang.get("site_credit", "Sound effects used from pixabay.com and edited using Audacity")
    site_text = render_text(site, True, (255, 255, 255))
    site_pos = ((manage_data.SCREEN_WIDTH // 2 - site_text.get_width() // 2), 200)

    logo = settings_lang.get("logo_credit", "Logo and Backgrounds made with canva.com")
    logo_text = render_text(logo, True, (255, 255, 255))
    logo_pos = ((manage_data.SCREEN_WIDTH // 2- logo_text.get_width() // 2), 240)

    credit = settings_lang.get("credit_credit", "Made by Omer Arfan")
    credit_text = render_text(credit, True, (255, 255, 255))
    credit_pos = ((manage_data.SCREEN_WIDTH // 2 - credit_text.get_width() // 2), 280)

    ver = settings_lang.get("version_credit", "Game Version: {version}").format(version=manage_data.version)
    ver_text = render_text(ver, True, (255, 255, 255))
    ver_pos = ((manage_data.SCREEN_WIDTH // 2 - ver_text.get_width() // 2), 320)

    ker = settings_lang.get("kernel_credit", "Cleobo Version: {kernel}").format(kernel=manage_data.kernel)
    ker_text = render_text(ker, True, (255, 255, 255))
    ker_pos = ((manage_data.SCREEN_WIDTH // 2 - ker_text.get_width() // 2), 360)

    thx = settings_lang.get("thanks", "Thank you for playing! You are amazing!")
    thx_text = render_text(thx, True, (0, 255, 0))
    thx_pos = ((manage_data.SCREEN_WIDTH // 2 - thx_text.get_width() // 2), 440)

    bugs = settings_lang.get("bugs", "If you find any bugs, please report them on the GitHub repository.")
    bugs_text = render_text(bugs, True, (242, 123, 32))
    bugs_pos = ((manage_data.SCREEN_WIDTH // 2 - bugs_text.get_width() // 2), 480)

    sorry = settings_lang.get("sorry", "Sorry for any inconvenience caused by bugs.")
    sorry_text = render_text(sorry, True, (242, 123, 32))
    sorry_pos = ((manage_data.SCREEN_WIDTH // 2 - sorry_text.get_width() // 2), 520)

    screen.blit(logo_text, logo_pos)
    screen.blit(site_text, site_pos)
    screen.blit(credit_text, credit_pos)
    screen.blit(ver_text, ver_pos)
    screen.blit(ker_text, ker_pos)
    screen.blit(thx_text, thx_pos)
    screen.blit(bugs_text, bugs_pos)
    screen.blit(sorry_text, sorry_pos)

    support_text = settings_lang.get("support", "Support / Report Bugs")
    support_rendered = render_text(support_text, True, (255, 255, 255))
    support_rect = support_rendered.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 122))
    buttons.append((support_rendered, support_rect, "Support", False))

    back_text = settings_lang.get("Back", "Back")
    rendered = render_text(back_text, True, (255, 255, 255))
    rect = rendered.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT - 50))
    buttons.append((rendered, rect, "Back", False))

def audio_settings_menu(screen, lang_code, manifest, progress, bgs, is_mute, is_mute_amb):
    global buttons
    buttons.clear()
    screen.blit(bgs['plain'], (0, 0))
    settings_lang = manage_data.load_language(lang_code, manifest).get('settings', {})

    # 1. Draw Title
    title_str = settings_lang.get("Audio", "Audio")
    title_txt = render_text(title_str, True, (255, 255, 255))
    screen.blit(title_txt, (manage_data.SCREEN_WIDTH // 2 - title_txt.get_width() // 2, 200))
    
    # 2. Sound Buttons (SFX)
    sound_label = settings_lang.get("Sound", "Sound")
    if is_mute:
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
    if is_mute_amb:
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


def create_quit_confirm_buttons(lang_code, manifest):
    global current_lang, buttons
    buttons.clear()

    # Get the quit confirmation text from the current language
    messages = manage_data.load_language(lang_code, manifest).get('messages', {})
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

    pygame.display.flip()  # Update the display to show the quit confirmation screen
