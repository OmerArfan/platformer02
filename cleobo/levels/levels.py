import pygame
import cleobo.ui.menu_ui as menu_ui
import time
from cleobo.data import manage_data, achievements
from cleobo.levels.logic import hazards, entities, env, mech, blockmgr
import cleobo.ui.state as state

def level_launcher(level_name, screen, transition, world_name):
    """
    Generic level launcher that loads and plays a level from Lua data.
    
    Args:
        level_name: Name of the level (e.g., 'lvl1', 'lvl2')
        screen: Pygame display surface
        transition: TransitionManager instance
        world_name: Name of the world/file (e.g., 'green')
    """
    from cleobo.levels.parser import load_level_data
    
    # Load level data from Lua file
    level_data = load_level_data(level_name, world_name)
    
    if not screen:
        return
    
    # Load level-specific assets
    background = manage_data.bgs.get(world_name)
    screen.blit(background, (0, 0))
    
    # Clear UI
    menu_ui.buttons.clear()
    
    # Get in-game language strings
    in_game = manage_data.load_language().get('in_game', {})
    
    manager = entities.LevelManager()
    # Player
    player_data = level_data['player']
    player = entities.Player(player_data['x'], player_data['y'])
    player.spawn_x, player.spawn_y = player_data['spawn_x'], player_data['spawn_y']
    
    clock = pygame.time.Clock()
    running = True
    
    # Build Level Elements from Data
    # Static blocks
    blocks = [pygame.FRect(b['x'], b['y'], b['w'], b['h']) for b in level_data.get('blocks', [])]
    
    # Moving blocks
    moving_blocks = []
    for mb_data in level_data.get('moving_block', []):
        moving_blocks.append({
            'rect': pygame.FRect(mb_data['x'], mb_data['y'], mb_data['w'], mb_data['h']),
            'direction': mb_data.get('direction', 1),
            'speed': mb_data.get('speed', 2),
            'limit_left': mb_data.get('limit_x', mb_data['x']),
            'limit_right': mb_data.get('limit_y', mb_data['x'] + 200),
        })
    
    # Spikes
    spikes = [spike for spike in level_data.get('spikes', [])]
    
    # Jump blocks (orange blocks)
    jump_blocks = [pygame.FRect(jb['x'], jb['y'], jb['w'], jb['h']) for jb in level_data.get('jump_blocks', [])]
    
    # Initialization inside level_launcher
    key_block_pairs = []
    for kbp in level_data.get('key_block_pairs', []):
        # Handle the Boolean Fix (String to Bool)
        collected_raw = kbp.get('collected', False)
        if isinstance(collected_raw, str):
            is_collected = collected_raw.lower() == "true"
        else:
            is_collected = bool(collected_raw)

        # Transform raw data into Game-Ready data
        key_block_pairs.append({
            'key': kbp['key'],  # This stays a dict with x, y, radius, color
            'block': pygame.FRect(kbp['block']['x'], kbp['block']['y'], kbp['block']['w'], kbp['block']['h']),
            'collected': is_collected
        })

    saws = level_data.get('saws', [])
    hazards.pre_render_saws(manage_data.assets['saw'], saws)

    lasers = [pygame.FRect(laser['x'], laser['y'], laser['w'], laser['h']) for laser in level_data.get('lasers', [])]

    # Flags/Checkpoints
    flags = level_data.get('flags', [])
    if not isinstance(flags, list):
        flags = [flags] if flags else []
    
    # Exit portal
    exit_data = level_data['exit']
    exit_portal = pygame.FRect(exit_data['x'], exit_data['y'], exit_data['w'], exit_data['h'])
    
    # Teleporters
    teleporters = []
    for tp in level_data.get('teleporters', []):
        teleporters.append({
            'entry': pygame.FRect(int(tp['entry_x']), int(tp['entry_y']), int(tp['entry_w']), int(tp['entry_h'])),
            'exit': pygame.FRect(int(tp['exit_x']), int(tp['exit_y']), int(tp['exit_w']), int(tp['exit_h']))
        })

    # Render text messages from data
    text_elements = []
    for text_key, text_data in level_data.get('text', {}).items():
        if isinstance(text_data, dict):
            lang_key = text_data['name']
            fallback_text = text_data['fallback']
            color = tuple(text_data['color'])
            x = text_data['x']
            y = text_data['y']
            
            display_text = in_game.get(lang_key, fallback_text)
            rendered = menu_ui.render_text(display_text, True, color)
            text_elements.append({'rendered': rendered, 'x': x, 'y': y})

    # Buttons
    weak_grav = level_data.get('grav_weak', {})
    strong_grav = level_data.get('grav_strong', {})
    speedster = level_data.get('speedster', {})
    lights = []
    for l in level_data.get('lights', []):
        lights.append({
            'button': pygame.FRect(int(l['button']['x']), int(l['button']['y']), 60, 60),
            'block': pygame.FRect(int(l['block']['x']), int(l['block']['y']), int(l['block']['w']), int(l['block']['h']))
        })

    # Pre-render fall message
    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))
            
    reset_text = in_game.get("reset_message", "Press R to reset")
    reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))
        
    quit_text = in_game.get("quit_message", "Press Q to quit")
    quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))

    # === MAIN GAME LOOP ===
    if not transition.active:
      while running:
        
        keys = pygame.key.get_pressed()
        
        real_dt = clock.tick_busy_loop(60) / 1000.0
        manager.current_time += real_dt

        formatted_time = "{:.2f}".format(manager.current_time)

        # === EVENT HANDLING ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                state.handle_action("quit", transition, manage_data.current_page)
        
        # Check exit portal collision
        if player.rect.colliderect(exit_portal):
            level_num = int(level_name.replace('lvl', ''))
            subsection = '1'
            
            # ✅ Added world_name and subsection parameters
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = manager.fin_lvl_logic(
                level_num, 
                player, 
                world_name=world_name,
                subsection=subsection
            )
            
            # ✅ Get medal from updated progress
            level_data_updated = manage_data.progress["lvls"][world_name][subsection][f"lvl{level_num}"]
            medal = level_data_updated.get('medal', 'None')
            
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)
            
            manage_data.save_progress(manage_data.progress, manage_data.manifest)
            
            next_page = level_data.get('next_page')
            state.handle_action(next_page, transition, manage_data.current_page)
            
            running = False
        
        # === UPDATE PLAYER INPUT & VELOCITY (BEFORE collisions) ===
        player.update(keys, manager, rendered_fall_text)
        
        # === RENDER ===
        screen.blit(background, (0, 0))

        # Draw spikes
        hazards.draw_spikes(screen, spikes, player)
        # Draw portal
        env.draw_portal(screen, manage_data.assets[f'{world_name}_exit'], exit_portal, player)

        # Handle buttons

        player.jump_mode = mech.handle_buttons(screen, weak_grav, player, player.jump_mode, "weak")
        player.jump_mode = mech.handle_buttons(screen, strong_grav, player, player.jump_mode, "strong")
        player.speed_mode = mech.handle_buttons(screen, speedster, player, player.speed_mode, "speedster")

        # 2. Check for saw deaths
        if hazards.handle_all_saws(screen, saws, player, blocks):
            player.die()
            manager.death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            manager.wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            for kbp in key_block_pairs: 
                kbp['collected'] = False

        if hazards.handle_lasers(screen, lasers, player):
            player.die()
            manager.death_text = menu_ui.render_text(in_game.get("laser_message", "Lasered!"), True, (255, 0, 0))
            manager.wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['laser'].play()
            for kbp in key_block_pairs: 
                kbp['collected'] = False

        # === PHYSICS: BLOCK COLLISIONS ===
        player, moving_blocks = blockmgr.handle_moving_blocks(screen, moving_blocks, player)

        player = blockmgr.handle_blocks(screen, blocks, player)

        player = blockmgr.handle_jump_blocks(screen, jump_blocks, player)

        player = blockmgr.handle_key_blocks(screen, key_block_pairs, player)

        player = env.handle_teleports(screen, teleporters, player)   
        # Spike collisions
        if hazards.check_spike_collisions(spikes, player):
            player.die()
            manager.death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            manager.wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            for kbp in key_block_pairs: 
                kbp['collected'] = False

        # Draw text elements
        for text_elem in text_elements:
            screen.blit(text_elem['rendered'], (text_elem['x'] - player.camera_x, text_elem['y'] - player.camera_y))

        # Lights
        player = mech.handle_light_blocks(screen, lights, player)

        # === UI ===
        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=player.deathcount)
        deaths_text = menu_ui.render_text(deaths_val, True, (255, 255, 255))
        
        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))
        
        manager.update(screen, player, deaths_text, reset_text, quit_text, timer_text)
        
        manager.medal = manager.get_medal(int(level_name.replace('lvl', '')), world_name, manager.current_time)

        # Reset level
        if keys[pygame.K_r]:
            player.reset_stats()
            manager.reset_stats()
            player.rect.x, player.rect.y = player.spawn_x, player.spawn_y
            player.velocity_y = 0
            player.deathcount = 0
            for kbp in key_block_pairs: 
                kbp['collected'] = False
        
        # Update Player sprite
        player.sprite.draw(screen, player, keys, manager)

        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update()

