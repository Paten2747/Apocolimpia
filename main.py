import pygame
import sys
import json
import os
from constants import *
from assets import load_all_assets, assets
from ui import Button, Menu

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(INITIAL_WINDOW_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption(WINDOW_TITLE)
        
        self.virtual_surface = pygame.Surface(VIRTUAL_RES)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Load assets
        load_all_assets()
        
        # State
        self.state = GameState.MAIN_MENU
        self.next_state = None
        self.fade_alpha = 255 # For startup fade
        
        # World Data Setup
        self.world_data_path = os.path.join(os.path.dirname(__file__), "world_data")
        if not os.path.exists(self.world_data_path):
            os.makedirs(self.world_data_path)
            
        self.worlds = self.load_worlds()
        self.active_popup = None
        
        self.menus = {
            GameState.MAIN_MENU: self.create_main_menu(),
            GameState.SETTINGS: self.create_settings_menu(),
            GameState.WORLD_SELECT: self.create_world_select_menu()
        }
        
    def create_main_menu(self):
        menu = Menu()
        center_x = VIRTUAL_RES[0] // 2
        
        menu.add_button(Button(
            "Start", 
            (center_x, 120), 
            assets.get("start"), 
            assets.get("pressed_long"), 
            lambda: self.change_state(GameState.WORLD_SELECT),
            scale=8.0
        ))
        
        menu.add_button(Button(
            "Settings", 
            (center_x, 240), 
            assets.get("settings"), 
            assets.get("pressed_short"), 
            lambda: self.change_state(GameState.SETTINGS),
            scale=6.0
        ))

        menu.add_button(Button(
            "Back", 
            (40, 40), 
            assets.get("back"), 
            assets.get("pressed_long"), 
            lambda: self.quit_game(),
            scale=1.0
        ))
        return menu

    def create_world_select_menu(self):
        menu = Menu()
        center_x = VIRTUAL_RES[0] // 2
        
        # List existing worlds
        for i, world_name in enumerate(self.worlds):
            y_pos = 80 + i * 80
            # World button
            menu.add_button(Button(
                world_name,
                (center_x, y_pos),
                assets.get("world"),
                assets.get("pressed_long"),
                lambda name=world_name: print(f"Selected {name}"),
                scale=3.0
            ))
            
            # Delete button (X)
            menu.add_button(Button(
                f"Delete_{world_name}",
                (center_x + 180, y_pos),
                assets.get("x"),
                assets.get("pressed_short"),
                lambda idx=i: self.delete_world(idx),
                scale=2.0
            ))
            
        # Back button in corner
        menu.add_button(Button(
            "Back", 
            (40, 40), 
            assets.get("back"), 
            assets.get("pressed_long"), 
            lambda: self.change_state(GameState.MAIN_MENU),
            scale=1.0
        ))
        
        # Plus button below Back button
        menu.add_button(Button(
            "Plus",
            (40, 80),
            assets.get("plus"),
            assets.get("pressed_short"),
            self.add_new_world_prompt,
            scale=1.0
        ))
        
        return menu

    def add_new_world_prompt(self):
        from ui import TextInputPopup
        self.active_popup = TextInputPopup("Enter World Name", self.confirm_add_world)

    def confirm_add_world(self, name):
        if name:
            # Create world directory
            world_dir = os.path.join(self.world_data_path, name)
            if not os.path.exists(world_dir):
                os.makedirs(world_dir)
            
            # Try to remove OS-generated desktop.ini if it appears
            ini_path = os.path.join(world_dir, "desktop.ini")
            if os.path.exists(ini_path):
                try:
                    os.remove(ini_path)
                except:
                    pass
                
            self.worlds.append(name)
            self.save_worlds()
            # Recreate menu to reflect changes
            self.menus[GameState.WORLD_SELECT] = self.create_world_select_menu()
        self.active_popup = None

    def delete_world(self, index):
        if 0 <= index < len(self.worlds):
            del self.worlds[index]
            self.save_worlds()
            # Recreate menu to reflect changes
            self.menus[GameState.WORLD_SELECT] = self.create_world_select_menu()

    def load_worlds(self):
        try:
            world_path = os.path.join("assets", "worlds.json")
            if os.path.exists(world_path):
                with open(world_path, "r") as f:
                    return json.load(f)
            else:
                return ["Default World"]
        except Exception as e:
            print(f"Error loading worlds: {e}")
            return ["Default World"]

    def save_worlds(self):
        try:
            world_path = os.path.join("assets", "worlds.json")
            with open(world_path, "w") as f:
                json.dump(self.worlds, f)
        except Exception as e:
            print(f"Error saving worlds: {e}")

    def create_settings_menu(self):
        menu = Menu()
        center_x = VIRTUAL_RES[0] // 2
        
        menu.add_button(Button(
            "Back", 
            (40, 40), 
            assets.get("back"), 
            assets.get("pressed_long"), 
            lambda: self.change_state(GameState.MAIN_MENU),
            scale=1.0
        ))
        return menu

    def change_state(self, new_state):
        self.next_state = new_state
        self.menus[self.state].target_alpha = 0

    def quit_game(self):
        self.running = False

    def handle_events(self):
        # Scale mouse position to virtual resolution
        mx, my = pygame.mouse.get_pos()
        ww, wh = self.screen.get_size()
        vw, vh = VIRTUAL_RES
        
        # Calculate aspect ratio scaling
        scale = min(ww/vw, wh/vh)
        off_x = (ww - vw * scale) / 2
        off_y = (wh - vh * scale) / 2
        
        virtual_mx = (mx - off_x) / scale
        virtual_my = (my - off_y) / scale
        self.mouse_pos = (virtual_mx, virtual_my)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            
            if event.type == pygame.VIDEORESIZE:
                # Handled by dynamic scaling in draw
                pass
                
            if self.active_popup:
                if self.active_popup.handle_event(event):
                    continue # Event consumed by popup
                    
            self.menus[self.state].handle_event(event)

    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        
        current_menu = self.menus[self.state]
        current_menu.update(dt, self.mouse_pos)
        
        # Handle state transitions
        if self.next_state and current_menu.alpha <= 0:
            self.state = self.next_state
            self.next_state = None
            self.menus[self.state].alpha = 0
            self.menus[self.state].target_alpha = 255
            
        if self.active_popup:
            self.active_popup.update(dt)
            
        # Startup fade
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - TRANSITION_SPEED * 255 * dt)

    def draw(self):
        self.virtual_surface.fill(COLOR_BG)
        
        # Draw Background
        bg = assets.get("bg")
        if bg:
            self.virtual_surface.blit(bg, (0, 0))
            
        # Draw Current Menu
        self.menus[self.state].draw(self.virtual_surface)
        
        # Draw Popup
        if self.active_popup:
            self.active_popup.draw(self.virtual_surface)
            
        # Apply startup fade
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface(VIRTUAL_RES)
            fade_surf.fill(COLOR_BLACK)
            fade_surf.set_alpha(int(self.fade_alpha))
            self.virtual_surface.blit(fade_surf, (0, 0))

        # Scale virtual surface to window size while keeping aspect ratio
        self.screen.fill(COLOR_BLACK)
        ww, wh = self.screen.get_size()
        vw, vh = VIRTUAL_RES
        scale = min(ww/vw, wh/vh)
        dest_size = (int(vw * scale), int(vh * scale))
        dest_pos = ((ww - dest_size[0]) // 2, (wh - dest_size[1]) // 2)
        
        scaled_surf = pygame.transform.scale(self.virtual_surface, dest_size)
        self.screen.blit(scaled_surf, dest_pos)
        
        pygame.display.flip()

    def run(self):
        # Initial fade in
        self.menus[self.state].alpha = 0
        self.menus[self.state].target_alpha = 255
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
