import pygame
import menu_ui
import random
import time
import manage_data
import level_logic
import state

def create_lvl1_screen(screen, transition):
    global player_img, current_time, medal, deathcount
    global new_hs, ctime
    global x, y, camera_x, camera_y, player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text,spawn_x, spawn_y,  player_rect, on_ground

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    new_hs = False

    menu_ui.buttons.clear()
    screen.blit(manage_data.bgs['green'], (0, 0))
    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

    wait_time = None
    death_text = None
    start_time = time.time()

    # Camera settings
    camera_x = 0  
    camera_y = 0
    player_x, player_y = 600, 200
    spawn_x, spawn_y = player_x, player_y
    running = True
    gravity = 1
    jump_strength = 20
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.05
    deathcount = 0
    was_moving = False

    blocks = [
        pygame.Rect(600, 450, 200, 50),
        pygame.Rect(1000, 400, 200, 50),
        pygame.Rect(1700, 300, 200, 50),
        pygame.Rect(2100, 300, 200, 50),
        pygame.Rect(2500, 250, 500, 50),
        pygame.Rect(1850, 400, 320, 50),
    ]

    moving_block = pygame.Rect(1300, 300, 100, 20)
    moving_direction1 = 1
    moving_speed = 2
    moving_limit_left1 = 1300
    moving_limit_right1 = 1500

    spikes = [
        [(1850, 400), (1900, 350), (1950, 400)],
        [(1960, 400), (2010, 350), (2060, 400)],
        [(2070, 400), (2120, 350), (2170, 400)],
        [(2650, 250), (2700, 200), (2750, 250)],
    ]

    exit_portal = pygame.Rect(2780, 60, 140, 180)
    clock = pygame.time.Clock()

    # Render the texts
    warning_text = in_game.get("warning_message", "Watch out for spikes!")
    rendered_warning_text = menu_ui.render_text(warning_text, True, (255, 0, 0))  # Render the warning text

    up_text = in_game.get("up_message", "Press UP to Jump!")
    rendered_up_text = menu_ui.render_text(up_text, True, (0, 0, 0))  # Render the up text

    exit_text = in_game.get("exit_message", "Exit Portal! Come here to win!")
    rendered_exit_text = menu_ui.render_text(exit_text, True, (0, 73, 0))  # Render the exit text

    moving_text = in_game.get("moving_message", "Not all blocks stay still...")
    rendered_moving_text = menu_ui.render_text(moving_text, True, (128, 0, 128))  # Render the moving text

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text

    pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

    level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)
    
    screen.blit(rendered_up_text, (700 - camera_x, 200 - camera_y))  # Draws the rendered up text
    screen.blit(rendered_warning_text, (1900 - camera_x, 150 - camera_y))  # Draws the rendered warning text
    screen.blit(rendered_moving_text, (1350 - camera_x, 170 - camera_y))  # Draws the rendered moving text
    screen.blit(rendered_exit_text, (2400 - camera_x, 300 - camera_y))  # Draws the rendered exit text

    for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)

    if not transition.active:
       while running:
        clock.tick_busy_loop(60)
        keys = pygame.key.get_pressed()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                state.handle_action("quit", transition, manage_data.current_page)

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not manage_data.is_mute:
                manage_data.sounds['jump'].play()
        

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
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

        # Moving blocks
        moving_block.x += moving_speed * moving_direction1
        if moving_block.x < moving_limit_left1 or moving_block.x > moving_limit_right1:
            moving_direction1 *= -1

        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        if player_y > 1100:
            player_x, player_y = 600, 200
            death_text = rendered_fall_text
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['fall'].play()
            velocity_y = 0
            deathcount += 1

        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 1)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)
            
            manage_data.Achievements.lvl1speed(current_time)
            manage_data.Achievements.check_green_gold()

            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            state.handle_action('lvl2_screen', transition, manage_data.current_page)
            
            running = False
            

        screen.blit(manage_data.bgs['green'], (0, 0))

        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))
    
        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)

        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1

        if player_rect.colliderect(moving_block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= moving_block.y:
                    player_y = moving_block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > moving_block.x and player_x < moving_block.x + moving_block.width:
                    if player_x < moving_block.x:  # Colliding with the left side of the block
                        player_x = moving_block.x - img_width
                    elif player_x + img_width > moving_block.x + moving_block.width:  # Colliding with the right side
                        player_x = moving_block.x + moving_block.width

        level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)

        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        # Inside the game loop:
        screen.blit(rendered_up_text, (700 - camera_x, 200 - camera_y))  # Draws the rendered up text
        screen.blit(rendered_warning_text, (1900 - camera_x, 150 - camera_y))  # Draws the rendered warning text
        screen.blit(rendered_moving_text, (1350 - camera_x, 170 - camera_y))  # Draws the rendered moving text
        screen.blit(rendered_exit_text, (2400 - camera_x, 300 - camera_y))  # Draws the rendered exit text


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

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(1, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        if keys[pygame.K_r]:
        #    resetting()
         #   if  time.time() - ctime > 3:
                ctime = None
                start_time = time.time()
                current_time = 0
                spawn_x, spawn_y = 600, 200
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                velocity_y = 0
                deathcount = 0
          #  else:
           #     countdown = max(0, 3 - round(time.time() - ctime, 2))
             #   reset_text = menu_ui.render_text(f"Resetting the level in {countdown:.2f}", True, (255, 0, 0))
            #    screen.blit(reset_text, (manage_data.SCREEN_WIDTH // 2 - 200 , 300))             
        #else:
         #   ctime = None

        level_logic.death_message(screen, death_text, wait_time, duration=2500)

        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)

        pygame.display.update()    

