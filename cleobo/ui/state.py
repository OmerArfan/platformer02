import sys
import pygame
from cleobo.data import manage_data
import cleobo.ui.menu_ui as menu_ui
import os
import json
import webbrowser
import cleobo.data.acc_sys as acc_sys
import time
from cleobo.levels import launcher
from cleobo.data.achievements import check_achievements

class TransitionManager:
    def __init__(self, screen, left_image, right_image, speed=65):
        self.screen = screen
        self.left_image = left_image
        self.right_image = right_image
        self.speed = speed
        self.active = False
        self.phase = 0  # 0: slide-in, 1: hold, 2: slide-out
        self.left_x = -left_image.get_width()  # Start off-screen left
        self.right_x = screen.get_width()  # Start off-screen right
        self.target_page = None
        self.hold_time = 0
        self.hold_duration = 250  # milliseconds

    def start(self, target_page):
        self.active = True
        self.phase = 0
        self.left_x = -self.left_image.get_width()
        self.right_x = self.screen.get_width()
        self.target_page = target_page
        self.hold_time = 0

    def update(self, screen, transition):
        global pending_lang_code, selected_id
        
        if not self.active:
            return

        if self.phase == 0:  # Slide-in phase
            # Move left image from left toward center
            self.left_x += self.speed
            # Move right image from right toward center
            self.right_x -= self.speed
            
            # Check if they've met in the middle
            mid_point = manage_data.SCREEN_WIDTH // 2
            if self.left_x + self.left_image.get_width() >= mid_point and self.right_x <= mid_point:
                self.left_x = mid_point - self.left_image.get_width()
                self.right_x = mid_point
                self.phase = 1
                self.hold_time = pygame.time.get_ticks()

        elif self.phase == 1:
            manage_data.saw_cache.clear()
            manage_data.text_cache.clear()
            manage_data.current_page = self.target_page  # Hold phase
            if pygame.time.get_ticks() - self.hold_time >= self.hold_duration:
                # Change language if pending
                if pending_lang_code:
                    manage_data.change_language(pending_lang_code, manage_data.manifest, manage_data.progress)
                    manage_data.lang_code = pending_lang_code
                    pending_lang_code = None
                # Update manifest to set 'last_used' so load_progress knows which one to grab
                if selected_id:
                    if os.path.exists(manage_data.ACCOUNTS_FILE):
                        with open(manage_data.ACCOUNTS_FILE, "r") as f:
                            manifest = json.load(f)
                        manifest["last_used"] = selected_id
                        with open(manage_data.ACCOUNTS_FILE, "w") as f:
                            json.dump(manifest, f, indent=4)
                    # Load the data and move to main menu
                    manage_data.progress = manage_data.load_progress()
                    selected_id = None
                set_page(screen, manage_data.current_page, transition)
                self.phase = 2

        elif self.phase == 2:  # Slide-out phase
            check_achievements()
            self.left_x -= self.speed
            self.right_x += self.speed
            
            if self.left_x <= -self.left_image.get_width() and self.right_x >= self.screen.get_width():
                self.active = False
                self.phase = 0

        # Draw both images
        self.screen.blit(self.left_image, (self.left_x, 0))
        self.screen.blit(self.right_image, (self.right_x, 0))

transition_time = None
is_transitioning = False
pending_lang_code = None
selected_id = None

locked_char_sound_time = None
locked_char_sound_played = False
wait_time = None

