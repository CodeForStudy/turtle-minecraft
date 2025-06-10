from .block import Block
import json
import numpy as np
from perlin_noise import PerlinNoise
from typing import Optional
import os
import random
from datetime import datetime

# Generation der WElt
def generate_world(world_size: list, seed: Optional[int]=None, scale=30.0, height_ratio=[0.6, 0.0]):
    # Seed generieren wenn keiner gegeben ist
    if seed is None:
      seed = random.randint(0, 2**32 - 1)
    np.random.seed(seed)

    # leeres 3D array der Welt
    world_array = np.full((world_size[0], world_size[1], world_size[2]), None, dtype=object)
  
    # Erzeugen einer Hightmap mit Perlinnoise
    half_width = world_size[0] // 2
    half_depth = world_size[2] // 2
  
    max_height = int(world_size[1] * height_ratio[0])
    noise = PerlinNoise(octaves=2, seed=seed)
    # Skalierung auf Eben und Höhe
    heightmap = np.array([[int((noise([(x - half_width) / scale, (z - half_depth) / scale]) + 1) / 1.5 * max_height) for z in range(world_size[2])] for x in range(world_size[0])])

    # erneute heightmap für Trees
    noise_tree = PerlinNoise(octaves=18, seed=seed+1)
    treemap = np.array([[noise_tree([(x - half_width) / scale, (z - half_depth) / scale]) for z in range(world_size[2])] for x in range(world_size[0])])
    # 1 Baum pro 200 Felder
    amount_trees = world_size[0] * world_size[2] // 200
    # Positionen der Bäume an den höchsten Noisewerten
    indizes = np.argsort(-treemap.reshape(-1))[:amount_trees]
    tree_xz_coords = np.unravel_index(indizes, (world_size[0], world_size[2]))
    tree_xz_coords = np.concatenate( [tree_xz_coords[0].reshape(-1,1), tree_xz_coords[1].reshape(-1,1)], axis=1)

    # Iteration durch jede Achse
    for x_coord in range(world_size[0]):
        for z_coord in range(world_size[2]):
            surface_y = heightmap[x_coord][z_coord]

            # Platzierung von Blöcken abhängig von ihrem Abstand zur Oberfläche
            for y_coord in range(world_size[1]):
                if y_coord > surface_y:
                  pass
                elif y_coord == surface_y:
                  world_array[x_coord, y_coord, z_coord] = {"id": "grass"}
                elif y_coord > surface_y - 3:
                   world_array[x_coord, y_coord, z_coord] = {"id": "dirt"}
                else:
                  world_array[x_coord, y_coord, z_coord] = {"id": "stone"}

    # Überprüfung ob Korrdinate im Rahmen der Wlt ist ist
    def is_valid(coord_x, coord_y, coord_z):
        return (0 <= coord_x < world_size[0] and
                0 <= coord_y < world_size[1] and
                0 <= coord_z < world_size[2])

    # Generation eines Baumes
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

