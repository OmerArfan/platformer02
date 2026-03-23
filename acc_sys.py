import pygame
import hashlib
import json
import os
import time
import manage_data
import copy
import menu_ui
import threading
import random

# Initalizing Player ID
HEX = "0123456789ABCDEF"

def generate_player_id():
    roll = random.random() * 100  # 0.0 → 100.0

    if roll < 0.001:        # 0.1%
        length = 3
    elif roll < 2.1:     # next 5%
        length = 4
    elif roll < 25:                 # rest
        length = 5
    else:
        length = 6

    return "".join(random.choices(HEX, k=length))

def hash_password(password):
    # Convert the string to bytes, then create a SHA-256 hash
    return hashlib.sha256(password.encode()).hexdigest()

def show_login_screen(lang_code, manifest, transition, screen, bgs, SCREEN_WIDTH, is_mute, sounds, draw_notifications, draw_syncing_status, buttons):
    global username, user_pass, input_mode, login_done, progress, er, notification_text, notification_time, notif, error_code
    settings = manage_data.load_language(lang_code, manifest).get('settings', {})
    login_done = False
    status_msg = ""
    status_color = (180, 180, 180)
    if transition.x <= -transition.image.get_width():
       while not login_done:
        screen.blit(bgs['plain'], (0, 0))
        # 1. Header
        id_title_text = settings.get("login_header", "LOGIN / REGISTER")
        id_title = menu_ui.render_text(id_title_text, True, (255, 255, 255))
        screen.blit(id_title, (SCREEN_WIDTH // 2 - id_title.get_width() // 2, 80))

        # 2. Instructions
        instr_txt = settings.get("login_instr1", "Enter your username and password to access your account, or create a new one.")
        instr = menu_ui.render_text(instr_txt, True, (255, 255, 255))
        screen.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2 , 200))
        
        instr_txt2 = settings.get("login_instr2", "If the account does not exist, a new account will be created for you.")
        instr2 = menu_ui.render_text(instr_txt2, True, (255, 255, 255))
        screen.blit(instr2, (SCREEN_WIDTH // 2 - instr2.get_width() // 2 , 230))

        instr_txt3 = settings.get("login_instr3", "Press TAB to switch between inputting Password and Username. To return, press ESC.")
        instr3 = menu_ui.render_text(instr_txt3, True, (255, 255, 255))
        screen.blit(instr3, (SCREEN_WIDTH // 2 - instr3.get_width() // 2 , 260))
        
        instr_txt4 = settings.get("case_warning", "Usernames and Passwords are case sensitive!")
        instr4 = menu_ui.render_text(instr_txt4, True, (255, 255, 255))
        screen.blit(instr4, (SCREEN_WIDTH // 2 - instr4.get_width() // 2 , 290))

        # 3. Status Message (Errors, Success, etc.)
        if status_msg:
            s_surf = menu_ui.render_text(status_msg, True, status_color)
            screen.blit(s_surf, (SCREEN_WIDTH // 2 - s_surf.get_width() // 2, 350))

        # 4. Inputs
        # USERNAME
        u_color = (255, 255, 255) if input_mode == "USER" else (80, 80, 80)
        u_text = settings.get("username_label", "Username") # Just gets the word
        u_surf = menu_ui.render_text(f"{u_text}: {username}", True, u_color) # Stick them together here
        screen.blit(u_surf, (SCREEN_WIDTH // 2 - u_surf.get_width() // 2, 400))

        # PASSWORD
        p_color = (255, 255, 255) if input_mode == "PASS" else (80, 80, 80) 
        p_text = settings.get("password_label", "Password") # Just gets the word
        stars = "*" * len(user_pass)
        p_surf = menu_ui.render_text(f"{p_text}: {stars}", True, p_color) # Stick them together here
        screen.blit(p_surf, (SCREEN_WIDTH // 2 - p_surf.get_width() // 2, 450))
        
        # Submit button
        submit_txt = settings.get("submit_prompt", "Press ENTER to Continue")
        submit_surf = menu_ui.render_text(submit_txt, True, (0, 255, 0))
        screen.blit(submit_surf, (SCREEN_WIDTH // 2 - submit_surf.get_width() // 2, 550))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                login_done = True
                set_page("quit_confirm")

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    input_mode = "PASS" if input_mode == "USER" else "USER"
                
                if event.key == pygame.K_ESCAPE:
                    login_done = True
                    set_page("Account")

                elif event.key == pygame.K_RETURN:
                    if len(username) > 2 and len(user_pass) > 3:
                        status_msg = settings.get("checking_vault", "Checking Cloud Vault...")
                        status_color = (255, 255, 0)
                        pygame.display.update()
                        result = manage_data.recover_account_from_cloud(username, user_pass)
        # Access the notification globals
                        global notif, notification_text, notification_time, er
                        if isinstance(result, dict):
            # [SCENARIO 1] SUCCESS
                         progress = result
                         manage_data.save_progress(progress)
            
            # TRIGGER NOTIFICATION
                         login_success_text = settings.get("login_success", "Login Successful!")
                         notification_text = menu_ui.render_text(login_success_text, True, (0, 255, 0))
                         notification_time = time.time()
                         notif = True
                         login_done = True
                         if not is_mute: sounds['notify'].play()
                         set_page("Account") # Explicitly set the page back
                         return

                        elif result == "CONN_ERROR":
                            if not is_mute: 
                                sounds['hit'].play()
                            conn_error_text = settings.get("conn_error", "Connection Error: Cloud Vault is unreachable.")
                            notification_text = menu_ui.render_text(conn_error_text, True, (255, 0, 0))
                            notif = True
                            notification_time = time.time()
                            set_page("main_menu")
                            return
                        
                        elif result == "WRONG_AUTH":
            # [SCENARIO 2] WRONG PASS
                         status_msg = settings.get("wrong_pass", "Incorrect Password.")
                         status_color = (255, 50, 50)
                         if not is_mute: sounds['death'].play()
            
                        else:
                         # CASE: Username doesn't exist in cloud. This is a signup.
                            guest_id_to_promote = None
                            
                            # Check the local manifest for a Guest (Username: "")
                            if os.path.exists(ACCOUNTS_FILE):
                                try:
                                    with open(ACCOUNTS_FILE, "r") as f:
                                        manifest = json.load(f)
                                        users_list = manifest.get("users", {})
                                        
                                        # We look specifically for the empty string ""
                                        for p_id, user_info in users_list.items():
                                            if user_info.get("username") == "":
                                                guest_id_to_promote = p_id
                                                break
                                except Exception as e:
                                    er = True
                                    error_code = f"Manifest Read Error: {e}"
                                    if not is_mute:
                                        sounds['hit'].play()
                                    notification_time = time.time()

                            # 2. Assign the ID
                            if guest_id_to_promote:
                                # PROMOTE the guest ID to this new username
                                progress["player"]["ID"] = guest_id_to_promote
                                print(f"Migrating Guest ID {guest_id_to_promote} to {username}")
                            else:
                                # No guest found, create a brand new ID
                                # Initialize with DEFAULT STATS for a new user
                                progress = copy.deepcopy(manage_data.default_progress)
                                progress["player"]["ID"] = manage_data.generate_player_id()
                                print(f"No guest found. Generated new ID: {progress['player']['ID']}")

                            # 3. Update the credentials
                            progress["player"]["Username"] = username
                            progress["player"]["Pass"] = hash_password(user_pass)

                            # 4. Save and Sync
                            # This will create/update the row in your Google Sheet using the selected ID
                            manage_data.save_progress(progress)
                            threading.Thread(target=manage_data.sync_vault, args=(progress,), daemon=True).start()
                            login_done = True
                            if not is_mute: sounds['notify'].play()
                            notification_txt = settings.get("account_created", "Account Created and Logged In!")
                            notification_text = menu_ui.render_text(notification_txt, True, (0, 255, 0))
                            notif = True
                            notification_time = time.time()
                            set_page("main_menu")
                            return        
                    else:
                        if not is_mute:
                            sounds['death'].play()
                        status_msg = settings.get("too_short", "Username or Password too short.")
                        status_color = (255, 50, 50)
                
                elif event.key == pygame.K_BACKSPACE:
                    if input_mode == "USER": username = username[:-1]
                    else: user_pass = user_pass[:-1]
                
                else:
                    if event.unicode.isalnum() or event.unicode in " _-":
                        if input_mode == "USER" and len(username) < 15:
                            username += event.unicode
                        elif input_mode == "PASS" and len(user_pass) < 20:
                            user_pass += event.unicode
        
        draw_notifications()
        draw_syncing_status()

        pygame.display.flip()
    pygame.display.update()

buttons = []
def create_account_selector(ACCOUNTS_FILE, lang_code, manifest, transition, screen, bgs, SCREEN_WIDTH, SCREEN_HEIGHT, is_mute, sounds, draw_notifications, draw_syncing_status, buttons):
    buttons.clear()
    settings = manage_data.load_language(lang_code, manifest).get('settings', {})

    # 1. Load manifest
    manifest = {"users": {}}
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, "r") as f:
                manifest = json.load(f)
        except: pass
    
    accounts = list(manifest.get("users", {}).items())
    
    # --- LAYOUT CONSTANTS ---
    COLUMN_WIDTH = 300
    START_Y = 200
    MAX_Y = SCREEN_HEIGHT - 150
    SPACING_Y = 72
    
    # Calculate how many columns we actually have
    num_accounts = len(accounts) + 1  # +1 for the "New Player" button
    items_per_col = (MAX_Y - START_Y) // SPACING_Y
    num_cols = (num_accounts // items_per_col) + 1
    
    # Calculate the starting X so the WHOLE group is centered
    # Total width is (number of columns * width), then we find the center
    total_group_width = num_cols * COLUMN_WIDTH
    start_x = (SCREEN_WIDTH // 2) - (total_group_width // 2) + (COLUMN_WIDTH // 2)

    current_x = start_x
    current_y = START_Y

    # 2. Render Account Buttons
    for p_id, info in accounts:
        name_str = info.get("username", "Unknown")
        rendered_name = menu_ui.render_text(name_str, True, (255, 255, 255))

        # Check if we need to wrap to a new column
        if current_y >= MAX_Y:
            current_y = START_Y
            current_x += COLUMN_WIDTH
            
        # Left-aligning looks better in columns:
        # We use current_x as the anchor for the left side of the text
        rect = rendered_name.get_rect(topleft=(current_x - 100, current_y))

        buttons.append((rendered_name, rect, f"load_user_{p_id}", False))
        current_y += SPACING_Y

    # 3. "New Player" Button (Follows the same grid logic)
    if current_y > MAX_Y:
        current_y = START_Y
        current_x += COLUMN_WIDTH

    new_txt = settings.get("new_acc", "+ NEW PLAYER")
    new_txt_rendered = menu_ui.render_text(new_txt, True, (0, 255, 200)) # Highlighted color
    new_rect = new_txt_rendered.get_rect(topleft=(current_x - 100, current_y))
    buttons.append((new_txt_rendered, new_rect, "new_account", False))