def handle_action(key, transition, current_page):
    global is_transitioning, transition_time, locked_char_sound_played, locked_char_sound_time, pending_lang_code, selected_id, pending_page
    if current_page == 'main_menu':
        if key == "start":
            if not is_transitioning:
                transition.start("worlds")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "worlds"
        elif key == "achievements":
            if not is_transitioning:
                transition.start("achievements")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "achievements"
        elif key == "character_select":
            if not is_transitioning:
                transition.start("character_select")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "character_select"
        elif key == "settings":
            if not is_transitioning:
                transition.start("settings")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "settings"
        elif key == "profile":
            if not is_transitioning:
                transition.start("profile")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "profile"
        elif key == "quit":
            if not is_transitioning:
                transition.start("quit_confirm")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "quit_confirm"
    elif current_page == "achievements":
        if key == "back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
    elif current_page == "settings":
        if key == "Back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
        if key == "About": # Note: Ensure capitalization matches your button_texts
            if not is_transitioning:
                transition.start("About")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "About"
        if key == "Audio": # Note: Ensure capitalization matches your button_texts
            if not is_transitioning:
                transition.start("Audio")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "Audio"
        if key == "Account": # Note: Ensure capitalization matches your button_texts
            if not is_transitioning:
                transition.start("Account")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "Account"
        if key == "Language":
            if not is_transitioning:
                transition.start("language_select")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "language_select"
    elif current_page == "About":
        if key == "Back":
            if not is_transitioning:
                transition.start("settings")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "settings"
        if key == "Support":
            webbrowser.open("https://github.com/OmerArfan/platformer02/blob/main/gameinfo/Support.md")
        if key == "License":
            webbrowser.open("https://www.gnu.org/licenses/gpl-3.0.html")
    elif current_page == "Audio":
        if key == "Back":
            if not is_transitioning:
                transition.start("settings")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "settings"
        elif key == "SFX":
            muting_sfx()
        elif key == "Ambience":
            muting_amb()
    elif current_page == "Account":
        if key == "back":
            if not is_transitioning:
                transition.start("settings")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "settings"
        if key == "login":
            # Go to login screen for existing users
            if not is_transitioning:
                transition.start("login_screen") 
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "login_screen"
        elif key == "new_account":
            # Go to registration screen for new accounts
            if not is_transitioning:
                transition.start("registration_screen") 
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "registration_screen"
        elif key and key.startswith("load_user_"):
            # Extract ID from the key string
            selected_id = key.replace("load_user_", "")
            # Load the selected user's progress
            user_save_file = os.path.join(manage_data.APP_DATA_DIR, f"{selected_id}.json")
            if os.path.exists(user_save_file):
                try:
                    with open(user_save_file, "r", encoding="utf-8") as f:
                        manage_data.progress = json.load(f)
                        manage_data.SAVE_FILE = user_save_file
                    # Update manifest to mark this user as the last used
                    manage_data.update_local_manifest(manage_data.progress)
                    if not is_transitioning:
                        transition.start("main_menu")
                        transition_time = pygame.time.get_ticks()
                        is_transitioning = True
                        pending_page = "main_menu"
                except Exception as e:
                    print(f"Error loading user {selected_id}: {e}")
    elif current_page == 'worlds':
        if key == "back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
        elif key == "levels":
            if not is_transitioning:
                transition.start("green")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "green"
        elif key == "mech_levels":
            if not is_transitioning:
                transition.start("mech")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "mech"
        elif key == "ship_levels":
            if not is_transitioning:
                transition.start("ship")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "ship"
        elif key == "desert_levels":
            if not is_transitioning:
                transition.start("desert")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "desert"
    elif current_page == 'language_select':
        if key == "back":
            if not is_transitioning:
                transition.start("settings")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "settings"
        elif key in ["en", "fr", "es", "de", "zh_cn", "tr", "ru", "jp", "id", "kr", "ar", "pk"]:
            if not is_transitioning:
                pending_lang_code = key
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
    elif current_page == 'green' or current_page == 'mech' or current_page == 'ship' or current_page == 'desert':
        if key is None:  # Ignore clicks on locked levels
            return
        elif key == "back":
            if not is_transitioning:
                transition.start("worlds")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "worlds"
        else:  # Trigger a level's screen
            if not is_transitioning:
                transition.start(f"{current_page}_{key}")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = f"{current_page}_{key}"
    elif "lvl" in current_page:
        if key == "quit":
            if not is_transitioning:
                transition.start("worlds")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "worlds"
        else:
            # This is for the in-level pause menu, so we don't want to trigger if they click on locked levels in the background
            if key and "lvl" in key and not is_transitioning:
                transition.start(key)
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = key
    elif current_page == "quit_confirm":
        if key == "yes":
            quit_game()
        elif key == "no":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
    elif current_page == "character_select":
        if key == "locked" and not locked_char_sound_played and not manage_data.is_mute:
            manage_data.sounds['death'].play()
            locked_char_sound_played = False
            locked_char_sound_time = time.time()
        if key == "back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
    elif current_page == "profile":
        if key == "back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
    elif current_page == "login_screen" or current_page == "registration_screen":
        if key == "back":
            if not is_transitioning:
                transition.start("Account")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "Account"
        if key == "done":
            if not is_transitioning:
                # After handling the login/registration logic, we want to go back to the Account page to show the updated state (logged in or new account created)
                transition.start("main_menu")  # Start transition to main menu, but we'll actually set it to Account after the transition finishes
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"

