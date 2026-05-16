import pygame
from constants import PLAYER_SPEED, COLOR_BLACK, VIRTUAL_RES

class Player:
    def __init__(self, world_x: float = 0, world_y: float = 0):
        self.world_x = world_x
        self.world_y = world_y
        self.size = 16  # 16x16 pixel box
        self.speed = PLAYER_SPEED

        # Input tracking
        self.keys_pressed = set()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.keys_pressed.add(event.key)
        elif event.type == pygame.KEYUP:
            self.keys_pressed.discard(event.key)

    def update(self, dt):
        """Update player position based on input"""
        dx = 0
        dy = 0

        # WASD and Arrow keys
        if pygame.K_w in self.keys_pressed or pygame.K_UP in self.keys_pressed:
            dy -= self.speed
        if pygame.K_s in self.keys_pressed or pygame.K_DOWN in self.keys_pressed:
            dy += self.speed
        if pygame.K_a in self.keys_pressed or pygame.K_LEFT in self.keys_pressed:
            dx -= self.speed
        if pygame.K_d in self.keys_pressed or pygame.K_RIGHT in self.keys_pressed:
            dx += self.speed

        self.world_x += dx
        self.world_y += dy

    def get_chunk_pos(self, chunk_size: int = 8) -> tuple:
        """Get which chunk the player is in"""
        chunk_x = int(self.world_x // chunk_size)
        chunk_y = int(self.world_y // chunk_size)
        return chunk_x, chunk_y

    def draw(self, surface, camera_x: float = 0, camera_y: float = 0, block_size: int = 16):
        """Draw player as a black box at screen center"""
        # Player is always at center of screen
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2

        rect = pygame.Rect(center_x - self.size // 2, center_y - self.size // 2, self.size, self.size)
        pygame.draw.rect(surface, COLOR_BLACK, rect)
