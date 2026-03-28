import pygame
import os
import sys
import time
import webbrowser

import menu_ui
import manage_data
import startup
import level_logic
import acc_sys
import state
import levels

# GAME VERSION
manage_data.version = "1.3.7.3"

# Initialize audio
pygame.mixer.init()

# Initialize pygame
pygame.init()

# Initializing screen resolution
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT = screen.get_size()

if sys.platform.startswith('linux'):
    os.environ['SDL_VIDEODRIVER'] = 'x11'

pygame.display.set_caption("Roboquix")
MIN_WIDTH, MIN_HEIGHT = 1250, 700

# First of all, LOAD THE DAMN BGGG
bg = pygame.image.load(manage_data.resource_path("bgs/PlainBackground.png")).convert()
bg = pygame.transform.scale(bg, (manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT))

# Load and set window icon
icon = pygame.image.load(manage_data.resource_path("oimgs/icons/icon.png")).convert_alpha()
pygame.display.set_icon(icon)

# Variables for handling display notifications
notif = False
er = False

pygame.mouse.set_visible(False)  # Hide the system cursor

notification_time = None

save_count = 0

is_syncing = False

# To handle sync status message output.        
sync_status = ""
sync_finish_time = None

running = False

loader = startup.load_game_generator(manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT)
loading = True

while loading:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

    try:
        stage, ps = next(loader)
        menu_ui.draw_loading_bar(screen, bg, stage, ps)
        
    except StopIteration:
        if manage_data.is_mute_amb:
            pygame.mixer.music.stop()
        else:
            pygame.mixer.music.set_volume(0.1)
            pygame.mixer.music.play(-1)
            
        loading = False

running = True

transition = state.TransitionManager(screen, manage_data.bgs['trans_left'], manage_data.bgs['trans_right'])
current_lang = manage_data.change_language(manage_data.lang_code, manage_data.manifest, manage_data.progress)
menu_ui.buttons = []

#def load_level(level_id):
#    global manage_data.current_page, buttons
   # Show "Loading..." text
#    screen.fill((30, 30, 30))
#    messages = manage_data.change_language(manage_data.lang_code, manage_data.manifest, manage_data.progress).get('messages', {})  # Reload messages with the current language
#    loading_text = messages.get("loading", "Loading...")
#    rendered_loading = menu_ui.render_text(loading_text, True, (255, 255, 255))
#    loading_rect = rendered_loading.get_rect(center=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT // 2))  # Center dynamically
#    screen.blit(rendered_loading, loading_rect)
#    pygame.display.flip()
 #   # Short delay to let the user see the loading screen
  #  pygame.time.delay(800)  # 800 milliseconds
    # Now switch the page
   # buttons.clear()

