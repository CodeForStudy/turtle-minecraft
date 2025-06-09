import math

def get_camera_vectors(cam_yaw_degrees, cam_pitch_degrees):
    yaw_rad = math.radians(cam_yaw_degrees)
    pitch_rad = math.radians(cam_pitch_degrees)

    fx = math.sin(yaw_rad) * math.cos(pitch_rad)
    fy = math.sin(pitch_rad)
    fz = math.cos(yaw_rad) * math.cos(pitch_rad)
    
    rx = math.cos(yaw_rad)
    ry = 0
    rz = -math.sin(yaw_rad)
    
    ux = -math.sin(yaw_rad) * math.sin(pitch_rad)
    uy = math.cos(pitch_rad)
    uz = -math.cos(yaw_rad) * math.sin(pitch_rad)
    
    return (fx, fy, fz), (rx, ry, rz), (ux, uy, uz)

def project_point(world_x, world_y, world_z, 
                  cam_x, cam_y, cam_z, 
                  forward_vec, right_vec, up_vec, 
                  projection_scale=200, min_depth=0.1):
    px, py, pz = world_x - cam_x, world_y - cam_y, world_z - cam_z

    dx = px * right_vec[0] + py * right_vec[1] + pz * right_vec[2]
    dy = px * up_vec[0] + py * up_vec[1] + pz * up_vec[2]
    dz = px * forward_vec[0] + py * forward_vec[1] + pz * forward_vec[2]

    if dz <= min_depth:
        dz = min_depth

    factor = projection_scale / dz
    screen_x = dx * factor
    screen_y = dy * factor
    
    return screen_x, screen_y
