# TextSprite - A pygame sprite class for rendering text
# Handles all text rendering with proper positioning, centering, and animations
# For now, this only contains static text. However, one day, I might actually build onto this further and better!

import pygame

class TextSprite(pygame.sprite.Sprite):
    # A sprite class for rendering text in pygame.
    # Handles single and multi-language text with proper positioning.
    
    def __init__(self, text, x=0, y=0, color=(255, 255, 255), font_key='def', center_x=False, center_y=False):
        # Initialize a TextSprite

        super().__init__()
        
        self.text = text
        self.color = color
        self.font_key = font_key
        self.center_x = center_x
        self.center_y = center_y
        self.alpha = 255
        
        # Render the text
        self.image = self._render_text()
        self.rect = self.image.get_rect()
        
        # Set position
        self._set_position(x, y)
    
    def _render_text(self):
        # Import here to avoid circular imports
        from menu_ui import render_text
        return render_text(self.text, True, self.color)
    
    def _set_position(self, x, y):
        # Set the sprite position, handling centering
        if self.center_x:
            self.rect.centerx = x
        else:
            self.rect.x = x
        
        if self.center_y:
            self.rect.centery = y
        else:
            self.rect.y = y
    
    def update(self, *args):
        # Update the sprite (override this for animations)
        pass
    
    def set_text(self, new_text):
        # Change the text and re-render
        self.text = new_text
        old_x = self.rect.x
        old_y = self.rect.y
        self.image = self._render_text()
        self.rect = self.image.get_rect()
        self._set_position(old_x, old_y)
    
    def set_color(self, new_color):
        # Change the text color and re-render
        self.color = new_color
        old_x = self.rect.x
        old_y = self.rect.y
        self.image = self._render_text()
        self.rect = self.image.get_rect()
        self._set_position(old_x, old_y)
    
    def set_position(self, x, y):
        # Update position
        self._set_position(x, y)
    
    def set_alpha(self, alpha):
        # Set transparency (0-255)
        self.alpha = alpha
        self.image.set_alpha(alpha)
    
    def get_width(self):
        # Get text width
        return self.rect.width
    
    def get_height(self):
        # Get text height
        return self.rect.height