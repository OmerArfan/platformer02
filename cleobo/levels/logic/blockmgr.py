import pygame
from cleobo.data import manage_data

"""
The purpose of this levels submodule is to store different types of blocks in one file.
If you do have an idea for a new block, do make sure to add it here without any hesitation, and hopefully, I will be able to check it out and test it.
"""

def handle_blocks(screen, blocks, player):
    for block in blocks:
            pygame.draw.rect(screen, (0, 0, 0), (block.x - player.camera_x, block.y - player.camera_y, block.width, block.height))
            if player.rect.colliderect(block):
                # Falling onto a block
                if player.velocity_y > 0 and player.rect.y + player.rect.height - player.velocity_y <= block.y:
                    player.rect.y = block.y - player.rect.height
                    player.velocity_y = 0
                    player.on_ground = True
                # Horizontal collision (left or right side of the block)
                elif player.rect.x + player.rect.width > block.x and player.rect.x < block.x + block.width:
                    if player.rect.x < block.x:  # Colliding with the left side of the block
                        player.rect.x = block.x - player.rect.width
                    elif player.rect.x + player.rect.width > block.x + block.width:  # Colliding with the right side
                        player.rect.x = block.x + block.width
    return player

def handle_bottom_collisions(blocks, player):
    for block in blocks:
            if block.width <= 100:
                laser_rect = pygame.FRect(block.x, block.y + block.height +10, block.width, 5)  # 5 px tall death zone
            else:
                laser_rect = pygame.FRect(block.x + 8, block.y + block.height, block.width - 16, 5)  # 5 px tall death zone
            
            if player.rect.colliderect(laser_rect) and player.velocity_y < 0:  # Only if jumping upward
                return True
    return False

def handle_moving_blocks(screen, moving_blocks, player):
        for mb in moving_blocks:
            pygame.draw.rect(screen, (128, 0, 128), (mb['rect'].x - player.camera_x, mb['rect'].y - player.camera_y, mb['rect'].width, mb['rect'].height))
            
            # Setup dimensions
            adj_x = mb['rect'].x + 5 - player.camera_x
            adj_y = mb['rect'].y + 5 - player.camera_y
            adj_w = (mb['rect'].width - 10) // 2  # Keep them side-by-side
            adj_h = mb['rect'].height - 10

            # Define colors
            bright = (224, 113, 224)
            dark = (180, 93, 180) # Darker shade for inactive direction

            # Define Left Triangle Points
            left_tri_points = [
                (adj_x + adj_w - 5, adj_y),               # Top Right of left half
                (adj_x + adj_w - 5, adj_y + adj_h),       # Bottom Right of left half
                (adj_x, adj_y + adj_h / 2)            # Left Tip
            ]

            # Define Right Triangle Points (Pointing Right)
            right_tri_points = [
                (adj_x + adj_w + 5, adj_y),               # Top Left of right half
                (adj_x + adj_w + 5, adj_y + adj_h),       # Bottom Left of right half
                (adj_x + (adj_w * 2), adj_y + adj_h / 2) # Right Tip
            ]

            # Draw them based on direction
            if mb['direction'] == 1: # Right is active
                pygame.draw.polygon(screen, dark, left_tri_points)
                pygame.draw.polygon(screen, bright, right_tri_points)
            else: # Left is active
                pygame.draw.polygon(screen, bright, left_tri_points)
                pygame.draw.polygon(screen, dark, right_tri_points)
                        
            mb['rect'].x += mb['speed'] * mb['direction']
            if mb['rect'].x < mb['limit_left'] or mb['rect'].x > mb['limit_right']:
                mb['direction'] *= -1
            
            if player.rect.colliderect(mb['rect']):
                # Standing on top of the moving block
                if player.velocity_y > 0 and player.rect.y + player.rect.height - player.velocity_y <= mb['rect'].y:
                    player.rect.y = mb['rect'].y - player.rect.height
                    player.velocity_y = 0
                    player.on_ground = True
                    # Carry the player along with the block's horizontal movement
                    player.rect.x += mb['speed'] * mb['direction']
                # Hitting from the side
                elif player.rect.x + player.rect.width > mb['rect'].x and player.rect.x < mb['rect'].x + mb['rect'].width:
                    if player.rect.x < mb['rect'].x:
                        player.rect.x = mb['rect'].x - player.rect.width
                    elif player.rect.x + player.rect.width > mb['rect'].x + mb['rect'].width:
                        player.rect.x = mb['rect'].x + mb['rect'].width
        
        return player, moving_blocks

