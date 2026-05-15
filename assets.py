import pygame
import os
from constants import COLOR_WHITE

class AssetManager:
    def __init__(self):
        self.images = {}
        self.base_path = os.path.join(os.path.dirname(__file__), "assets")
        
    def load_image(self, name, filename):
        path = os.path.join(self.base_path, filename)
        try:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.images[name] = img
                print(f"Loaded {filename} as {name}")
            else:
                print(f"Warning: {filename} not found. Creating placeholder.")
                self.images[name] = self._create_placeholder(name)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            self.images[name] = self._create_placeholder(name)

    def _create_placeholder(self, name):
        # Create a simple colored rectangle with text as a fallback
        font = pygame.font.SysFont("Arial", 12)
        surf = pygame.Surface((100, 40), pygame.SRCALPHA)
        surf.fill((100, 100, 100, 200))
        text = font.render(name, True, COLOR_WHITE)
        surf.blit(text, (surf.get_width()//2 - text.get_width()//2, surf.get_height()//2 - text.get_height()//2))
        return surf

    def get(self, name):
        return self.images.get(name)

# Global asset manager instance
assets = AssetManager()

def load_all_assets():
    # Using actual filenames found in directory
    assets.load_image("bg", "Menu background.png")
    assets.load_image("pressed_long", "Pressed long buton.png")
    assets.load_image("pressed_short", "Pressed short button.png")
    assets.load_image("start", "Start.png")
    assets.load_image("settings", "Settings.png")
    
    # Missing assets - will create placeholders
    assets.load_image("exit", "Exit.png")
    assets.load_image("back", "Back.png")
    assets.load_image("arrow", "Arrow.png")
    assets.load_image("world", "world.png")
    assets.load_image("plus", "plus.png")
    assets.load_image("x", "x.png")
