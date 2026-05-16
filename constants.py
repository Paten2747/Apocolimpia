import pygame

# Screen settings
VIRTUAL_RES = (640, 360)  # Pixel-art friendly resolution
INITIAL_WINDOW_SIZE = (1280, 720)
WINDOW_TITLE = "Apocalympia - Main Menu"
FPS = 60

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BG = (20, 20, 25)  # Dark apocalyptic fallback

# UI Constants
BUTTON_FLOAT_AMPLITUDE = 0.0
BUTTON_FLOAT_SPEED = 0.003
HOVER_SCALE_SPEED = 15.0  # Lerp speed
TRANSITION_SPEED = 5.0    # Fade speed

# World Constants
CHUNK_SIZE = 8            # 8x8 blocks per chunk
PLAYER_SPEED = 1          # blocks per frame
VIEW_RADIUS = 2           # 2-chunk radius (5x5 chunks visible)
BLOCK_PIXEL_SIZE = 16     # 16x16 pixels per block on screen

# Menu States
class GameState:
    MAIN_MENU = "main_menu"
    SETTINGS = "settings"
    WORLD_SELECT = "world_select"
    WORLD_EDITOR = "world_editor"
    EXIT = "exit"