def create_lvl2_screen(screen, transition):
    global player_img, complete_levels, wait_time, transition_time, is_transitioning, current_time, medal, deathcount, score
    global new_hs, hs, stars, ctime
    global x, y, camera_x, camera_y, spawn_x, spawn_y,  player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    new_hs = False

    screen.blit(manage_data.bgs['green'], (0, 0))
    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

    wait_time = None
    death_text = None
    start_time = time.time()

    camera_x = 0  
    camera_y = 0
    player_x, player_y = 150, 500
    spawn_x, spawn_y = player_x, player_y  # Set the spawn point
    running = True
    gravity = 1
    jump_strength = 20
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.05
    deathcount = 0
    was_moving = False

    # Draw flag
    flag = pygame.Rect(2150, 650, 80, 50)  # x, y, width, height
    checkpoint_reached = False
    flag_1_x, flag_1_y = 2150, 650

    blocks = [
        pygame.Rect(100, 650, 1000, 50),
        pygame.Rect(500, 500, 200, 50),
        pygame.Rect(1900, 200, 200, 50),
        pygame.Rect(2080, 750, 620, 50),        
        pygame.Rect(2150, 530, 300, 50),
        pygame.Rect(2340, 50, 110, 500),
        pygame.Rect(2900, 450, 400, 50),
        pygame.Rect(3300, 650, 260, 50),
        pygame.Rect(3800, 650, 220, 50),
        pygame.Rect(4260, 650, 220, 50),
        pygame.Rect(3300, 200, 1300, 50),
    ]

    jump_blocks = [
        pygame.Rect(1000, 550, 100, 100), # Jump blocks to help the character go up and then fall down
        pygame.Rect(2730, 751, 100, 100),
        pygame.Rect(3600, 645, 160, 100),
        pygame.Rect(4060, 645, 160, 100),
    ]

    moving_block = pygame.Rect(1500, 300, 100, 20)
    moving_direction1 = 1
    moving_speed = 2
    moving_limit_left1 = 1300
    moving_limit_right1 = 1700

    spikes = [
        [(350, 650), (400, 600), (450, 650)],
        [(460, 650), (510, 600), (560, 650)],
        [(570, 650), (620, 600), (670, 650)],
        [(680, 650), (730, 600), (780, 650)],
        [(790, 650), (840, 600), (890, 650)],
        [(900, 650), (950, 600), (1000, 650)],
        [(2040, 200), (2070, 150), (2100, 200)],
        [(3100, 450), (3135, 400), (3170, 450)],
        [(3300, 250), (3350, 300), (3400, 250)],
        [(3400, 250), (3450, 300), (3500, 250)],
        [(3500, 250), (3550, 300), (3600, 250)],
        [(3600, 250), (3650, 300), (3700, 250)],
        [(3700, 250), (3750, 300), (3800, 250)],
        [(3800, 250), (3850, 300), (3900, 250)],
        [(3900, 250), (3950, 300), (4000, 250)],
        [(4000, 250), (4050, 300), (4100, 250)],
        [(4100, 250), (4150, 300), (4200, 250)],
        [(4200, 250), (4250, 300), (4300, 250)],
        [(4300, 250), (4350, 300), (4400, 250)],
        [(4400, 250), (4450, 300), (4500, 250)],
        [(4500, 250), (4550, 300), (4600, 250)],        
        ]

    exit_portal = pygame.Rect(4330, 460, 140, 180)
    clock = pygame.time.Clock()
    
    # Render the texts
    jump_message = in_game.get("jump_message", "Use orange blocks to jump high distances!")
    rendered_jump_text = menu_ui.render_text(jump_message, True, (255, 128, 0))  # Render the jump text

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text

    if checkpoint_reached:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))



    pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

    for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (jump_block.x - camera_x, jump_block.y - camera_y, jump_block.width, jump_block.height))

    level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)

            # Inside the game loop:
    screen.blit(rendered_jump_text, (900 - camera_x, 500 - camera_y))  # Draws the rendered up text

    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)

    if not transition.active:
      while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            current_time = 0
            checkpoint_reached = False  # Reset checkpoint status
            spawn_x, spawn_y = 150, 500
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                state.handle_action("quit", transition, manage_data.current_page)

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not manage_data.is_mute:
                manage_data.sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
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

        # Moving blocks
        moving_block.x += moving_speed * moving_direction1
        if moving_block.x < moving_limit_left1 or moving_block.x > moving_limit_right1:
            moving_direction1 *= -1


        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        if player_y > 1100:
                death_text = rendered_fall_text
                if not manage_data.is_mute:
                    manage_data.sounds['fall'].play()
                wait_time = pygame.time.get_ticks()
                player_x, player_y = spawn_x, spawn_y
                velocity_y = 0
                deathcount += 1

        # Exit portal
        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 2)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)
            
            manage_data.Achievements.check_green_gold()

            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            
            state.handle_action('lvl3_screen', transition, manage_data.current_page)
            running = False

        # Drawing
        screen.blit(manage_data.bgs['green'], (0, 0))

        if player_rect.colliderect(flag) and not checkpoint_reached:
            checkpoint_reached = True
            spawn_x, spawn_y = 2150, 620  # Store checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            
        if checkpoint_reached:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 
        
        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], False, False)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1
        
        if player_rect.colliderect(moving_block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= moving_block.y:
                    player_y = moving_block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > moving_block.x and player_x < moving_block.x + moving_block.width:
                    if player_x < moving_block.x:  # Colliding with the left side of the block
                        player_x = moving_block.x - img_width
                    elif player_x + img_width > moving_block.x + moving_block.width:  # Colliding with the right side
                        player_x = moving_block.x + moving_block.width

        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

        level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        screen.blit(rendered_jump_text, (900 - camera_x, 500 - camera_y))  # Draws the rendered up text

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

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(2, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        if keys[pygame.K_r]:
                ctime = None
                start_time = time.time()
                current_time = 0
                spawn_x, spawn_y = 150, 500
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                velocity_y = 0
                deathcount = 0
        
        level_logic.death_message(screen, death_text, wait_time, duration=2500)

        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)

        pygame.display.update()    

def create_lvl3_screen(screen, transition):
    global player_img, font, complete_levels, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global x, y, camera_x, camera_y, spawn_x, spawn_y,  player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    new_hs = False
    screen.blit(manage_data.bgs['green'], (0, 0))
    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

    # Camera settings
    camera_x = 0  
    camera_y = 0
    spawn_x, spawn_y = 150, 600
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False

    # Draw flag
    flag = pygame.Rect(200, 200, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(2080, -260, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 200, 200
    flag_2_x, flag_2_y = 2080, -260

    key_block_pairs = [
        {
            "key": (250, 175, 30, (255, 255, 0)),
            "block": pygame.Rect(2550, 250, 200, 200),
            "collected": False
        },
    ]

    saws = [
        (620, 750, 80,(255, 0, 0)),  # (x, y, radius, color)
        (1700, 335, 100,(255, 0, 0)),  # (x, y, radius, color)
        (1200, 335, 100,(255, 0, 0)),
        (800, 335, 100,(255, 0, 0)),
        (1850, -170, 80,(255, 0, 0)),
        (1550, -400, 80,(255, 0, 0)),
        (1250, -400, 80,(255, 0, 0)),
        (950, -170, 80,(255, 0, 0)),
    ]

    blocks=[
        pygame.Rect(-1500, 906, 900, 100),
        pygame.Rect(100, 750, 2000, 900),
        pygame.Rect(100, 300, 2000, 50),
        pygame.Rect(100, -150, 2200, 50),
        pygame.Rect(-900, -360, 1000, 9000),
        pygame.Rect(1220, -425, 360, 50),
    ]

    jump_blocks = [
        pygame.Rect(950, 700, 100, 50), # Jump blocks to help the character go up and then fall down
        pygame.Rect(2300, 751, 100, 100),
        pygame.Rect(2600, 285, 120, 100),
    ]

    spikes = [
    [(900, 350), (950, 400), (1000, 350)],
    [(1000, 350), (1050, 400), (1100, 350)],
    [(2000, 750), (2050, 700), (2100, 750)],
    ]

    exit_portal = pygame.Rect(430, -350, 140, 180)
    clock = pygame.time.Clock()

    saw_text = in_game.get("saws_message", "Saws are also dangerous!")
    rendered_saw_text = menu_ui.render_text(saw_text, True, (255, 0, 0))  # Render the saw text

    key_text = in_game.get("key_message", "Grab the coin and open the block!")
    rendered_key_text = menu_ui.render_text(key_text, True, (255, 255, 0))  # Render the key text

    # Drawing
    screen.blit(manage_data.bgs['green'], (0, 0))

    screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
        # Draw all saws first
    for x, y, r, color in saws:
            saw_ig_img = pygame.transform.scale(manage_data.assets['saw'], (int(r*2), int(r*2)))
            screen.blit(saw_ig_img, (int(x - r - camera_x), int(y - r - camera_y)))

    for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

    for spike in spikes:
            pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    for pair in key_block_pairs:
        key_x, key_y, key_r, key_color = pair["key"]
        block = pair["block"]
        pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)
        pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

    level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)

    # Draw the texts
    screen.blit(rendered_saw_text, (int(550 - camera_x), int(600 - camera_y)))  # Draws the rendered up text
    screen.blit(rendered_key_text, (int(2500 - camera_x), int(200 - camera_y)))  # Draws the rendered up text

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text

    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)

    if not transition.active:
      while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            current_time = 0
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 150, 600
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                state.handle_action("quit", transition, manage_data.current_page)

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not manage_data.is_mute:
                manage_data.sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
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

        # Moving blocks

        # Collisions and Ground Detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        if player_y > 1100:
                death_text = rendered_fall_text
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:
                    manage_data.sounds['fall'].play()
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                velocity_y = 0
                deathcount += 1

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 200, 100  # Store checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            spawn_x, spawn_y = 2100, -400  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 3)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)
            
            manage_data.Achievements.check_green_gold()

            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            
            state.handle_action('lvl4_screen', transition, manage_data.current_page)
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
        screen.blit(manage_data.bgs['green'], (0, 0))

        if checkpoint_reached:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
        # Draw all saws first
        level_logic.draw_saws(screen, saws, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)

        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                key_block_pairs[0]["collected"] = False  # Reset key block status
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], False, False)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1
            
        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.handle_key_blocks(screen, manage_data.sounds['open'], key_block_pairs, manage_data.is_mute, on_ground, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y)

        level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        # Draw the texts
        screen.blit(rendered_saw_text, (int(550 - camera_x), int(600 - camera_y)))  # Draws the rendered up text
        screen.blit(rendered_key_text, (int(2500 - camera_x), int(200 - camera_y)))  # Draws the rendered up text

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

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(3, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)

        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)

        pygame.display.update()    