def handle_jump_blocks(screen, jump_blocks, player):
        for jump_block in jump_blocks:
            pygame.draw.rect(screen, (255, 128, 0), (jump_block.x - player.camera_x, jump_block.y - player.camera_y, jump_block.width, jump_block.height))

            adj_x = jump_block.x + 5 - player.camera_x
            adj_y = jump_block.y + 5 - player.camera_y # Changed to +5 to keep it inside the top of the block
            adj_w = jump_block.width - 10
            adj_h = jump_block.height - 10

            #  Define the three points of the triangle
            points = [
                (adj_x + adj_w / 2, adj_y),          # Top Tip (Middle)
                (adj_x, adj_y + adj_h),              # Bottom Left
                (adj_x + adj_w, adj_y + adj_h)       # Bottom Right
            ]

            # Draw the triangle
            pygame.draw.polygon(screen, (255, 190, 81), points)
            
            if player.rect.colliderect(jump_block):
                # Falling onto a jump block
                if player.velocity_y > 0 and player.rect.y + player.rect.height - player.velocity_y < jump_block.y + 5:
                    player.rect.bottom = jump_block.y
                    if player.jump_mode == "strong":
                        player.velocity_y = -21
                    elif player.jump_mode == "weak":
                        player.velocity_y = -54
                    else:
                        player.velocity_y = -33  # Apply upward velocity for the jump
                    if not manage_data.is_mute:
                        manage_data.sounds["bounce"].play()

                # Hitting the bottom of a jump block
                elif player.velocity_y < 0 and player.rect.y >= jump_block.y + jump_block.height - player.velocity_y:
                    player.rect.y = jump_block.y + jump_block.height
                    player.velocity_y = 0

                # Horizontal collision (left or right side of the jump block)
                elif player.rect.x + player.rect.width > jump_block.x and player.rect.x < jump_block.x + jump_block.width:
                    if player.rect.x < jump_block.x:  # Colliding with the left side of the jump block
                        player.rect.x = jump_block.x - player.rect.width
                    elif player.rect.x + player.rect.width > jump_block.x + jump_block.width:  # Colliding with the right side
                        player.rect.x = jump_block.x + jump_block.width
        
        return player

def handle_key_blocks(screen, key_block_pairs, player):
    for pair in key_block_pairs:
        # 1. DRAW & COLLECT THE KEY
        if not pair['collected']:
            key_data = pair['key']
            kx, ky, kr = key_data['x'], key_data['y'], key_data['radius']
            k_color = tuple(key_data.get('color', (255, 255, 0)))

            # Draw the key (Relative to camera!)
            pygame.draw.circle(screen, k_color, (int(kx - player.camera_x), int(ky - player.camera_y)), int(kr))

            # Collision check for key collection (Player hits the circle)
            key_rect = pygame.FRect(kx - kr, ky - kr, kr * 2, kr * 2)
            if player.rect.colliderect(key_rect):
                pair['collected'] = True
                if not manage_data.is_mute:
                    manage_data.sounds['open'].play()

        # 2. DRAW & COLLIDE WITH THE BLOCK
        if not pair['collected']:
            block = pair['block'] # This is now a proper FRect
            
            # Draw the block (Relative to camera!)
            pygame.draw.rect(screen, (102, 51, 0), (block.x - player.camera_x, block.y - player.camera_y, block.width, block.height))
            
            # Physics Collision (AABB Overlap Resolution)
            if player.rect.colliderect(block):
                overlap_x = min(player.rect.right, block.right) - max(player.rect.left, block.left)
                overlap_y = min(player.rect.bottom, block.bottom) - max(player.rect.top, block.top)

                if overlap_y < overlap_x:
                    if player.velocity_y > 0: # Landing
                        player.rect.bottom = block.top
                        player.velocity_y = 0
                        player.on_ground = True
                    elif player.velocity_y < 0: # Ceiling hit
                        player.rect.top = block.bottom
                        player.velocity_y = 0
                else:
                    if player.rect.centerx < block.centerx: # Left wall
                        player.rect.right = block.left
                    else: # Right wall
                        player.rect.left = block.right
                        
    return player

def handle_key_blocks_timed(screen, key_block_pairs_timed, player):
    for pair in key_block_pairs_timed:
        key_x, key_y, key_r, key_color = pair["key"]
        block = pair["block"]

        key_rect = pygame.FRect(key_x - key_r, key_y - key_r, key_r * 2, key_r * 2)

        if player.rect.colliderect(key_rect):
            if not pair["collected"]:
                pair["locked_time"] = pygame.time.get_ticks()
                pair["collected"] = True
                if not manage_data.is_mute:
                    manage_data.sounds['open'].play()

        # Draw key and block only if not collected
        if not pair["collected"]:
            pygame.draw.circle(screen, key_color, (int(key_x - player.camera_x), int(key_y - player.camera_y)), key_r)
            pygame.draw.rect(screen, (102, 51, 0), (block.x - player.camera_x, block.y - player.camera_y, block.width, block.height))

        # Reset after duration
        if pair.get("locked_time") is not None:
            if pair["collected"] and (pygame.time.get_ticks() - pair["locked_time"]) > pair["duration"]:
                pair["collected"] = False
                pair["locked_time"] = None  # Reset timer
                # Check if player is inside block when it reappears
        
                if player.rect.colliderect(pair["block"]):
                    return True, player

        if not pair["collected"]:  # Only active locked blocks
            block = pair["block"]
            if player.rect.colliderect(block):
        # Falling onto a block
                if player.velocity_y > 0 and player.rect.y + player.rect.height - player.velocity_y <= block.y:
                    player.rect.y = block.y - player.rect.height
                    player.velocity_y = 0
                    player.ground = True

        # Horizontal collisions
                elif player.rect.x + player.rect.width > block.x and player.rect.x < block.x + block.width:
                    if player.rect.x < block.x:
                        player.rect.x = block.x - player.rect.width
                    elif player.rect.x + player.rect.width > block.x + block.width:
                        player.rect.x = block.x + block.width

    return False, player