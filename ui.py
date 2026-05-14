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
        self.scale = scale
        self.target_scale = scale
        self.float_offset = 0.0
        self.time_offset = pos[0] * 0.01 + pos[1] * 0.01 # Unique start phase

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
            if not hasattr(self, '_prev_hovered') or not self._prev_hovered:
                # Placeholder for hover sound
                print(f"Hover sound: {self.name}")
        self._prev_hovered = self.hovered
            
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

        # Draw white background box on hover
        if self.hovered:
            # Calculate the size of the background box (2 pixels wider, 1 pixel taller)
            # Start and Back buttons get an extra pixel on each side (total 4 wider)
            extra_width = 4 if self.name in ["Start", "Back"] else 2
            box_width = rect.width + extra_width
            box_height = rect.height + 1
            
            # Create the white box surface with transparency support
            bg_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            # Fill with white and set 70% opacity (approx 178/255)
            bg_box.fill((255, 255, 255, 178))
            
            # Position the box (offset based on extra width and 1 pixel down)
            surface.blit(bg_box, (rect.x - (extra_width // 2), rect.y + 1))

        surface.blit(img, rect)

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
        
    def add_button(self, button):
        self.buttons.append(button)
        
    def handle_event(self, event):
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt, mouse_pos):
        # Fade logic
        if self.alpha < self.target_alpha:
            self.alpha = min(255, self.alpha + TRANSITION_SPEED * 255 * dt)
        elif self.alpha > self.target_alpha:
            self.alpha = max(0, self.alpha - TRANSITION_SPEED * 255 * dt)
            
        for btn in self.buttons:
            btn.update(dt, mouse_pos)
            
    def draw(self, surface):
        for btn in self.buttons:
            btn.draw(surface)
            
        # Apply menu fade overlay
        if self.alpha < 255:
            self.fade_surface.set_alpha(255 - int(self.alpha))
            surface.blit(self.fade_surface, (0, 0))