#Initialize default character
manage_data.selected_character = manage_data.progress["pref"].get("character", manage_data.default_progress["pref"]["character"])
# Get rects and position them
manage_data.robo_rects = {
    'robot': manage_data.robos['robot'].get_rect(topleft=(manage_data.SCREEN_WIDTH // 2 - 300, manage_data.SCREEN_HEIGHT // 2 - 50)),
    'evilrobot': manage_data.robos['evilrobot'].get_rect(topleft=(manage_data.SCREEN_WIDTH // 2 - 150, manage_data.SCREEN_HEIGHT // 2 - 50)),
    'greenrobot': manage_data.robos['greenrobot'].get_rect(topleft=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT // 2 - 50)),
    'ironrobot': manage_data.robos['ironrobot'].get_rect(topleft=(manage_data.SCREEN_WIDTH // 2 + 150, manage_data.SCREEN_HEIGHT // 2 - 50))
}

#def go_back():
#    global last_page_change_time
#    last_page_change_time = time.time()  # Track the time when going back
#    state.set_page('main_menu')

# For saw images
saw_cache = {}
ctime = None # global only for resetting

def resetting():
    global ctime
    if ctime is None:
        ctime = pygame.time.get_ticks()

# Start with main menu
state.set_page(screen, 'main_menu', manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.Achievements, manage_data.bgs, manage_data.disks, manage_data.version, manage_data.is_mute, manage_data.is_mute_amb, transition)
manage_data.update_locked_levels(manage_data.progress, manage_data.manifest) # Update locked levels every frame!

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

# First define current XP outside the loop
level, xp_needed, xp_total = manage_data.xp(manage_data.progress, manage_data.Achievements)
if level < 20:
    color = (255, 255, 255)
else:
    color = (225, 212, 31)

XP_text = manage_data.fonts['mega'].render(f"{level}", True, color)
if level < 20:
    XP_text2 = menu_ui.render_text(f"{xp_needed}/{xp_total}", True, color)
else:
    max_txt = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('messages', {}).get("max_level", "MAX LEVEL!")
    XP_text2 = menu_ui.render_text(max_txt, True, color)

if not manage_data.is_mute and manage_data.SCREEN_WIDTH > MIN_WIDTH and manage_data.SCREEN_HEIGHT > MIN_HEIGHT:
    manage_data.sounds['click'].play()

while running:
    print(manage_data.current_page)  # Debugging line to track current page
    # This is in the main loop, unlike the other texts, because it needs to update if the player changes!
    ID_text = menu_ui.render_text(f"ID: {manage_data.progress['player']['ID']}", True, (255, 255, 255))
    ID_pos = (manage_data.SCREEN_WIDTH - (ID_text.get_width() + 10), 0)

    messages = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('messages', {})
    # Clear screen!
    screen.blit(manage_data.bgs['plain'], (0, 0))
    mouse_pos = pygame.mouse.get_pos()

    if state.transition_time is not None and pygame.time.get_ticks() - state.transition_time > 1000:
        state.transition_time = None
        state.is_transitioning = False

    # Handle transition timer and page change
    if state.is_transitioning and state.transition_time is not None and state.pending_page is not None:
        if transition.phase == 1:
            # Then recheck if XP has been added or not.
            level, xp_needed, xp_total = manage_data.xp(manage_data.progress, manage_data.Achievements)
            if level < 20:
                color = (255, 255, 255)
            else:
                color = (225, 212, 31)

            XP_text = manage_data.fonts['mega'].render(f"{level}", True, color)
            if level < 20:
                XP_text2 = menu_ui.render_text(f"{xp_needed}/{xp_total}", True, color)
            else:
                max_txt = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('messages', {}).get("max_level", "MAX LEVEL!")
                XP_text2 = menu_ui.render_text(max_txt, True, color)
                # Then let transition loop play as normal
            state.is_transitioning = False
            current_pending = state.pending_page
            state.transition_time = None
            state.pending_page = None
            state.set_page(screen, current_pending, manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.Achievements, manage_data.bgs, manage_data.disks, manage_data.version, manage_data.is_mute, manage_data.is_mute_amb, transition)

    XP_pos2 = (manage_data.SCREEN_WIDTH - (XP_text2.get_width() + 10), 50)
    XP_pos = (manage_data.SCREEN_WIDTH - (XP_text.get_width() + XP_text2.get_width() + 30), 30)
    xp_center_x = XP_pos[0] + (XP_text.get_width() / 2)
    badge_x = xp_center_x - (manage_data.assets['badge'].get_width() / 2)
    badge_pos = (badge_x, 32)

    if manage_data.SCREEN_WIDTH < MIN_WIDTH or manage_data.SCREEN_HEIGHT < MIN_HEIGHT:
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
            screen.blit(manage_data.bgs['evilrobot'], (manage_data.SCREEN_WIDTH // 2 - manage_data.bgs['evilrobot'].get_width() // 2, manage_data.SCREEN_HEIGHT // 2 - 200))

            # Render the text
            messages = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('messages', {})
            deny_text = messages.get("deny_message", "Access denied!")
            rendered_deny_text = menu_ui.render_text(deny_text, True, (255, 100, 100))
            error_text = messages.get("error_message","Your screen resolution is too small! Increase the screen")
            rendered_error_text = menu_ui.render_text(error_text, True, (255, 255, 255))
            error_text2 = messages.get("error_message2", "resolution in your system settings.")
            rendered_error_text2 = menu_ui.render_text(error_text2, True, (255, 255, 255))
            countdown_text = messages.get("countdown_message", "Closing in {countdown} second(s)...").format(countdown=countdown)
            rendered_countdown_text = menu_ui.render_text(countdown_text, True, (255, 100, 100))

            # Center the text
            screen.blit(rendered_deny_text, (manage_data.SCREEN_WIDTH // 2 - rendered_deny_text.get_width() // 2, manage_data.SCREEN_HEIGHT // 2 - 280))            
            screen.blit(rendered_error_text, (manage_data.SCREEN_WIDTH // 2 - rendered_error_text.get_width() // 2, manage_data.SCREEN_HEIGHT // 2 - 40))
            screen.blit(rendered_error_text2, (manage_data.SCREEN_WIDTH // 2 - rendered_error_text2.get_width() // 2, manage_data.SCREEN_HEIGHT // 2))
            screen.blit(rendered_countdown_text, (manage_data.SCREEN_WIDTH // 2 - rendered_countdown_text.get_width() // 2, manage_data.SCREEN_HEIGHT // 2 + 50))

            pygame.display.flip()
            clock.tick(30)

        pygame.quit()
        sys.exit()

    else:
        # Collect events ONCE per frame
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                state.set_page(screen, "quit_confirm", manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.Achievements, manage_data.bgs, manage_data.disks, manage_data.version, manage_data.is_mute, manage_data.is_mute_amb, transition)

            # Handle login screen events
            elif manage_data.current_page == "login_screen" and event.type == pygame.KEYDOWN:
                acc_sys.handle_login_events(events, manage_data.manifest, manage_data.lang_code, manage_data.is_mute, manage_data.sounds, manage_data.progress, state.set_page)
                break  # Stop processing other events for this frame

            # Handle registration screen events
            elif manage_data.current_page == "registration_screen" and event.type == pygame.KEYDOWN:
                acc_sys.handle_registration_events(events, manage_data.manifest, manage_data.lang_code, manage_data.is_mute, manage_data.sounds, manage_data.progress, state.set_page, manage_data.ACCOUNTS_FILE)
                break  # Stop processing other events for this frame

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Only process clicks if enough time has passed since last page change
                if manage_data.current_page == "Account":
                    for _, rect, key, is_locked in menu_ui.buttons:
                        if rect.collidepoint(event.pos):
                            if key is not None and not manage_data.is_mute:
                                manage_data.sounds['click'].play()
                            # Only execute action when transition is fully covering screen
                            state.handle_action(key, transition, manage_data.current_page)
                            last_page_change_time = time.time()
                elif manage_data.current_page not in ["levels", "mech_levels", "worlds", "login_screen", "registration_screen"]:
                    for _, rect, key, is_locked in menu_ui.buttons:
                        if rect.collidepoint(event.pos):
                            if key is not None and not manage_data.is_mute:
                                manage_data.sounds['click'].play()
                            state.handle_action(key, transition, manage_data.current_page)
                            last_page_change_time = time.time()
                elif manage_data.current_page in ["levels", "mech_levels", "worlds"]:
                    for rendered, rect, key, is_locked in menu_ui.buttons:
                        if rect.collidepoint(event.pos):
                            if key is not None and not manage_data.is_mute:
                                manage_data.sounds['click'].play()
                            state.handle_action(key, transition, manage_data.current_page)  # Only load level on click!
                    
        if manage_data.current_page == "main_menu":
            screen.blit(manage_data.ui['logo'], ((manage_data.SCREEN_WIDTH // 2 - manage_data.ui['logo'].get_width() // 2), -20))
            screen.blit(manage_data.bgs['lilrobopeek'], ((manage_data.SCREEN_WIDTH - manage_data.bgs['lilrobopeek'].get_width()), (manage_data.SCREEN_HEIGHT - manage_data.bgs['lilrobopeek'].get_height())))
            screen.blit(ID_text, ID_pos)
            if level < 20:
                screen.blit(manage_data.assets['badge'], badge_pos)
            else:
                screen.blit(manage_data.assets['max_badge'], badge_pos)
            screen.blit(XP_text, XP_pos)
            screen.blit(XP_text2, XP_pos2)
        # Render the main menu buttons
            hovered_key = None
            for rendered, rect, key, is_locked in menu_ui.buttons:
                mouse_pos = pygame.mouse.get_pos()
                if manage_data.ui['studio_logo_rect'].collidepoint(mouse_pos):
                    screen.blit(manage_data.ui['studio_glow'], manage_data.ui['studio_glow_rect'].topleft)
                    if not logo_hover:
                        if not manage_data.is_mute:
                            manage_data.sounds['hover'].play()
                        logo_hover = True
                    if event.type == pygame.MOUSEBUTTONDOWN and not logo_click:    
                        if not manage_data.is_mute:
                            manage_data.sounds['click'].play()    
                        webbrowser.open("https://omerarfan.github.io/lilrobowebsite/") 
                        logo_click = True
                else:
                    screen.blit(manage_data.ui['studio_logo'], manage_data.ui['studio_logo_rect'].topleft)
                    logo_hover = False
                    logo_click = False

                if rect.collidepoint(mouse_pos):
                    hovered_key = key
                    if hovered_key != last_hovered_key and not manage_data.is_mute:
                        manage_data.sounds['hover'].play()

                screen.blit(rendered, rect)
            last_hovered_key = hovered_key

        if manage_data.current_page == "achievements":
            menu_ui.create_achieve_screen(screen, manage_data.lang_code, manage_data.manifest, manage_data.progress)

        if manage_data.current_page == "character_select":
         screen.blit(manage_data.bgs['plain'], (0, 0))

         # Initialize locked sound effect and mouse position
         locked_sound_played = False
         mouse_pos = pygame.mouse.get_pos()

         messages = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('messages', {})  # Fetch localized messages
         header_txt = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('main_menu', {})
         char_sel = header_txt.get("character_select", "Character Select")
         char_text = menu_ui.render_text(char_sel, True, (255, 255, 255))
         screen.blit(char_text, (manage_data.SCREEN_WIDTH // 2 - 100, 50))

         # Check if characters are locked
         robo_unlock = True
         evilrobo_unlock = manage_data.progress["char"].get("evilrobo", False)
         greenrobo_unlock = manage_data.progress["char"].get("greenrobo", False)
         ironrobo_unlock = manage_data.progress["char"].get("ironrobo", False)
         # Get currently selected character
         selected_character = manage_data.progress["pref"].get("character", manage_data.default_progress["pref"]["character"])
         # Draw images
         screen.blit(manage_data.robos['robot'], manage_data.robo_rects['robot'])     
         screen.blit(manage_data.robos['evilrobot'] if evilrobo_unlock else manage_data.robos['locked'], manage_data.robo_rects['evilrobot'])
         screen.blit(manage_data.robos['greenrobot'] if greenrobo_unlock else manage_data.robos['locked'], manage_data.robo_rects['greenrobot'])
         screen.blit(manage_data.robos['ironrobot'] if ironrobo_unlock else manage_data.robos['locked'], manage_data.robo_rects['ironrobot'])
         # Draw a highlight border around the selected character
         highlight_colors = {
          "robot": (63, 72, 204),
          "evilrobot": (128, 0, 128),
          "greenrobot": (25, 195, 21),
          "ironrobot": (64, 64, 64),
         }
        
         if selected_character in manage_data.robo_rects:
          pygame.draw.rect(screen, highlight_colors[selected_character], manage_data.robo_rects[selected_character].inflate(5, 5), 5)

            # --- Use MOUSEBUTTONDOWN instead of continuous mouse.get_pressed ---
         for event in events:
           if event.type == pygame.QUIT:
            state.set_page(screen, "quit_confirm", manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.Achievements, manage_data.bgs, manage_data.disks, manage_data.version, manage_data.is_mute, manage_data.is_mute_amb, transition)

           elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if manage_data.robo_rects['robot'].collidepoint(mouse_pos):
                manage_data.try_select_robo(robo_unlock, "robot", manage_data.robo_rects['robot'], "placeholder", "Imagine if this actually popped up in game BRO-", transition)
            elif manage_data.robo_rects['evilrobot'].collidepoint(mouse_pos):
                manage_data.try_select_robo(evilrobo_unlock, "evilrobot", manage_data.robo_rects['evilrobot'], "evillocked_message", "Encounter this robot in an alternative route to unlock him!", transition)
            elif manage_data.robo_rects['greenrobot'].collidepoint(mouse_pos):
                manage_data.try_select_robo(greenrobo_unlock, "greenrobot", manage_data.robo_rects['greenrobot'], "greenlocked_message", "Get GOLD rank in all Green World Levels to unlock this robot!", transition)
            elif manage_data.robo_rects['ironrobot'].collidepoint(mouse_pos):
                manage_data.try_select_robo(ironrobo_unlock, "ironrobot", manage_data.robo_rects['ironrobot'], "ironlocked_message", "Unlock the Zenith Of Six achievement to get this character!", transition)
            elif manage_data.robo_rects['locked'].collidepoint(mouse_pos):
                state.handle_action(key, transition, manage_data.current_page)

         keys = pygame.key.get_pressed()
         if keys[pygame.K_ESCAPE]:
            state.set_page(screen, "main_menu", manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.Achievements, manage_data.bgs, manage_data.disks, manage_data.version, manage_data.is_mute, manage_data.is_mute_amb, transition)

        if manage_data.current_page == "language_select":
            menu_ui.create_language_buttons(screen, manage_data.lang_code, manage_data.manifest, manage_data.progress)
            
        if manage_data.current_page == "quit_confirm":
            screen.blit(manage_data.bgs['plain'], (0, 0))
            # Render the quit confirmation text
            quit_text, quit_text_rect = menu_ui.create_quit_confirm_buttons(manage_data.lang_code, manage_data.manifest)
            screen.blit(quit_text, quit_text_rect)
            #screen.blit(manage_data.bgs['greenrobot_moving'], (manage_data.SCREEN_WIDTH // 2 - manage_data.bgs['robot'].get_width() // 2, manage_data.SCREEN_HEIGHT // 2 - 200))
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "lvl1_screen":
            levels.create_lvl1_screen()

        elif manage_data.current_page == "lvl2_screen":
            levels.create_lvl2_screen()
    
        elif manage_data.current_page == "lvl3_screen":
            levels.create_lvl3_screen()

        elif manage_data.current_page == "lvl4_screen":
            levels.create_lvl4_screen()

        elif manage_data.current_page == "lvl5_screen":
            levels.create_lvl5_screen()

        elif manage_data.current_page == "lvl6_screen":
            levels.create_lvl6_screen()

        elif manage_data.current_page == "lvl7_screen":
            levels.create_lvl7_screen()

        elif manage_data.current_page == "lvl8_screen":
            levels.create_lvl8_screen()

        elif manage_data.current_page == "lvl9_screen":
            levels.create_lvl9_screen()

        elif manage_data.current_page == "lvl10_screen":
            levels.create_lvl10_screen()

        elif manage_data.current_page == "lvl11_screen":
            levels.create_lvl11_screen()

        elif manage_data.current_page == "lvl12_screen":
            levels.create_lvl12_screen()
        
        elif manage_data.current_page == "levels" or manage_data.current_page == "mech_levels":
            if manage_data.current_page == "levels":
                screen.blit(manage_data.bgs['green'], (0, 0))
                disk_img = manage_data.disks['green']
            else:
                screen.blit(manage_data.bgs['mech'], (0, 0))
                disk_img = manage_data.disks['mech']
            # Fetch the localized "Select a Level" text dynamically
            select_text = current_lang.get("level_display", "Select a Level")
            rendered_select_text = menu_ui.render_text(select_text, True, (255, 255, 255))
            select_text_rect = rendered_select_text.get_rect(center=(manage_data.SCREEN_WIDTH // 2, 50))

            # Draw the "Select a Level" text
            screen.blit(rendered_select_text, select_text_rect)

            # Render buttons for levels

            for rendered, rect, key, is_locked in menu_ui.buttons:
                if rect.collidepoint(mouse_pos):
                    if key is not None:
                        # Unlocked level
                        screen.blit(disk_img, rect)
                    else:
                        screen.blit(manage_data.disks['locked'], rect)
                    button_hovered_last_frame = menu_ui.hover_effect(screen, rect, manage_data.sounds['hover'], manage_data.is_mute, button_hovered_last_frame)
            # Show Level stats - check current mouse position every frame
            for text_surface, disk_rect, key, is_locked in menu_ui.buttons:
                if disk_rect.collidepoint(mouse_pos):
                    if key != "next" and key != "back" and not is_locked:
                        hs = manage_data.progress["lvls"]['score'][key]
                        high_text = messages.get("hs_m", "Highscore: {hs}").format(hs=hs)
                        lvl_score_text = menu_ui.render_text(high_text, True, (255, 255, 0))

                        # Adjust position as needed
                        screen.blit(lvl_score_text, (manage_data.SCREEN_WIDTH // 2 - lvl_score_text.get_width() // 2, manage_data.SCREEN_HEIGHT - 50))
                        s = key
                        num = int(s[3:])  # Skip the first 3 characters
                        medal_name = manage_data.progress["lvls"]['medals'][key]
                        if medal_name != "None":
                            screen.blit(manage_data.medals[medal_name], (manage_data.SCREEN_WIDTH // 2 - manage_data.medals[medal_name].get_width() // 2 - 210, manage_data.SCREEN_HEIGHT - 80))
                        stars = level_logic.get_stars(num, manage_data.progress["lvls"]['score'][key])
                        if stars >= 1:
                            screen.blit(manage_data.assets['star_small'], (manage_data.SCREEN_WIDTH // 2 - 25, manage_data.SCREEN_HEIGHT - 80))
                        if stars >= 2:
                            screen.blit(manage_data.assets['star_small'], (manage_data.SCREEN_WIDTH // 2 , manage_data.SCREEN_HEIGHT - 80))
                        if stars == 3:
                            screen.blit(manage_data.assets['star_small'], (manage_data.SCREEN_WIDTH // 2 + 25, manage_data.SCREEN_HEIGHT - 80))
            
            for text_surface, disk_rect, key, is_locked in menu_ui.buttons: 
                if key is not None:
                    screen.blit(disk_img, disk_rect)
                else:
                    screen.blit(manage_data.disks['locked'], disk_rect)
                text_rect = text_surface.get_rect(center=(disk_rect.x + 50, disk_rect.y + 50))
                screen.blit(text_surface, text_rect)

        elif manage_data.current_page == "settings":
            menu_ui.settings_menu(screen, manage_data.lang_code, manage_data.manifest, manage_data.bgs)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "About":   
            menu_ui.about_menu(screen, manage_data.lang_code, manage_data.manifest, manage_data.bgs, manage_data.version)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)
            
        elif manage_data.current_page == "Audio":
            menu_ui.audio_settings_menu(screen, manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.bgs, manage_data.is_mute, manage_data.is_mute_amb)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "Account":
            screen.blit(manage_data.bgs['plain'], (0, 0))
            account_lang = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('settings', {})  # Fetch localized messages
            # 1. Draw the Title Manually Here

            title_text = account_lang.get("select", "SELECT PROFILE")
            title = menu_ui.render_text(title_text, True, (255, 255, 255))
            screen.blit(title, (manage_data.SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

            # 2. Draw the Buttons (Using the standard button loop)
            acc_sys.create_account_selector(manage_data.ACCOUNTS_FILE, manage_data.lang_code, manage_data.manifest, transition, screen, manage_data.bgs, manage_data.is_mute, manage_data.sounds, menu_ui.draw_notifs, menu_ui.draw_syncing_status, menu_ui.buttons)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "login_screen":
            acc_sys.draw_login_screen(screen, manage_data.lang_code, manage_data.manifest, manage_data.bgs)

        elif manage_data.current_page == "registration_screen":
            acc_sys.draw_registration_screen(screen, manage_data.lang_code, manage_data.manifest, manage_data.bgs)
    
        else:
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)
        
        menu_ui.draw_notifs(notif, er, notification_time, None, None, screen)
        menu_ui.draw_syncing_status(sync_status, sync_finish_time, is_syncing, screen)

        mouse_pos = pygame.mouse.get_pos()
        screen.blit(manage_data.ui['cursor'], mouse_pos)

        if transition.active:
            transition.update(manage_data.lang_code, screen, manage_data.version, transition, manage_data.manifest, manage_data.progress)
        
        pygame.display.flip()

pygame.quit()