from .block import Block
import json
import numpy as np
from perlin_noise import PerlinNoise
from typing import Optional
import os
import random
from datetime import datetime

def generate_world(world_size: list, seed: Optional[int]=None, scale=30.0, height_ratio=[0.6, 0.0]):
  if seed is None:
    seed = random.randint(0, 2**32 - 1)
  np.random.seed(seed)

  world_array = np.full((world_size[0], world_size[1], world_size[2]), None, dtype=object)
  
  half_width = world_size[0] // 2
  half_depth = world_size[2] // 2
  
  max_height = int(world_size[1] * height_ratio[0])
  noise = PerlinNoise(octaves=2, seed=seed)
  heightmap = np.array([[int((noise([(x - half_width) / scale, (z - half_depth) / scale]) + 1) / 1.5 * max_height) for z in range(world_size[2])] for x in range(world_size[0])])


  noise_tree = PerlinNoise(octaves=18, seed=seed+1)
  treemap = np.array([[noise_tree([(x - half_width) / scale, (z - half_depth) / scale]) for z in range(world_size[2])] for x in range(world_size[0])])
  amount_trees = world_size[0] * world_size[2] // 200
  indizes = np.argsort(-treemap.reshape(-1))[:amount_trees]
  tree_xz_coords = np.unravel_index(indizes, (world_size[0], world_size[2]))
  tree_xz_coords = np.concatenate( [tree_xz_coords[0].reshape(-1,1), tree_xz_coords[1].reshape(-1,1)], axis=1)

  for x_coord in range(world_size[0]):
    for z_coord in range(world_size[2]):
      surface_y = heightmap[x_coord][z_coord]

      for y_coord in range(world_size[1]):
        if y_coord > surface_y:
          pass
        elif y_coord == surface_y:
          world_array[x_coord, y_coord, z_coord] = {"id": "grass"}
        elif y_coord > surface_y - 3:
           world_array[x_coord, y_coord, z_coord] = {"id": "dirt"}
        else:
          world_array[x_coord, y_coord, z_coord] = {"id": "stone"}

  def is_valid(coord_x, coord_y, coord_z):
      return (0 <= coord_x < world_size[0] and
              0 <= coord_y < world_size[1] and
              0 <= coord_z < world_size[2])

  def generate_tree_at_pos(pos3_idx):
    for i in range(4):
        if is_valid(pos3_idx[0], pos3_idx[1] + i, pos3_idx[2]):
            world_array[pos3_idx[0], pos3_idx[1] + i, pos3_idx[2]] = {"id": "log"}
        else:
            return

    leaf_y1_idx = pos3_idx[1] + 3
    for lx_offset in range(-2, 3):
        for lz_offset in range(-2, 3):
            leaf_x_idx, leaf_z_idx = pos3_idx[0] + lx_offset, pos3_idx[2] + lz_offset
            if is_valid(leaf_x_idx, leaf_y1_idx, leaf_z_idx):
                if world_array[leaf_x_idx, leaf_y1_idx, leaf_z_idx] is None or world_array[leaf_x_idx, leaf_y1_idx, leaf_z_idx]["id"] != "log":
                    world_array[leaf_x_idx, leaf_y1_idx, leaf_z_idx] = {"id": "leaves"}
    
    leaf_y2_idx = pos3_idx[1] + 4
    for lx_offset in range(-1, 2):
        for lz_offset in range(-1, 2):
            leaf_x_idx, leaf_z_idx = pos3_idx[0] + lx_offset, pos3_idx[2] + lz_offset
            if is_valid(leaf_x_idx, leaf_y2_idx, leaf_z_idx):
                 if world_array[leaf_x_idx, leaf_y2_idx, leaf_z_idx] is None or world_array[leaf_x_idx, leaf_y2_idx, leaf_z_idx]["id"] != "log":
                    world_array[leaf_x_idx, leaf_y2_idx, leaf_z_idx] = {"id": "leaves"}
  
  for tree_x_idx, tree_z_idx in tree_xz_coords:
    if 0 <= tree_x_idx < heightmap.shape[0] and 0 <= tree_z_idx < heightmap.shape[1]:
        surface_y_idx = heightmap[tree_x_idx, tree_z_idx]
        tree_y_idx = surface_y_idx + 1

        if world_array[tree_x_idx, surface_y_idx, tree_z_idx] is not None and \
           world_array[tree_x_idx, surface_y_idx, tree_z_idx]["id"] == "grass" and \
           tree_y_idx < world_size[1] - 5:
            generate_tree_at_pos(np.array([tree_x_idx, tree_y_idx, tree_z_idx]))

  return world_array, seed

