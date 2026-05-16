import json
import os
import random
import pygame
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

@dataclass
class Block:
    id: str
    name: str
    texture: Optional[pygame.Surface] = None
    properties: Dict = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}

class BlockRegistry:
    def __init__(self, blocks_json_path: str):
        self.blocks_json_path = blocks_json_path
        self.blocks: Dict[str, Block] = {}
        self.block_textures: Dict[str, pygame.Surface] = {}
        self.block_list: List[str] = []
        self.load_definitions()

    def load_definitions(self):
        try:
            with open(self.blocks_json_path, 'r') as f:
                data = json.load(f)

            blocks_data = data.get('blocks', {})
            base_path = os.path.dirname(self.blocks_json_path)

            for block_id, block_data in blocks_data.items():
                block = Block(
                    id=block_data['id'],
                    name=block_data['name'],
                    properties=block_data.get('properties', {})
                )
                self.blocks[block_id] = block
                self.block_list.append(block_id)

            print(f"Loaded {len(self.blocks)} block definitions")
        except Exception as e:
            print(f"Error loading block definitions: {e}")
            self.blocks = {}
            self.block_list = []

    def load_textures(self, assets_manager=None):
        try:
            with open(self.blocks_json_path, 'r') as f:
                data = json.load(f)

            blocks_data = data.get('blocks', {})
            base_path = os.path.dirname(self.blocks_json_path)

            for block_id, block_data in blocks_data.items():
                texture_file = block_data['texture']
                texture_path = os.path.join(base_path, texture_file)

                if os.path.exists(texture_path):
                    try:
                        img = pygame.image.load(texture_path).convert_alpha()
                        self.block_textures[block_id] = img
                        if block_id in self.blocks:
                            self.blocks[block_id].texture = img
                        print(f"Loaded texture for block: {block_id}")
                    except Exception as e:
                        print(f"Error loading texture for {block_id}: {e}")
                        self.block_textures[block_id] = self._create_placeholder(block_id)
                else:
                    print(f"Texture file not found: {texture_path}")
                    self.block_textures[block_id] = self._create_placeholder(block_id)

        except Exception as e:
            print(f"Error in load_textures: {e}")

    def _create_placeholder(self, block_id: str) -> pygame.Surface:
        colors = {
            'grass': (34, 139, 34),
            'dirt': (139, 69, 19),
            'stone': (128, 128, 128),
            'log': (101, 67, 33),
            'plank': (139, 90, 43),
            'grass_side': (34, 139, 34)
        }
        color = colors.get(block_id, (100, 100, 100))
        surf = pygame.Surface((16, 16))
        surf.fill(color)
        return surf

    def get_block(self, block_id: str) -> Optional[Block]:
        return self.blocks.get(block_id)

    def get_texture(self, block_id: str) -> Optional[pygame.Surface]:
        return self.block_textures.get(block_id)

    def get_random_block_id(self) -> str:
        if not self.block_list:
            return 'grass'
        return random.choice(self.block_list)


class Chunk:
    def __init__(self, chunk_x: int, chunk_y: int, size: int = 8):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.size = size
        self.grid: List[List[str]] = [['grass' for _ in range(size)] for _ in range(size)]

    def get_block(self, local_x: int, local_y: int) -> Optional[str]:
        if 0 <= local_x < self.size and 0 <= local_y < self.size:
            return self.grid[local_y][local_x]
        return None

    def set_block(self, local_x: int, local_y: int, block_id: str):
        if 0 <= local_x < self.size and 0 <= local_y < self.size:
            self.grid[local_y][local_x] = block_id

    def to_dict(self) -> Dict:
        return {
            'chunk_x': self.chunk_x,
            'chunk_y': self.chunk_y,
            'grid': self.grid
        }

    @staticmethod
    def from_dict(data: Dict) -> 'Chunk':
        chunk = Chunk(data['chunk_x'], data['chunk_y'])
        chunk.grid = data.get('grid', [['grass' for _ in range(8)] for _ in range(8)])
        return chunk


class ChunkGenerator:
    def __init__(self, seed: int):
        self.seed = seed

    def generate_chunk(self, chunk_x: int, chunk_y: int, block_registry: BlockRegistry) -> Chunk:
        """Generate a deterministic chunk based on seed and coordinates"""
        chunk = Chunk(chunk_x, chunk_y)

        block_weights = {
            'grass': 1,
            'dirt': 0,
            'stone': 0,
            'grass_side': 0,
            'log': 0,
            'plank': 0
        }

        for y in range(8):
            for x in range(8):
                # Deterministic random based on seed + chunk coords + block coords
                hash_input = f"{self.seed}:{chunk_x}:{chunk_y}:{x}:{y}"
                hash_obj = hashlib.md5(hash_input.encode())
                rand_val = int(hash_obj.hexdigest(), 16) / (2 ** 128)

                cumulative = 0
                for block_id, weight in block_weights.items():
                    cumulative += weight
                    if rand_val <= cumulative:
                        chunk.grid[y][x] = block_id
                        break

        return chunk