# Central page switcher
def set_page(screen, page, transition):
    global current_page, current_lang  # Explicitly mark current_page and current_lang as global
    page = manage_data.current_page
    current_page = page  # Update the global current_page variable

    # Reload the current language data for the new page
    if page == 'main_menu':
        current_lang = manage_data.load_language().get('main_menu', {})
        menu_ui.create_main_menu_buttons()
    elif page == "profile":
        menu_ui.draw_profile(screen)
    elif page == "achievements":
        menu_ui.create_achieve_screen(screen)
    elif page == 'language_select':
        current_lang = manage_data.load_language().get('language_select', {})
        menu_ui.create_language_buttons(screen)
    elif page == "worlds":
        menu_ui.worlds(screen)
    elif page == "settings":
        menu_ui.settings_menu(screen)
    elif page == "About":
        menu_ui.about_menu(screen)
    elif page == "Audio":
        menu_ui.audio_settings_menu(screen)
    elif page == "Account":
        acc_sys.create_account_selector()
    elif page == "login_screen":
        acc_sys.reset_login_state()
    elif page == "registration_screen":
        acc_sys.reset_login_state()
    elif page == 'green':
        current_lang = manage_data.load_language().get('levels', {})
        menu_ui.green_world_buttons(screen)
        manage_data.change_ambience("green")
    elif page == 'mech':
        current_lang = manage_data.load_language().get('levels', {})
        menu_ui.mech_world_buttons(screen)
        manage_data.change_ambience("mech")
    elif page == 'ship':
        current_lang = manage_data.load_language().get('levels', {})
        menu_ui.ship_world_buttons(screen)
        manage_data.change_ambience("ship")
    elif page == 'desert':
        current_lang = manage_data.load_language().get('levels', {})
        menu_ui.desert_world_buttons(screen)
        manage_data.change_ambience("desert")
    elif page == 'quit_confirm':
        current_lang = manage_data.load_language().get('messages', {})
        menu_ui.create_quit_confirm_buttons()
    elif "lvl" in page:
        current_lang = manage_data.load_language().get('in_game', {})
        # Extract world and level from page name
        world_name, level_name = page.split("_", 1)
        # Call the generic level launcher
        launcher.level_launcher(level_name, screen, transition, world_name)

def muting_sfx():
    manage_data.is_mute = not manage_data.is_mute
    # Save directly to manage_data.manifest (pass 'manage_data.progress' so it can see player ID/Level)
    manage_data.update_local_manifest(manage_data.progress)

def muting_amb():
    # Toggle the state
    manage_data.is_mute_amb = not manage_data.is_mute_amb
    
    # Apply the change to the mixer
    if manage_data.is_mute_amb:
        pygame.mixer.music.stop()
    else:
        # If your game has a specific music file, trigger it here
        pygame.mixer.music.play(-1) 
        pass
        
    # Save directly to manage_data.manifest
    manage_data.update_local_manifest(manage_data.progress)

def quit_game():
    manage_data.sync_vault_to_cloud(manage_data.progress)
    pygame.quit()
    sys.exit()