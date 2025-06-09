from engine.block import Block
import math

class Entity:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def get_position(self):
        return (self.x, self.y, self.z)

    def update(self, world):
        pass

class Player(Entity):
    def __init__(self, x, y, z, yaw=0.0, pitch=0.0):
        super().__init__(x, y, z)
        self.yaw = yaw
        self.pitch = pitch
        self.mode = 'player'
        
        self.move_speed = 2.5
        self.sprint_multiplier = 1.5
        self.turn_speed = 3.0 * 60
        self.y_velocity = 0.0
        self.gravity_acceleration = 20.0
        self.jump_initial_speed = 8.0
        self.on_ground = False
        self.radius = 0.2
        self.height = 1.8
        self.hitbox_center_adjustment = -0.5

    def _intersects_xz(self, player_center_x, player_center_z, block_x, block_z):
        
        closest_x = max(block_x, min(player_center_x, block_x + 1))
        closest_z = max(block_z, min(player_center_z, block_z + 1))

        distance_x = player_center_x - closest_x
        distance_z = player_center_z - closest_z

        distance_squared = (distance_x**2) + (distance_z**2)
        return distance_squared < (self.radius**2)

    def set_mode(self, mode):
        self.mode = mode
        if mode == 'spectator':
            self.y_velocity = 0

    def jump(self):
        if self.on_ground and self.mode == 'player':
            self.y_velocity = self.jump_initial_speed
            self.on_ground = False

    def update(self, world, input_state, delta_time):
        dx, dy, dz = 0, 0, 0
        

        moving = input_state['moving']
        turning = input_state['turning']
        jumping = input_state.get('jumping', False)
        sprinting = input_state.get('sprinting', False)
        

        
        if turning['Left']:
            self.yaw -= self.turn_speed * delta_time
        if turning['Right']:
            self.yaw += self.turn_speed * delta_time
        if turning['Up']:
            self.pitch -= self.turn_speed * delta_time
        if turning['Down']:
            self.pitch += self.turn_speed * delta_time

        
        self.yaw = (self.yaw + 180) % 360 - 180

        
        
        self.pitch = max(-89, min(89, self.pitch))

        yaw_rad = math.radians(self.yaw)
        pitch_rad = math.radians(self.pitch)

        if jumping:
            self.jump()

        current_move_speed_actual = self.move_speed
        
        if sprinting and moving['w']:
            current_move_speed_actual *= self.sprint_multiplier
        elif not moving['w']:
            sprinting = False

        if self.mode == 'spectator':
            
            if moving['w']:
                dx += math.sin(yaw_rad) * math.cos(pitch_rad) * current_move_speed_actual * delta_time
                dy += math.sin(pitch_rad) * current_move_speed_actual * delta_time
                dz += math.cos(yaw_rad) * math.cos(pitch_rad) * current_move_speed_actual * delta_time
            if moving['s']:
                dx -= math.sin(yaw_rad) * math.cos(pitch_rad) * self.move_speed * delta_time
                dy -= math.sin(pitch_rad) * self.move_speed * delta_time
                dz -= math.cos(yaw_rad) * math.cos(pitch_rad) * self.move_speed * delta_time
            if moving['a']:
                dx -= math.cos(yaw_rad) * self.move_speed * delta_time
                dz += math.sin(yaw_rad) * self.move_speed * delta_time
            if moving['d']:
                dx += math.cos(yaw_rad) * self.move_speed * delta_time
                dz -= math.sin(yaw_rad) * self.move_speed * delta_time
            
            self.x += dx
            self.y += dy
            self.z += dz
        else:
            adjustment = self.hitbox_center_adjustment
            collision_check_radius = 3
            nearby_blocks = world.get_blocks(self.x, self.y, self.z, collision_check_radius)

            
            if moving['w']:
                dx_player = math.sin(yaw_rad) * current_move_speed_actual * delta_time
                dz_player = math.cos(yaw_rad) * current_move_speed_actual * delta_time
                dx += dx_player
                dz += dz_player
            if moving['s']:
                dx_player = math.sin(yaw_rad) * self.move_speed * delta_time
                dz_player = math.cos(yaw_rad) * self.move_speed * delta_time
                dx -= dx_player
                dz -= dz_player
            if moving['a']:
                dx_player = math.cos(yaw_rad) * self.move_speed * delta_time
                dz_player = math.sin(yaw_rad) * self.move_speed * delta_time
                dx -= dx_player
                dz += dz_player
            if moving['d']:
                dx_player = math.cos(yaw_rad) * self.move_speed * delta_time
                dz_player = math.sin(yaw_rad) * self.move_speed * delta_time
                dx += dx_player
                dz -= dz_player

            
            self.y_velocity -= self.gravity_acceleration * delta_time
            
            current_y_before_vertical_move = self.y
            
            potential_y_change_this_frame = self.y_velocity * delta_time
            potential_next_y = current_y_before_vertical_move + potential_y_change_this_frame

            self.on_ground = False

            if self.y_velocity > 0:
                colliding_ceiling_blocks = []
                eff_player_x_for_collision = self.x - adjustment
                eff_player_z_for_collision = self.z - adjustment

                for block in nearby_blocks:
                    if self._intersects_xz(eff_player_x_for_collision, eff_player_z_for_collision, block.x, block.z):
                        current_head_y = current_y_before_vertical_move + self.height
                        potential_head_y = potential_next_y + self.height
                        block_bottom_y = float(block.y)
                        
                        if current_head_y <= block_bottom_y + 0.01 and potential_head_y >= block_bottom_y - 0.01:
                            colliding_ceiling_blocks.append(block)
                
                if colliding_ceiling_blocks:
                    lowest_colliding_ceiling = min(colliding_ceiling_blocks, key=lambda b: b.y)
                    self.y = lowest_colliding_ceiling.y - self.height - 0.001
                    self.y_velocity = 0
                    potential_next_y = self.y
            
            if self.y_velocity <= 0:
                colliding_ground_blocks = []
                eff_player_x_for_ground = self.x - adjustment
                eff_player_z_for_ground = self.z - adjustment

                for block in nearby_blocks:
                    if self._intersects_xz(eff_player_x_for_ground, eff_player_z_for_ground, block.x, block.z):
                        block_top_y = float(block.y) + 1.0
                        
                        
                        if current_y_before_vertical_move >= block_top_y - 0.01 and potential_next_y <= block_top_y + 0.01:
                            colliding_ground_blocks.append(block)
                
                if colliding_ground_blocks:
                    highest_landing_block = max(colliding_ground_blocks, key=lambda b: b.y)
                    self.y = highest_landing_block.y + 1.0
                    self.y_velocity = 0
                    self.on_ground = True
                else:
                    self.y = potential_next_y
            else:
                 self.y = potential_next_y

            
            potential_eff_player_x = (self.x + dx) - adjustment
            current_eff_player_z = self.z - adjustment

            if dx != 0:
                collided_x_flag = False
                for block in nearby_blocks:
                    player_bottom = self.y
                    player_top = self.y + self.height
                    block_bottom_y = float(block.y)
                    block_top_y = float(block.y) + 1.0
                    y_overlap = (player_bottom < block_top_y and player_top > block_bottom_y)

                    if y_overlap:
                        if self._intersects_xz(potential_eff_player_x, current_eff_player_z, block.x, block.z):
                            resolved_eff_player_x = 0
                            if dx > 0:
                                resolved_eff_player_x = float(block.x) - self.radius - 0.001
                            else:
                                resolved_eff_player_x = float(block.x) + 1.0 + self.radius + 0.001
                            self.x = resolved_eff_player_x + adjustment
                            collided_x_flag = True
                            break
                if not collided_x_flag:
                    self.x += dx
            
            potential_eff_player_z = (self.z + dz) - adjustment
            current_eff_player_x = self.x - adjustment
            
            if dz != 0:
                collided_z_flag = False
                for block in nearby_blocks:
                    player_bottom = self.y
                    player_top = self.y + self.height
                    block_bottom_y = float(block.y)
                    block_top_y = float(block.y) + 1.0
                    y_overlap = (player_bottom < block_top_y and player_top > block_bottom_y)

                    if y_overlap:
                        if self._intersects_xz(current_eff_player_x, potential_eff_player_z, block.x, block.z):
                            resolved_eff_player_z = 0
                            if dz > 0:
                                resolved_eff_player_z = float(block.z) - self.radius - 0.001
                            else:
                                resolved_eff_player_z = float(block.z) + 1.0 + self.radius + 0.001
                            self.z = resolved_eff_player_z + adjustment
                            collided_z_flag = True
                            break
                if not collided_z_flag:
                    self.z += dz

        if self.y < -40:
            self.x = 0
            self.z = 0
            self.y = self._find_teleport_y(world, self.x, self.z)
            self.y_velocity = 0

    def _find_teleport_y(self, world, x, z):
        blocks_at_xz = [b for b in world.get_blocks() if int(b.x) == int(x) and int(b.z) == int(z)]
        if blocks_at_xz:
            max_y_at_xz = max(b.y for b in blocks_at_xz)
            return max_y_at_xz + 1
        else:
            new_block = Block(x, 0, z)
            world.blocks.append(new_block)
            return 1