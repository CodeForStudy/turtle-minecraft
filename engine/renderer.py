from engine.block import BLOCK_COLORS
from game.player import Player
import turtle
import math
import time
import json
from .camera_utils import get_camera_vectors, project_point
from .input_handler import InputHandler

# Objekt für übersciht und Funktionensammlung
class Renderer:
    # Definition aller Möglichen Sachen
    def __init__(self, world=None, on_exit_to_main_menu=None):
        # laden der Configs
        with open("config.json", "r") as f:
            self.config = json.load(f)
        self.pause_hotkey = self.config.get("hotkeys", {}).get("toggle_pause", "Escape")
        self.on_exit_to_main_menu = on_exit_to_main_menu
        self.outlines = self.config.get("outlines", False)

        # Laden der Welt
        self.world = world
        
        # Anfangsblickrichtung- und Position setzen
        initial_player_x, initial_player_y, initial_player_z = 0, 0, 0
        initial_player_yaw, initial_player_pitch = 0.0, 0.0

        # Spieler laden
        if self.world and self.world.player_initial_state:
            state = self.world.player_initial_state
            initial_player_x = state.get('x', 0)
            initial_player_y = state.get('y', self.find_spawn_y(state.get('x', 0), state.get('z', 0)))
            initial_player_z = state.get('z', 0)
            initial_player_yaw = state.get('yaw', 0.0)
            initial_player_pitch = state.get('pitch', 0.0)
        else:
            initial_player_y = self.find_spawn_y(initial_player_x, initial_player_z)

        self.player = Player(initial_player_x, initial_player_y, initial_player_z, initial_player_yaw, initial_player_pitch)
        
        self.player_eye_height = 1
        self.cam_x = self.player.x
        self.cam_y = self.player.y + self.player_eye_height
        self.cam_z = self.player.z
        self.cam_yaw = self.player.yaw
        self.cam_pitch = self.player.pitch

        # Turtle Initiieren
        self.screen = turtle.Screen()
        self.screen.title("3D Sandbox Game")
        self.screen.setup(width=self.config.get("window_width", 800), height=self.config.get("window_height", 600))
        self.screen.bgcolor("light blue")
        self.t = turtle.Turtle()
        self.t.hideturtle()
        self.t.speed(0)
        self.t.pensize(2)
        self.screen.tracer(0, 0)
        self.sides = [
            ((-1, 0, 0), [0, 3, 7, 4], 0.55),
            ((1, 0, 0), [1, 2, 6, 5], 0.75),
            ((0, -1, 0), [0, 1, 5, 4], 0.60),
            ((0, 1, 0), [2, 3, 7, 6], 0.85),
            ((0, 0, -1), [0, 1, 2, 3], 0.50),
            ((0, 0, 1), [4, 5, 6, 7], 0.70),
        ]
        
        # Inputhandler initiieren
        self.input_handler = InputHandler(self.screen, self.player, self, self.config)

        # Turtle für das Pausenmenü erstellen
        self.pause_menu_turtle = turtle.Turtle()
        self.pause_menu_turtle.hideturtle()
        self.pause_menu_turtle.speed(0)
        self.pause_menu_turtle.penup()
        self.pause_menu_buttons = []
        self.hovered_pause_button_action = None

        # Turtle für den Debugscreen erstellen
        self.fps = 0
        self.fps_turtle = turtle.Turtle()
        self.fps_turtle.hideturtle()
        self.fps_turtle.penup()
        self.fps_turtle.speed(0)
        self.fps_turtle.color('black')
        self.last_time = time.time()
        self.show_debug = False
        
        # Turtle für das Crosshair erstellen
        self.crosshair_turtle = turtle.Turtle()
        self.crosshair_turtle.hideturtle()
        self.crosshair_turtle.penup()
        self.crosshair_turtle.speed(0)
        self.crosshair_turtle.pensize(2)

        # Turtle für das Hud erstellen
        self.hud_block_turtle = turtle.Turtle()
        self.hud_block_turtle.hideturtle()
        self.hud_block_turtle.penup()
        self.hud_block_turtle.speed(0)
        self.hud_block_turtle.pensize(1)

        # Werte für hud Animation
        self.hud_animation_active = False
        self.hud_animation_elapsed_time = 0
        self.hud_animation_duration = 0.25
        self.hud_animation_intensity_x_shift = 0.1
        self.hud_animation_intensity_size_factor = 0.2
        self.hud_animation_intensity_iso_x_factor = 0.3
        self.hud_animation_intensity_iso_y_factor = 0.3

        # etc.
        canvas = self.screen.getcanvas()
        canvas.config(cursor="none")
        self.paused = False
        self.render_distance = self.config.get("render_distance", 5)
        self._last_player_pos = (None, None, None)
        self._last_player_yaw = None
        self._last_player_pitch = None
        self._visible_blocks_cache = []
        self.block_set = set()

        # laden der Definierten Blöcke
        self.available_block_types = list(BLOCK_COLORS.keys())
        self.current_block_type_index = 0
        if not self.available_block_types:
            self.available_block_types = ["stone"]
        self.selected_block_type = self.available_block_types[self.current_block_type_index]

        # erstes Update der Welt
        self.update()

    # nächsten Block auswählen
    def select_next_block(self):
        self.current_block_type_index = (self.current_block_type_index + 1) % len(self.available_block_types)
        self.selected_block_type = self.available_block_types[self.current_block_type_index]

    # vorherigen Block auswählen
    def select_previous_block(self):
        self.current_block_type_index = (self.current_block_type_index - 1 + len(self.available_block_types)) % len(self.available_block_types)
        self.selected_block_type = self.available_block_types[self.current_block_type_index]

    # ausgewählter Block ausgeben
    def get_selected_block_type(self):
        return self.selected_block_type

    # hud animation initiieren
    def trigger_hud_block_animation(self):
        self.hud_animation_active = True
        self.hud_animation_elapsed_time = 0
    
    # hud malen
    def draw_selected_block_hud(self, delta_time):
        # shading
        self.hud_block_turtle.clear()
        block_type = self.get_selected_block_type()
        base_color = BLOCK_COLORS.get(block_type, (255, 255, 255))

        top_color_val = tuple(int(c * 0.9) for c in base_color)
        side_color_val = tuple(int(c * 0.75) for c in base_color)
        front_color_val = base_color

        hex_front_color = f"#{front_color_val[0]:02x}{front_color_val[1]:02x}{front_color_val[2]:02x}"
        hex_top_color = f"#{top_color_val[0]:02x}{top_color_val[1]:02x}{top_color_val[2]:02x}"
        hex_side_color = f"#{side_color_val[0]:02x}{side_color_val[1]:02x}{side_color_val[2]:02x}"
        
        outline_color = "#000000"

        # skalierung
        screen_w = self.screen.window_width()
        screen_h = self.screen.window_height()

        original_size = screen_w * 0.20
        original_depth = original_size * 0.5
        
        visible_front_width_on_screen = original_size * 0.9
        original_base_x = (screen_w / 2) - visible_front_width_on_screen
        
        overlap_y_pixels = original_size * 0.40
        original_base_y = (-screen_h / 2) - overlap_y_pixels

        current_base_x = original_base_x
        current_base_y = original_base_y
        current_size = original_size
        
        animated_iso_x = original_depth
        animated_iso_y = original_depth

        # animation ausführen
        if self.hud_animation_active:
            self.hud_animation_elapsed_time += delta_time
            if self.hud_animation_elapsed_time < self.hud_animation_duration:
                # Fortschritt der Animation berechnen
                progress = self.hud_animation_elapsed_time / self.hud_animation_duration
                wave = math.sin(progress * math.pi)

                # nächsten Zustand berechnen
                current_base_x = original_base_x - (original_size * self.hud_animation_intensity_x_shift * wave)

                current_size = original_size * (1 - self.hud_animation_intensity_size_factor * wave)
                
                animated_iso_x = original_depth * (1 + self.hud_animation_intensity_iso_x_factor * wave)
                animated_iso_y = original_depth * (1 - self.hud_animation_intensity_iso_y_factor * wave)
            else:
                # Beenden der Animation
                self.hud_animation_active = False
                self.hud_animation_elapsed_time = 0
                
                current_base_x = original_base_x
                current_size = original_size
                animated_iso_x = original_depth
                animated_iso_y = original_depth
        else:
            current_base_x = original_base_x
            current_size = original_size
            animated_iso_x = original_depth
            animated_iso_y = original_depth


        
        # manuelle Festlegung der Vertecies und Faces
        front_face_points = [
            (current_base_x, current_base_y),
            (current_base_x + current_size, current_base_y),
            (current_base_x + current_size, current_base_y + current_size),
            (current_base_x, current_base_y + current_size)
        ]
        top_face_points = [
            (current_base_x, current_base_y + current_size),
            (current_base_x + animated_iso_x, current_base_y + current_size + animated_iso_y),
            (current_base_x + current_size + animated_iso_x, current_base_y + current_size + animated_iso_y),
            (current_base_x + current_size, current_base_y + current_size)
        ]
        side_face_points = [
            (current_base_x + current_size, current_base_y),
            (current_base_x + current_size + animated_iso_x, current_base_y + animated_iso_y),
            (current_base_x + current_size + animated_iso_x, current_base_y + current_size + animated_iso_y),
            (current_base_x + current_size, current_base_y + current_size)
        ]
        faces_to_draw = [
            (top_face_points, hex_top_color),
            (side_face_points, hex_side_color),
            (front_face_points, hex_front_color)
        ]
        
        # Malen des Aktuellen Zusatndes
        for points, fill_color in faces_to_draw:
            self.hud_block_turtle.penup()
            self.hud_block_turtle.goto(points[0][0], points[0][1])
            self.hud_block_turtle.fillcolor(fill_color)
            self.hud_block_turtle.pencolor(outline_color)
            self.hud_block_turtle.pensize(2)
            self.hud_block_turtle.begin_fill()
            self.hud_block_turtle.pendown()
            for x, y in points[1:]:
                self.hud_block_turtle.goto(x, y)
            self.hud_block_turtle.goto(points[0][0], points[0][1])
            self.hud_block_turtle.end_fill()
            self.hud_block_turtle.penup()

    # Finden/Erzeugen der Spawnhöhe
    def find_spawn_y(self, x, z):
        height = self.world.blocks.shape[1]
        
        column_blocks = list(self.world.blocks[int(x), 0:int(height), int(z)].reshape(-1))
        column_blocks = [x for x in column_blocks if x is not None]

        max_y = -1
        if len(column_blocks) > 0:
            max_y = max(b.y for b in column_blocks if b is not None)
        
        # Überprüfen jeder Höhe
        for y_coord in range(max_y + 2, -2, -1):
            is_space_free = not any(b.y == y_coord for b in column_blocks)
            is_block_below = any(b.y == y_coord - 1 for b in column_blocks)

            if is_space_free and is_block_below:
                return y_coord
        
        return max_y + 1

    # Malen des Pausemenüs
    def draw_pause_menu(self):
        self.pause_menu_turtle.clear()
        self.pause_menu_buttons = []

        # Definieren der Größen
        button_width = 250
        button_height = 50
        button_spacing = 20
        
        num_buttons = 3
        total_menu_height = num_buttons * button_height + (num_buttons - 1) * button_spacing
        start_y_center = total_menu_height / 2 - button_height / 2

        buttons_config = [
            {"text": "Zurück zum Spiel", "action": "resume", "color": "#cccccc", "hover_color": "#aaaaaa", "text_color": "black"},
            {"text": "Hauptmenü", "action": "main_menu", "color": "#cccccc", "hover_color": "#aaaaaa", "text_color": "black"},
            {"text": "Spiel beenden", "action": "exit_game", "color": "#cccccc", "hover_color": "#aaaaaa", "text_color": "black"}
        ]

        # Iteration durch die Konfigurationen um Widerholenden Code zu vermeiden
        for i, btn_config in enumerate(buttons_config):
            current_y_center = start_y_center - i * (button_height + button_spacing)
            
            
            draw_color = btn_config["hover_color"] if self.hovered_pause_button_action == btn_config["action"] else btn_config["color"]
            
            self._draw_pause_button(self.pause_menu_turtle, btn_config["text"], 0, current_y_center, button_width, button_height, 
                                    color=draw_color, text_color=btn_config["text_color"])
            
            min_x = 0 - button_width / 2
            max_x = 0 + button_width / 2
            min_y = current_y_center - button_height / 2
            max_y = current_y_center + button_height / 2
            
            
            self.pause_menu_buttons.append({
                "min_x": min_x, "min_y": min_y, "max_x": max_x, "max_y": max_y, 
                "action": btn_config["action"], 
                "text": btn_config["text"], 
                "x_center": 0, "y_center": current_y_center, 
                "width": button_width, "height": button_height,
                "color": btn_config["color"], "hover_color": btn_config["hover_color"],
                "text_color": btn_config["text_color"]
            })
        
        # Aktualisieren des Bildschirms
        self.screen.update()

    # Malen eines Buttons
    def _draw_pause_button(self, turtle_obj, text, x_center, y_center, width, height, color="#cccccc", text_color="black", border_color="black"):
        turtle_obj.penup()
        
        turtle_obj.pencolor(border_color)
        turtle_obj.fillcolor(color)
        
        bottom_left_x = x_center - width / 2
        bottom_left_y = y_center - height / 2
        
        turtle_obj.goto(bottom_left_x, bottom_left_y)
        turtle_obj.pendown()
        turtle_obj.begin_fill()
        for _ in range(2):
            turtle_obj.forward(width)
            turtle_obj.left(90)
            turtle_obj.forward(height)
            turtle_obj.left(90)
        turtle_obj.end_fill()
        turtle_obj.penup()
        
        turtle_obj.pencolor(text_color)
        text_y_baseline = y_center - 8
        
        turtle_obj.goto(x_center, text_y_baseline)
        turtle_obj.write(text, align="center", font=("Arial", 16, "normal"))

    # Handler für Klicks im Pausemenü
    def handle_pause_menu_click(self, x_click, y_click):
        # Iteration durch die Schaltflächen und Abgleich der Mausposition
        for btn_info in self.pause_menu_buttons:
            if btn_info["min_x"] <= x_click <= btn_info["max_x"] and \
               btn_info["min_y"] <= y_click <= btn_info["max_y"]:
                action = btn_info["action"]
                # Asführen der Funktionen
                if action == "resume":
                    self.toggle_pause()
                elif action == "main_menu":
                    self.exit_to_main_menu()
                elif action == "exit_game":
                    self.exit_game()
                break
             
    # Pausemenü löschen
    def clear_pause_menu(self):
        self.pause_menu_turtle.clear()
        self.pause_menu_turtle.hideturtle()
        self.pause_menu_buttons = []
        self.hovered_pause_button_action = None
        self.screen.update()

    # Zurück zum startmenü kehren
    def exit_to_main_menu(self):
        self.save_current_world_state()
        self.cleanup_for_main_menu()
        if self.on_exit_to_main_menu:
            self.on_exit_to_main_menu()

    # Löschen für Startmenü
    def cleanup_for_main_menu(self):
        # Turtels clear
        self.t.clear()
        self.fps_turtle.clear()
        self.crosshair_turtle.clear()
        self.hud_block_turtle.clear()
        if hasattr(self, 'pause_menu_turtle') and self.pause_menu_turtle:
            self.pause_menu_turtle.clear()
            self.pause_menu_turtle.hideturtle()
        
        # keybinds lösen
        if hasattr(self, 'input_handler') and self.input_handler:
            self.input_handler.unbind_all()
        # handler lösen
        self.screen.onclick(None, btn=1)

        canvas = self.screen.getcanvas()
        canvas.config(cursor="arrow")
        
        # Aktualisieren
        self.paused = True
        self.screen.update()

    # Spiel beenden
    def exit_game(self):
        # Speichern
        self.save_current_world_state()
        # Löschen und trotz Fehler beenden
        try:
            self.cleanup_for_main_menu()
        except Exception:
            pass
        finally:
            # Beenden
            self.screen.bye()

    # Speichern der aktuellen Welt
    def save_current_world_state(self):
        if self.world and self.world.path:
            # Verpacken der Spielereigenschaften
            player_state = {
                "x": self.player.x,
                "y": self.player.y,
                "z": self.player.z,
                "yaw": self.player.yaw,
                "pitch": self.player.pitch
            }
            self.world.save(player_state=player_state)
 
    # Spielmodus wechseln
    def toggle_mode(self):
        self.player.mode = 'spectator' if self.player.mode == 'player' else 'player'
        if self.player.mode == 'player':
            self.player.y = self.find_spawn_y(round(self.player.x), round(self.player.z))

    # Debugscreen öffnen
    def toggle_debug(self):
        self.show_debug = not self.show_debug

    # Pausenbildschirm öffnen
    def toggle_pause(self):
        self.paused = not self.paused
        self.input_handler.set_paused(self.paused)
        if self.paused:
            self.screen.getcanvas().config(cursor="arrow")
            self.screen.getcanvas().bind("<Motion>", self.handle_pause_menu_mouse_motion)
            self.draw_pause_menu()
        else:
            self.screen.getcanvas().config(cursor="none")
            self.clear_pause_menu()
            
    # hover effekte
    def handle_pause_menu_mouse_motion(self, event):
        x_turtle = event.x - self.screen.window_width() / 2
        y_turtle = self.screen.window_height() / 2 - event.y
        previous_hovered_action = self.hovered_pause_button_action
        current_hovered_action = None

        # Positionsabglecih
        for btn_info in self.pause_menu_buttons:
            if btn_info["min_x"] <= x_turtle <= btn_info["max_x"] and \
               btn_info["min_y"] <= y_turtle <= btn_info["max_y"]:
                current_hovered_action = btn_info["action"]
                break

        # Neumalen des Buttons
        if previous_hovered_action != current_hovered_action:
            self.hovered_pause_button_action = current_hovered_action
            
            self.pause_menu_turtle.clear()
            
            for btn_info_redraw in self.pause_menu_buttons:
                draw_color = btn_info_redraw["hover_color"] if self.hovered_pause_button_action == btn_info_redraw["action"] else btn_info_redraw["color"]
                self._draw_pause_button(
                    self.pause_menu_turtle, btn_info_redraw["text"], 
                    btn_info_redraw["x_center"], btn_info_redraw["y_center"], 
                    btn_info_redraw["width"], btn_info_redraw["height"],
                    color=draw_color, text_color=btn_info_redraw["text_color"]
                )
            # Aktualisieren
            self.screen.update()

    # Vollbild
    def toggle_fullscreen(self):
        canvas = self.screen.getcanvas()
        root = canvas.winfo_toplevel()
        if not hasattr(self, 'maximized') or not self.maximized:
            root.state('zoomed')
            self.maximized = True
        else:
            root.state('normal')
            self.maximized = False

    # Aktualisieren des Bildes
    def update(self):
        # Bei Pausierung abbrechen
        if self.paused:
            self.screen.update()
            self.screen.ontimer(self.update, 50)
            return

        # Berechnen der Deltatime und fps
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        if delta_time > 0:
            self.fps = 1.0 / delta_time
        else:
            self.fps = 0

        # Aktualisieren der Eingaben und des Spielers
        input_state = self.input_handler.get_input_state()
        self.player.update(self.world, input_state, delta_time)

        # kamerawerte anpassen
        self.cam_x = self.player.x
        self.cam_y = self.player.y + self.player_eye_height
        self.cam_z = self.player.z
        self.cam_yaw = self.player.yaw
        self.cam_pitch = self.player.pitch

        # Welt rendern
        self.render(delta_time)
        # Bild Aktualisieren
        self.screen.update()
        self.screen.ontimer(self.update, 0)

    # Kamerarotationsvektoren weiterleitung
    def get_camera_vectors(self):
        return get_camera_vectors(self.cam_yaw, self.cam_pitch)

    # Projektion weiterleitung
    def project(self, x, y, z):
        forward, right, up = self.get_camera_vectors()
        win_w = self.screen.window_width()
        win_h = self.screen.window_height()
        fov = self.config['fov']
        return project_point(x, y, z, 
                             self.cam_x, self.cam_y, self.cam_z,
                             forward, right, up, 
                             win_w, win_h, fov)

    # Sichtbare Blöcke berechnen, um Performance zu gewinnen
    def get_visible_blocks(self):
        # Gerundete Position
        current_rounded_pos = (round(self.player.x, 2), round(self.player.y, 2), round(self.player.z, 2))
        current_rounded_yaw = round(self.player.yaw, 1)
        current_rounded_pitch = round(self.player.pitch, 1)

        # bei keiner Bewegung wird der Cache verwendet
        if (current_rounded_pos == self._last_player_pos and
            current_rounded_yaw == self._last_player_yaw and
            current_rounded_pitch == self._last_player_pitch):
            return self._visible_blocks_cache
        
        # Blöcke in einem Radius auflisten
        px, py, pz = self.player.x, self.player.y, self.player.z
        radius = self.render_distance

        visible_blocks = self.world.get_blocks(px, py, pz, radius)

        # Frustum culling
        visible_blocks = self.frustum_cull(visible_blocks)
        
        self._last_player_pos = current_rounded_pos
        self._last_player_yaw = current_rounded_yaw
        self._last_player_pitch = current_rounded_pitch
        self._visible_blocks_cache = visible_blocks
        self.block_set = set((b.x, b.y, b.z) for b in visible_blocks)
        # Ausgaeb
        return visible_blocks
    
    # Frustum culling
    def frustum_cull(self, blocks:list):
        win_w = self.screen.window_width()
        win_h = self.screen.window_height()
        margin = win_w * 0.3
        culled_blocks = []

        for b in blocks:
            uv, dz = self.project(b.x, b.y, b.z)
            u, v = uv
            u += win_w/2
            v += win_h/2
            if (u > 0-margin and u < win_w+margin and v > 0-margin and v < win_h+margin) or dz < 1:
                culled_blocks.append(b)

        return culled_blocks
    

    # Rendern der Welt
    def render(self, delta_time):
        # Bild Löschen
        self.t.clear()
        
        # nur das nötigste rendern
        blocks_to_render = self.get_visible_blocks()
        
        #scale = 200
        #win_w = self.screen.window_width()
        #win_h = self.screen.window_height()
        #fov_x = math.degrees(2 * math.atan((win_w/2) / scale))
        #fov_y = math.degrees(2 * math.atan((win_h/2) / scale))

        # Faces der Blöcke besorgen
        faces = []
        for block in blocks_to_render:
            faces.extend(block.draw(self))
        
        # Sortieren der Faces damit sie richtigrum abgebildet werden
        faces.sort(key=lambda f: -f["dist"])
        
        num_total_faces_after_culling = len(faces)

        for face in faces:
            points = face["points"]
            shade = face["shade"]
            base_color = face["color"]
            
            # Farben in hex Format bringen
            shaded_color = tuple(int(c * shade) for c in base_color)
            hex_color = f"#{shaded_color[0]:02x}{shaded_color[1]:02x}{shaded_color[2]:02x}"
            
            # Malen der Außenlinien
            self.t.penup()
            self.t.goto(points[0][0], points[0][1])
            self.t.fillcolor(hex_color)
            self.t.begin_fill()
            # Zeichnen wenn outlines erlaubt sind
            if self.outlines:
                self.t.pencolor("#1e1e1e")
                self.t.pendown()
            for x, y in points[1:]:
                self.t.goto(x, y)
            self.t.goto(points[0][0], points[0][1])
            self.t.end_fill()
            self.t.penup()
            #   self.t.goto(points[0][0], points[0][1])
            #   self.t.pendown()
            #   for x, y in points[1:]+[points[0]]:
            #       self.t.goto(x, y)
            #   self.t.penup()

        # Debug Screen updaten
        self.t.pencolor("#000000")
        self.fps_turtle.clear()
        y_offset = 30
        if self.show_debug:
            self.fps_turtle.goto(-self.screen.window_width()//2 + 10, self.screen.window_height()//2 - y_offset)
            self.fps_turtle.write(f"FPS: {self.fps:.1f}", font=("Arial", 14, "normal"))
            y_offset += 22
            
            px, py, pz = self.player.x, self.player.y, self.player.z
            yaw, pitch = self.player.yaw, self.player.pitch
            self.fps_turtle.goto(-self.screen.window_width()//2 + 10, self.screen.window_height()//2 - y_offset)
            self.fps_turtle.write(f"Player - X: {px:.3f} Y: {py:.3f} Z: {pz:.3f} | Y: {yaw:.1f} P: {pitch:.1f}", font=("Arial", 12, "normal"))
            y_offset += 20
            
            block_pos, _ = self.get_looked_at_block(max_dist=10)
            self.fps_turtle.goto(-self.screen.window_width()//2 + 10, self.screen.window_height()//2 - y_offset)
            if block_pos:
                bx, by, bz = block_pos
                self.fps_turtle.write(f"Block - X: {bx} Y: {by} Z: {bz}", font=("Arial", 12, "normal"))
            else:
                self.fps_turtle.write("Block - None", font=("Arial", 12, "normal"))
            y_offset += 20

            self.fps_turtle.goto(-self.screen.window_width()//2 + 10, self.screen.window_height()//2 - y_offset)
            self.fps_turtle.write(f"Rendered Faces: {num_total_faces_after_culling}", font=("Arial", 12, "normal"))

        # crosshair neu malen
        self.crosshair_turtle.clear()
        w = self.screen.window_width()
        h = self.screen.window_height()
        center_x, center_y = 0, 0
        size = 10
        self.crosshair_turtle.pencolor("black")
        self.crosshair_turtle.goto(center_x - size, center_y)
        self.crosshair_turtle.pendown()
        self.crosshair_turtle.goto(center_x + size, center_y)
        self.crosshair_turtle.penup()
        self.crosshair_turtle.goto(center_x, center_y - size)
        self.crosshair_turtle.pendown()
        self.crosshair_turtle.goto(center_x, center_y + size)
        self.crosshair_turtle.penup()

        # hud malen
        self.draw_selected_block_hud(delta_time)

    # Position des Angeschauten Blocks ermitteln
    def get_looked_at_block(self, max_dist=10, step=0.05):
        # if self.player.mode == 'player':
        x, y, z = self.player.x, self.player.y + self.player_eye_height, self.player.z
        # else:
        #     x, y, z = self.player.x, self.player.y, self.player.z

        # Blickrichnung berechnen
        yaw = math.radians(self.player.yaw)
        pitch = math.radians(self.player.pitch)
        dx = math.sin(yaw) * math.cos(pitch)
        dy = math.sin(pitch)
        dz = math.cos(yaw) * math.cos(pitch)
        last_air = None
        # tracen der Richtung bis ein Block getroffen wird
        for i in range(int(max_dist / step)):
            rx = x + dx * i * step
            ry = y + dy * i * step
            rz = z + dz * i * step
            bx, by, bz = round(rx), round(ry), round(rz)
            if (bx, by, bz) in self.block_set:
                return (bx, by, bz), last_air
            last_air = (bx, by, bz)
        return None, last_air

    # render Distance erhöhen
    def increase_render_distance(self):
        self.render_distance += 1
        self._last_player_pos = (None, None, None)
        
    # render Distance erniedrigen
    def decrease_render_distance(self):
        self.render_distance = max(self.render_distance - 1, 1)
        self._last_player_pos = (None, None, None)
