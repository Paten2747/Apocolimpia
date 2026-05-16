import pygame
import math
from constants import *
from assets import assets

class Button:
    def __init__(self, name, pos, idle_img, pressed_img, callback, scale=6.0):
        self.name = name
        self.base_pos = pygame.Vector2(pos)
        self.pos = pygame.Vector2(pos)
        self.idle_img = idle_img
        self.pressed_img = pressed_img
        self.callback = callback
        
        self.rect = self.idle_img.get_rect(center=pos)
        self.hovered = False
        self.pressed = False
        
        # Animation states
        self.base_scale = scale
        self.scale = scale
        self.target_scale = scale
        self.float_offset = 0.0
        self.time_offset = pos[0] * 0.01 + pos[1] * 0.01 # Unique start phase

        # Text rendering
        self.font = pygame.font.SysFont("Arial", 16, bold=True)
        self.text_surf = self.font.render(self.name, True, COLOR_WHITE)

        # Initialize rect with scaled size
        scaled_size = (int(self.idle_img.get_width() * self.scale), int(self.idle_img.get_height() * self.scale))
        self.rect = pygame.Rect(0, 0, *scaled_size)
        self.rect.center = pos
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1:
                self.pressed = True
                # Placeholder for click sound
                print(f"Click sound: {self.name}")
                
        if event.type == pygame.MOUSEBUTTONUP:
            if self.pressed and self.hovered and event.button == 1:
                self.callback()
            self.pressed = False

    def update(self, dt, mouse_pos):
        # Hover detection
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        if self.hovered:
            # Scale up on hover
            self.target_scale = self.base_scale * 1.2
            
            if not hasattr(self, '_prev_hovered') or not self._prev_hovered:
                # Placeholder for hover sound
                print(f"Hover sound: {self.name}")
        else:
            self.target_scale = self.base_scale 
        self._prev_hovered = self.hovered
            
        # Smooth scaling
        self.scale += (self.target_scale - self.scale) * HOVER_SCALE_SPEED * dt
            
        # Floating animation
        self.float_offset = math.sin(pygame.time.get_ticks() * BUTTON_FLOAT_SPEED + self.time_offset) * BUTTON_FLOAT_AMPLITUDE
        
        # Update current position
        self.pos.y = self.base_pos.y + self.float_offset
        if self.pressed:
            self.pos.y += 4 # Push down effect
            
        # Update rect for collision
        img = self.idle_img
        scaled_size = (int(img.get_width() * self.scale), int(img.get_height() * self.scale))
        self.rect = pygame.Rect(0, 0, *scaled_size)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, surface):
        img = self.pressed_img if self.pressed else self.idle_img
        
        if self.scale != 1.0:
            scaled_size = (int(img.get_width() * self.scale), int(img.get_height() * self.scale))
            img = pygame.transform.scale(img, scaled_size)
        
        rect = img.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        surface.blit(img, rect)

        # Draw text
        if self.name and not self.name.startswith("Delete_") and self.name not in ["Back", "Plus", "Settings", "Start"]:
            # Centered at 2/3 for world buttons
            if self.idle_img == assets.get("world"):
                 text_x = rect.left + rect.width * (2/3)
            else:
                 text_x = rect.centerx
            
            text_rect = self.text_surf.get_rect(center=(int(text_x), int(self.pos.y)))
            surface.blit(self.text_surf, text_rect)

        # Draw hover arrow
        if self.hovered:
            arrow_img = assets.get("arrow")
            if arrow_img:
                # Scale to 8x8 (half of previous 16x16)
                arrow_img = pygame.transform.scale(arrow_img, (8, 8))
                a_rect = arrow_img.get_rect()
                a_rect.midtop = rect.midbottom
                surface.blit(arrow_img, a_rect)

