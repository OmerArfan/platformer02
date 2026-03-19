import pygame

def draw_buttons(screen, buttons, hover_sound, is_mute, mouse_pos, button_hovered_last_frame):
    for rendered, rect, key, is_locked in buttons:
        if rect.collidepoint(mouse_pos):
            button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
            button_surface.fill((8, 81, 179, 255))
            screen.blit(button_surface, rect.inflate(20, 10).topleft)
            pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
            button_hovered_last_frame = hover_effect(screen, rect, hover_sound, is_mute, button_hovered_last_frame)
        else:
            button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
            button_surface.fill((8, 81, 179, 255))
            screen.blit(button_surface, rect.inflate(20, 10).topleft)
            pygame.draw.rect(screen, (0, 163, 255), rect.inflate(30, 15), 6)
        screen.blit(rendered, rect)
    return button_hovered_last_frame

def hover_effect(screen, rect, hover_sound, is_mute, button_hovered_last_frame):
    button_surface = pygame.Surface(rect.inflate(20, 10).size, pygame.SRCALPHA)
    button_surface.fill((200, 200, 250, 100))  # RGBA: 100 is alpha (transparency)
    screen.blit(button_surface, rect.inflate(20, 10).topleft)                    
    hovered = rect.collidepoint(pygame.mouse.get_pos())
    if hovered and not button_hovered_last_frame and not is_mute:
        hover_sound.play()
    button_hovered_last_frame = hovered
    return button_hovered_last_frame