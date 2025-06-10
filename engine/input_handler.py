from engine.block import Block

# Objekt für Eingabefunktionen
class InputHandler:
    # Definition Grundlegender Eigenschaften und Vektoren
    def __init__(self, screen, player, renderer_instance, config):
        self.screen = screen
        self.player = player
        self.renderer = renderer_instance 
        self.config = config
        self.moving = {'w': False, 'a': False, 's': False, 'd': False}
        self.turning = {'Left': False, 'Right': False, 'Up': False, 'Down': False}
        self.actions = {'jump': False, 'sprint': False}
        self.mouse_sens = self.config.get("mouse_sens", 0.2)
        self.mouse_warp = self.config.get("mouse_warp", True)
        self.ignore_next_mouse_event = False
        self.bind_keys()
        self.bind_mouse()
        self.bind_mouse_scroll()
        self.paused = False

    # Keybinds lösen
    def set_paused(self, paused):
        self.paused = paused
        if paused:
            self.unbind_keys_for_menu()
        else:
            self.bind_keys()
            self.bind_mouse()
            self.bind_mouse_scroll()

    # Keybinds setzen
    def bind_keys(self):
        # Lesen von config.json
        hotkeys = self.config.get("hotkeys", {})
        self.screen.listen()

        # Setzen von Bewegung
        self.screen.onkeypress(lambda: self.set_move('w', True), hotkeys.get("move_forward", 'w'))
        self.screen.onkeyrelease(lambda: self.set_move('w', False), hotkeys.get("move_forward", 'w'))
        self.screen.onkeypress(lambda: self.set_move('a', True), hotkeys.get("move_left", 'a'))
        self.screen.onkeyrelease(lambda: self.set_move('a', False), hotkeys.get("move_left", 'a'))
        self.screen.onkeypress(lambda: self.set_move('s', True), hotkeys.get("move_backward", 's'))
        self.screen.onkeyrelease(lambda: self.set_move('s', False), hotkeys.get("move_backward", 's'))
        self.screen.onkeypress(lambda: self.set_move('d', True), hotkeys.get("move_right", 'd'))
        self.screen.onkeyrelease(lambda: self.set_move('d', False), hotkeys.get("move_right", 'd'))
        
        # Setzen von Blickrichtung
        self.screen.onkeypress(lambda: self.set_turn('Left', True), hotkeys.get("look_left", 'Left'))
        self.screen.onkeyrelease(lambda: self.set_turn('Left', False), hotkeys.get("look_left", 'Left'))
        self.screen.onkeypress(lambda: self.set_turn('Right', True), hotkeys.get("look_right", 'Right'))
        self.screen.onkeyrelease(lambda: self.set_turn('Right', False), hotkeys.get("look_right", 'Right'))
        self.screen.onkeypress(lambda: self.set_turn('Up', True), hotkeys.get("look_up", 'Up'))
        self.screen.onkeyrelease(lambda: self.set_turn('Up', False), hotkeys.get("look_up", 'Up'))
        self.screen.onkeypress(lambda: self.set_turn('Down', True), hotkeys.get("look_down", 'Down'))
        self.screen.onkeyrelease(lambda: self.set_turn('Down', False), hotkeys.get("look_down", 'Down'))

        # Tasten für Spielmodus, Debug, Pause, render distance
        self.screen.onkeypress(self.renderer.toggle_mode, hotkeys.get("toggle_mode", 'p'))
        self.screen.onkeypress(self.renderer.toggle_debug, hotkeys.get("toggle_debug", 'F3'))
        self.screen.onkeypress(self.renderer.toggle_pause, self.renderer.pause_hotkey)
        self.screen.onkeypress(self.renderer.increase_render_distance, hotkeys.get("increase_render_distance", "+"))
        self.screen.onkeypress(self.renderer.decrease_render_distance, hotkeys.get("decrease_render_distance", "-"))
        
        # Springen
        jump_hotkey = hotkeys.get("jump", "space")
        self.screen.onkeypress(lambda: self.set_action('jump', True), jump_hotkey)
        self.screen.onkeyrelease(lambda: self.set_action('jump', False), jump_hotkey)
        
        # Sprinten
        sprint_hotkey_config = hotkeys.get("sprint", "Control_L") 
        self.screen.onkeypress(lambda: self.set_action('sprint', True), sprint_hotkey_config)
        self.screen.onkeyrelease(lambda: self.set_action('sprint', False), sprint_hotkey_config)
        
    # Keybinds lösen, um Steuerung im Menü zu lösen
    def unbind_keys_for_menu(self):
        hotkeys = self.config.get("hotkeys", {})
        keys_to_unbind = [
            hotkeys.get("move_forward", 'w'),
            hotkeys.get("move_left", 'a'),
            hotkeys.get("move_backward", 's'),
            hotkeys.get("move_right", 'd'),
            hotkeys.get("look_left", 'Left'),
            hotkeys.get("look_right", 'Right'),
            hotkeys.get("look_up", 'Up'),
            hotkeys.get("look_down", 'Down'),
            hotkeys.get("toggle_mode", 'p'),
            
            
            hotkeys.get("increase_render_distance", "+"),
            hotkeys.get("decrease_render_distance", "-"),
            hotkeys.get("jump", "space"),
            hotkeys.get("sprint", "Control_L")
            
        ]
        for key in keys_to_unbind:
            self.screen.onkeypress(None, key)
            self.screen.onkeyrelease(None, key)

    # Alle Keybinds lösen
    def unbind_all(self):
        # Für Menp lösen
        self.unbind_keys_for_menu()
        
        # Debug, Pause lösen
        hotkeys = self.config.get("hotkeys", {})
        self.screen.onkeypress(None, hotkeys.get("toggle_debug", 'F3'))
        self.screen.onkeypress(None, self.renderer.pause_hotkey)

        # Maus lösen
        self.unbind_mouse()
        canvas = self.screen.getcanvas()
        canvas.unbind('<Button-1>')
        canvas.unbind('<Button-3>')
        
        canvas.unbind("<MouseWheel>")
        canvas.unbind("<Button-4>")
        canvas.unbind("<Button-5>")
        
        # Bewegungen entfernen
        self.moving = {k: False for k in self.moving}
        self.turning = {k: False for k in self.turning}
        self.actions = {k: False for k in self.actions}

    # Maus scroll binden
    def bind_mouse_scroll(self):
        canvas = self.screen.getcanvas()
        
        canvas.bind("<MouseWheel>", self.on_mouse_scroll)
        canvas.bind("<Button-4>", lambda event: self.on_mouse_scroll(event, direction=-1))
        canvas.bind("<Button-5>", lambda event: self.on_mouse_scroll(event, direction=1))

    # Maus scroll Event
    def on_mouse_scroll(self, event, direction=None):
        # Bei Pausierungn abbrechen
        if self.paused:
            return
        
        # Blockauswahl
        if direction is None:
            if event.delta > 0:
                self.renderer.select_previous_block()
            elif event.delta < 0:
                self.renderer.select_next_block()
        else:
            if direction == -1:
                self.renderer.select_previous_block()
            elif direction == 1:
                self.renderer.select_next_block()

    # Werte für Movement
    def set_move(self, key, value):
        self.moving[key] = value

    # Werte für Bewegung
    def set_turn(self, key, value):
        self.turning[key] = value

    # Werte für Aktion
    def set_action(self, action, value):
        self.actions[action] = value

    # Maus binden
    def bind_mouse(self):
        canvas = self.screen.getcanvas()
        canvas.bind('<Motion>', self.on_mouse_move)
        canvas.bind('<Button-1>', self.on_left_click)
        canvas.bind('<Button-3>', self.on_right_click)
        w = self.screen.window_width()
        h = self.screen.window_height()
        canvas.winfo_toplevel().update()
        self.ignore_next_mouse_event = True
        canvas.event_generate('<Motion>', warp=True, x=w//2, y=h//2)

    # Maus lösen
    def unbind_mouse(self):
        canvas = self.screen.getcanvas()
        canvas.unbind('<Motion>')
        
    # Event für Mausbewegung
    def on_mouse_move(self, event):
        # Abbruch bei Pausierung
        if self.paused:
            return
        # Mittelpunkt des Bildschirms
        w = self.screen.window_width()
        h = self.screen.window_height()
        center_x = w // 2
        center_y = h // 2

        # Ignorieren bei Initialisierung der Maus
        if self.ignore_next_mouse_event:
            self.ignore_next_mouse_event = False
            
            if event.x == center_x and event.y == center_y:
                 return

        # Berechnung der X und Y veränderung zum Mittelpunkt
        dx = event.x - center_x
        dy = event.y - center_y

        # Bei Bewegung Blickrichtung anpassen
        if dx != 0 or dy != 0:
            self.player.yaw += dx * self.mouse_sens
            self.player.pitch -= dy * self.mouse_sens
            self.player.pitch = max(-89, min(89, self.player.pitch))
            # Maus wrap für unendliche Bewegung
            if self.mouse_warp:
                canvas = self.screen.getcanvas()
                self.ignore_next_mouse_event = True
                canvas.event_generate('<Motion>', warp=True, x=center_x, y=center_y)

    # Event für Linksklick
    def on_left_click(self, event):
        # Bei Pausoierung: Menüfunktionen
        if self.paused:
            if hasattr(self.renderer, 'handle_pause_menu_click'):
                x_turtle = event.x - self.screen.window_width() / 2
                y_turtle = self.screen.window_height() / 2 - event.y
                self.renderer.handle_pause_menu_click(x_turtle, y_turtle)
            return

        # Sonst: Block zerstören
        # Position des angeschauten Blocks
        block_pos, _ = self.renderer.get_looked_at_block(max_dist=4)
        if block_pos:
            # Entfernen des Blocks, Zurücksetzen der letzten Spielerposition, Animation
            self.renderer.world.blocks = [b for b in self.renderer.world.blocks if (b.x, b.y, b.z) != block_pos]
            self.renderer._last_player_pos = (None, None, None)
            self.renderer.trigger_hud_block_animation()

    # Event für Recchtsklick
    def on_right_click(self, event):
        # Abbruch bei Pausierung
        if self.paused:
            return

        # Position für angeschauten Block, Position für Platzierten Block
        looked_at_block_pos, place_pos = self.renderer.get_looked_at_block(max_dist=4)

        # Wenn es Werte gibt
        if looked_at_block_pos and place_pos:
            px, py, pz = place_pos

            # Wenn nicht schon ein Block dort ist
            if not any(b.x == px and b.y == py and b.z == pz for b in self.renderer.world.blocks):
                # Berechnung der Entfernung
                cam_x = self.player.x
                cam_y = self.player.y + self.renderer.player_eye_height if self.player.mode == 'player' else self.player.y
                cam_z = self.player.z
                
                dist_to_cam = ((px - cam_x)**2 + (py - cam_y)**2 + (pz - cam_z)**2)**0.5

                # Wenn in Reichweite
                if dist_to_cam <= 4:
                    # Laden von Werten für Hitbox
                    player_x = self.player.x
                    player_y_feet = self.player.y
                    player_z = self.player.z
                    player_radius = self.player.radius
                    player_height = self.player.height
                    hitbox_adj = self.player.hitbox_center_adjustment

                    # Player Mittelpunkt auf horizontaler Ebene
                    player_col_cx = player_x - hitbox_adj 
                    player_col_cz = player_z - hitbox_adj

                    # Block Hitbox
                    block_min_x, block_max_x = float(px), float(px) + 1.0
                    block_min_y, block_max_y = float(py), float(py) + 1.0
                    block_min_z, block_max_z = float(pz), float(pz) + 1.0

                    # Nächster 'Eckpunkt' Auf der Ebene
                    closest_block_x_to_player_center = max(block_min_x, min(player_col_cx, block_max_x))
                    closest_block_z_to_player_center = max(block_min_z, min(player_col_cz, block_max_z))

                    # xz distanz
                    dist_sq_xz = (player_col_cx - closest_block_x_to_player_center)**2 + \
                                 (player_col_cz - closest_block_z_to_player_center)**2
                    
                    # Innerhalb des Spielers?
                    xz_intersects = dist_sq_xz < (player_radius**2)
                    y_intersects = (player_y_feet < block_max_y and player_y_feet + player_height > block_min_y)
                    if xz_intersects and y_intersects:
                        return 

                    # Platzieren des Blocks
                    selected_block_type = self.renderer.get_selected_block_type()
                    self.renderer.world.blocks.append(Block(px, py, pz, block_id=selected_block_type))
                    self.renderer._last_player_pos = (None, None, None)
                    self.renderer.trigger_hud_block_animation()
    
    # Dictionary für inputstatus
    def get_input_state(self):
        return {
            'moving': self.moving,
            'turning': self.turning,
            'jumping': self.actions.get('jump', False),
            'sprinting': self.actions.get('sprint', False)   
        }