class Menu:
    def __init__(self):
        self.buttons = []
        self.alpha = 0
        self.target_alpha = 255
        self.fade_surface = pygame.Surface(VIRTUAL_RES)
        self.fade_surface.fill(COLOR_BLACK)
        
        # Scrolling logic
        self.scroll_y = 0
        self.target_scroll_y = 0
        self.scroll_speed = 10.0
        
    def add_button(self, button):
        self.buttons.append(button)
        
    def handle_event(self, event):
        # Handle scrolling
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: # Scroll up
                self.target_scroll_y += 30
            elif event.button == 5: # Scroll down
                self.target_scroll_y -= 30
        
        # Don't propagate events to buttons if they are scrolled off screen?
        # For now, just propagate as usual
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt, mouse_pos):
        # Fade logic
        if self.alpha < self.target_alpha:
            self.alpha = min(255, self.alpha + TRANSITION_SPEED * 255 * dt)
        elif self.alpha > self.target_alpha:
            self.alpha = max(0, self.alpha - TRANSITION_SPEED * 255 * dt)
            
        # Smooth scrolling
        self.scroll_y += (self.target_scroll_y - self.scroll_y) * self.scroll_speed * dt
        
        # Apply scroll to mouse position for button collision
        # This is tricky because the button's internal rect isn't scrolled, 
        # but the drawing is.
        # We should probably shift the mouse pos in the opposite direction.
        scrolled_mouse_pos = (mouse_pos[0], mouse_pos[1] - self.scroll_y)
        
        for btn in self.buttons:
            # We don't want to scroll fixed buttons like 'Back' or 'Plus'
            if btn.name in ["Back", "Plus"]:
                btn.update(dt, mouse_pos)
            else:
                btn.update(dt, scrolled_mouse_pos)
            
    def draw(self, surface):
        for btn in self.buttons:
            # Shift drawing position for non-fixed buttons
            if btn.name in ["Back", "Plus"]:
                btn.draw(surface)
            else:
                # Temporarily shift base position for drawing
                original_y = btn.pos.y
                btn.pos.y += self.scroll_y
                btn.draw(surface)
                btn.pos.y = original_y
            
        # Apply menu fade overlay
        if self.alpha < 255:
            self.fade_surface.set_alpha(255 - int(self.alpha))
            surface.blit(self.fade_surface, (0, 0))

class TextInputPopup:
    def __init__(self, title, callback):
        self.title = title
        self.callback = callback
        self.text = ""
        self.bg_img = assets.get("box")
        self.scale = 4.0
        
        # Dim surface
        self.dim_surf = pygame.Surface(VIRTUAL_RES)
        self.dim_surf.fill(COLOR_BLACK)
        self.dim_surf.set_alpha(150)
        
        self.font = pygame.font.SysFont("Arial", 14)
        self.title_font = pygame.font.SysFont("Arial", 12, bold=True)
        
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.text.strip():
                    self.callback(self.text.strip())
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.callback(None) # Cancel
                return True
            else:
                if len(self.text) < 20 and event.unicode.isprintable():
                    self.text += event.unicode
        return False

    def update(self, dt):
        pass

    def draw(self, surface):
        # Draw dim background
        surface.blit(self.dim_surf, (0, 0))
        
        # Draw box
        if self.bg_img:
            scaled_w = int(self.bg_img.get_width() * self.scale)
            scaled_h = int(self.bg_img.get_height() * self.scale)
            box_img = pygame.transform.scale(self.bg_img, (scaled_w, scaled_h))
            rect = box_img.get_rect(center=(VIRTUAL_RES[0]//2, VIRTUAL_RES[1]//2))
            surface.blit(box_img, rect)
            
            # Draw Title
            title_surf = self.title_font.render(self.title, True, COLOR_WHITE)
            surface.blit(title_surf, (rect.centerx - title_surf.get_width()//2, rect.top + 10))
            
            # Draw Input Text
            text_surf = self.font.render(self.text + ("|" if pygame.time.get_ticks() % 1000 < 500 else ""), True, COLOR_WHITE)
            surface.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery))
