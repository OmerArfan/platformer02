import sys
import platform
# In case someone actually tries using older Windows versions (Very unlikely, but still)
if platform.system() == "Windows":
    if sys.getwindowsversion().major < 10:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, 
            "Roboquix requires at least Windows 10 or above to function!", 
            "Unsupported Operating System!", 
            0x10
        )
        sys.exit()

import pygame
from cleobo.data import manage_data
import cleobo.startup as startup
import cleobo.data.acc_sys as acc_sys
import cleobo.ui.menu_ui as menu_ui
import cleobo.ui.state as state
from cleobo.levels import launcher
import threading
# Initialize pygame
pygame.init()
# Initializing screen resolution
screen = pygame.display.set_mode((1600, 900), pygame.FULLSCREEN)
manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT = screen.get_size()

# Load and set window icon
icon = pygame.image.load(manage_data.resource_path("assets/imgs/icons/icon.png")).convert_alpha()
pygame.display.set_icon(icon)
pygame.mouse.set_visible(False)  # Hide the system cursor   

pygame.display.set_caption("Roboquix")
MIN_WIDTH, MIN_HEIGHT = 1366, 768

running = False
loader = startup.load_game_generator(manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT)
loading = True

while loading:
    screen.fill((0,119,171))
    screen.blit(manage_data.power, (manage_data.SCREEN_WIDTH // 2 - manage_data.power.get_width() // 2, 150))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
    try:
        stage, ps = next(loader)
        menu_ui.draw_loading_bar(screen, stage, ps)
    except StopIteration:
        new_update_available = manage_data.check_for_new_update(False)
        if manage_data.is_mute_amb:
            pygame.mixer.music.stop()
        else:
            pygame.mixer.music.set_volume(1)
            pygame.mixer.music.play(-1)
        loading = False
running = True

transition = state.TransitionManager(screen, manage_data.bgs['trans_left'], manage_data.bgs['trans_right'])
current_lang = manage_data.change_language(manage_data.lang_code, manage_data.manifest, manage_data.progress)

# Start with main menu
state.set_page(screen, 'main_menu', transition)

# Global variables(only needed before main loop)!
button_hovered_last_frame = False
last_hovered_key = None
logo_hover = False
logo_click = False

if not manage_data.is_mute and manage_data.SCREEN_WIDTH > MIN_WIDTH and manage_data.SCREEN_HEIGHT > MIN_HEIGHT:
    manage_data.sounds['click'].play()

while running:
    messages = manage_data.load_language().get('messages', {})
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
        state.set_page(screen, current_pending, transition)

    if manage_data.SCREEN_WIDTH < MIN_WIDTH or manage_data.SCREEN_HEIGHT < MIN_HEIGHT:
        menu_ui.show_resolution_limit(screen)
    else:
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                if not state.is_transitioning:
                    transition.start("quit_confirm")
                    state.transition_time = pygame.time.get_ticks()
                    state.is_transitioning = True
                    state.pending_page = "quit_confirm"

            # Handle login screen events
            elif manage_data.current_page == "login_screen":
                acc_sys.handle_login_events(screen, transition, events, manage_data.manifest, manage_data.is_mute, manage_data.sounds, manage_data.progress)
                break  # Stop processing other events for this frame

            elif manage_data.current_page == "registration_screen":
                acc_sys.handle_registration_events(screen, transition, events, manage_data.manifest, manage_data.is_mute, manage_data.sounds, manage_data.progress, manage_data.ACCOUNTS_FILE)
                break  # Stop processing other events for this frame

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if manage_data.current_page == "Account" and manage_data.current_page not in ["green", "mech", "worlds", "login_screen", "registration_screen"]:
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
                'new_news': new_update_available
            }
            
            # One line to rule them all
            updated_states = menu_ui.draw_main_menu(screen, event, ui_states)
            
            # Sync states back
            logo_hover = updated_states['logo_hover']
            logo_click = updated_states['logo_click']
            last_hovered_key = updated_states['last_hovered']
            new_update_available = updated_states['new_news']

        if manage_data.current_page == 'profile':
            menu_ui.draw_profile(screen)

        if manage_data.current_page == "achievements":
            menu_ui.create_achieve_screen(screen)

        if manage_data.current_page == "character_select":
           menu_ui.draw_character_select(screen, mouse_pos, events, transition, rect, key)

        if manage_data.current_page == "language_select":
            menu_ui.create_language_buttons(screen)
            
        if manage_data.current_page == "quit_confirm":
            screen.blit(manage_data.bgs['plain'], (0, 0))
            quit_text, quit_text_rect = menu_ui.create_quit_confirm_buttons()
            screen.blit(quit_text, quit_text_rect)
            screen.blit(manage_data.robos['ironrobot'], (manage_data.SCREEN_WIDTH // 2 - manage_data.robos['robot'].get_width() // 2, manage_data.SCREEN_HEIGHT // 2 - 200))
            button_hovered_last_frame = menu_ui.draw_buttons(screen, mouse_pos, button_hovered_last_frame)
        
        elif "lvl" in manage_data.current_page:
            parts = manage_data.current_page.split("_")
            world_name = parts[0]
            subsection = int(parts[1])
            level_name = "_".join(parts[2:]) if len(parts) > 2 else parts[1]
            launcher.level_launcher(level_name, screen, transition, world_name, subsection)
        
        elif any(manage_data.current_page.startswith(world) for world in ["green", "mech", "ship", "desert"]):
            button_hovered_last_frame = menu_ui.draw_level_select(screen, mouse_pos, manage_data.current_page, current_lang, messages, button_hovered_last_frame)

        elif manage_data.current_page == "settings":
            menu_ui.settings_menu(screen)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "About":   
            menu_ui.about_menu(screen)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, mouse_pos, button_hovered_last_frame)            
        
        elif manage_data.current_page == "Audio":
            menu_ui.audio_settings_menu(screen)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "worlds":
            menu_ui.worlds(screen)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "Account":
            screen.blit(manage_data.bgs['plain'], (0, 0))
            account_lang = manage_data.load_language().get('settings', {})  # Fetch localized messages
            
            title_text = account_lang.get("select", "SELECT PROFILE")
            title = menu_ui.render_text(title_text, True, (255, 255, 255))
            screen.blit(title, (manage_data.SCREEN_WIDTH // 2 - title.get_width() // 2, 80))
            
            acc_sys.create_account_selector(screen)
            button_hovered_last_frame = menu_ui.draw_buttons(screen, mouse_pos, button_hovered_last_frame)

        elif manage_data.current_page == "login_screen":
            acc_sys.draw_login_screen(screen)

        elif manage_data.current_page == "registration_screen":
            acc_sys.draw_registration_screen(screen)
    
        else:
            button_hovered_last_frame = menu_ui.draw_buttons(screen, mouse_pos, button_hovered_last_frame)

        screen.blit(manage_data.ui['cursor'], mouse_pos)

        if transition.active:
            transition.update(screen, transition)

        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        
        pygame.display.flip()

pygame.quit()