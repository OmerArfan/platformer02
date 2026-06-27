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
    player.init_x, player.init_y = player_data['spawn_x'], player_data['spawn_y']
    player.spawn_x, player.spawn_y = player.init_x, player.init_y
    
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
    cacti_spikes = []
    for spike in level_data.get('cacti_spikes', []):
        cacti_spikes.append({
            'def_cord': spike['cord'],
            'cord': spike['cord'],
            'axis': spike['axis'],
            'dir': spike['dir'],
            'limit': spike['limit'],
            'activated': False,
            'cycle_complete': True,
            'init_speed': 6 * spike['dir'],
            'speed': 6 * spike['dir'],
            'acc': 0.3 * spike['dir']
        })
    
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

    key_block_pairs_timed = []
    for kbp in level_data.get('key_block_pairs_timed', []):
        # Handle the Boolean Fix (String to Bool)
        collected_raw = kbp.get('collected', False)
        if isinstance(collected_raw, str):
            is_collected = collected_raw.lower() == "true"
        else:
            is_collected = bool(collected_raw)

        # Transform raw data into Game-Ready data
        key_block_pairs_timed.append({
            'key': kbp['key'],  # This stays a dict with x, y, radius, color
            'block': pygame.FRect(kbp['block']['x'], kbp['block']['y'], kbp['block']['w'], kbp['block']['h']),
            'collected': is_collected,
            'duration': kbp['duration'],
            'locked_time': kbp['locked_time']
        })

    saws = level_data.get('saws', [])
    hazards.pre_render_saws(manage_data.assets['saw'], saws)

    lasers = [pygame.FRect(laser['x'], laser['y'], laser['w'], laser['h']) for laser in level_data.get('lasers', [])]

    # Flags/Checkpoints
    # Ensure flags are dicts and append status/rect safely
    raw_flags = level_data.get('flags', [])
    flags = []
    for f in raw_flags:
        if isinstance(f, dict) and all(k in f for k in ('x', 'y', 'w', 'h')):
            new_f = f.copy()
            new_f['status'] = 'unused'
            new_f['rect'] = pygame.FRect(new_f['x'], new_f['y'], new_f['w'], new_f['h'])
            flags.append(new_f)
        else:
            print(f"Skipping invalid flag entry: {f}")

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
            
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, manager.medal, stars)
            
            manage_data.save_progress(manage_data.progress, manage_data.manifest)
            
            next_page = level_data.get('next_page')
            state.handle_action(next_page, transition, manage_data.current_page)
            
            running = False
        
        # === UPDATE PLAYER INPUT & VELOCITY (BEFORE collisions) ===
        player.update(keys, manager, rendered_fall_text, key_block_pairs, key_block_pairs_timed)
        
        # === RENDER ===
        screen.blit(background, (0, 0))

        player, flags = env.handle_flags(screen, flags, player)

        # Draw spikes
        hazards.draw_spikes(screen, spikes, player)

        if hazards.handle_cacti_spikes(screen, player, cacti_spikes):
            player.die()
            manager.death_text = menu_ui.render_text(in_game.get("cacti_message", "Prickled!"), True, (255, 0, 0))
            manager.wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            for kbp in key_block_pairs: 
                kbp['collected'] = False
            for kbp in key_block_pairs_timed: 
                kbp['collected'] = False
                
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
            for kbp in key_block_pairs_timed: 
                kbp['collected'] = False

        if hazards.handle_lasers(screen, lasers, player):
            player.die()
            manager.death_text = menu_ui.render_text(in_game.get("laser_message", "Lasered!"), True, (255, 0, 0))
            manager.wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['laser'].play()
            for kbp in key_block_pairs: 
                kbp['collected'] = False
            for kbp in key_block_pairs_timed: 
                kbp['collected'] = False

        # === PHYSICS: BLOCK COLLISIONS ===
        player, moving_blocks = blockmgr.handle_moving_blocks(screen, moving_blocks, player)

        player = blockmgr.handle_blocks(screen, blocks, player)

        player = blockmgr.handle_jump_blocks(screen, jump_blocks, player)

        player = blockmgr.handle_key_blocks(screen, key_block_pairs, player)

        player = blockmgr.handle_key_blocks_timed(screen, key_block_pairs_timed, player)

        player = env.handle_teleports(screen, teleporters, player)   

        # moving_blocks is a list of dicts; pass a list of their rects to the collision helper
        moving_rects = [mb['rect'] for mb in moving_blocks]
        if blockmgr.handle_bottom_collisions(blocks, player) or blockmgr.handle_bottom_collisions(moving_rects, player) or blockmgr.handle_bottom_collisions(jump_blocks, player):
            player.die()
            manager.death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
            manager.wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['hit'].play()
            for kbp in key_block_pairs: 
                kbp['collected'] = False
            for kbp in key_block_pairs_timed: 
                kbp['collected'] = False

        # Death if got inside a locked block (or if crushed in general)
        if player.crushed:
            player.die()
            manager.death_text = menu_ui.render_text(in_game.get("crushed_message", "Crushed!"), True, (255, 0, 0))
            manager.wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['hit'].play()
            for kbp in key_block_pairs: 
                kbp['collected'] = False
            for kbp in key_block_pairs_timed: 
                kbp['collected'] = False

        # Spike collisions
        if hazards.check_spike_collisions(spikes, player):
            player.die()
            manager.death_text = menu_ui.render_text(in_game.get("dead_message", "You Died!"), True, (255, 0, 0))
            manager.wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            for kbp in key_block_pairs: 
                kbp['collected'] = False
            for kbp in key_block_pairs_timed: 
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
            for kbp in key_block_pairs_timed: 
                kbp['collected'] = False
            for flag in flags:
                flag['status'] = 'unused'
        
        # Update Player sprite
        player.sprite.draw(screen, player, keys, manager)

        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update()

# IMPORTANT!
# ANYTHING BELOW THIS IS OLD, LEGACY CODE WHICH WILL GET PHASED OUT AS TIME GOES ON.