class InfiniteWorld:
    def __init__(self, seed: int, block_registry: BlockRegistry, world_dir: str, chunk_size: int = 8):
        self.seed = seed
        self.block_registry = block_registry
        self.world_dir = world_dir
        self.chunk_size = chunk_size
        self.generator = ChunkGenerator(seed)
        self.chunks: Dict[Tuple[int, int], Chunk] = {}
        self.chunks_dir = os.path.join(world_dir, 'chunks')

        if not os.path.exists(self.chunks_dir):
            os.makedirs(self.chunks_dir)

    def get_chunk_key(self, chunk_x: int, chunk_y: int) -> str:
        return f"chunk_{chunk_x}_{chunk_y}.json"

    def load_or_generate_chunk(self, chunk_x: int, chunk_y: int) -> Chunk:
        """Load chunk from disk or generate if doesn't exist"""
        key = (chunk_x, chunk_y)

        if key in self.chunks:
            return self.chunks[key]

        chunk_file = os.path.join(self.chunks_dir, self.get_chunk_key(chunk_x, chunk_y))

        if os.path.exists(chunk_file):
            try:
                with open(chunk_file, 'r') as f:
                    data = json.load(f)
                chunk = Chunk.from_dict(data)
                self.chunks[key] = chunk
                print(f"Loaded chunk ({chunk_x}, {chunk_y})")
                return chunk
            except Exception as e:
                print(f"Error loading chunk ({chunk_x}, {chunk_y}): {e}")
                return self.generate_and_save_chunk(chunk_x, chunk_y)
        else:
            return self.generate_and_save_chunk(chunk_x, chunk_y)

    def generate_and_save_chunk(self, chunk_x: int, chunk_y: int) -> Chunk:
        """Generate a new chunk and save to disk"""
        chunk = self.generator.generate_chunk(chunk_x, chunk_y, self.block_registry)
        self.chunks[(chunk_x, chunk_y)] = chunk
        self.save_chunk(chunk_x, chunk_y)
        print(f"Generated and saved chunk ({chunk_x}, {chunk_y})")
        return chunk

    def save_chunk(self, chunk_x: int, chunk_y: int):
        """Save chunk to disk"""
        if (chunk_x, chunk_y) not in self.chunks:
            return

        chunk = self.chunks[(chunk_x, chunk_y)]
        chunk_file = os.path.join(self.chunks_dir, self.get_chunk_key(chunk_x, chunk_y))

        try:
            with open(chunk_file, 'w') as f:
                json.dump(chunk.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving chunk ({chunk_x}, {chunk_y}): {e}")

    def get_block_at(self, world_x: float, world_y: float) -> Optional[str]:
        """Get block at world coordinates"""
        chunk_x = int(world_x // self.chunk_size)
        chunk_y = int(world_y // self.chunk_size)
        local_x = int(world_x % self.chunk_size)
        local_y = int(world_y % self.chunk_size)

        chunk = self.load_or_generate_chunk(chunk_x, chunk_y)
        return chunk.get_block(local_x, local_y)

    def set_block_at(self, world_x: float, world_y: float, block_id: str):
        """Set block at world coordinates"""
        chunk_x = int(world_x // self.chunk_size)
        chunk_y = int(world_y // self.chunk_size)
        local_x = int(world_x % self.chunk_size)
        local_y = int(world_y % self.chunk_size)

        chunk = self.load_or_generate_chunk(chunk_x, chunk_y)
        chunk.set_block(local_x, local_y, block_id)

    def get_visible_chunks(self, player_x: float, player_y: float, view_radius: int) -> List[Chunk]:
        """Get all chunks visible around player"""
        player_chunk_x = int(player_x // self.chunk_size)
        player_chunk_y = int(player_y // self.chunk_size)

        visible = []
        for cx in range(player_chunk_x - view_radius, player_chunk_x + view_radius + 1):
            for cy in range(player_chunk_y - view_radius, player_chunk_y + view_radius + 1):
                chunk = self.load_or_generate_chunk(cx, cy)
                visible.append(chunk)

        return visible

    def save_all_chunks(self):
        """Save all loaded chunks to disk"""
        for chunk_x, chunk_y in self.chunks.keys():
            self.save_chunk(chunk_x, chunk_y)

    def pregenerate_chunks(self, center_x: int, center_y: int, radius: int):
        """Pregenerate chunks in a radius around a center point"""
        print(f"Pregenerating {(radius*2+1)**2} chunks in radius {radius} around ({center_x}, {center_y})...")
        pregenerated_count = 0
        for cx in range(center_x - radius, center_x + radius + 1):
            for cy in range(center_y - radius, center_y + radius + 1):
                self.load_or_generate_chunk(cx, cy)
                pregenerated_count += 1
        print(f"Pregeneration complete: {pregenerated_count} chunks generated")
