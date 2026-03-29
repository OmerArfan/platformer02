import sys
import pygame
import manage_data
import menu_ui
import os
import json
import webbrowser
import acc_sys
import time
import levels

class TransitionManager:
    def __init__(self, screen, left_image, right_image, speed=40):
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

    def update(self, lang_code, screen, version, transition, manifest, progress):
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
            manage_data.current_page = self.target_page  # Hold phase
            if pygame.time.get_ticks() - self.hold_time >= self.hold_duration:
                # Change language if pending
                if pending_lang_code:
                    manage_data.change_language(pending_lang_code, manifest, progress)
                    lang_code = pending_lang_code
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
                set_page(screen, manage_data.current_page, lang_code, manifest, progress, manage_data.Achievements, manage_data.bgs, manage_data.disks, version, manage_data.is_mute, manage_data.is_mute_amb, transition)
                self.phase = 2

        elif self.phase == 2:  # Slide-out phase
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
    global progress, is_transitioning, transition_time, locked_char_sound_played, locked_char_sound_time, manifest, lang_code, pending_lang_code, selected_id
    
    global pending_page
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
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
    elif current_page == 'worlds':
        if key == "back":
            if not is_transitioning:
                transition.start("main_menu")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "main_menu"
        elif key == "levels":
            if not is_transitioning:
                transition.start("levels")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "levels"
        elif key == "mech_levels":
            if not is_transitioning:
                transition.start("mech_levels")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = "mech_levels"
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
    elif current_page == 'levels' or current_page == 'mech_levels':
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
                transition.start(f"{key}_screen")
                transition_time = pygame.time.get_ticks()
                is_transitioning = True
                pending_page = f"{key}_screen"
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

# Central page switcher
def set_page(screen, page, lang_code, manifest, progress, Achievements, bgs, disks, version, is_mute, is_mute_amb, transition):
    global current_page, current_lang  # Explicitly mark current_page and current_lang as global
    page = manage_data.current_page
    current_page = page  # Update the global current_page variable

    # Reload the current language data for the new page
    if page == 'main_menu':
        current_lang = manage_data.load_language(lang_code, manifest).get('main_menu', {})
        menu_ui.create_main_menu_buttons(screen, lang_code, manifest, progress)
    elif page == "profile":
        menu_ui.draw_profile(screen)
    elif page == "achievements":
        menu_ui.create_achieve_screen(screen, lang_code, manifest, progress)
    elif page == 'character_select':
        menu_ui.character_select(lang_code, manifest)
    elif page == 'language_select':
        current_lang = manage_data.load_language(lang_code, manifest).get('language_select', {})
        menu_ui.create_language_buttons(screen, lang_code, manifest, progress)
    elif page == "worlds":
        menu_ui.worlds(screen, lang_code, manifest, progress, bgs, manage_data.disks)
    elif page == "settings":
        menu_ui.settings_menu(screen, lang_code, manifest, bgs)
    elif page == "About":
        menu_ui.about_menu(screen, lang_code, manifest, bgs, version)
    elif page == "Audio":
        menu_ui.audio_settings_menu(screen, lang_code, manifest, progress, bgs, is_mute, is_mute_amb)
    elif page == "Account":
        acc_sys.create_account_selector()
    elif page == "login_screen":
        acc_sys.reset_login_state()
    elif page == "registration_screen":
        acc_sys.reset_login_state()
    elif page == 'levels':
        current_lang = manage_data.load_language(lang_code, manifest).get('levels', {})
        menu_ui.green_world_buttons(screen, lang_code, manifest, progress, bgs, disks)
        manage_data.change_ambience("audio/amb/greenambience.wav")
    elif page == 'mech_levels':
        current_lang = manage_data.load_language(lang_code, manifest).get('levels', {})
        menu_ui.mech_world_buttons(screen, lang_code, manifest, progress, bgs, disks)
        manage_data.change_ambience("audio/amb/mechambience.wav")
    elif page == 'quit_confirm':
        current_lang = manage_data.load_language(lang_code, manifest).get('messages', {})
        menu_ui.create_quit_confirm_buttons(lang_code, manifest)
    elif page == 'lvl1_screen':  # New page for Level 1
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl1_screen(screen, transition)
    elif page == 'lvl2_screen':  # New page for Level 2
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl2_screen()
    elif page == 'lvl3_screen':  # New page for Level 3
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl3_screen()
    elif page == 'lvl4_screen':  # New page for Level 4
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl4_screen()
    elif page == 'lvl5_screen':  # New page for Level 5
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl5_screen()
    elif page == 'lvl6_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl6_screen()
    elif page == 'lvl7_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl7_screen()
    elif page == 'lvl8_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl8_screen()
    elif page == 'lvl9_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl9_screen()
    elif page == 'lvl10_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl10_screen()
    elif page == 'lvl11_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl11_screen()
    elif page == 'lvl12_screen':
        current_lang = manage_data.load_language(lang_code, manifest).get('in_game', {})
        levels.create_lvl12_screen()

def muting_sfx():
    global is_mute
    manage_data.is_mute = not manage_data.is_mute
    # Save directly to manage_data.manifest (pass 'manage_data.progress' so it can see player ID/Level)
    manage_data.update_local_manifest(manage_data.progress)

def muting_amb():
    global is_mute_amb
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
    manage_data.sync_vault_to_cloud(manage_data.progress, manage_data.manifest)
    pygame.quit()
    sys.exit()()