# Weltobjekt
class World:
    # Initiieren von Metadaten
    def __init__(self, path: Optional[str] = None, generate_new_size: Optional[list] = None, world_name: Optional[str] = None, seed: Optional[int] = None):
        self.blocks = []
        self.world_name = world_name
        self.seed = seed
        self.path = path
        self.player_initial_state = None
        self.world_size = None

        # laden oder generieren der Welt
        if path:
            self.load(path)
        else:
            self.generate(generate_new_size)

    def generate(self, world_size):
        if not world_size:
            world_size = [32,16,32]
        
        # generieren eines Seeds wenn keiner gegeben
        actual_seed_for_generation = self.seed if self.seed is not None else random.randint(0, 2**32 - 1)
        world_array, self.seed = generate_world(world_size=world_size, seed=actual_seed_for_generation)
        # Konvertieren des Numpy Arrays zu Blockobjekten
        # self.blocks = []
        half_width = world_array.shape[0] // 2
        half_depth = world_array.shape[2] // 2
        # for x_idx in range(world_array.shape[0]):
        #     for y_coord in range(world_array.shape[1]):
        #         for z_idx in range(world_array.shape[2]):
        #             block_data = world_array[x_idx, y_coord, z_idx]
        #             if block_data is not None:
        #                 world_x = x_idx - half_width
        #                 world_z = z_idx - half_depth
        #                 self.blocks.append(Block(world_x, y_coord, world_z, block_data["id"]))

        # Erstellen  er Block-objekte
        for x in range(world_array.shape[0]):
            for y in range(world_array.shape[1]):
                for z in range(world_array.shape[2]):
                    if world_array[x, y, z]:
                        world_array[x, y, z] = Block(x-half_width, y, z-half_depth, world_array[x,y,z]['id'])
        self.blocks = world_array
            
        # Überprüfen des Weltordners
        if not os.path.exists("worlds"):
            os.makedirs("worlds")

        # Speichern, etc.
        save_path = self._get_save_path(self.world_name, self.seed)
        self.path = save_path
            
        self.world_name = os.path.splitext(os.path.basename(save_path))[0]
        self.save(save_path)

    # Speicherpfad generieren
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
        
    # Welt laden
    def load(self, path):
        self.path = path
        # Aus Pfad laden
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        # neu generieren falls fehlschlägt
        except FileNotFoundError:
            self.generate()
            return

        # Laden von metadaten
        metadata = data.get("metadata", {})
        self.world_name = metadata.get("world_name", os.path.splitext(os.path.basename(path))[0])
        self.seed = metadata.get("seed", None)
        self.player_initial_state = data.get("player_state", None)
        world_size = data.get("world_size", [64,32,64])
        # Laden von Blockobjekten
        self.blocks = np.full((world_size[0], world_size[1], world_size[2]), None, dtype=object)
        half_width = self.blocks.shape[0] // 2
        half_depth = self.blocks.shape[2] // 2
        blocks_data = data.get('blocks', [])
        for b in blocks_data:
            self.blocks[b['x']+half_width, b['y'], b['z']+half_depth] = Block(b['x'], b['y'], b['z'], b.get('id', 'stone'))
        # self.blocks = [Block(b['x'], b['y'], b['z'], b.get('id', 'stone')) for b in data.get('blocks', [])]

    # Speichern der Welt
    def save(self, path: Optional[str] = None, player_state: Optional[dict] = None):
        # Festlegen des Pfades
        save_path = path if path else self.path
        if not save_path:
            save_path = self._get_save_path(self.world_name, self.seed)
            self.path = save_path

        dir_name = os.path.dirname(save_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        elif not os.path.exists(save_path):
            pass
        
        # Formatieren in JSON Format
        blocks_data = []
        for x in range(self.blocks.shape[0]):
            for y in range(self.blocks.shape[1]):
                for z in range(self.blocks.shape[2]):
                    if self.blocks[x, y, z]:
                        blocks_data.append({
                            "x": self.blocks[x, y, z].x,
                            "y": self.blocks[x, y, z].y,
                            "z": self.blocks[x, y, z].z,
                            "id": self.blocks[x, y, z].id
                        })
        # for block in self.blocks:
        #     blocks_data.append({
        #         "x": block.x,
        #         "y": block.y,
        #         "z": block.z,
        #         "id": block.id
        #     })
        
        # hinzufügen von Metadaten
        last_saved_timestamp = datetime.now().isoformat()

        data_to_save = {
            "metadata": {
                "world_name": self.world_name,
                "seed": self.seed,
                "last_saved": last_saved_timestamp,
                "version": "1.0",
                "world_size": list(self.blocks.shape)
            },
            "player_state": player_state if player_state else self.player_initial_state,
            "blocks": blocks_data
        }

        # Speichern sonst Fehlermeldung
        try:
            with open(save_path, 'w') as f:
                json.dump(data_to_save, f, indent=4)
            
        except Exception as e:
            print(f"Fehler beim Speichern der Welt {save_path}: {e}")

    # Ausgabe von Blöcken um einen Punkt herum
    def get_blocks(self, x=None, y=None, z=None, radius=None):
        # bei ungültigen Eingaben alle Blöcke ausgeben
        if x is None or y is None or z is None or radius is None:
            return list(self.blocks.reshape(-1))
        
        half_width = self.blocks.shape[0] // 2
        half_depth = self.blocks.shape[2] // 2

        # Begrenzung der Werte
        def minmax(mi, val, ma):
            return int(min(max(mi, val), ma))
        
        # Auflisten aller Blöcke im Radius
        nearby_blocks = self.blocks[minmax(0, x+half_width-radius, self.blocks.shape[0]):minmax(0, x+half_width+radius, self.blocks.shape[0]),
                                    minmax(0, y-radius, self.blocks.shape[1]):minmax(0, y+radius, self.blocks.shape[1]),
                                    minmax(0, z+half_depth-radius, self.blocks.shape[2]):minmax(0, z+half_depth+radius, self.blocks.shape[2])]
        nearby_blocks = nearby_blocks[nearby_blocks != np.array(None)]

        # Auflisten aller Blöcke im Radius
        # for block in self.blocks:
        #     if abs(block.x - player_x) <= render_distance and \
        #        abs(block.y - player_y) <= render_distance and \
        #        abs(block.z - player_z) <= render_distance:
        #         nearby_blocks.append(block)
        return list(nearby_blocks.reshape(-1))

    # Ausgabe eines gezielten Blocks
    def get_block_at(self, x, y, z):
        x, y, z = int(x), int(y), int(z)
        half_width = self.blocks.shape[0] // 2
        half_depth = self.blocks.shape[2] // 2
        # Wenn die Position in der Welt existiert
        if x+half_width in range(self.blocks.shape[0]) and y in range(self.blocks.shape[1]) and z+half_depth in range(self.blocks.shape[2]):
            return self.blocks[x+half_width, y, z+half_depth]
        return None
    
    # Änderung eies gezielten Blocks
    def change_block_at(self, x, y, z, val):
        x, y, z = int(x), int(y), int(z)
        half_width = self.blocks.shape[0] // 2
        half_depth = self.blocks.shape[2] // 2
        # Wenn die Position in der Welt existiert
        if x+half_width in range(self.blocks.shape[0]) and y in range(self.blocks.shape[1]) and z+half_depth in range(self.blocks.shape[2]):
            self.blocks[x+half_width, y, z+half_depth] = val