import pygame
import sys
import json
import os
import shutil
from constants import *
from assets import load_all_assets, assets
from ui import Button, Menu, WorldView
from blocks import BlockRegistry
from world_manager import WorldManager
from player import Player

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

        # Block and World system
        blocks_json_path = os.path.join(os.path.dirname(__file__), "assets", "blocks", "blocks.json")
        self.block_registry = BlockRegistry(blocks_json_path)
        self.block_registry.load_textures()
        self.world_manager = WorldManager(self.world_data_path, self.block_registry)
        self.current_infinite_world = None
        self.current_world_name = None
        self.player = None

        self.worlds = self.load_worlds()
        self.active_popup = None

        self.menus = {
            GameState.MAIN_MENU: self.create_main_menu(),
            GameState.SETTINGS: self.create_settings_menu(),
            GameState.WORLD_SELECT: self.create_world_select_menu(),
            GameState.WORLD_EDITOR: None
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
                lambda name=world_name: self.view_world(name),
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
            # Create world using world manager (creates infinite world)
            self.world_manager.create_world(name)
            self.worlds.append(name)
            self.save_worlds()
            # Recreate menu to reflect changes
            self.menus[GameState.WORLD_SELECT] = self.create_world_select_menu()
        self.active_popup = None

    def view_world(self, world_name):
        """Load and view a world"""
        self.current_world_name = world_name
        self.current_infinite_world = self.world_manager.load_world(world_name)
        if self.current_infinite_world:
            # Get spawn position
            spawn_x, spawn_y = self.world_manager.get_player_spawn_pos()
            self.player = Player(spawn_x, spawn_y)
            
            # Pregenerate a city-sized area (10x10 chunks = 80x80 blocks)
            spawn_chunk_x = int(spawn_x // 8)
            spawn_chunk_y = int(spawn_y // 8)
            self.current_infinite_world.pregenerate_chunks(spawn_chunk_x, spawn_chunk_y, radius=5)
            
            # Save all pregenerated chunks to disk
            self.current_infinite_world.save_all_chunks()
            
            self.menus[GameState.WORLD_EDITOR] = self.create_world_editor()
            self.change_state(GameState.WORLD_EDITOR)
        else:
            print(f"Failed to load world: {world_name}")

    def delete_world(self, index):
        if 0 <= index < len(self.worlds):
            world_name = self.worlds[index]
            # Delete directory
            world_dir = os.path.join(self.world_data_path, world_name)
            if os.path.exists(world_dir):
                try:
                    shutil.rmtree(world_dir)
                    print(f"Deleted world data: {world_dir}")
                except Exception as e:
                    print(f"Error deleting world data: {e}")

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

    def create_world_editor(self):
        if self.current_infinite_world and self.block_registry and self.player:
            world_view = WorldView(self.current_infinite_world, self.block_registry, self.player)
            world_view.target_alpha = 255
            return world_view
        return None

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
                    continue  # Event consumed by popup

            if self.state == GameState.WORLD_EDITOR:
                # Handle world editor events (player input, back button)
                world_view = self.menus[self.state]
                if world_view:
                    world_view.handle_event(event)

                # Handle back button (ESC key or click)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.save_and_exit_world()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        # Check if back button clicked (40, 40)
                        if 20 <= virtual_mx <= 60 and 20 <= virtual_my <= 60:
                            self.save_and_exit_world()
            else:
                self.menus[self.state].handle_event(event)

    def save_and_exit_world(self):
        """Save world and return to world select"""
        if self.current_world_name and self.current_infinite_world:
            self.world_manager.save_world(self.current_world_name)
        self.change_state(GameState.WORLD_SELECT)

    def update(self):
        dt = self.clock.tick(FPS) / 1000.0

        if self.state == GameState.WORLD_EDITOR:
            world_view = self.menus[self.state]
            if world_view:
                world_view.update(dt, self.mouse_pos)
                # Pre-load chunks around player (dynamic radius)
                if self.player and self.current_infinite_world:
                    view_radius = world_view.calculate_view_radius()
                    self.current_infinite_world.get_visible_chunks(
                        self.player.world_x, self.player.world_y, view_radius
                    )
        else:
            current_menu = self.menus[self.state]
            current_menu.update(dt, self.mouse_pos)

        # Handle state transitions
        if self.next_state:
            current_menu = self.menus.get(self.state)
            if current_menu and hasattr(current_menu, 'alpha'):
                if current_menu.alpha <= 0:
                    self.state = self.next_state
                    self.next_state = None
                    next_menu = self.menus[self.state]
                    if hasattr(next_menu, 'alpha'):
                        next_menu.alpha = 0
                        next_menu.target_alpha = 255
            else:
                self.state = self.next_state
                self.next_state = None
                next_menu = self.menus[self.state]
                if hasattr(next_menu, 'alpha'):
                    next_menu.alpha = 0
                    next_menu.target_alpha = 255

        if self.active_popup:
            self.active_popup.update(dt)

        # Startup fade
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - TRANSITION_SPEED * 255 * dt)

    def draw(self):
        self.virtual_surface.fill(COLOR_BG)

        if self.state == GameState.WORLD_EDITOR:
            # Draw world editor view
            world_view = self.menus[self.state]
            if world_view:
                world_view.draw(self.virtual_surface)

            # Draw back button overlay
            back_button = Button(
                "Back",
                (40, 40),
                assets.get("back"),
                assets.get("pressed_long"),
                lambda: self.save_and_exit_world(),
                scale=1.0
            )
            back_button.draw(self.virtual_surface)
        else:
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
