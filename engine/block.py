import math

# Definieren der Blockfarben
BLOCK_COLORS = {
    "stone": (128, 128, 128),
    "dirt": (139, 69, 19),
    "grass": (0, 100, 0),
    "leaves": (50, 205, 50),
    "log": (160, 82, 45)
}

# Klasse für Blöcke, als Veranschaulichung und Sammlund der Funktionen
class Block:
    # Initialisierung mit den wichtigsten Eigenschaften
    def __init__(self, x, y, z, block_id="stone"):
        self.x = x
        self.y = y
        self.z = z
        self.id = block_id
        self.color = BLOCK_COLORS.get(block_id, (255, 255, 255))

    # Ausgabe der Position
    def get_position(self):
        return (self.x, self.y, self.z)

    # Malen des Blocks
    def draw(self, renderer):
        # Größe um den Mittelpunkt; Mittelpunkt; Liste der gemalten; Seiten; Eckpunkte 
        size = 0.5
        bx, by, bz = self.x, self.y, self.z
        block_set = renderer.block_set
        sides = renderer.sides
        faces = []
        vertices = [
            (bx-size, by-size, bz-size),
            (bx+size, by-size, bz-size),
            (bx+size, by+size, bz-size),
            (bx-size, by+size, bz-size),
            (bx-size, by-size, bz+size),
            (bx+size, by-size, bz+size),
            (bx+size, by+size, bz+size),
            (bx-size, by+size, bz+size),
        ]

        # Für jede Seite:
        for (offset, idxs, shade) in sides:
            # 
            nx, ny, nz = bx+offset[0], by+offset[1], bz+offset[2]
            if (nx, ny, nz) not in block_set:
                mx = sum(vertices[i][0] for i in idxs) / 4
                my = sum(vertices[i][1] for i in idxs) / 4
                mz = sum(vertices[i][2] for i in idxs) / 4
                normal = offset
                to_cam = (
                    renderer.cam_x - mx,
                    renderer.cam_y - my,
                    renderer.cam_z - mz
                )
                dot = (normal[0]*to_cam[0] + normal[1]*to_cam[1] + normal[2]*to_cam[2])
                if dot <= 0:
                    continue
                # forward, _, _ = renderer.get_camera_vectors()
                # visible = True
                # for idx in idxs:
                #     vx, vy, vz = vertices[idx]
                #     face_vec = (vx-renderer.cam_x, vy-renderer.cam_y, vz-renderer.cam_z)
                #     face_len = sum(i*i for i in face_vec) ** 0.5
                #     if face_len == 0:
                #         continue
                #     face_dir = tuple(i/face_len for i in face_vec)
                #     dot_fwd = sum(face_dir[i]*forward[i] for i in range(3))
                #     angle = math.degrees(math.acos(max(-1,min(1,dot_fwd))))
                #     if angle <= fov_x/2 + 10:
                #         visible = True
                #         break
                # if not visible:
                #     continue

                #?????
                # dzs = []
                # cam = (renderer.cam_x, renderer.cam_y, renderer.cam_z)
                # forward, right, up = renderer.get_camera_vectors()
                # for idx in idxs:
                #     vx, vy, vz = vertices[idx]
                #     px, py, pz = vx-cam[0], vy-cam[1], vz-cam[2]
                #     dz = px*forward[0] + py*forward[1] + pz*forward[2]
                #     dzs.append(dz)


                # Projektion der Eckpunkte auf die Bildfläche
                projected = []
                dzs = []
                for (x, y, z) in vertices:
                    uv, dz = renderer.project(x, y, z) 
                    dzs.append(dz)
                    projected.append(uv)


                if all(dz <= 0.1 for dz in dzs):
                    continue
                
                # Entfernen ungültiger Flächern
                if any([projected[i] is None for i in idxs]):
                    continue

                dist = (mx-renderer.cam_x)**2 + (my-renderer.cam_y)**2 + (mz-renderer.cam_z)**2
                face = {
                    "points": [projected[i] for i in idxs],
                    "shade": shade,
                    "dist": dist,
                    "color": self.color
                }
                faces.append(face)
        return faces
