import pygame
import math
import hashlib
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

class WorldView:
    def __init__(self, infinite_world, block_registry, player):
        self.infinite_world = infinite_world
        self.block_registry = block_registry
        self.player = player
        self.tile_size = 16  # 16 pixels per block
        self.fade_surface = pygame.Surface(VIRTUAL_RES)
        self.fade_surface.fill(COLOR_BLACK)
        self.alpha = 0
        self.target_alpha = 255
        
        # Texture cache for pre-scaled textures to reduce per-frame computation
        self.scaled_texture_cache = {}
        self.rotated_texture_cache = {}
        self._cache_textures()

    def _cache_textures(self):
        """Pre-scale and cache all textures at startup to reduce per-frame overhead"""
        for block_id, texture in self.block_registry.block_textures.items():
            if texture:
                scaled = pygame.transform.scale(texture, (self.tile_size, self.tile_size))
                self.scaled_texture_cache[block_id] = scaled
    
    def _get_cached_texture(self, block_id: str):
        """Get pre-scaled texture from cache"""
        if block_id in self.scaled_texture_cache:
            return self.scaled_texture_cache[block_id]
        placeholder = pygame.Surface((self.tile_size, self.tile_size))
        placeholder.fill((100, 100, 100))
        return placeholder

    def calculate_view_radius(self):
        """Calculate how many chunks to load based on screen size with 1 chunk ahead"""
        from constants import CHUNK_SIZE
        # Calculate pixels per chunk
        chunk_pixel_width = CHUNK_SIZE * self.tile_size
        chunk_pixel_height = CHUNK_SIZE * self.tile_size

        # How many chunks fit on screen (plus 2 for safety margin, plus 1 for one chunk ahead)
        chunks_x = (VIRTUAL_RES[0] // chunk_pixel_width) + 2
        chunks_y = (VIRTUAL_RES[1] // chunk_pixel_height) + 2

        # Return the radius needed to cover the screen plus one chunk buffer, capped at 3 for performance
        radius = max(chunks_x, chunks_y) + 1
        return min(radius, 3)  # Cap at 3 chunks radius to prevent loading excessive chunks

    def handle_event(self, event):
        if self.player:
            self.player.handle_event(event)

    def update(self, dt, mouse_pos):
        if self.player:
            self.player.update(dt)

        if self.alpha < self.target_alpha:
            self.alpha = min(255, self.alpha + TRANSITION_SPEED * 255 * dt)
        elif self.alpha > self.target_alpha:
            self.alpha = max(0, self.alpha - TRANSITION_SPEED * 255 * dt)

    def _get_block_rotation(self, block_id, world_x, world_y):
        root_seed = getattr(self.infinite_world, 'seed', 0)
        hash_input = f"{root_seed}:{block_id}:{world_x}:{world_y}"
        hash_obj = hashlib.md5(hash_input.encode())
        rotation_index = int(hash_obj.hexdigest(), 16) % 4
        return rotation_index * 90

    def draw(self, surface):
        surface.fill(COLOR_BG)

        if not self.infinite_world or not self.block_registry or not self.player:
            return

        # Calculate dynamic view radius based on screen size
        from constants import CHUNK_SIZE
        view_radius = self.calculate_view_radius()

        # Get visible chunks around player
        visible_chunks = self.infinite_world.get_visible_chunks(
            self.player.world_x, self.player.world_y, view_radius
        )

        # Calculate camera offset so player is at center
        screen_center_x = VIRTUAL_RES[0] // 2
        screen_center_y = VIRTUAL_RES[1] // 2
        # Use round() for pixel-perfect positioning to prevent jitter
        camera_offset_x = screen_center_x - int(round(self.player.world_x * self.tile_size))
        camera_offset_y = screen_center_y - int(round(self.player.world_y * self.tile_size))

        # Draw chunks with optimizations for low-end hardware
        for chunk in visible_chunks:
            for local_y in range(CHUNK_SIZE):
                for local_x in range(CHUNK_SIZE):
                    block_id = chunk.grid[local_y][local_x]
                    
                    # Convert chunk-local coords to world coords
                    world_x = chunk.chunk_x * CHUNK_SIZE + local_x
                    world_y = chunk.chunk_y * CHUNK_SIZE + local_y

                    # Convert to screen coords with pixel-perfect rounding
                    screen_x = int(round(world_x * self.tile_size + camera_offset_x))
                    screen_y = int(round(world_y * self.tile_size + camera_offset_y))

                    # Early cull: skip if block is completely off-screen
                    if not (-self.tile_size < screen_x < VIRTUAL_RES[0] and -self.tile_size < screen_y < VIRTUAL_RES[1]):
                        continue
                    
                    # Get pre-scaled cached texture (no per-frame scaling)
                    scaled_texture = self._get_cached_texture(block_id)

                    # Apply deterministic random orientation per block position
                    rotation = self._get_block_rotation(block_id, world_x, world_y)
                    if rotation != 0:
                        # Cache rotated textures to avoid recalculating
                        cache_key = (block_id, rotation)
                        if cache_key not in self.rotated_texture_cache:
                            self.rotated_texture_cache[cache_key] = pygame.transform.rotate(scaled_texture, rotation)
                        scaled_texture = self.rotated_texture_cache[cache_key]

                    surface.blit(scaled_texture, (screen_x, screen_y))

        # Draw player at screen center
        if self.player:
            self.player.draw(surface)

        # Apply fade
        if self.alpha < 255:
            self.fade_surface.set_alpha(255 - int(self.alpha))
            surface.blit(self.fade_surface, (0, 0))
