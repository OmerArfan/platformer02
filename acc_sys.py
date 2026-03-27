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

# Global state for login/registration pages (persistent across frames)
login_state = {
    "username": "",
    "password": "",
    "input_mode": "USER",  # "USER" or "PASS"
    "status_msg": "",
    "status_color": (180, 180, 180)
}

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

def reset_login_state():
    """Reset login state for a fresh login/registration screen"""
    global login_state
    login_state = {
        "username": "",
        "password": "",
        "input_mode": "USER",
        "status_msg": "",
        "status_color": (180, 180, 180)
    }

def draw_login_screen(screen, SCREEN_WIDTH, SCREEN_HEIGHT, lang_code, manifest, bgs):
    """Render the login screen (called from main loop)"""
    settings = manage_data.load_language(lang_code, manifest).get('settings', {})
    
    screen.blit(bgs['plain'], (0, 0))
    
    # Header
    id_title_text = settings.get("login_header", "LOGIN")
    id_title = menu_ui.render_text(id_title_text, True, (255, 255, 255))
    screen.blit(id_title, (SCREEN_WIDTH // 2 - id_title.get_width() // 2, 80))

    # Instructions
    instr_txt = settings.get("login_instr1", "Enter your username and password to access your account.")
    instr = menu_ui.render_text(instr_txt, True, (255, 255, 255))
    screen.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2, 200))
    
    instr_txt3 = settings.get("login_instr3", "Press TAB to switch between Username and Password. ESC to return.")
    instr3 = menu_ui.render_text(instr_txt3, True, (255, 255, 255))
    screen.blit(instr3, (SCREEN_WIDTH // 2 - instr3.get_width() // 2, 230))
    
    instr_txt4 = settings.get("case_warning", "Usernames and Passwords are case sensitive!")
    instr4 = menu_ui.render_text(instr_txt4, True, (255, 255, 255))
    screen.blit(instr4, (SCREEN_WIDTH // 2 - instr4.get_width() // 2, 260))

    # Status Message
    if login_state["status_msg"]:
        s_surf = menu_ui.render_text(login_state["status_msg"], True, login_state["status_color"])
        screen.blit(s_surf, (SCREEN_WIDTH // 2 - s_surf.get_width() // 2, 330))

    # Username
    u_color = (255, 255, 255) if login_state["input_mode"] == "USER" else (80, 80, 80)
    u_text = settings.get("username_label", "Username")
    u_surf = menu_ui.render_text(f"{u_text}: {login_state['username']}", True, u_color)
    screen.blit(u_surf, (SCREEN_WIDTH // 2 - u_surf.get_width() // 2, 380))

    # Password
    p_color = (255, 255, 255) if login_state["input_mode"] == "PASS" else (80, 80, 80)
    p_text = settings.get("password_label", "Password")
    stars = "*" * len(login_state['password'])
    p_surf = menu_ui.render_text(f"{p_text}: {stars}", True, p_color)
    screen.blit(p_surf, (SCREEN_WIDTH // 2 - p_surf.get_width() // 2, 430))
    
    # Submit button
    submit_txt = settings.get("submit_prompt", "Press ENTER to Login")
    submit_surf = menu_ui.render_text(submit_txt, True, (0, 255, 0))
    screen.blit(submit_surf, (SCREEN_WIDTH // 2 - submit_surf.get_width() // 2, 520))

def handle_login_events(events, manifest, lang_code, is_mute, sounds, progress, set_page):
    """Handle events for login screen (called from main loop)"""
    settings = manage_data.load_language(lang_code, manifest).get('settings', {})
    
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                login_state["input_mode"] = "PASS" if login_state["input_mode"] == "USER" else "USER"
            
            elif event.key == pygame.K_ESCAPE:
                reset_login_state()
                set_page("Account")
                return False  # Signal to go back

            elif event.key == pygame.K_RETURN:
                if len(login_state["username"]) > 2 and len(login_state["password"]) > 3:
                    login_state["status_msg"] = settings.get("checking_vault", "Checking Cloud Vault...")
                    login_state["status_color"] = (255, 255, 0)
                    
                    # Try to recover account from cloud
                    result = manage_data.recover_account_from_cloud(login_state["username"], login_state["password"])
                    
                    if isinstance(result, dict):
                        # Login successful
                        progress.update(result)
                        manage_data.save_progress(progress)
                        if not is_mute: sounds['notify'].play()
                        login_success_text = settings.get("login_success", "Login Successful!")
                        # You'll want to set a notification in platformer.py
                        reset_login_state()
                        set_page("main_menu")
                        return True  # Signal successful login
                    
                    elif result == "CONN_ERROR":
                        if not is_mute: sounds['hit'].play()
                        conn_error_text = settings.get("conn_error", "Connection Error: Cloud Vault unreachable.")
                        login_state["status_msg"] = conn_error_text
                        login_state["status_color"] = (255, 0, 0)
                    
                    elif result == "WRONG_AUTH":
                        if not is_mute: sounds['death'].play()
                        login_state["status_msg"] = settings.get("wrong_pass", "Incorrect Password.")
                        login_state["status_color"] = (255, 50, 50)
                else:
                    if not is_mute: sounds['death'].play()
                    login_state["status_msg"] = settings.get("too_short", "Username or Password too short.")
                    login_state["status_color"] = (255, 50, 50)
            
            elif event.key == pygame.K_BACKSPACE:
                if login_state["input_mode"] == "USER":
                    login_state["username"] = login_state["username"][:-1]
                else:
                    login_state["password"] = login_state["password"][:-1]
            
            else:
                if event.unicode.isalnum() or event.unicode in " _-":
                    if login_state["input_mode"] == "USER" and len(login_state["username"]) < 15:
                        login_state["username"] += event.unicode
                    elif login_state["input_mode"] == "PASS" and len(login_state["password"]) < 20:
                        login_state["password"] += event.unicode
    
    return None  # Still processing login

def draw_registration_screen(screen, SCREEN_WIDTH, SCREEN_HEIGHT, lang_code, manifest, bgs):
    settings = manage_data.load_language(lang_code, manifest).get('settings', {})
    
    screen.blit(bgs['plain'], (0, 0))
    
    # Header
    id_title_text = settings.get("register_header", "CREATE ACCOUNT")
    id_title = menu_ui.render_text(id_title_text, True, (255, 255, 255))
    screen.blit(id_title, (SCREEN_WIDTH // 2 - id_title.get_width() // 2, 80))

    # Instructions
    instr_txt = settings.get("register_instr1", "Create a new account with a username and password.")
    instr = menu_ui.render_text(instr_txt, True, (255, 255, 255))
    screen.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2, 200))
    
    instr_txt2 = settings.get("register_instr2", "Your account will be synced to the cloud.")
    instr2 = menu_ui.render_text(instr_txt2, True, (255, 255, 255))
    screen.blit(instr2, (SCREEN_WIDTH // 2 - instr2.get_width() // 2, 230))
    
    instr_txt3 = settings.get("login_instr3", "Press TAB to switch between Username and Password. ESC to return.")
    instr3 = menu_ui.render_text(instr_txt3, True, (255, 255, 255))
    screen.blit(instr3, (SCREEN_WIDTH // 2 - instr3.get_width() // 2, 260))
    
    instr_txt4 = settings.get("case_warning", "Usernames and Passwords are case sensitive!")
    instr4 = menu_ui.render_text(instr_txt4, True, (255, 255, 255))
    screen.blit(instr4, (SCREEN_WIDTH // 2 - instr4.get_width() // 2, 290))

    # Status Message
    if login_state["status_msg"]:
        s_surf = menu_ui.render_text(login_state["status_msg"], True, login_state["status_color"])
        screen.blit(s_surf, (SCREEN_WIDTH // 2 - s_surf.get_width() // 2, 350))

    # Username
    u_color = (255, 255, 255) if login_state["input_mode"] == "USER" else (80, 80, 80)
    u_text = settings.get("username_label", "Username")
    u_surf = menu_ui.render_text(f"{u_text}: {login_state['username']}", True, u_color)
    screen.blit(u_surf, (SCREEN_WIDTH // 2 - u_surf.get_width() // 2, 400))

    # Password
    p_color = (255, 255, 255) if login_state["input_mode"] == "PASS" else (80, 80, 80)
    p_text = settings.get("password_label", "Password")
    stars = "*" * len(login_state['password'])
    p_surf = menu_ui.render_text(f"{p_text}: {stars}", True, p_color)
    screen.blit(p_surf, (SCREEN_WIDTH // 2 - p_surf.get_width() // 2, 450))
    
    # Create Account button
    create_txt = settings.get("create_account", "Press ENTER to Create Account")
    create_surf = menu_ui.render_text(create_txt, True, (0, 255, 0))
    screen.blit(create_surf, (SCREEN_WIDTH // 2 - create_surf.get_width() // 2, 540))

def handle_registration_events(events, manifest, lang_code, is_mute, sounds, progress, set_page, ACCOUNTS_FILE):
    settings = manage_data.load_language(lang_code, manifest).get('settings', {})
    
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                login_state["input_mode"] = "PASS" if login_state["input_mode"] == "USER" else "USER"
            
            elif event.key == pygame.K_ESCAPE:
                reset_login_state()
                set_page("Account")
                return False  # Signal to go back

            elif event.key == pygame.K_RETURN:
                if len(login_state["username"]) > 2 and len(login_state["password"]) > 3:
                    # Create new account
                    guest_id_to_promote = None
                    
                    # Check for guest account in manifest
                    if os.path.exists(ACCOUNTS_FILE):
                        try:
                            with open(ACCOUNTS_FILE, "r") as f:
                                manifest_data = json.load(f)
                                users_list = manifest_data.get("users", {})
                                for p_id, user_info in users_list.items():
                                    if user_info.get("username") == "":
                                        guest_id_to_promote = p_id
                                        break
                        except Exception as e:
                            login_state["status_msg"] = f"Error reading manifest: {e}"
                            login_state["status_color"] = (255, 0, 0)
                            if not is_mute: sounds['hit'].play()
                            return None

                    # Assign or create ID
                    if guest_id_to_promote:
                        progress["player"]["ID"] = guest_id_to_promote
                    else:
                        new_progress = copy.deepcopy(manage_data.default_progress)
                        progress.update(new_progress)
                        progress["player"]["ID"] = generate_player_id()

                    # Set credentials and save
                    progress["player"]["Username"] = login_state["username"]
                    progress["player"]["Pass"] = hash_password(login_state["password"])

                    manage_data.save_progress(progress)
                    threading.Thread(target=manage_data.sync_vault_to_cloud, args=(progress, manifest), daemon=True).start()
                    
                    if not is_mute: sounds['notify'].play()
                    login_state["status_msg"] = settings.get("account_created", "Account Created!")
                    login_state["status_color"] = (0, 255, 0)
                    
                    reset_login_state()
                    set_page("main_menu")
                    return True  # Signal successful registration
                else:
                    if not is_mute: sounds['death'].play()
                    login_state["status_msg"] = settings.get("too_short", "Username or Password too short.")
                    login_state["status_color"] = (255, 50, 50)
            
            elif event.key == pygame.K_BACKSPACE:
                if login_state["input_mode"] == "USER":
                    login_state["username"] = login_state["username"][:-1]
                else:
                    login_state["password"] = login_state["password"][:-1]
            
            else:
                if event.unicode.isalnum() or event.unicode in " _-":
                    if login_state["input_mode"] == "USER" and len(login_state["username"]) < 15:
                        login_state["username"] += event.unicode
                    elif login_state["input_mode"] == "PASS" and len(login_state["password"]) < 20:
                        login_state["password"] += event.unicode
    
    return None  # Still processing registration

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

    # 3. "Login" and "New Account" Buttons at the bottom
    login_txt = settings.get("login_button", "Login")
    login_txt_rendered = menu_ui.render_text(login_txt, True, (0, 200, 255)) # Blue color
    login_rect = login_txt_rendered.get_rect(center=((SCREEN_WIDTH // 2) - 400, SCREEN_HEIGHT - 50))
    buttons.append((login_txt_rendered, login_rect, "login", False))
    
    new_txt = settings.get("new_acc", "New Account")
    new_txt_rendered = menu_ui.render_text(new_txt, True, (0, 255, 200)) # Green color  
    new_rect = new_txt_rendered.get_rect(center=((SCREEN_WIDTH // 2) + 400, SCREEN_HEIGHT - 50))
    buttons.append((new_txt_rendered, new_rect, "new_account", False))

    back_txt = settings.get("back", "Back")
    back_txt_rendered = menu_ui.render_text(back_txt, True, (255, 255, 255)) # Red color
    back_rect = back_txt_rendered.get_rect(center=((SCREEN_WIDTH // 2), SCREEN_HEIGHT - 50))
    buttons.append((back_txt_rendered, back_rect, "back", False))