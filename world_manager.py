import json
import os
from blocks import BlockRegistry, InfiniteWorld

class WorldManager:
    def __init__(self, world_data_path: str, block_registry: BlockRegistry):
        self.world_data_path = world_data_path
        self.block_registry = block_registry
        self.loaded_world: InfiniteWorld = None
        self.world_metadata = None

    def create_world(self, world_name: str) -> InfiniteWorld:
        """Create a new infinite world"""
        import random
        world_dir = os.path.join(self.world_data_path, world_name)

        if not os.path.exists(world_dir):
            os.makedirs(world_dir)

        # Create chunks directory
        chunks_dir = os.path.join(world_dir, 'chunks')
        if not os.path.exists(chunks_dir):
            os.makedirs(chunks_dir)

        # Generate world seed
        seed = random.randint(0, 2**31 - 1)

        # Save world metadata
        world_metadata = {
            'name': world_name,
            'seed': seed,
            'player_x': 4.0,
            'player_y': 4.0
        }

        world_file = os.path.join(world_dir, 'world.json')
        try:
            with open(world_file, 'w') as f:
                json.dump(world_metadata, f, indent=2)
            print(f"Created world: {world_name} with seed {seed}")
        except Exception as e:
            print(f"Error creating world metadata: {e}")

        # Create infinite world instance
        infinite_world = InfiniteWorld(seed, self.block_registry, world_dir)

        # Generate initial chunk
        infinite_world.load_or_generate_chunk(0, 0)
        infinite_world.save_all_chunks()

        self.loaded_world = infinite_world
        self.world_metadata = world_metadata

        return infinite_world

    def load_world(self, world_name: str) -> InfiniteWorld:
        """Load an existing infinite world"""
        world_dir = os.path.join(self.world_data_path, world_name)
        world_file = os.path.join(world_dir, 'world.json')

        if not os.path.exists(world_file):
            print(f"World file not found: {world_file}")
            return None

        try:
            with open(world_file, 'r') as f:
                world_metadata = json.load(f)

            seed = world_metadata.get('seed', 0)
            infinite_world = InfiniteWorld(seed, self.block_registry, world_dir)

            self.loaded_world = infinite_world
            self.world_metadata = world_metadata

            print(f"Loaded world: {world_name} with seed {seed}")
            return infinite_world

        except Exception as e:
            print(f"Error loading world: {e}")
            return None

    def save_world(self, world_name: str):
        """Save all chunks and metadata"""
        if self.loaded_world:
            self.loaded_world.save_all_chunks()

            # Update metadata
            if self.world_metadata:
                world_dir = os.path.join(self.world_data_path, world_name)
                world_file = os.path.join(world_dir, 'world.json')
                try:
                    with open(world_file, 'w') as f:
                        json.dump(self.world_metadata, f, indent=2)
                    print(f"Saved world: {world_name}")
                except Exception as e:
                    print(f"Error saving world metadata: {e}")

    def get_block_registry(self) -> BlockRegistry:
        return self.block_registry

    def get_player_spawn_pos(self) -> tuple:
        """Get player spawn position"""
        if self.world_metadata:
            return (
                self.world_metadata.get('player_x', 4.0),
                self.world_metadata.get('player_y', 4.0)
            )
        return (4.0, 4.0)