class World:
    def __init__(self, path: Optional[str] = None, generate_new_size: Optional[list] = None, world_name: Optional[str] = None, seed: Optional[int] = None):
        self.blocks = []
        self.world_name = world_name
        self.seed = seed
        self.path = path
        self.player_initial_state = None

        if path:
            self.load(path)
        elif generate_new_size:
            
            actual_seed_for_generation = self.seed if self.seed is not None else random.randint(0, 2**32 - 1)
            world_array, self.seed = generate_world(world_size=generate_new_size, seed=actual_seed_for_generation)
            
            self.blocks = []
            half_width = world_array.shape[0] // 2
            half_depth = world_array.shape[2] // 2
            for x_idx in range(world_array.shape[0]):
                for y_coord in range(world_array.shape[1]):
                    for z_idx in range(world_array.shape[2]):
                        block_data = world_array[x_idx, y_coord, z_idx]
                        if block_data is not None:
                            world_x = x_idx - half_width
                            world_z = z_idx - half_depth
                            self.blocks.append(Block(world_x, y_coord, world_z, block_data["id"]))
            
            if not os.path.exists("worlds"):
                os.makedirs("worlds")

            
            save_path = self._get_save_path(self.world_name, self.seed)
            self.path = save_path
            
            self.world_name = os.path.splitext(os.path.basename(save_path))[0]
            self.save(save_path)
            
        else:
            
            actual_seed_for_generation = self.seed if self.seed is not None else random.randint(0, 2**32 - 1)
            world_array, self.seed = generate_world(world_size=[32,16,32], seed=actual_seed_for_generation)
            self.blocks = []
            half_width = world_array.shape[0] // 2
            half_depth = world_array.shape[2] // 2
            for x_idx in range(world_array.shape[0]):
                for y_coord in range(world_array.shape[1]):
                    for z_idx in range(world_array.shape[2]):
                        block_data = world_array[x_idx, y_coord, z_idx]
                        if block_data is not None:
                            world_x = x_idx - half_width
                            world_z = z_idx - half_depth
                            self.blocks.append(Block(world_x, y_coord, world_z, block_data["id"]))
            
            save_path = self._get_save_path(self.world_name, self.seed)
            self.path = save_path
            
            self.world_name = os.path.splitext(os.path.basename(save_path))[0]
            self.save(save_path)
            

    def _get_save_path(self, world_name: Optional[str], seed: Optional[int]) -> str:
        base_path = "worlds"
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        name_part = world_name if world_name else (str(seed) if seed is not None else "world")
        
        filename = f"{name_part}.json"
        potential_path = os.path.join(base_path, filename)
        
        if not os.path.exists(potential_path):
            return potential_path
        else:
            i = 1
            while True:
                numbered_filename = f"{name_part}_{i}.json"
                potential_path = os.path.join(base_path, numbered_filename)
                if not os.path.exists(potential_path):
                    return potential_path
                i += 1
        

    def load(self, path):
        self.path = path
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.world_name = os.path.splitext(os.path.basename(path))[0]
            actual_seed_for_generation = self.seed if self.seed is not None else random.randint(0, 2**32 - 1)
            world_array, self.seed = generate_world(world_size=[64, 32, 64], seed=actual_seed_for_generation) 
            self.blocks = []
            half_width = world_array.shape[0] // 2
            half_depth = world_array.shape[2] // 2
            for x_idx in range(world_array.shape[0]):
                for y_idx in range(world_array.shape[1]):
                    for z_idx in range(world_array.shape[2]):
                        if world_array[x_idx, y_idx, z_idx] is not None:
                            block_id = world_array[x_idx, y_idx, z_idx].get("id", "stone")
                            self.blocks.append(Block(x_idx - half_width, y_idx, z_idx - half_depth, block_id))
            new_save_path = self._get_save_path(self.world_name, self.seed)
            self.path = new_save_path
            self.world_name = os.path.splitext(os.path.basename(new_save_path))[0]
            self.save(new_save_path)
            return

        metadata = data.get("metadata", {})
        self.world_name = metadata.get("world_name", os.path.splitext(os.path.basename(path))[0])
        self.seed = metadata.get("seed", None)
        self.player_initial_state = data.get("player_state", None)

        self.blocks = [Block(b['x'], b['y'], b['z'], b.get('id', 'stone')) for b in data.get('blocks', [])]


    def save(self, path: Optional[str] = None, player_state: Optional[dict] = None):
        save_path = path if path else self.path
        if not save_path:
            save_path = self._get_save_path(self.world_name, self.seed)
            self.path = save_path

        dir_name = os.path.dirname(save_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        elif not os.path.exists(save_path):
            pass

        blocks_data = []
        for block in self.blocks:
            blocks_data.append({
                "x": block.x,
                "y": block.y,
                "z": block.z,
                "id": block.id
            })
        
        
        last_saved_timestamp = datetime.now().isoformat()

        data_to_save = {
            "metadata": {
                "world_name": self.world_name,
                "seed": self.seed,
                "last_saved": last_saved_timestamp,
                "version": "1.0"
            },
            "player_state": player_state if player_state else self.player_initial_state,
            "blocks": blocks_data
        }

        try:
            with open(save_path, 'w') as f:
                json.dump(data_to_save, f, indent=4)
            
        except Exception as e:
            print(f"Fehler beim Speichern der Welt {save_path}: {e}")


    def get_blocks(self, player_x=None, player_y=None, player_z=None, render_distance=None):
        if player_x is None or player_y is None or player_z is None or render_distance is None:
            return self.blocks

        nearby_blocks = []
        for block in self.blocks:
            if abs(block.x - player_x) <= render_distance and \
               abs(block.y - player_y) <= render_distance and \
               abs(block.z - player_z) <= render_distance:
                nearby_blocks.append(block)
        return nearby_blocks

    def get_block_at(self, x, y, z):
        for block in self.blocks:
            if block.x == x and block.y == y and block.z == z:
                return block
        return None