def create_lvl4_screen(screen, transition):
    global player_img, font, complete_levels, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global x, y, camera_x, camera_y, spawn_x, spawn_y,  player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    new_hs = False
    menu_ui.buttons.clear()
    screen.blit(manage_data.bgs['green'], (0, 0))
    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

    # Camera settings
    camera_x = 0  
    camera_y = 0
    spawn_x, spawn_y = 250, 450
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    saw_angle = 0

    # Draw flag
    flag = pygame.Rect(1500, 550, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(3200, 120, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 1500, 550
    flag_2_x, flag_2_y = 3200, 120

    key_block_pairs = [
        {
            "key": (3820, -130, 30, (255, 255, 0)),
            "block": pygame.Rect(2800, 30, 200, 200),
            "collected": False
        },
    ]

    moving_blocks = [
        {
        'rect': pygame.Rect(4050, 450, 100, 20),
        'axis': 'x',  # 'x' for horizontal, 'y' for vertical
        'speed': 2,
        'min': 4050,
        'max': 4350
        },
        {
        'rect': pygame.Rect(4850, 450, 100, 20),
        'axis': 'x',
        'speed': 2,
        'min': 4550,
        'max': 4850
        },
    ]

    lasers = [
        pygame.Rect(3000, -50, 1000, 15),
    ]

    blocks = [
        pygame.Rect(200, 650, 650, 100),
        pygame.Rect(1100, 510, 100, 100),
        pygame.Rect(1450, 650, 650, 100),
        pygame.Rect(2300, 230, 1000, 1800),
        pygame.Rect(2800, 400, 1200, 1600),
        pygame.Rect(2800, -370, 200, 400),
        pygame.Rect(3100, -300, 450, 100),
        pygame.Rect(3700, -100, 200, 100),
        pygame.Rect(4000, -370, 200, 400),
    ]

    moving_saws = [ 
        {'r': 100, 'speed': 5, 'cx': 3800, 'cy': -300, 'max': -50, 'min': -700},
    ]

    saws = [
        (650, 630, 80,(255, 0, 0)),  # (x, y, radius, color)
        (2520, 230 , 90,(255, 0, 0)),
        (3320, 400, 100,(255, 0, 0)),  # (x, y, radius, color)
        (4950, 150, 100,(255, 0, 0)),  # (x, y, radius, color)
        (4950, 550, 100,(255, 0, 0)),  # (x, y, radius, color)
        (4500, 425, 60, (255, 0, 0)),  # (x, y, radius, color)
    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 90, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 180, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 270, 'speed': 2, "block": 1},
    ]


    jump_blocks = [
        pygame.Rect(2200, 751, 100, 100),
        pygame.Rect(2400, 130, 120, 100),
        
    ]

    spikes = [
    [(2000, 650), (2050, 600), (2100, 650)],
    [(3300,-300), (3350, -350), (3400, -300)],
    [(3800, 400), (3850, 350), (3900, 400)],
    [(3900, 400), (3950, 350), (4000, 400)],
    ]
    exit_portal = pygame.Rect(4870, 265, 140, 180)
    clock = pygame.time.Clock()

    # Drawing
    screen.blit(manage_data.bgs['green'], (0, 0))

    screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))

    for x, y, r, color in saws:
        scale_factor = (r * 2.5) / manage_data.assets['saw'].get_width()
        rotated_saw = pygame.transform.rotozoom(manage_data.assets['saw'], saw_angle, scale_factor)
        rect = rotated_saw.get_rect(center=(int(x - camera_x), int(y - camera_y)))
        screen.blit(rotated_saw, rect)

        # Draw all lasers first
    for laser in lasers:
        pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for jump_block in jump_blocks:
        pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text
        
    for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]
            pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)
            pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

    for block in moving_blocks:
        rect = block['rect']
        axis = block['axis']
        speed = block['speed']
        pygame.draw.rect(screen, (128, 0, 128), rect.move(-camera_x, -camera_y))


    level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)

    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)
    
    if not transition.active:
       while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 250, 450
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                state.handle_action("quit", transition, manage_data.current_page)

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not manage_data.is_mute:
                manage_data.sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
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
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in moving_blocks:
            rect = block['rect']
            axis = block['axis']
            speed = block['speed']

    # Update the block's position
            if axis == 'x':
                rect.x += speed
                if rect.x < block['min'] or rect.x > block['max']:
                    block['speed'] = -speed  # Reverse direction
            elif axis == 'y':
                rect.y += speed
                if rect.y < block['min'] or rect.y > block['max']:
                    block['speed'] = -speed  # Reverse direction

    # Check if the player is standing on the block
            
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
            death_text = rendered_fall_text
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 1500, 500  # Store checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3150, 100  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 4)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)
            
            manage_data.Achievements.check_green_gold()

            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            
            state.handle_action('lvl5_screen', transition, manage_data.current_page)
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
        screen.blit(manage_data.bgs['green'], (0, 0))

        if checkpoint_reached:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        
        # Draw key only if not collected
 
         # Draw all lasers first
        for laser in lasers:
            pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))
            # Check if the player collides with the laser
            if player_rect.colliderect(laser):
                # Trigger death logic
                player_x, player_y = spawn_x, spawn_y
                death_text = menu_ui.render_text(in_game.get("laser_message", "Lasered!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:
                    manage_data.sounds['laser'].play()
                velocity_y = 0
                deathcount += 1
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

# Saw collision detection and drawing
        if level_logic.handle_rotating_saws(screen, rotating_saws, blocks, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False
        
        level_logic.draw_saws(screen, saws, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.handle_key_blocks(screen, manage_data.sounds['open'], key_block_pairs, manage_data.is_mute, on_ground, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y)

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)

        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                key_block_pairs[0]["collected"] = False  # Reset key block status
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], False, False)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False
        
        for block in moving_blocks:
            rect = block['rect']
            axis = block['axis']
            speed = block['speed']

            if axis == 'x':
                rect.x += speed
                if rect.x < block['min'] or rect.x > block['max']:
                    block['speed'] = -speed  # Reverse direction
            elif axis == 'y':
                rect.y += speed
                if rect.y < block['min'] or rect.y > block['max']:
                    block['speed'] = -speed  # Reverse direction

            # Draw the block
            pygame.draw.rect(screen, (128, 0, 128), rect.move(-camera_x, -camera_y))


        level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

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

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(4, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update()   

def create_lvl5_screen(screen, transition):
    global player_img, font, complete_levels, current_time, medal, deathcount, score
    global new_hs, hs, stars
    global x, y, camera_x, camera_y, spawn_x, spawn_y,  player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    new_hs = False
    menu_ui.buttons.clear()
    screen.blit(manage_data.bgs['green'], (0, 0))
    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

    # Camera settings
    camera_x = 0  
    camera_y = 0
    spawn_x, spawn_y = 20, 500
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    saw_angle = 0

    # Draw flag
    flag = pygame.Rect(2100, -150, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(3450, -450, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 2100, -150
    flag_2_x, flag_2_y = 3450, -450

    key_block_pairs = [
        {
            "key": (4250, -900, 30, (255, 255, 0)),
            "block": pygame.Rect(1300, -250, 200, 250),
            "collected": False
        },
    ]

    walls = [        
        pygame.Rect(2700, -310, 50, 91),
        pygame.Rect(2880, -310, 50, 140)
        ]

    blocks = [
        pygame.Rect(-50, 650, 860, 100),
        pygame.Rect(920, 510, 100, 100),
        pygame.Rect(1450, 650, 650, 100),
        pygame.Rect(1500, -50, 700, 50),
        pygame.Rect(1700, -350, 1050, 50),
        pygame.Rect(1500, -250, 50, 200),
        pygame.Rect(2700, -220, 200, 50),
        pygame.Rect(2880, -350, 700, 50),
        pygame.Rect(3900, -350, 100, 30),
        pygame.Rect(3900, -50, 100, 30),
        pygame.Rect(3900, -650, 100, 30),
        pygame.Rect(4200, -150, 100, 30),
        pygame.Rect(4200, -750, 100, 30),
        pygame.Rect(4200, -450, 100, 30),
        pygame.Rect(4500, -50, 100, 30),
        pygame.Rect(4500, -350, 100, 30),
        pygame.Rect(4500, -650, 100, 30),
        pygame.Rect(4800, -150, 100, 30),
        pygame.Rect(4800, -750, 100, 30),
        pygame.Rect(4800, -450, 100, 30),        
    ]
    
    moving_saws = [ 
        {'r': 100, 'speed': 6, 'cx': 1250, 'cy': 200, 'max': 700, 'min': 200},
    ]

    moving_saws_x = [
        {'r': 100, 'speed': 8, 'cx': 2400, 'cy': -500, 'max': 3300, 'min': 2400},
    ]

    saws = [
        (500, 630, 80,(255, 0, 0)),  # (x, y, radius, color)
        (2000, -360, 80,(255, 0, 0)),  # (x, y, radius, color)
        (2400, -360, 80,(255, 0, 0)),  # (x, y, radius, color)
    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 180, 'speed': 2, "block": 1},
    ]


    jump_blocks = [
        pygame.Rect(2200, 751, 100, 100),
        pygame.Rect(2570, 400, 100, 100),
    ]

    spikes = [
        [(1660, 650), (1710, 600), (1760, 650)],
        [(2000, 650), (2050, 600), (2100, 650)],
        [(3300,-350), (3350, -400), (3400, -350)],
        [(3900, -50), (3950, -100), (4000, -50)],
        [(3900, -650), (3950, -700), (4000, -650)],
        [(4200, -450), (4250, -500), (4300, -450)],
        [(4500, -50), (4550, -100), (4600, -50)],
        [(4800, -750), (4850, -800), (4900, -750)],
        [(4800, -150), (4850, -200), (4900, -150)],
        [(3900, -20), (3950, 30), (4000, -20)],
        [(3900, -320), (3950, -270), (4000, -320)],
        [(3900, -620), (3950, -570), (4000, -620)],
        [(4200, -120), (4250, -70), (4300, -120)],
        [(4200, -420), (4250, -370), (4300, -420)],
        [(4500, -20), (4550, 30), (4600, -20)],
        [(4500, -320), (4550, -270), (4600, -320)],
        [(4500, -620), (4550, -570), (4600, -620)],
        [(4800, -720), (4850, -670), (4900, -720)],
        [(4800, -420), (4850, -370), (4900, -420)],
        [(4800, -120), (4850, -70), (4900, -120)],
    ]

    exit_portal = pygame.Rect(1360, 20, 140, 180)
    clock = pygame.time.Clock()

    
    # Render the texts
    screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
    
    for x, y, r, color in saws:
        scale_factor = (r * 2.5) / manage_data.assets['saw'].get_width()
        rotated_saw = pygame.transform.rotozoom(manage_data.assets['saw'], saw_angle, scale_factor)
        rect = rotated_saw.get_rect(center=(int(x - camera_x), int(y - camera_y)))
        screen.blit(rotated_saw, rect)

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for jump_block in jump_blocks:
        pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]
            pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)
            pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

    level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text
    
    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)
    if not transition.active:
      while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 20, 500
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                state.handle_action("quit", transition, manage_data.current_page)

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not manage_data.is_mute:
                manage_data.sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
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
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in walls:
            if player_rect.colliderect(block):
                # Horizontal collision (left or right side of the block)
                if player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        if player_y > 1100:
            death_text = rendered_fall_text
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Saw collision detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2050, -200  # Store checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3450, -550  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 5)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)
            
            manage_data.Achievements.check_green_gold()

            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            
            state.handle_action('lvl6_screen', transition, manage_data.current_page)
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
        screen.blit(manage_data.bgs['green'], (0, 0))

        if checkpoint_reached:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        if level_logic.handle_rotating_saws(screen, rotating_saws, blocks, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False

        level_logic.draw_saws(screen, saws, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False 

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.handle_key_blocks(screen, manage_data.sounds['open'], key_block_pairs, manage_data.is_mute, on_ground, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y)
        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 
                key_block_pairs[0]["collected"] = False 

        for block in walls:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], False, False)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False 

        level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)
       
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

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

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(5, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)
        
        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        
        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update()   