# IMPORTANT!
# ANYTHING BELOW THIS IS OLD, LEGACY CODE WHICH WILL GET PHASED OUT AS TIME GOES ON.

def create_lvl11_screen(screen, transition):
    global player_img, font, complete_levels, current_time, medal, deathcount, score
    global new_hs, hs, stars

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    new_hs = False
    menu_ui.buttons.clear()
    screen.blit(manage_data.bgs['mech'], (0, 0))

    in_game = manage_data.load_language().get('in_game', {})

    wait_time = None
    death_text = None
    start_time = time.time()

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y =  -400, 300
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21

    # Gravity menu_ui.buttons
    strong_jump_strength = 15
    strong_grav = False
    weak_grav_strength = 37
    weak_grav = False
    
    # Speed settings
    move_speed = 8
    stamina = False
    stamina_speed = 19

    # Other settings
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    lights_off = True

    # Preparation for fight with Evil Robo
    suspicious_x = 4200
    trigger_x = 4650
    espawn_x, espawn_y = 5200, -400
    epos_x, epos_y = espawn_x, espawn_y
    evilrobo_mascot = pygame.image.load(manage_data.resource_path(f"char/evilrobot/evilrobot.png")).convert_alpha()
    evilrobo_phase = 0    

    # Logic for unlocking Evil Robo
    unlock = manage_data.progress.get("evilrobo_unlocked", False)
    unlock_time = None

    # Draw flag
    flag = pygame.FRect(1400, 420, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.FRect(5600, 330, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 1400, 420
    flag_2_x, flag_2_y = 5600, 330

    blocks = [
        pygame.FRect(-600, 525, 2850, 50),
        pygame.FRect(1065, 200, 70, 375),
        pygame.FRect(1625, -200, 100, 590),
        pygame.FRect(1625, 50, 150, 50),
        pygame.FRect(2200, 400, 150, 50),
        pygame.FRect(2250, -300, 600, 2200),
        pygame.FRect(2300, 200, 3000, 100),
        pygame.FRect(3100, -300, 2600, 100),
        pygame.FRect(3050, -500, 120, 300),
        pygame.FRect(5180, 250, 120, 300),
        pygame.FRect(5250, 450, 1500, 100),
        pygame.FRect(5600, -1400, 520, 1700),
    ]

    jump_blocks = [
        pygame.FRect(630, 425, 100, 100),
        pygame.FRect(14000, 600, 100, 100),
    ]

    moving_saws = [ 
        {'r': 70, 'speed': 6, 'cx': 3500, 'cy': -350, 'max': 500, 'min': -500},
        {'r': 70, 'speed': 6, 'cx': 4000, 'cy': -200, 'max': 500, 'min': -500},
        {'r': 70, 'speed': 6, 'cx': 4500, 'cy': -50, 'max': 500, 'min': -500},
        {'r': 70, 'speed': 6, 'cx': 5000, 'cy': 50, 'max': 500, 'min': -500},
    ]

    moving_saws_x = [
        {'r': 30, 'speed': 3, 'cx': 1700, 'cy': 320, 'min': 1650, 'max': 1900},
        {'r': 30, 'speed': 4, 'cx': 2100, 'cy': -130, 'min': 1750, 'max': 2100},
    ]

    rushing_saws = [
        {'r': 200, 'speed': 21, 'cx': 3000, 'cy': 0, 'max': 5920, "min": 2700},
    ]

    moving_block = [
        {'x': 1700, 'y': 270, 'width': 110, 'height': 100, 'direction': 1, 'speed': 3, 'left_limit': 1650, 'right_limit': 1900 },
        {'x': 2100, 'y': -180, 'width': 110, 'height': 100, 'direction': 1, 'speed': 4, 'left_limit': 1750, 'right_limit': 2100 },
    ]

    saws = [
        (1100, 200, 200, (255, 0, 0)),
        (6300, 450, 80, (255, 0, 0)),
    ]

    spikes = [
    [(0, 525), (100, 475), (200, 525)],
    [(210, 525), (310, 475), (410, 525)],
    [(420, 525), (520, 475), (620, 525)],
    [(1625, -50), (1575, 0), (1625, 50)],
    [(1625, 60), (1575, 110), (1625, 160)],
    [(1625, 170), (1575, 220), (1625, 270)],
    [(1625, 280), (1575, 330), (1625, 380)],
    ]

    lights = [
        {
        "button": pygame.FRect(2350, -425, 50, 50),
        "block": pygame.FRect(3050, -200, 120, 400)
        }
    ]

    exit_portal = pygame.FRect(6600, 250, 140, 180)
    clock = pygame.time.Clock()

    speedsters = [
        (-100, 400, 30, (51, 255, 51)),
        (2450, -400, 30, (51, 255, 51)),
    ]
    
    for x, y, r, color in saws:
            angle = (pygame.time.get_ticks() // 3) % 360
            saw_ig_img = manage_data.assets['saw']
            curr_w, curr_h = saw_ig_img.get_size()
            center_x = x - camera_x
            center_y = y - camera_y
            draw_x = center_x - (curr_w / 2)
            draw_y = center_y - (curr_h / 2)
            screen.blit(saw_ig_img, (draw_x, draw_y))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [((x - camera_x),( y - camera_y)) for x, y in spike])

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)

    button4_text = in_game.get("button4_message", "Green menu_ui.buttons, upon activation, will give you a massive speed boost!")
    rendered_button4_text = menu_ui.render_text(button4_text, True, (51, 255, 51))

    if not transition.active:
       while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            lights_off = True
            stamina = False
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = -400, 300
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0
            evilrobo_phase = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                state.handle_action("quit", transition, manage_data.current_page)

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if strong_grav:
                velocity_y = -strong_jump_strength
            elif weak_grav:
                velocity_y = -weak_grav_strength
            else:
                velocity_y = -jump_strength
            if not manage_data.is_mute:
                manage_data.sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                if stamina:
                    player_x -= stamina_speed
                else:
                    player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if stamina:
                    player_x += stamina_speed
                else:
                    player_x += move_speed

            if on_ground and not was_moving and not manage_data.is_mute:
                manage_data.sounds['move'].play()
            was_moving = True
        else:
            was_moving = False

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

        # Collisions and Ground Detection
        player_rect = pygame.FRect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in moving_block:
            rect = pygame.FRect(block['x'], block['y'], block['width'], block['height'])
            if player_rect.colliderect(rect):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= rect.y:
                    player_y = rect.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > rect.x and player_x < rect.x + rect.width:
                    if player_x < rect.x:  # Colliding with the left side of the block
                        player_x = rect.x - img_width
                    elif player_x + img_width > rect.x + rect.width:  # Colliding with the right side
                        player_x = rect.x + rect.width

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            evilrobo_phase = 0
            epos_x, epos_y = espawn_x, espawn_y
            lights_off = True
            stamina = False
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:    
                manage_data.sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

        # Moving blocks
        for block in moving_block:
            block['x'] += block['speed'] * block['direction']
            if block['x'] < block['left_limit'] or block['x'] > block['right_limit']:
                block['direction'] *= -1

        player_rect = pygame.FRect(player_x, player_y, img_width, img_height)

        # Checkpoint logic
        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            stamina = False  # Reset stamina status
            lights_off = True
            spawn_x, spawn_y = 1400, 420  # Store checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            lights_off = True
            stamina = False
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 5600, 330  # Checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_fin_lvl_logic(current_time, deathcount, medal, 11)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)

            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            
            state.handle_action('lvl12_screen', transition, manage_data.current_page)
            running = False    

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        if checkpoint_reached2:
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag2.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(manage_data.bgs['mech'], (0, 0))

        if checkpoint_reached:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))

        # Handle Moving Saws
        if level_handle_moving_saws(screen, moving_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            lights_off = True
            stamina = False
            evilrobo_phase = 0
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_handle_moving_saws_x(screen, moving_saws_x, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            lights_off = True
            stamina = False
            evilrobo_phase = 0
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0

        if level_handle_rushing_saws(screen, rushing_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            lights_off = True
            stamina = False
            evilrobo_phase = 0
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0

        player_x, player_y, velocity_y = level_jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], strong_grav, weak_grav)
        level_draw_saws(screen, saws, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache)

        # 2. Check for saw deaths
        if level_check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1
            lights_off = True
            stamina = False
            evilrobo_phase = 0

        for block in moving_block:
            pygame.draw.rect(screen, (128, 0, 128), (block['x'] - camera_x, block['y'] - camera_y, block['width'], block['height']))
        
        for block in moving_block:
            pygame.draw.rect(screen, (128, 0, 128), ((block['x'] - camera_x), (block['y'] - camera_y), block['width'], block['height']))
            if block['width'] < 100:
                laser_rect = pygame.FRect(block['x'], block['y'] + block['height'] +10, block['width'], 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.FRect(block['x'] + 4, block['y'] + block['height'] + 5, block['width'] - 8 , 5)  # 5 px tall death zone
            if player_rect.colliderect(laser_rect) and not on_ground and player_x != block['x']:  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                evilrobo_phase = 0
                epos_x, epos_y = espawn_x, espawn_y
                stamina = False
                wait_time = pygame.time.get_ticks()
                lights_off = True
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1

        level_draw_spikes(screen, spikes, camera_x, camera_y)

        if level_check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1
            lights_off = True
            stamina = False
            evilrobo_phase = 0

        player_x, player_y, velocity_y, on_ground, player_rect = level_block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1
                lights_off = True
                stamina = False
                evilrobo_phase = 0 

        if level_handle_speedsters(screen, speedsters, player_rect, camera_x, camera_y, stamina):
            stamina = True

        level_draw_portal(screen, manage_data.assets['mech_exit'], exit_portal, camera_x, camera_y)
        # Player Image
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        # Boss Trigger Area
        if lights_off or evilrobo_phase > 0:
         if player_x > suspicious_x and player_y < -300:
            screen.blit(evilrobo_mascot, ((epos_x - camera_x), (epos_y - camera_y)))

            if evilrobo_phase == 0 and player_x < trigger_x:
                evilrobo_txt1 = in_game.get("evilrobo1", "Huh? Is there anyone there?")
                sus_message = menu_ui.render_text(evilrobo_txt1, True, (255, 20, 12))
                screen.blit(sus_message, (4800 - camera_x, -450 - camera_y))
            else:
                if evilrobo_phase < 1:
                    evilrobo_phase = 1  # Prevents repeating

         if evilrobo_phase == 1 and player_y < -300 and lights_off:
            evilrobo_txt2 = in_game.get("evilrobo2", "HEY! Get away from here!")
            holup_message = menu_ui.render_text(evilrobo_txt2, True, (185, 0, 0))
            screen.blit(holup_message, (4800 - camera_x, -450 - camera_y))
            
         if evilrobo_phase == 1 and lights_off:
            screen.blit(evilrobo_mascot, (int(epos_x - camera_x), int(epos_y - camera_y)))
            if epos_x > player_x + 10:
                epos_x -= 20
                
            elif epos_x < player_x - 10:
                epos_x += 20
            else:
                epos_x = player_x

         if epos_x < 2150 and evilrobo_phase < 2:
            evilrobo_phase = 2

         if evilrobo_phase == 2:
            screen.blit(evilrobo_mascot, (int(epos_x - camera_x), int(epos_y - camera_y)))
            if player_y > -300:
                evilrobo_txt3 = in_game.get("evilrobo3", "WHERE DID HE GO????")
                confused_text = menu_ui.render_text(evilrobo_txt3, True, (82, 0, 0))
                screen.blit(confused_text, ((epos_x - camera_x), (epos_y - camera_y - 40)))
                if not unlock:
                    unlock = True
                    unlock_time = pygame.time.get_ticks()
            epos_x -= 12

         if unlock and unlock_time is not None:
            achievements.evilchase()
            unlock_time = None

        evilrobo_rect = pygame.FRect(int(epos_x), int(epos_y), evilrobo_mascot.get_width(), evilrobo_mascot.get_height())
        
        if player_rect.colliderect(evilrobo_rect) and lights_off:
            evilrobo_phase = 0
            velocity_y = 0
            epos_x, epos_y = espawn_x, espawn_y
            player_x, player_y = spawn_x, spawn_y
            screen.fill((255, 255, 255))
            stamina = False
            if not manage_data.is_mute:
                manage_data.sounds['hit'].play()
            deathcount += 1

        if player_x > 4800 and player_y < -300 and not lights_off and evilrobo_phase == 2:
            epos_x = 4799
            epos_y = player_y
            screen.blit(evilrobo_mascot, ((epos_x - camera_x), (epos_y - camera_y)))
            if player_rect.colliderect(evilrobo_rect):
                evilrobo_phase = 0
                screen.fill((255, 255, 255))
                epos_x, epos_y = espawn_x, espawn_y
                player_x, player_y = spawn_x, spawn_y
                stamina = False
                lights_off = True
                if not manage_data.is_mute:
                    manage_data.sounds['hit'].play()

        screen.blit(rendered_button4_text, (-320 - camera_x, 300 - camera_y))

        level_player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_get_medal(11, current_time)
        level_draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        level_death_message(screen, death_text, wait_time, duration=2500)
        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update()

def create_lvl12_screen(screen, transition):
    global player_img, font, complete_levels, current_time, medal, deathcount, score
    global new_hs, hs, stars

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    new_hs = False
    menu_ui.buttons.clear()
    screen.blit(manage_data.bgs['mech'], (0, 0))

    in_game = manage_data.load_language().get('in_game', {})

    wait_time = None
    death_text = None
    start_time = time.time()

    # Camera settings
    camera_x = 0
    camera_y = -500
    spawn_x, spawn_y =  100, 0
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21

    # Gravity menu_ui.buttons
    strong_jump_strength = 15
    strong_grav = False
    weak_grav_strength = 37
    weak_grav = False
    
    # Speed settings
    move_speed = 8
    stamina = False
    stamina_speed = 19
    velocity_x = move_speed

    # Other settings
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False

    # Draw flag
    flag = pygame.FRect(3900, 200, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag_1_x, flag_1_y = 3900, 200

    gravity_strongers = [
        (3800, 250, 30, (204, 102, 204)),  # Strong gravity button
    ]

    gravity_weakers = [
        (5000, 700, 30, (0, 102, 204)),
    ]

    key_block_pairs_timed = [
        {
            "key": (300, 100, 30, (255, 119, 0)),
            "block": pygame.FRect(1900, 0, 100, 200),
            "collected": False,
            "duration": 5000,  # Duration for which the block is active
            "locked_time": None
        },
        {
            "key": (4000, 250, 30, (255, 119, 0)),
            "block": pygame.FRect(4150, 400, 50, 250),
            "collected": False,
            "duration": 3500,  # Duration for which the block is active
            "locked_time": None
        }
    ]

    blocks = [
        pygame.FRect(0, 200, 2000, 100),
        pygame.FRect(1900, -1000, 100, 1000),
        pygame.FRect(3200, -50, 800, 100),
        pygame.FRect(3600, 300, 500, 100),
        pygame.FRect(4100, -700, 101, 1100),
        pygame.FRect(3450, 650, 1000, 100),
        pygame.FRect(3350, 0, 100, 750),
        pygame.FRect(2300, 200, 150, 100),
        pygame.FRect(2600, 20, 200, 100),
        pygame.FRect(4500, 750, 600, 200),
    ]

    jump_blocks = [
        pygame.FRect(3000, 250, 100, 100),
        pygame.FRect(4300, 550, 100, 100),
    ]

    moving_saws = [ 
        {'r': 70, 'speed': 4, 'cx': 800, 'cy': 0, 'max': 500, 'min': -100},
        {'r': 70, 'speed': 5, 'cx': 1400, 'cy': 300, 'max': 600, 'min': 0},
    ]

    moving_saws_x = [
        {'r': 95, 'speed': 6, 'cx': 3350, 'cy': -50, 'min': 3300, 'max': 3900},
    ]

    saws = [
        (4600, 550, 80, (255, 0, 0)),
    ]

    spikes = [
    [(1000, 200), (1050, 150), (1100, 200)],
    [(2710, 20), (2755, -30), (2800, 20)],
    [(3600, 300), (3650, 250), (3700, 300)],
    [(3650, 650), (3700, 600), (3750, 650)],
    [(3900, 650), (3950, 600), (4000, 650)]
    ]

    exit_portal = pygame.FRect(4080, -910, 140, 180)
    clock = pygame.time.Clock()

    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)

    timed_coin_text_2 = in_game.get("timed_coin_message_2", "time. Run before they close again, or at worst, crush you...")
    rendered_timed_text_2 = menu_ui.render_text(timed_coin_text_2, True, (255, 128, 0))

    timed_coin_text = in_game.get("timed_coin_message", "Orange coins are timed! They open blocks for a limited")
    rendered_timed_text = menu_ui.render_text(timed_coin_text, True, (255, 128, 0))

    if not transition.active:
      while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            lights_off = True
            stamina = False
            weak_grav = False
            strong_grav = False
            checkpoint_reached = False  # Reset checkpoint status
            spawn_x, spawn_y = 100, 0
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["locked_time"] = None  # Reset the timer for all key blocks

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                state.handle_action("quit", transition, manage_data.current_page)

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if strong_grav:
                velocity_y = -strong_jump_strength
            elif weak_grav:
                velocity_y = -weak_grav_strength
            else:
                velocity_y = -jump_strength
            if not manage_data.is_mute:
                manage_data.sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                if stamina:
                    velocity_x = stamina_speed
                    player_x -= velocity_x
                else:
                    velocity_x = move_speed
                    player_x -= velocity_x
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if stamina:
                    velocity_x = stamina_speed
                    player_x += velocity_x
                else:
                    velocity_x = move_speed
                    player_x += velocity_x

            if on_ground and not was_moving and not manage_data.is_mute:
                manage_data.sounds['move'].play()
            was_moving = True
        else:
            was_moving = False

        # Gravity and stamina
        if not on_ground:
            velocity_y += gravity
        player_y += velocity_y

        # Collisions and Ground Detection
        player_rect = pygame.FRect(player_x, player_y, img_width, img_height)
        on_ground = False

        player_rect = pygame.FRect(player_x, player_y, img_width, img_height)

        # Checkpoint logic
        if player_rect.colliderect(flag) and not checkpoint_reached:
            checkpoint_reached = True
            stamina = False  # Reset stamina status
            weak_grav = False
            strong_grav = False
            spawn_x, spawn_y = 3900, 150  # Store checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag

        # Exit portal
        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_fin_lvl_logic(current_time, deathcount, medal, 12)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)
            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            
            state.handle_action('quit', transition, manage_data.current_page)
            running = False  

        # Draw flag
        if checkpoint_reached:
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle for active checkpoint
        else:
            pygame.draw.rect(screen, (255, 215, 0), flag.move(-camera_x, -camera_y))  # Gold rectangle for inactive checkpoint

        # Drawing
        screen.blit(manage_data.bgs['mech'], (0, 0))

        if checkpoint_reached:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))

        # Handle Moving Saws
        if level_handle_moving_saws(screen, moving_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_handle_moving_saws_x(screen, moving_saws_x, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            weak_grav = False
            strong_grav = False
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["locked_time"] = None  # Reset the timer for all key blocks

        level_draw_saws(screen, saws, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache)

        # 2. Check for saw deaths
        if level_check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1
            strong_grav = False
            weak_grav = False
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["locked_time"] = None  # Reset the timer for all key blocks

        player_x, player_y, velocity_y = level_jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], strong_grav, weak_grav)
        level_draw_spikes(screen, spikes, camera_x, camera_y)

        player_x, player_y, velocity_y, on_ground, player_rect = level_block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 
                strong_grav = False
                weak_grav = False
                for pair in key_block_pairs_timed:
                    pair["collected"] = False  # Reset the collected status for all keys
                    pair["locked_time"] = None  # Reset the timer for all key blocks

        level_draw_portal(screen, manage_data.assets['mech_exit'], exit_portal, camera_x, camera_y)

        screen.blit(rendered_timed_text, (0 - camera_x, -80 - camera_y))
        screen.blit(rendered_timed_text_2, (-20 - camera_x, -30 - camera_y))
        
        if level_handling_gravity_strongers(screen, gravity_strongers, player_rect, camera_x, camera_y, strong_grav):
            strong_grav = True
            weak_grav = False

        if level_handling_gravity_weakers(screen, gravity_weakers, player_rect, camera_x, camera_y, weak_grav):
            strong_grav = False
            weak_grav = True

        is_crushed, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y, on_ground = level_handle_key_blocks_timed(screen, key_block_pairs_timed, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y, on_ground)
        if is_crushed:
            if not manage_data.is_mute:
                manage_data.sounds['hit'].play()
            deathcount += 1
            stamina = False  # Reset stamina status
            weak_grav = False
            strong_grav = False
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["locked_time"] = None  # Reset the timer for all key blocks
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0  # Reset vertical speed
            wait_time = pygame.time.get_ticks()  # Start the wait time
            death_text = menu_ui.render_text(in_game.get("crushed_message", "Crushed!"), True, (255, 0, 0))

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_get_medal(12, current_time)
        level_draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        level_draw_spikes(screen, spikes, camera_x, camera_y)

        if level_check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1
            strong_grav = False
            weak_grav = False
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["locked_time"] = None  # Reset the timer for all key blocks

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()  # Start the wait time
            weak_grav = False
            strong_grav = False
            for pair in key_block_pairs_timed:
                pair["collected"] = False  # Reset the collected status for all keys
                pair["locked_time"] = None  # Reset the timer for all key blocks
            if not manage_data.is_mute:    
                manage_data.sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

        # Player Image
        level_player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        level_death_message(screen, death_text, wait_time, duration=2500)
        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update() 
