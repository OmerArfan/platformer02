import pygame
import os
import sys

import menu_ui
import manage_data
import startup
import acc_sys
import state
import levels

# GAME VERSION
manage_data.version = "1.3.9.3"
manage_data.kernel = "0.1.5"

# Initialize pygame
pygame.init()

# Initializing screen resolution
screen = pygame.display.set_mode((1600, 900), pygame.FULLSCREEN)
manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT = screen.get_size()

if sys.platform.startswith('linux'):
    os.environ['SDL_VIDEODRIVER'] = 'x11'

pygame.display.set_caption("Roboquix")
MIN_WIDTH, MIN_HEIGHT = 1150, 800

# First of all, LOAD THE DAMN BGGG
bg = pygame.image.load(manage_data.resource_path("bgs/PlainBackground.png")).convert()
bg = pygame.transform.scale(bg, (manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT))

# Load and set window icon
icon = pygame.image.load(manage_data.resource_path("oimgs/icons/icon.png")).convert_alpha()
pygame.display.set_icon(icon)

pygame.mouse.set_visible(False)  # Hide the system cursor

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
        new_news_available = manage_data.check_for_new_gamenews(False)
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
manage_data.saw_cache = {}

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
   # buttons.clear()

# To handle notifications
menu_ui.notification_time = None
menu_ui.notif = False
menu_ui.er = False

# Related to online saving
menu_ui.save_count = 0
menu_ui.is_syncing = False      
menu_ui.sync_status = ""
menu_ui.sync_finish_time = None

