import pygame
from config import *

class Button:
    def __init__(self, x, y, w, h, text, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.hover = False
        self.font = pygame.font.SysFont("Arial", 16)
        
        # Dynamic Colors (Can be overridden externally)
        self.bg_color = COLOR_BTN_IDLE
        self.hover_color = COLOR_BTN_HOVER
        self.text_color = COLOR_TEXT

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.hover and event.button == 1:
                self.callback()

    def draw(self, surface):
        # Use the dynamic colors
        current_bg = self.hover_color if self.hover else self.bg_color
        
        pygame.draw.rect(surface, current_bg, self.rect, border_radius=5)
        pygame.draw.rect(surface, (150,150,150), self.rect, 2, border_radius=5)
        
        txt_surf = self.font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surface.blit(txt_surf, txt_rect)