import pygame
import arabic_reshaper
import json
import time
from bidi.algorithm import get_display
from manage_data import init_fonts, update_local_manifest

fonts = init_fonts()

def render_text(text, Boolean, color):
    # 1. PICK THE FONT (Your existing Unicode Logic)
    font_to_use = fonts['def'] # Default
    display_text = text

    if any('\u0590' <= c <= '\u06FF' for c in text):  # Urdu/Arabic range
        reshaped = arabic_reshaper.reshape(text)
        display_text = get_display(reshaped)
        font_to_use = fonts['ar']
    elif any('\u4e00' <= c <= '\u9fff' for c in text):  # Chinese
        font_to_use = fonts['ch']
    elif any('\u3040' <= c <= '\u30FF' for c in text): # Japanese
        font_to_use = fonts['jp']   
    elif any('\uAC00' <= c <= '\uD7A3' for c in text):  # Korean
        font_to_use = fonts['kr']

    # 2. RENDER THE SHADOW (For Readability on Green/Mech BGs)
    shadow_color = (0, 0, 0)
    shadow_surf = font_to_use.render(display_text, True, shadow_color)
    
    # 3. RENDER MAIN TEXT
    main_surf = font_to_use.render(display_text, True, color)
    
    # 4. COMBINE INTO ONE SURFACE
    w = max(1, main_surf.get_width() + 2)
    h = max(1, main_surf.get_height() + 1)
    combined_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    combined_surf.blit(shadow_surf, (1, 1)) # The offset shadow
    combined_surf.blit(main_surf, (0, 0))   # The original text
    
    return combined_surf

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