#Initialize default character
manage_data.selected_character = manage_data.progress["pref"].get("character", manage_data.default_progress["pref"]["character"])
# Get rects and position them
manage_data.robo_rects = {
    'robot': manage_data.robos['robot'].get_rect(topleft=(manage_data.SCREEN_WIDTH // 2 - 300, manage_data.SCREEN_HEIGHT // 2 - 50)),
    'evilrobot': manage_data.robos['evilrobot'].get_rect(topleft=(manage_data.SCREEN_WIDTH // 2 - 150, manage_data.SCREEN_HEIGHT // 2 - 50)),
    'greenrobot': manage_data.robos['greenrobot'].get_rect(topleft=(manage_data.SCREEN_WIDTH // 2, manage_data.SCREEN_HEIGHT // 2 - 50)),
    'ironrobot': manage_data.robos['ironrobot'].get_rect(topleft=(manage_data.SCREEN_WIDTH // 2 + 150, manage_data.SCREEN_HEIGHT // 2 - 50))
}

# Start with main menu
state.set_page(screen, 'main_menu', manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.Achievements, manage_data.bgs, manage_data.disks, manage_data.version, manage_data.is_mute, manage_data.is_mute_amb, transition)
manage_data.update_locked_levels(manage_data.progress, manage_data.manifest) # Update locked levels every frame!

# Global variables(only needed before main loop)!
button_hovered_last_frame = False
last_hovered_key = None
logo_hover = False
logo_click = False

if not manage_data.is_mute and manage_data.SCREEN_WIDTH > MIN_WIDTH and manage_data.SCREEN_HEIGHT > MIN_HEIGHT:
    manage_data.sounds['click'].play()

while running:
    messages = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('messages', {})
    # Clear screen!
    screen.blit(manage_data.bgs['plain'], (0, 0))
    mouse_pos = pygame.mouse.get_pos()

    if state.transition_time is not None and pygame.time.get_ticks() - state.transition_time > 1000:
        state.transition_time = None
        state.is_transitioning = False

    if transition.phase == 1:
            state.is_transitioning = False
            current_pending = state.pending_page
            state.transition_time = None
            state.pending_page = None
            state.set_page(screen, current_pending, manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.Achievements, manage_data.bgs, manage_data.disks, manage_data.version, manage_data.is_mute, manage_data.is_mute_amb, transition)

    if manage_data.SCREEN_WIDTH < MIN_WIDTH or manage_data.SCREEN_HEIGHT < MIN_HEIGHT:
        menu_ui.show_resolution_limit(screen)
    else:
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                state.set_page(screen, "quit_confirm", manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.Achievements, manage_data.bgs, manage_data.disks, manage_data.version, manage_data.is_mute, manage_data.is_mute_amb, transition)

            # Handle login screen events
            elif manage_data.current_page == "login_screen":
                acc_sys.handle_login_events(screen, transition, events, manage_data.manifest, manage_data.lang_code, manage_data.is_mute, manage_data.sounds, manage_data.progress)
                break  # Stop processing other events for this frame

            elif manage_data.current_page == "registration_screen":
                acc_sys.handle_registration_events(screen, transition, events, manage_data.manifest, manage_data.lang_code, manage_data.is_mute, manage_data.sounds, manage_data.progress, manage_data.ACCOUNTS_FILE)
                break  # Stop processing other events for this frame

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if manage_data.current_page == "Account" and manage_data.current_page not in ["levels", "mech_levels", "worlds", "login_screen", "registration_screen"]:
                    for _, rect, key, is_locked in menu_ui.buttons:
                        if rect.collidepoint(event.pos):
                            if key is not None and not manage_data.is_mute:
                                manage_data.sounds['click'].play()
                            state.handle_action(key, transition, manage_data.current_page)
                else:
                    for rendered, rect, key, is_locked in menu_ui.buttons:
                        if rect.collidepoint(event.pos):
                            if key is not None and not manage_data.is_mute:
                                manage_data.sounds['click'].play()
                            state.handle_action(key, transition, manage_data.current_page)
                    
        if manage_data.current_page == "main_menu":
            ui_states = {
                'logo_hover': logo_hover, 
                'logo_click': logo_click, 
                'last_hovered': last_hovered_key, 
                'new_news': new_news_available
            }
            
            # One line to rule them all
            updated_states = menu_ui.draw_main_menu(screen, event, ui_states)
            
            # Sync states back
            logo_hover = updated_states['logo_hover']
            logo_click = updated_states['logo_click']
            last_hovered_key = updated_states['last_hovered']
            new_news_available = updated_states['new_news']

        if manage_data.current_page == 'profile':
            menu_ui.draw_profile(screen)

        if manage_data.current_page == "achievements":
            menu_ui.create_achieve_screen(screen, manage_data.lang_code, manage_data.manifest, manage_data.progress)

        if manage_data.current_page == "character_select":
           menu_ui.draw_character_select(screen, mouse_pos, events, transition, rect, key)

        if manage_data.current_page == "language_select":
            menu_ui.create_language_buttons(screen, manage_data.lang_code, manage_data.manifest, manage_data.progress)
            
        if manage_data.current_page == "quit_confirm":
            screen.blit(manage_data.bgs['plain'], (0, 0))
            quit_text, quit_text_rect = menu_ui.create_quit_confirm_buttons(manage_data.lang_code, manage_data.manifest)
            screen.blit(quit_text, quit_text_rect)
            screen.blit(manage_data.robos['ironrobot'], (manage_data.SCREEN_WIDTH // 2 - manage_data.robos['robot'].get_width() // 2, manage_data.SCREEN_HEIGHT // 2 - 200))
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)

        elif "lvl" in manage_data.current_page:
            # Dynamically find and call the function in the levels module
            lvl_func = getattr(levels, f"create_{manage_data.current_page}")
            lvl_func(screen, transition)
        
        elif manage_data.current_page == "levels" or manage_data.current_page == "mech_levels":
            button_hovered_last_frame = menu_ui.draw_level_select(screen, mouse_pos, manage_data.current_page, current_lang, messages, button_hovered_last_frame)

        elif manage_data.current_page == "settings":
            menu_ui.settings_menu(screen, manage_data.lang_code, manage_data.manifest, manage_data.bgs)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "About":   
            menu_ui.about_menu(screen, manage_data.lang_code, manage_data.manifest, manage_data.bgs, manage_data.version)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)
            
        elif manage_data.current_page == "Audio":
            menu_ui.audio_settings_menu(screen, manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.bgs, manage_data.is_mute, manage_data.is_mute_amb)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "worlds":
            menu_ui.worlds(screen, manage_data.lang_code, manage_data.manifest, manage_data.progress, manage_data.bgs, manage_data.disks)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "Account":
            screen.blit(manage_data.bgs['plain'], (0, 0))
            account_lang = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('settings', {})  # Fetch localized messages
            
            title_text = account_lang.get("select", "SELECT PROFILE")
            title = menu_ui.render_text(title_text, True, (255, 255, 255))
            screen.blit(title, (manage_data.SCREEN_WIDTH // 2 - title.get_width() // 2, 80))
            
            acc_sys.create_account_selector()
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "login_screen":
            acc_sys.draw_login_screen(screen)

        elif manage_data.current_page == "registration_screen":
            acc_sys.draw_registration_screen(screen)
    
        else:
            button_hovered_last_frame = menu_ui.draw_buttons(screen, menu_ui.buttons, manage_data.sounds['hover'], manage_data.is_mute, mouse_pos, button_hovered_last_frame)
        
        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)

        mouse_pos = pygame.mouse.get_pos()
        screen.blit(manage_data.ui['cursor'], mouse_pos)

        if transition.active:
            transition.update(manage_data.lang_code, screen, manage_data.version, transition, manage_data.manifest, manage_data.progress)
        
        pygame.display.flip()

pygame.quit()