def create_lvl6_screen(screen, transition):
    global player_img, font, complete_levels, current_time, medal, deathcount, score
    start_time = time.time()
    global new_hs, hs, stars
    global x, y, camera_x, camera_y, spawn_x, spawn_y,  player_x, player_y,deathcount, in_game, velocity_y, wait_time,death_text, player_rect, on_ground

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    new_hs = False
    menu_ui.buttons.clear()
    screen.blit(manage_data.bgs['green'], (0, 0))

    wait_time = None
    death_text = None
    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = 0
    spawn_x, spawn_y = 220, 500
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    val = 1
    guide = False
    saw_angle = 0

    # Draw flag
    flag = pygame.Rect(2400, 380, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(3200, 410, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 2400, 380
    flag_2_x, flag_2_y = 3200, 410

    key_block_pairs = [
        {
            "key": (5800, 50, 30, (255, 255, 0)),
            "block": pygame.Rect(2950, 10, 200, 170),
            "collected": False
        },
    ]

    lasers = [
        pygame.Rect(5870, 180, 15, 350),
    ]

    blocks = [
        pygame.Rect(-200, 700, 1200, 100),
        pygame.Rect(800, 400, 100, 100),
        pygame.Rect(1400, 400, 100, 100),
        pygame.Rect(1700, 400, 100, 100),
        pygame.Rect(2000, 400, 100, 100),
        pygame.Rect(2300, 500, 450, 50),
        pygame.Rect(2900, 10, 50, 570),
        pygame.Rect(3150, 10, 50, 170),
        pygame.Rect(2950, 530, 2950, 50),
        pygame.Rect(3200, 130, 2700, 50)
    ]


    moving_saws = [ 
        {'r': 100, 'speed': 20, 'cx': 3800, 'cy': -400, 'max': 600, 'min': -400},
    ]

    moving_saws_x = [
        {'r': 100, 'speed':16, 'cx': 4900, 'cy': 165, 'max': 5800, 'min': 4900}
    ]

    saws = [
        (5000, 550, 100, (255, 0, 0)),
        (5400, 550, 100, (255, 0, 0)),

    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 120, 'speed': 2, "block": 1},
        {'r': 40, 'orbit_radius': 230, 'angle': 240, 'speed': 2, "block": 1},
    ]

    jump_blocks = [
        pygame.Rect(1000, 600, 100, 50),
        pygame.Rect(400, 650, 100, 50),
        pygame.Rect(2650, 400, 100, 100),
    ]

    spikes = [
    [(500, 700), (545, 600), (590, 700)],
    [(600,700), (645, 600), (690, 700)],
    [(700, 700), (745, 600), (790, 700)],
    [(800, 700), (845, 600), (890, 700)],
    [(900,700), (945, 600), (990, 700)],
    [(4100, 130), (4150, 80), (4200, 130)],
    [(4610, 130),(4660, 80),(4710, 130)],
    [(4300, 530),(4345, 480), (4390, 530)],
    [(4400, 530), (4445, 480), (4490, 530)],
    ]

    exit_portal = pygame.Rect(5630, 340, 140, 180)
    clock = pygame.time.Clock()


    screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for x, y, r, color in saws:
            angle = (pygame.time.get_ticks() // 3) % 360
            saw_ig_img = manage_data.assets['saw']
            curr_w, curr_h = saw_ig_img.get_size()
            center_x = x - camera_x
            center_y = y - camera_y
            draw_x = center_x - (curr_w / 2)
            draw_y = center_y - (curr_h / 2)
            screen.blit(saw_ig_img, (draw_x, draw_y))

        # Draw all lasers first
    for laser in lasers:
        pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for jump_block in jump_blocks:
        pygame.draw.rect(screen, (255, 128, 0), (int(jump_block.x - camera_x), int(jump_block.y - camera_y), jump_block.width, jump_block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

        
    for pair in key_block_pairs:
            key_x, key_y, key_r, key_color = pair["key"]
            block = pair["block"]
            pygame.draw.circle(screen, key_color, (int(key_x - camera_x), int(key_y - camera_y)), key_r)
            pygame.draw.rect(screen, (102, 51, 0), (block.x - camera_x, block.y - camera_y, block.width, block.height))

    level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)

    fall_message = in_game.get("fall_message", "Fell too far!")
    rendered_fall_text = menu_ui.render_text(fall_message, True, (255, 0, 0))  # Render the fall text

    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)
    if not transition.active:
      while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        if wait_time is None:
            val = random.random()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            for pair in key_block_pairs:
                pair["collected"] = False  # Reset the collected status for all keys
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 220, 500
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                state.handle_action("quit", transition, manage_data.current_page)

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not manage_data.is_mute:
                manage_data.sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
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
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        if player_y > 1100:
            death_text = rendered_fall_text
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute and val > 0.35: # type: ignore
                manage_data.sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False  # Reset the collected status for the key

        # Saw collision detection
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2400, 350  # Store checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 3150, 400  # Checkpoint position

        # Exit portal
        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 6)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)
            
            manage_data.Achievements.check_green_gold()
            manage_data.Achievements.perfect6(current_time, deathcount)
            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            
            state.handle_action('quit', transition, manage_data.current_page)
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
        screen.blit(manage_data.bgs['green'], (0, 0))

        if checkpoint_reached:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
        if checkpoint_reached2:
            screen.blit(manage_data.assets['cpoint_act'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        else:
            screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        if level_logic.handle_rotating_saws(screen, rotating_saws, blocks, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False 

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False 
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            key_block_pairs[0]["collected"] = False 

        level_logic.draw_saws(screen, saws, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False 

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.handle_key_blocks(screen, manage_data.sounds['open'], key_block_pairs, manage_data.is_mute, on_ground, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y)

        for laser in lasers:
            pygame.draw.rect(screen, (255, 0, 0), (int(laser.x - camera_x), int(laser.y - camera_y), laser.width, laser.height))
            # Check if the player collides with the laser
            if player_rect.colliderect(laser):
                # Trigger death logic
                death_text = menu_ui.render_text(in_game.get("laser_message", "Lasered!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute and val > 0.35:
                    manage_data.sounds['laser'].play()
                player_x, player_y = spawn_x, spawn_y # type: ignore
                deathcount += 1
                velocity_y = 0
                key_block_pairs[0]["collected"] = False  # Reset the collected status for the key
        
        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1
                key_block_pairs[0]["collected"] = False  

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], False, False)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1
            key_block_pairs[0]["collected"] = False 

        level_logic.draw_portal(screen, manage_data.assets['exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

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

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(6, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        if wait_time is not None:
            if pygame.time.get_ticks() - wait_time < 2500:
                if val > 0.3:
                    screen.blit(death_text, (20, 50))
                else:
                    if not guide:
                        manage_data.sounds['hscore'].play()
                        guide = True
                    
                    if val < 0.15:
                        screen.blit(menu_ui.render_text('"The strong is not the one who overcomes the people by his strength, but the strong is', True, (255, 255, 0)), (20, 50))
                        screen.blit(menu_ui.render_text('the one who controls himself while in anger." (Bukhari 6114)', True, (255, 255, 0)), (20, 80)) 
                    else:
                        screen.blit(menu_ui.render_text('"Indeed, with hardship comes ease." (Quran 94:6)', True, (255, 255, 0)), (20, 50))
            
            else:
                wait_time = None
                val = None

        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update()   

def create_lvl7_screen(screen, transition):
    global player_img, font, complete_levels, current_time, medal, deathcount, score
    start_time = time.time()
    global new_hs, hs, stars

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    new_hs = False
    menu_ui.buttons.clear()
    screen.blit(manage_data.bgs['mech'], (0, 0))

    wait_time = None
    death_text = None
    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = 0
    spawn_x, spawn_y = 100, 200
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    saw_angle = 0

    # Draw flag
    flag = pygame.Rect(2600, 300, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(240, -1360, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 2600, 300
    flag_2_x, flag_2_y = 240, -1360

    blocks = [
        pygame.Rect(0, 400, 3000, 50),
        pygame.Rect(3200, 500, 500, 50),
        pygame.Rect(3900, 500, 500, 50),
        pygame.Rect(4600, 500, 700, 50),
        pygame.Rect(100, -1250, 300, 50),
        pygame.Rect(600, -1000, 700, 50),
        pygame.Rect(1450, -1125, 650, 50)
    ]
    
    moving_saws = [ 
        {'r': 100, 'speed': 9, 'cx': 3800, 'cy': 200, 'max': 700, 'min': 200},
        {'r': 100, 'speed': 9, 'cx': 4500, 'cy': 600, 'max': 700, 'min': 200},
    ]

    moving_saws_x = [
        {'r': 100, 'speed':11, 'cx': 700, 'cy': -975, 'max': 1200, 'min': 700},
        {'r': 100, 'speed': 7, 'cx': 1550, 'cy': -1100, 'max': 2000, 'min': 1550}
    ]

    saws = [
        (5000, 550, 100, (255, 0, 0)),
    ]

    rotating_saws = [
        {'r': 40, 'orbit_radius': 230, 'angle': 0, 'speed': 3, 'block': 0},
        {'r': 40, 'orbit_radius': 230, 'angle': 120, 'speed': 3, 'block': 0},
        {'r': 40, 'orbit_radius': 230, 'angle': 240, 'speed': 3, 'block': 0},
        {'r': 60, 'orbit_radius': 500, 'angle': 60, 'speed': 2, 'block': 0},
        {'r': 60, 'orbit_radius': 500, 'angle': 180, 'speed': 2, 'block': 0},
        {'r': 60, 'orbit_radius': 500, 'angle': 300, 'speed': 2, 'block': 0},
        {'r': 80, 'orbit_radius': 900, 'angle': 0, 'speed': 1, 'block': 0},
        {'r': 80, 'orbit_radius': 900, 'angle': 120, 'speed': 1, 'block': 0},
        {'r': 80, 'orbit_radius': 900, 'angle': 240, 'speed': 1, 'block': 0},
    ]

    spikes = [
    [(3400, 500), (3450, 450), (3500, 500)],
    [(4100, 500), (4150, 450), (4200, 500)],
    ]

    exit_portal = pygame.Rect(1960, -1320, 140, 180)
    clock = pygame.time.Clock()

    teleporters = [
        {
            "entry": pygame.Rect(5150, 300, 140, 180),
            "exit": pygame.Rect(100, -1400, 50, 50),
            "color": (0, 196, 255)
        }
    ]

    screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))

    for x, y, r, color in saws:
            angle = (pygame.time.get_ticks() // 3) % 360
            saw_ig_img = manage_data.assets['saw']
            curr_w, curr_h = saw_ig_img.get_size()
            center_x = x - camera_x
            center_y = y - camera_y
            draw_x = center_x - (curr_w / 2)
            draw_y = center_y - (curr_h / 2)
            screen.blit(saw_ig_img, (draw_x, draw_y))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    level_logic.draw_portal(screen, manage_data.assets['mech_exit'], exit_portal, camera_x, camera_y)
    
    portal_text = menu_ui.render_text(in_game.get("portal_message", "These blue portals teleport you! But to good places... mostly!"), True, (0, 102, 204))

    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)
    if not transition.active:
       while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()

        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 100, 200
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                state.handle_action("quit", transition, manage_data.current_page)

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            velocity_y = -jump_strength
            if not manage_data.is_mute:
                manage_data.sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
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
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

        # Checkpoint Logic
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            spawn_x, spawn_y = 2600, 250  # Store checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 150, -1500  # Checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 7)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)

            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            
            state.handle_action('lvl8_screen', transition, manage_data.current_page)
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
        
        # Draw key only if not collected
 
# Saw collision detection and drawing
        if level_logic.handle_rotating_saws(screen, rotating_saws, blocks, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0

        for teleporter in teleporters:
            # Draw the entry rectangle
            level_logic.draw_portal(screen, manage_data.assets['teleport'], teleporter["entry"], camera_x, camera_y)
            # Draw the exit rectangle
            level_logic.draw_portal(screen, manage_data.assets['teleport_exit'], teleporter["exit"], camera_x, camera_y)

           # Check if the player collides with the entry rectangle
            if player_rect.colliderect(teleporter["entry"]):
                # Teleport the player to the exit rectangle
                if not manage_data.is_mute:
                    manage_data.sounds['warp'].play()
                player_x, player_y = teleporter["exit"].x, teleporter["exit"].y
        
        level_logic.draw_saws(screen, saws, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

        level_logic.draw_portal(screen, manage_data.assets['mech_exit'], exit_portal, camera_x, camera_y)
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)          

        screen.blit(portal_text, (4400 - camera_x, 300 - camera_y))

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

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(7, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update()   

def create_lvl8_screen(screen, transition):
    global player_img, font, complete_levels, current_time, medal, deathcount, score
    global new_hs, hs, stars

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)

    new_hs = False
    menu_ui.buttons.clear()
    screen.blit(manage_data.bgs['mech'], (0, 0))

    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y = 0, 260
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    # When the gravity is weaker
    weak_jump_strength = 37
    weak_grav = False
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    saw_angle = 0

    # Draw flag
    flag = pygame.Rect(8700, -320, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(10000, -320, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 8700, -320
    flag_2_x, flag_2_y = 10000, -320

    blocks = [
        pygame.Rect(0, 400, 100, 100),
        pygame.Rect(460, 650, 540, 50),
        pygame.Rect(1200, 200, 1050, 50),
        pygame.Rect(8200, -200, 6000, 400),
        pygame.Rect(9000, -750, 50, 600),
        pygame.Rect(9600, -750, 50, 600),
        pygame.Rect(10000, -1650, 2000, 500),
        pygame.Rect(10000, -1650, 100, 1220),
        pygame.Rect(10750, -360, 600, 170),
    ]
    
    jump_blocks = [
        pygame.Rect(1100, 600, 100, 100),
        pygame.Rect(11000, -460, 100, 100),
    ]

    moving_saws = [
        {'r': 60, 'speed': 11, 'cx': 350, 'cy': 200, 'max': 800, 'min': 0},
    ]

    moving_saws_x = [
        {'r': 130, 'speed':19, 'cx': 11000, 'cy': -950, 'max': 11300, 'min': 10700}
    ]

    saws = [
        (1850, 200, 80, (255, 0, 0)),
        (9025, -175, 150, (255, 0, 0)),
        (9625, -175, 150, (255, 0, 0)),
        
    ]

    spikes = [
    [(700, 650), (750, 600), (800, 650)],
    [(1400, 200), (1475, 120), (1550, 200)],
    [(9000, -750), (9025, -800), (9050, -750)],
    [(9600, -750), (9625, -800), (9650, -750)],
    [(10100, -1150), (10150, -1100), (10200, -1150)],
    [(10200, -1150), (10250, -1100), (10300, -1150)],
    [(10300, -1150), (10350, -1100), (10400, -1150)],
    [(10400, -1150), (10450, -1100), (10500, -1150)],
    [(10500, -1150), (10550, -1100), (10600, -1150)],
    [(10600, -1150), (10650, -1100), (10700, -1150)],
    [(10700, -1150), (10750, -1100), (10800, -1150)],
    [(10800, -1150), (10850, -1100), (10900, -1150)],
    [(10900, -1150), (10950, -1100), (11000, -1150)],
    [(11000, -1150), (11050, -1100), (11100, -1150)],
    [(11100, -1150), (11150, -1100), (11200, -1150)],
    [(11200, -1150), (11250, -1100), (11300, -1150)],
    [(11300, -1150), (11350, -1100), (11400, -1150)],
    ]

    exit_portal = pygame.Rect(10980, -1050, 140, 180)
    clock = pygame.time.Clock()

    gravity_weakers = [
        (8700, -350, 30, (0, 102, 204)),
    ]

    teleporters = [
        {
            "entry": pygame.Rect(2090, 0, 140, 180),
            "exit": pygame.Rect(8300, -400, 100, 100),
            "color": (0, 196, 255)
        }
    ]

    screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for x, y, r, color in saws:
            angle = (pygame.time.get_ticks() // 3) % 360
            saw_ig_img = manage_data.assets['saw']
            curr_w, curr_h = saw_ig_img.get_size()
            center_x = x - camera_x
            center_y = y - camera_y
            draw_x = center_x - (curr_w / 2)
            draw_y = center_y - (curr_h / 2)
            screen.blit(saw_ig_img, (draw_x, draw_y))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    level_logic.draw_portal(screen, manage_data.assets['mech_exit'], exit_portal, camera_x, camera_y)

    button1_text = in_game.get("button1_message", "Blue menu_ui.buttons, upon activation, will make you jump higher!")
    button1_text = menu_ui.render_text(button1_text, True, (0, 102, 204))

    clarify_text = in_game.get("clarify_message", "Until you reach a checkpoint, of course!")
    clarify_text = menu_ui.render_text(clarify_text, True, (0, 102, 204))

    mock_text = in_game.get("mock_message", "Wrong way my guy nothing to see here...")
    mock_text = menu_ui.render_text(mock_text, True, (255, 0, 0))

    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)
    if not transition.active:
       while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()
        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()  # Reset the timer
            weak_grav = False # Reset weak gravity status
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 0, 260
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys[pygame.K_q]:
                running = False
                state.handle_action("quit", transition, manage_data.current_page)

        # Input
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and on_ground:
            if weak_grav:
                velocity_y = -weak_jump_strength
            else:
                velocity_y = -jump_strength
            if not manage_data.is_mute:
                manage_data.sounds['jump'].play()

        # Detect if any movement key is pressed
        moving = (keys[pygame.K_LEFT] or keys[pygame.K_a] or
                  keys[pygame.K_RIGHT] or keys[pygame.K_d])

        if moving:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
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
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            weak_grav = False # Reset weak gravity status
            if not manage_data.is_mute:
                manage_data.sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

        # Checkpoint Logic
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            weak_grav = False # Reset weak gravity status
            spawn_x, spawn_y = 8680, -500  # Store checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            weak_grav = False # Reset weak gravity status
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 10000, -350  # Checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 8)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)

            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            
            state.handle_action('lvl9_screen', transition, manage_data.current_page)
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
        for teleporter in teleporters:
            # Draw the entry rectangle
            level_logic.draw_portal(screen, manage_data.assets['teleport'], teleporter["entry"], camera_x, camera_y)
            # Draw the exit rectangle
            level_logic.draw_portal(screen, manage_data.assets['teleport_exit'], teleporter["exit"], camera_x, camera_y)

           # Check if the player collides with the entry rectangle
            if player_rect.colliderect(teleporter["entry"]):
                # Teleport the player to the exit rectangle
                if not manage_data.is_mute:
                    manage_data.sounds['warp'].play()
                player_x, player_y = teleporter["exit"].x, teleporter["exit"].y

        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            weak_grav = False
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            weak_grav = False

        level_logic.draw_saws(screen, saws, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1
            weak_grav = False

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], False, weak_grav)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1
            weak_grav = False

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1
                weak_grav = False 

        if level_logic.handling_gravity_weakers(screen, gravity_weakers, player_rect, camera_x, camera_y, weak_grav):
            weak_grav = True

        level_logic.draw_portal(screen, manage_data.assets['mech_exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        screen.blit(button1_text, (8400 - camera_x, -150 - camera_y))
        screen.blit(clarify_text, (9800 - camera_x, -150 - camera_y))
        screen.blit(mock_text, (13200 - camera_x, -300 - camera_y))

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

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(8, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update()   

def create_lvl9_screen(screen, transition):
    global player_img, font, complete_levels, current_time, medal, deathcount, score
    global new_hs, hs, stars

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    new_hs = False
    menu_ui.buttons.clear()
    screen.blit(manage_data.bgs['mech'], (0, 0))
    
    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y =  50, -50
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    # When the gravity is stronger
    strong_jump_strength = 15
    strong_grav = False
    weak_grav_strength = 37
    # When the gravity is weaker
    weak_grav = False
    move_speed = 8
    on_ground = False
    saw_angle = 0

    # Draw flag
    flag = pygame.Rect(2350, 300, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(5600, 550, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 2350, 300
    flag_2_x, flag_2_y = 5600, 550

    key_block_pairs = [
        {
            "key": (3700, 550, 30, (255, 255, 0)),
            "block": pygame.Rect(3200, 0, 400, 200),
            "collected": False
        },
    ]

    blocks = [
        pygame.Rect(0, 100, 1000, 50),
        pygame.Rect(500, 60, 500, 80),
        pygame.Rect(0, -300, 1000, 100),
        pygame.Rect(1600, 600, 300, 100),
        pygame.Rect(2050, 500, 100, 100),
        pygame.Rect(2300, 400, 600, 100),
        pygame.Rect(2800, -300, 100, 500),
        pygame.Rect(3200, 200, 100, 530),
        pygame.Rect(2900, -600, 1100, 100),
        pygame.Rect(3500, 200, 2030, 100),
        pygame.Rect(3550, 650, 2280, 100)
    ]

    walls = [
        pygame.Rect(3500, 220, 100, 830)
    ]

    jump_blocks = [
        pygame.Rect(1250, 600, 100, 100),
        pygame.Rect(2970, 420, 100, 100),
        pygame.Rect(5730, 550, 100, 100),
    ]

    moving_saws = [ 
        {'r': 70, 'speed': 6, 'cx': 3700, 'cy': 500, 'max': 900, 'min': 300},
        {'r': 70, 'speed': 10, 'cx': 4500, 'cy': 600, 'max': 700, 'min': -60},
    ]

    moving_saws_x = [
        {'r': 100, 'speed':14, 'cx': 3800, 'cy': 700, 'min': 3700, 'max': 5400}
    ]

    spikes = [
    [(0, -200), (50, -150), (100, -200)],
    [(110, -200), (160, -150), (210, -200)],
    [(220, -200), (270, -150), (320, -200)],
    [(330, -200), (380, -150), (430, -200)],    
    [(440, -200), (490, -150), (540, -200)],
    [(550, -200), (600, -150), (650, -200)],    
    [(660, -200), (710, -150), (760, -200)],
    [(770, -200), (820, -150), (870, -200)],
    [(880, -200), (930, -150), (980, -200)],
    [(2900, 200), (2950, 150), (2900, 100)],
    [(2900, 90), (2950, 40), (2900, -10)],
    [(2900, -20), (2950, -70), (2900, -120)],
    [(2900, -130), (2950, -180), (2900, -230)],
    [(2900, -240), (2950, -265), (2900, -290)],
    [(3200, 0), (3150, 50), (3200, 100)],
    [(3200, 110), (3150, 160), (3200, 210)],
    [(3200, 220), (3150, 270), (3200, 320)],
    [(3200, 330), (3150, 380), (3200, 430)],
    [(2900, -500), (2950, -450), (3000, -500)],
    [(3010, -500), (3060, -450), (3110, -500)],
    [(3120, -500), (3170, -450), (3220, -500)],
    [(3230, -500), (3280, -450), (3330, -500)],
    [(3340, -500), (3390, -450), (3440, -500)],
    [(3450, -500), (3500, -450), (3550, -500)],
    [(3560, -500), (3610, -450), (3660, -500)],
    [(3670, -500), (3720, -450), (3770, -500)],
    [(3780, -500), (3830, -450), (3880, -500)],
    [(3890, -500), (3940, -450), (3990, -500)],
    [(4000, 200), (4050, 150), (4100, 200)],
    [(4110, 200), (4160, 150), (4210, 200)],
    [(4220, 200), (4270, 150), (4320, 200)],
    [(4330, 200), (4380, 150), (4430, 200)],
    [(4440, 200), (4490, 150), (4540, 200)],
    [(4550, 200), (4600, 150), (4650, 200)],
    [(4660, 200), (4710, 150), (4760, 200)],
    [(4770, 200), (4820, 150), (4870, 200)],
    [(4880, 200), (4930, 150), (4980, 200)],
    [(4990, 200), (5040, 150), (5090, 200)],
    [(5100, 200), (5150, 150), (5200, 200)],
    [(5210, 200), (5260, 150), (5310, 200)],
    [(5320, 200), (5370, 150), (5420, 200)],
    [(5430, 200), (5480, 150), (5530, 200)],
    [(4950, 300), (5000, 350), (5050, 300)],
    [(4350, 300), (4400, 350), (4450, 300)],
    ]

    exit_portal = pygame.Rect(3325, 420, 140, 180)
    clock = pygame.time.Clock()

    gravity_strongers = [
        (300, 50, 30, (204, 102, 204)),
    ]

    gravity_weakers = [
        (2550, 350, 30, (0, 102, 204)),
    ]

    moving_block = pygame.Rect(4450, 30, 100, 20)
    moving_direction1 = 1
    moving_speed = 5
    moving_limit_left1 = 4050
    moving_limit_right1 = 5600

    screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))
 
    for x, y, r, color in gravity_strongers:
            # Draw the button as a circle
                pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for spike in spikes:
        pygame.draw.polygon(screen, (255, 0, 0), [(x - camera_x, y - camera_y) for x, y in spike])

    level_logic.draw_portal(screen, manage_data.assets['mech_exit'], exit_portal, camera_x, camera_y)
    
    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)

    if not transition.active:
       while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()
        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()  # Reset the timer
            key_block_pairs[0]["collected"] = False  # Reset key block status
            weak_grav = False
            strong_grav = False # Reset gravity status
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 50, -50
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

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
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
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
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in moving_block:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        for block in walls:
            if player_rect.colliderect(block):
                # Horizontal collision (left or right side of the block)
                if player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            key_block_pairs[0]["collected"] = False  # Reset key block status
            strong_grav = False # Reset strong gravity status
            weak_grav = False # Reset weak gravity status
            if not manage_data.is_mute:    
                manage_data.sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

                # Moving blocks
        moving_block.x += moving_speed * moving_direction1
        if moving_block.x < moving_limit_left1 or moving_block.x > moving_limit_right1:
            moving_direction1 *= -1

        # Checkpoint Logic
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            weak_grav = False # Reset weak gravity status
            strong_grav = False # Reset strong gravity status
            spawn_x, spawn_y = 2300, 260  # Store checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            weak_grav = False
            strong_grav = False # Reset gravity status
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 5600, 500  # Checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 9)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)
            
            manage_data.Achievements.lvl90000(score)

            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            
            state.handle_action('lvl10_screen', transition, manage_data.current_page)
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
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            weak_grav = False 
            strong_grav = False
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
            weak_grav = False 
            strong_grav = False

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.handle_key_blocks(screen, manage_data.sounds['open'], key_block_pairs, manage_data.is_mute, on_ground, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y)

        for block in walls:
            pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], strong_grav, weak_grav)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1
            weak_grav = False 
            strong_grav = False

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 
                weak_grav = False 
                strong_grav = False

        if level_logic.handling_gravity_strongers(screen, gravity_strongers, player_rect, camera_x, camera_y, strong_grav):
            strong_grav = True
            weak_grav = False 

        if level_logic.handling_gravity_weakers(screen, gravity_weakers, player_rect, camera_x, camera_y, weak_grav):
            weak_grav = True
            strong_grav = False

        level_logic.draw_portal(screen, manage_data.assets['mech_exit'], exit_portal, camera_x, camera_y)
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        button2_text = in_game.get("button2_message", "Lavender menu_ui.buttons, upon activation, will make you jump lower!")
        screen.blit(menu_ui.render_text(button2_text, True, (204, 102, 204)), (100 - camera_x, 100 - camera_y))

        clarify2_text = in_game.get("clarify_message2", "They also affect your jumps on jump blocks!")
        screen.blit(menu_ui.render_text(clarify2_text, True, (204, 102, 204)), (1000 - camera_x, 450 - camera_y))

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

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(9, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)
        
        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update() 

def create_lvl10_screen(screen, transition):
    global player_img, font, complete_levels, current_time, medal, deathcount, score
    global new_hs, hs, stars
    new_hs = False

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    menu_ui.buttons.clear()
    screen.blit(manage_data.bgs['mech'], (0, 0))

    wait_time = None
    death_text = None
    start_time = time.time()

    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

    # Camera settings
    camera_x = 300
    camera_y = -500
    spawn_x, spawn_y =  0, 250
    player_x, player_y = spawn_x, spawn_y
    running = True
    gravity = 1
    jump_strength = 21
    # When the gravity is weaker
    strong_jump_strength = 15
    strong_grav = False
    weak_grav_strength = 37
    weak_grav = False
    move_speed = 8
    on_ground = False
    velocity_y = 0
    camera_speed = 0.5
    deathcount = 0
    was_moving = False
    lights_off = True
    saw_angle = 0

    # Draw flag
    flag = pygame.Rect(3100, 370, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(5000, 370, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 3100, 370
    flag_2_x, flag_2_y = 5000, 370

    blocks = [
        pygame.Rect(-100, 500, 1200, 50),
        pygame.Rect(1300, 400, 200, 50),
        pygame.Rect(1625, 500, 200, 50),
        pygame.Rect(1920, 400, 100, 100),
        pygame.Rect(3000, 480, 300, 50),
        pygame.Rect(3500, 480, 100, 300),
        pygame.Rect(3800, 260, 100, 520),
        pygame.Rect(4100, 40, 100, 740),
        pygame.Rect(4400, 260, 100, 520),
        pygame.Rect(4700, 480, 100, 300),
        pygame.Rect(4950, 480, 1200, 100)
    ]

    jump_blocks = [
        pygame.Rect(11000, 600, 100, 100),
        pygame.Rect(14000, 600, 100, 100),
    ]

    moving_saws = [ 
        {'r': 70, 'speed': 7, 'cx': 5900, 'cy': 400, 'max': 600, 'min': 100},
    ]

    moving_saws_x = [
        {'r': 100, 'speed':4, 'cx': 600, 'cy': 500, 'min': 600, 'max': 1000},
        {'r': 50, 'speed': 14, 'cx':3550, 'cy': 430, 'min': 3550, 'max': 4750},
        {'r': 50, 'speed': 14, 'cx':3550, 'cy': -10, 'min': 3550, 'max': 4750},
        {'r': 50, 'speed': 9, 'cx':5200, 'cy': 480, 'min': 5200, 'max': 6000},
        {'r': 50, 'speed': 9, 'cx':5200, 'cy': 180, 'min': 5200, 'max': 6000},
    ]

    saws = [
        (1500, 425, 80, (255, 0, 0)),
        (1825, 525, 80, (255, 0, 0)),
        (2500, 310, 50, (255, 0, 0)),
    ]


    rotating_saws = [
        {'r': 40, 'orbit_radius': 300, 'angle': 0, 'speed': 3, 'block': 0},
    ]

    lights = [
        {
            "button": pygame.Rect(400, 380, 50, 50),
            "block": pygame.Rect(1300, 0, 200, 400),
        }
    ]

    exit_portal = pygame.Rect(5960, 280, 140, 180)
    clock = pygame.time.Clock()

    gravity_strongers = [
        (5050, 420, 30, (204, 102, 204)),
    ]

    moving_block = pygame.Rect(2200, 300, 100, 20)
    moving_direction1 = 1
    moving_speed = 5
    moving_limit_left1 = 2200
    moving_limit_right1 = 2800

    screen.blit(manage_data.assets['cpoint_inact'], ((flag_1_x - camera_x), (flag_1_y - camera_y)))
    screen.blit(manage_data.assets['cpoint_inact'], ((flag_2_x - camera_x), (flag_2_y - camera_y)))

    for block in blocks:
        pygame.draw.rect(screen, (0, 0, 0), (int(block.x - camera_x), int(block.y - camera_y), block.width, block.height))

    for x, y, r, color in saws:
            angle = (pygame.time.get_ticks() // 3) % 360
            saw_ig_img = manage_data.assets['saw']
            curr_w, curr_h = saw_ig_img.get_size()
            center_x = x - camera_x
            center_y = y - camera_y
            draw_x = center_x - (curr_w / 2)
            draw_y = center_y - (curr_h / 2)
            screen.blit(saw_ig_img, (draw_x, draw_y))

    
    menu_ui.draw_notifs(screen)
    menu_ui.draw_syncing_status(screen)

    if not transition.active:
       while running:
        clock.tick(60)
        keys = pygame.key.get_pressed()
        current_time = time.time() - start_time
        formatted_time = "{:.2f}".format(current_time)

        if keys[pygame.K_r]:
            start_time = time.time()  # Reset the timer
            lights_off = True
            strong_grav = False # Reset gravity status
            checkpoint_reached = False  # Reset checkpoint status
            checkpoint_reached2 = False  # Reset checkpoint status
            spawn_x, spawn_y = 0, 250
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount = 0

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
                player_x -= move_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
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
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in blocks + [moving_block]:
            if player_rect.colliderect(block):
                # Falling onto a block
                if velocity_y > 0 and player_y + img_height - velocity_y <= block.y:
                    player_y = block.y - img_height
                    velocity_y = 0
                    on_ground = True

                # Hitting the bottom of a block
                elif velocity_y < 0 and player_y >= block.y + block.height - velocity_y:
                    player_y = block.y + block.height
                    velocity_y = 0

                # Horizontal collision (left or right side of the block)
                elif player_x + img_width > block.x and player_x < block.x + block.width:
                    if player_x < block.x:  # Colliding with the left side of the block
                        player_x = block.x - img_width
                    elif player_x + img_width > block.x + block.width:  # Colliding with the right side
                        player_x = block.x + block.width

        if player_y > 1100:
            death_text = menu_ui.render_text(in_game.get("fall_message", "Fell too far!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            lights_off = True
            strong_grav = False # Reset strong gravity status
            if not manage_data.is_mute:    
                manage_data.sounds['fall'].play()
            player_x, player_y = spawn_x, spawn_y  # Reset player position
            velocity_y = 0
            deathcount += 1

                # Moving blocks
        moving_block.x += moving_speed * moving_direction1
        if moving_block.x < moving_limit_left1 or moving_block.x > moving_limit_right1:
            moving_direction1 *= -1

        # Checkpoint Logic
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

        if player_rect.colliderect(flag) and not checkpoint_reached and not checkpoint_reached2:
            checkpoint_reached = True
            lights_off = True
            strong_grav = False # Reset strong gravity status
            spawn_x, spawn_y = 3100, 260  # Store checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()
            pygame.draw.rect(screen, (0, 105, 0), flag.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
        if player_rect.colliderect(flag2) and not checkpoint_reached2 and checkpoint_reached:
            checkpoint_reached = False
            checkpoint_reached2 = True
            lights_off = True
            strong_grav = False # Reset gravity status
            pygame.draw.rect(screen, (0, 105, 0), flag2.move(-camera_x, -camera_y))  # Green rectangle representing the active flag
            pygame.draw.rect(screen, (71, 71, 71), flag.move(-camera_x, -camera_y))  # Gray rectangle representing the flag
            spawn_x, spawn_y = 4950, 300  # Checkpoint position
            if not manage_data.is_mute:
                manage_data.sounds['checkpoint'].play()

        # Exit portal
        if player_rect.colliderect(exit_portal):
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 10)
            menu_ui.level_complete(screen, base_score, medal_score, death_score, time_score, score, new_hs, hs, medal, stars)

            manage_data.save_progress(manage_data.progress, manage_data.manifest)  # Save manage_data.progress to JSON file
            
            state.handle_action('lvl11_screen', transition, manage_data.current_page)
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

# Saw collision detection and drawing
        if level_logic.handle_rotating_saws(screen, rotating_saws, blocks, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0

        # Handle Moving Saws
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], strong_grav, weak_grav)
        level_logic.draw_saws(screen, saws, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 


        pygame.draw.rect(screen, (128, 0, 128), (moving_block.x - camera_x, moving_block.y - camera_y, moving_block.width, moving_block.height))

        if level_logic.handling_gravity_strongers(screen, gravity_strongers, player_rect, camera_x, camera_y, strong_grav):
            strong_grav = True
            weak_grav = False

        level_logic.draw_portal(screen, manage_data.assets['mech_exit'], exit_portal, camera_x, camera_y)
        
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        button2_text = in_game.get("button3_message", "Purple menu_ui.buttons, upon activation, will turn out almost all the lights!")
        screen.blit(menu_ui.render_text(button2_text, True, (104, 102, 204)), (100 - camera_x, 300 - camera_y))

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        player_x, player_y, velocity_y, on_ground, player_rect, lights_off = level_logic.handle_light_blocks(screen, lights, on_ground, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, lights_off, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, manage_data.is_mute, manage_data.sounds['button'])

        deaths_val = in_game.get("deaths_no", "Deaths: {deathcount}").format(deathcount=deathcount)
        deaths_rendered = menu_ui.render_text(deaths_val, True, (255, 255, 255))

        timer_txt = in_game.get("time", f"Time: {time}s").format(time=formatted_time)
        timer_text = menu_ui.render_text(timer_txt, True, (255, 255, 255))  # white color

        # Initialize and draw the reset and quit text
        reset_text = in_game.get("reset_message", "Press R to reset")
        rendered_reset_text = menu_ui.render_text(reset_text, True, (255, 255, 255))  # Render the reset text

        quit_text = in_game.get("quit_message", "Press Q to quit")
        rendered_quit_text = menu_ui.render_text(quit_text, True, (255, 255, 255))  # Render the quit text

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(10, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update() 

def create_lvl11_screen(screen, transition):
    global player_img, font, complete_levels, current_time, medal, deathcount, score
    global new_hs, hs, stars

    player_img, blink_img, moving_img, moving_img_l, img_width, img_height = manage_data.char_assets(manage_data.selected_character)
    new_hs = False
    menu_ui.buttons.clear()
    screen.blit(manage_data.bgs['mech'], (0, 0))

    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

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
    flag = pygame.Rect(1400, 420, 100, 125)  # x, y, width, height
    checkpoint_reached = False
    flag2 = pygame.Rect(5600, 330, 100, 125)  # x, y, width, height
    checkpoint_reached2 = False
    flag_1_x, flag_1_y = 1400, 420
    flag_2_x, flag_2_y = 5600, 330

    blocks = [
        pygame.Rect(-600, 525, 2850, 50),
        pygame.Rect(1065, 200, 70, 375),
        pygame.Rect(1625, -200, 100, 590),
        pygame.Rect(1625, 50, 150, 50),
        pygame.Rect(2200, 400, 150, 50),
        pygame.Rect(2250, -300, 600, 2200),
        pygame.Rect(2300, 200, 3000, 100),
        pygame.Rect(3100, -300, 2600, 100),
        pygame.Rect(3050, -500, 120, 300),
        pygame.Rect(5180, 250, 120, 300),
        pygame.Rect(5250, 450, 1500, 100),
        pygame.Rect(5600, -1400, 520, 1700),
    ]

    jump_blocks = [
        pygame.Rect(630, 425, 100, 100),
        pygame.Rect(14000, 600, 100, 100),
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
        "button": pygame.Rect(2350, -425, 50, 50),
        "block": pygame.Rect(3050, -200, 120, 400)
        }
    ]

    exit_portal = pygame.Rect(6600, 250, 140, 180)
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
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        for block in moving_block:
            rect = pygame.Rect(block['x'], block['y'], block['width'], block['height'])
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

        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

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
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 11)
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
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0

        if level_logic.handle_rushing_saws(screen, rushing_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], strong_grav, weak_grav)
        level_logic.draw_saws(screen, saws, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            player_x, player_y = spawn_x, spawn_y
            velocity_y = 0
            deathcount += 1

        for block in moving_block:
            pygame.draw.rect(screen, (128, 0, 128), (block['x'] - camera_x, block['y'] - camera_y, block['width'], block['height']))
        
        for block in moving_block:
            pygame.draw.rect(screen, (128, 0, 128), ((block['x'] - camera_x), (block['y'] - camera_y), block['width'], block['height']))
            if block['width'] < 100:
                laser_rect = pygame.Rect(block['x'], block['y'] + block['height'] +10, block['width'], 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.Rect(block['x'] + 4, block['y'] + block['height'] + 5, block['width'] - 8 , 5)  # 5 px tall death zone
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

        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("dead_message", "You Died"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            if not manage_data.is_mute:
                manage_data.sounds['death'].play()
            velocity_y = 0
            deathcount += 1

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
                player_x, player_y = spawn_x, spawn_y  # Reset player position
                death_text = menu_ui.render_text(in_game.get("hit_message", "Hit on the head!"), True, (255, 0, 0))
                wait_time = pygame.time.get_ticks()
                if not manage_data.is_mute:    
                    manage_data.sounds['hit'].play()
                velocity_y = 0
                deathcount += 1 

        for x, y, r, color in speedsters:
            # Draw the button as a circle
            if not stamina:
                pygame.draw.circle(screen, color, (int(x - camera_x), int(y - camera_y)), int(r))

        for speedster in speedsters:
            speedster_x, speedster_y, speedster_radius, _ = speedster

        # Find the closest point on the player's rectangle to the button's center
            closest_x = max(player_rect.left, min(speedster_x, player_rect.right))
            closest_y = max(player_rect.top, min(speedster_y, player_rect.bottom))

            # Calculate the distance between the closest point and the button's center
            dx = closest_x - speedster_x
            dy = closest_y - speedster_y
            distance = (dx**2 + dy**2)**0.5

            # If distance is less than radius, stronger gravity activated
            if distance < speedster_radius and not stamina:
                if not manage_data.is_mute:
                    manage_data.sounds['button'].play()
                strong_grav = False
                stamina = True
                weak_grav = False

        level_logic.draw_portal(screen, manage_data.assets['mech_exit'], exit_portal, camera_x, camera_y)
        # Player Image
        screen.blit(player_img, (int(player_x - camera_x), int(player_y - camera_y)))

        # Boss Trigger Area

        if player_x > suspicious_x and player_y < -300 and lights_off:
            screen.blit(evilrobo_mascot, ((epos_x - camera_x), (epos_y - camera_y)))

            if evilrobo_phase == 0 and player_x < trigger_x:
                sus_message = menu_ui.render_text("Huh? Is there anyone there?", True, (255, 20, 12))
                screen.blit(sus_message, (4800 - camera_x, -450 - camera_y))
            else:
                if evilrobo_phase < 1:
                    evilrobo_phase = 1  # Prevents repeating

        if evilrobo_phase == 1 and player_y < -300 and lights_off:
            holup_message = menu_ui.render_text("HEY! Get away from here!", True, (185, 0, 0))
            screen.blit(holup_message, (4800 - camera_x, -450 - camera_y))
            
        if evilrobo_phase == 1 and lights_off:
            screen.blit(evilrobo_mascot, (int(epos_x - camera_x), int(epos_y - camera_y)))
            if epos_x > player_x + 10:
                epos_x -= 20
                
            elif epos_x < player_x - 10:
                epos_x += 20
            else:
                epos_x = player_x

        if evilrobo_phase == 2:
            screen.blit(evilrobo_mascot, (int(epos_x - camera_x), int(epos_y - camera_y)))
            if player_y > -300:
                confused_text = menu_ui.render_text("WHERE DID HE GO????", True, (82, 0, 0))
                screen.blit(confused_text, ((epos_x - camera_x), (epos_y - camera_y - 40)))
                if not unlock:
                    unlock = True
                    unlock_time = pygame.time.get_ticks()
            epos_x -= 12

        if epos_x < 2150:
            evilrobo_phase = 2

        if unlock and unlock_time is not None:
            manage_data.Achievements.evilchase()
            unlock_time = None

        evilrobo_rect = pygame.Rect(int(epos_x), int(epos_y), evilrobo_mascot.get_width(), evilrobo_mascot.get_height())
        
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

        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)
        
        player_x, player_y, velocity_y, on_ground, player_rect, lights_off = level_logic.handle_light_blocks(screen, lights, on_ground, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, lights_off, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, manage_data.is_mute, manage_data.sounds['button'])

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

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(11, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
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

    in_game = manage_data.load_language(manage_data.lang_code, manage_data.manifest).get('in_game', {})

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
    flag = pygame.Rect(3900, 200, 100, 125)  # x, y, width, height
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
            "block": pygame.Rect(1900, 0, 100, 200),
            "collected": False,
            "duration": 5000,  # Duration for which the block is active
            "locked_time": None
        },
        {
            "key": (4000, 250, 30, (255, 119, 0)),
            "block": pygame.Rect(4150, 400, 50, 250),
            "collected": False,
            "duration": 3500,  # Duration for which the block is active
            "locked_time": None
        }
    ]

    blocks = [
        pygame.Rect(0, 200, 2000, 100),
        pygame.Rect(1900, -1000, 100, 1000),
        pygame.Rect(3200, -50, 800, 100),
        pygame.Rect(3600, 300, 500, 100),
        pygame.Rect(4100, -700, 101, 1100),
        pygame.Rect(3450, 650, 1000, 100),
        pygame.Rect(3350, 0, 100, 750),
        pygame.Rect(2300, 200, 150, 100),
        pygame.Rect(2600, 20, 200, 100),
        pygame.Rect(4500, 750, 600, 200),
    ]

    jump_blocks = [
        pygame.Rect(3000, 250, 100, 100),
        pygame.Rect(4300, 550, 100, 100),
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

    exit_portal = pygame.Rect(4080, -910, 140, 180)
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
        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)
        on_ground = False

        player_rect = pygame.Rect(player_x, player_y, img_width, img_height)

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
            score, base_score, medal_score, death_score, time_score, stars, new_hs, hs = level_logic.fin_lvl_logic(current_time, deathcount, medal, 12)
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
        if level_logic.handle_moving_saws(screen, moving_saws, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
            # Death logic (same as above)
            player_x, player_y = spawn_x, spawn_y
            death_text = menu_ui.render_text(in_game.get("sawed_message", "Sawed to bits!"), True, (255, 0, 0))
            wait_time = pygame.time.get_ticks()
            deathcount += 1
            if not manage_data.is_mute: manage_data.sounds['death'].play()
            velocity_y = 0
        
        # Handle Moving Saws
        if level_logic.handle_moving_saws_x(screen, moving_saws_x, player_rect, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache):
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

        level_logic.draw_saws(screen, saws, manage_data.assets['saw'], camera_x, camera_y, manage_data.saw_cache)

        # 2. Check for saw deaths
        if level_logic.check_saw_collisions(player_rect, saws):
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

        player_x, player_y, velocity_y = level_logic.jump_block_func(screen, jump_blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, manage_data.is_mute, manage_data.sounds['bounce'], strong_grav, weak_grav)
        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        player_x, player_y, velocity_y, on_ground, player_rect = level_logic.block_func(screen, blocks, camera_x, camera_y, player_x, player_y, img_width, img_height, velocity_y, player_rect, on_ground)
        
        if level_logic.handle_bottom_collisions(blocks, player_rect, velocity_y):  # Only if jumping upward
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

        level_logic.draw_portal(screen, manage_data.assets['mech_exit'], exit_portal, camera_x, camera_y)

        screen.blit(rendered_timed_text, (0 - camera_x, -80 - camera_y))
        
        screen.blit(rendered_timed_text_2, (-20 - camera_x, -30 - camera_y))
        
        if level_logic.handling_gravity_strongers(screen, gravity_strongers, player_rect, camera_x, camera_y, strong_grav):
            strong_grav = True
            weak_grav = False

        if level_logic.handling_gravity_weakers(screen, gravity_weakers, player_rect, camera_x, camera_y, weak_grav):
            strong_grav = False
            weak_grav = True

        is_crushed, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y, on_ground = level_logic.handle_key_blocks_timed(screen, key_block_pairs_timed, player_rect, player_x, player_y, img_width, img_height, velocity_y, camera_x, camera_y, on_ground)
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

        level_logic.draw_level_ui(screen, manage_data.SCREEN_WIDTH, manage_data.SCREEN_HEIGHT, deaths_rendered, rendered_reset_text, rendered_quit_text, timer_text)
        
        medal = level_logic.get_medal(12, current_time)
        level_logic.draw_medals(screen, medal, deathcount, manage_data.medals, timer_text.get_width(), manage_data.SCREEN_WIDTH)

        level_logic.draw_spikes(screen, spikes, camera_x, camera_y)

        if level_logic.check_spike_collisions(spikes, player_x, player_y, img_width, img_height):
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
        level_logic.player_image(current_time, moving_img, moving_img_l, player_img, blink_img,screen, keys, player_x, player_y, camera_x, camera_y)

        # Camera logic
        camera_x += (player_x - camera_x - screen.get_width() // 2 + img_width // 2) * camera_speed

        # Adjust the camera's Y position when the player moves up
        if player_y <= 200:
            camera_y = player_y - 200
        else:
            camera_y = 0  # Keep the camera fixed when the player is below the threshold

        level_logic.death_message(screen, death_text, wait_time, duration=2500)
        menu_ui.draw_notifs(screen)
        menu_ui.draw_syncing_status(screen)
        pygame.display.update() 
