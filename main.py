import turtle
from engine.renderer import Renderer
from engine.world import World
import os
import json
from datetime import datetime


# Definitiion von Größen und Farben
BUTTON_HOVER_COLOR = "lightgray"
BUTTON_NORMAL_COLOR = "white"
BUTTON_TEXT_COLOR = "black"
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
BUTTON_PADDING = 20
CONFIRM_BUTTON_COLOR = "green"
BACK_BUTTON_COLOR = "gray"

WORLD_BUTTON_WIDTH = 350
WORLD_BUTTON_HEIGHT = 75
WORLD_BUTTON_DETAIL_COLOR = "darkgray"
WORLD_BUTTON_DETAIL_FONT = ("Arial", 10, "italic")
WORLD_BUTTON_NAME_FONT = ("Arial", 14, "bold")

SCROLL_BUTTON_HEIGHT = 30
SCROLL_BUTTON_WIDTH = 150

join_menu_scroll_state = {
    "offset": 0,
    "items_per_view": 3,
    "world_data_cache": []
}

menu_turtle = turtle.Turtle()
menu_turtle.hideturtle()
menu_turtle.speed(0)
menu_turtle.penup()

screen = turtle.Screen()
screen.setup(width=800, height=600)
screen.title("3D Sandbox Game - Hauptmenü")
screen.bgcolor("lightblue")
screen.tracer(0)

buttons = []
game_renderer_instance = None

def draw_button(text, x, y, width, height, color=BUTTON_NORMAL_COLOR, text_color=BUTTON_TEXT_COLOR, enabled=True):
    menu_turtle.goto(x - width / 2, y - height / 2)
    current_fill_color = color if enabled else "#cccccc"
    current_text_color = text_color if enabled else "#888888"
    menu_turtle.color(current_fill_color)
    menu_turtle.begin_fill()
    for _ in range(2):
        menu_turtle.forward(width)
        menu_turtle.left(90)
        menu_turtle.forward(height)
        menu_turtle.left(90)
    menu_turtle.end_fill()
    menu_turtle.goto(x, y - (height/4) )
    menu_turtle.color(current_text_color)
    font_size = 16 if height >= 50 else 12
    menu_turtle.write(text, align="center", font=("Arial", font_size, "bold"))

def return_to_main_menu_from_game():
    global game_renderer_instance, screen
    
    if game_renderer_instance:
        game_renderer_instance.cleanup_for_main_menu()
        game_renderer_instance = None

    screen.onclick(None) 
    screen.getcanvas().unbind("<Motion>")
    keys_to_unbind = ["w", "a", "s", "d", "space", "Shift_L", "Control_L", "Tab", "q", "e", "f", "g", "r", "t", "Escape"]
    for key in keys_to_unbind:
        screen.onkeypress(None, key)
        screen.onkeyrelease(None, key)
    screen.listen()

    draw_main_menu()

def start_game(world_path=None, world_name=None, seed=None):
    global game_renderer_instance
    menu_turtle.clear()
    screen.onclick(None)
    screen.getcanvas().unbind("<Motion>")
    screen.onkey(None, "Up")
    screen.onkey(None, "Down")
    screen.onkey(None, "Return")
    screen.bgcolor("white")

    if world_path:
        world = World(path=world_path)
    elif world_name or seed is not None:
        world = World(generate_new_size=[64, 32, 64], world_name=world_name if world_name else None, seed=seed)
    else:
        world = World(generate_new_size=[64, 32, 64])
        
    game_renderer_instance = Renderer(world=world, on_exit_to_main_menu=return_to_main_menu_from_game)
    
def prompt_world_creation_details():
    menu_turtle.clear()
    screen.update()

    world_name = screen.textinput("Weltname", "Namen für die neue Welt eingeben (optional):")
    if world_name is None:
        draw_main_menu()
        return

    seed_str = screen.textinput("Seed", "Seed für die Weltengenerierung eingeben (optional, numerisch):")
    if seed_str is None:
        draw_main_menu()
        return
        
    final_seed = None
    if seed_str:
        try:
            final_seed = int(seed_str)
        except ValueError:
            pass

    draw_create_world_confirmation_menu(world_name, final_seed)

def draw_create_world_confirmation_menu(world_name, seed):
    menu_turtle.clear()
    buttons.clear()
    screen.bgcolor("lightblue")

    menu_turtle.goto(0, 200)
    menu_turtle.color("black")
    menu_turtle.write("Welt erstellen: Bestätigung", align="center", font=("Arial", 24, "bold"))

    display_name = f"Weltname: {world_name if world_name else 'Standard'}"
    display_seed = f"Seed: {seed if seed is not None else 'Standard'}"

    menu_turtle.goto(0, 120)
    menu_turtle.write(display_name, align="center", font=("Arial", 16, "normal"))
    menu_turtle.goto(0, 80)
    menu_turtle.write(display_seed, align="center", font=("Arial", 16, "normal"))

    btn_confirm_text = "Bestätigen"
    btn_confirm_y = 0
    confirm_action = lambda: start_game(world_name=world_name, seed=seed)
    draw_button(btn_confirm_text, 0, btn_confirm_y, BUTTON_WIDTH, BUTTON_HEIGHT, color=CONFIRM_BUTTON_COLOR, text_color="white")
    buttons.append({"text": btn_confirm_text, "x": 0, "y": btn_confirm_y, "width": BUTTON_WIDTH, "height": BUTTON_HEIGHT, "action": confirm_action, "color": CONFIRM_BUTTON_COLOR, "hover_color": "darkgreen"})

    btn_back_text = "Zurück"
    btn_back_y = btn_confirm_y - (BUTTON_HEIGHT + BUTTON_PADDING)
    draw_button(btn_back_text, 0, btn_back_y, BUTTON_WIDTH, BUTTON_HEIGHT, color=BACK_BUTTON_COLOR, text_color="white")
    buttons.append({"text": btn_back_text, "x": 0, "y": btn_back_y, "width": BUTTON_WIDTH, "height": BUTTON_HEIGHT, "action": draw_main_menu, "color": BACK_BUTTON_COLOR, "hover_color": "darkgray"})
    
    screen.update()
    screen.onclick(handle_menu_click)
    screen.getcanvas().bind("<Motion>", canvas_mouse_move_handler)


def create_world_action():
    prompt_world_creation_details()

def join_world_action():
    join_menu_scroll_state["offset"] = 0
    join_menu_scroll_state["world_data_cache"] = [] 
    draw_join_world_menu(refresh_cache=True)

def draw_world_button(world_info, x, y, width, height, color=BUTTON_NORMAL_COLOR):
    menu_turtle.goto(x - width / 2, y - height / 2)
    menu_turtle.color(color)
    menu_turtle.begin_fill()
    for _ in range(2):
        menu_turtle.forward(width)
        menu_turtle.left(90)
        menu_turtle.forward(height)
        menu_turtle.left(90)
    menu_turtle.end_fill()

    name_x = x - width / 2 + 15
    name_y = y + height / 2 - 28
    menu_turtle.goto(name_x, name_y)
    menu_turtle.color(BUTTON_TEXT_COLOR)
    menu_turtle.write(world_info.get('name', 'Unbekannte Welt'), align="left", font=WORLD_BUTTON_NAME_FONT)

    detail_y = y + height / 2 - 50
    
    seed_text = f"Seed: {world_info.get('seed', 'N/A')}"
    menu_turtle.goto(name_x, detail_y)
    menu_turtle.color(WORLD_BUTTON_DETAIL_COLOR)
    menu_turtle.write(seed_text, align="left", font=WORLD_BUTTON_DETAIL_FONT)

    last_saved_dt = world_info.get('last_saved_dt')
    if last_saved_dt and last_saved_dt != datetime.min:
        last_saved_text = last_saved_dt.strftime('%d.%m.%Y %H:%M')
    else:
        last_saved_text = world_info.get('last_saved', 'N/A') 

    last_saved_x = x + width / 2 - 15
    menu_turtle.goto(last_saved_x, detail_y)
    menu_turtle.color(WORLD_BUTTON_DETAIL_COLOR)
    menu_turtle.write(last_saved_text, align="right", font=WORLD_BUTTON_DETAIL_FONT)

def draw_join_world_menu(refresh_cache=True):
    menu_turtle.clear()
    buttons.clear()
    screen.bgcolor("lightblue")

    state = join_menu_scroll_state

    if refresh_cache:
        state["offset"] = 0
        state["world_data_cache"] = []
        worlds_dir = "worlds"
        if not os.path.exists(worlds_dir):
            os.makedirs(worlds_dir)
        
        world_files = [f for f in os.listdir(worlds_dir) if f.endswith(".json")]
        temp_world_data = []
        for world_file in world_files:
            world_path = os.path.join(worlds_dir, world_file)
            try:
                with open(world_path, 'r') as f:
                    data = json.load(f)
                metadata = data.get("metadata", {})
                world_name = metadata.get("world_name", os.path.splitext(world_file)[0])
                seed = metadata.get("seed", "N/A")
                last_saved_str = metadata.get("last_saved", "N/A")
                
                last_saved_dt = None
                if last_saved_str != "N/A":
                    try:
                        last_saved_dt = datetime.fromisoformat(last_saved_str)
                    except ValueError:
                        try:
                            last_saved_dt = datetime.strptime(last_saved_str, '%Y-%m-%d %H:%M:%S.%f')
                        except ValueError:
                            try:
                                last_saved_dt = datetime.strptime(last_saved_str, '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                try:
                                    last_saved_dt = datetime.strptime(last_saved_str, '%d.%m.%Y %H:%M')
                                except ValueError:
                                    print(f"Ungültiges Datumsformat für last_saved in {world_file}: {last_saved_str}")
                                    last_saved_dt = datetime.min

                temp_world_data.append({
                    "name": world_name, 
                    "seed": seed, 
                    "last_saved": last_saved_str,
                    "path": world_path, 
                    "last_saved_dt": last_saved_dt
                })
            except Exception as e:
                print(f"Fehler beim Laden der Welt-Metadaten {world_path}: {e}")

        state["world_data_cache"] = sorted(temp_world_data, key=lambda x: x["last_saved_dt"] if x["last_saved_dt"] else datetime.min, reverse=True)
    
    title_y = screen.window_height() / 2 - 50
    menu_turtle.goto(0, title_y)
    menu_turtle.color("black")
    menu_turtle.write("Welt beitreten", align="center", font=("Arial", 24, "bold"))

    list_area_top_y = title_y - 70
    list_area_height = screen.window_height() * 0.5
    list_area_bottom_y = list_area_top_y - list_area_height

    if WORLD_BUTTON_HEIGHT + BUTTON_PADDING > 0:
        state["items_per_view"] = int(list_area_height // (WORLD_BUTTON_HEIGHT + BUTTON_PADDING))
    else:
        state["items_per_view"] = 0
    if state["items_per_view"] <= 0: state["items_per_view"] = 1

    start_index = state["offset"]
    end_index = state["offset"] + state["items_per_view"]
    visible_worlds = state["world_data_cache"][start_index:end_index]

    scroll_button_y_top = list_area_top_y + SCROLL_BUTTON_HEIGHT / 2 + BUTTON_PADDING / 2
    scroll_button_y_bottom = list_area_bottom_y - SCROLL_BUTTON_HEIGHT / 2 - BUTTON_PADDING / 2

    can_scroll_up = state["offset"] > 0
    can_scroll_down = (state["offset"] + state["items_per_view"]) < len(state["world_data_cache"])

    if len(state["world_data_cache"]) > state["items_per_view"]:
        draw_button("Hoch", 0, scroll_button_y_top, SCROLL_BUTTON_WIDTH, SCROLL_BUTTON_HEIGHT, enabled=can_scroll_up)
        if can_scroll_up:
            buttons.append({"text": "Hoch", "x": 0, "y": scroll_button_y_top, "width": SCROLL_BUTTON_WIDTH, "height": SCROLL_BUTTON_HEIGHT, "action": lambda: scroll_join_menu(-1), "color": BUTTON_NORMAL_COLOR, "hover_color": BUTTON_HOVER_COLOR})
        
        draw_button("Runter", 0, scroll_button_y_bottom, SCROLL_BUTTON_WIDTH, SCROLL_BUTTON_HEIGHT, enabled=can_scroll_down)
        if can_scroll_down:
            buttons.append({"text": "Runter", "x": 0, "y": scroll_button_y_bottom, "width": SCROLL_BUTTON_WIDTH, "height": SCROLL_BUTTON_HEIGHT, "action": lambda: scroll_join_menu(1), "color": BUTTON_NORMAL_COLOR, "hover_color": BUTTON_HOVER_COLOR})

    if not state["world_data_cache"]:
        menu_turtle.goto(0, list_area_top_y - list_area_height / 2)
        menu_turtle.write("Keine Welten gefunden.", align="center", font=("Arial", 16, "normal"))
    else:
        for i, world_info in enumerate(visible_worlds):
            btn_x = 0
            btn_y = list_area_top_y - (i * (WORLD_BUTTON_HEIGHT + BUTTON_PADDING)) - WORLD_BUTTON_HEIGHT / 2
            
            draw_world_button(world_info, btn_x, btn_y, WORLD_BUTTON_WIDTH, WORLD_BUTTON_HEIGHT)
            buttons.append({
                "text": world_info["name"], "world_info": world_info,
                "x": btn_x, "y": btn_y, "width": WORLD_BUTTON_WIDTH, "height": WORLD_BUTTON_HEIGHT,
                "action": lambda p=world_info["path"]: start_game(world_path=p),
                "color": BUTTON_NORMAL_COLOR, "hover_color": BUTTON_HOVER_COLOR,
                "is_world_button": True
            })

    back_button_y = -screen.window_height() / 2 + BUTTON_HEIGHT / 2 + BUTTON_PADDING
    draw_button("Zurück", 0, back_button_y, BUTTON_WIDTH, BUTTON_HEIGHT, color=BACK_BUTTON_COLOR, text_color="white")
    buttons.append({"text": "Zurück", "x": 0, "y": back_button_y, "width": BUTTON_WIDTH, "height": BUTTON_HEIGHT, "action": draw_main_menu, "color": BACK_BUTTON_COLOR, "hover_color": "darkgray"})

    screen.update()
    screen.onclick(handle_menu_click)
    screen.getcanvas().bind("<Motion>", canvas_mouse_move_handler)

def scroll_join_menu(direction):
    state = join_menu_scroll_state
    num_total_items = len(state["world_data_cache"])

    new_offset = state["offset"] + direction

    max_offset = num_total_items - state["items_per_view"]
    if max_offset < 0:
        max_offset = 0
        
    state["offset"] = max(0, min(new_offset, max_offset))
    
    draw_join_world_menu(refresh_cache=False)

def draw_main_menu():
    menu_turtle.clear()
    buttons.clear()
    screen.bgcolor("lightblue")

    menu_turtle.goto(0, 200)
    menu_turtle.color("black")
    menu_turtle.write("3D Sandbox Game", align="center", font=("Arial", 30, "bold"))

    button_y_start = 50
    button_spacing = BUTTON_HEIGHT + BUTTON_PADDING

    btn_create_text = "Welt erstellen"
    btn_create_y = button_y_start
    draw_button(btn_create_text, 0, btn_create_y, BUTTON_WIDTH, BUTTON_HEIGHT)
    buttons.append({"text": btn_create_text, "x": 0, "y": btn_create_y, "width": BUTTON_WIDTH, "height": BUTTON_HEIGHT, "action": create_world_action, "color": BUTTON_NORMAL_COLOR, "hover_color": BUTTON_HOVER_COLOR})

    btn_join_text = "Welt beitreten"
    btn_join_y = btn_create_y - button_spacing
    draw_button(btn_join_text, 0, btn_join_y, BUTTON_WIDTH, BUTTON_HEIGHT)
    buttons.append({"text": btn_join_text, "x": 0, "y": btn_join_y, "width": BUTTON_WIDTH, "height": BUTTON_HEIGHT, "action": join_world_action, "color": BUTTON_NORMAL_COLOR, "hover_color": BUTTON_HOVER_COLOR})

    version_text = "v1"
    version_x = -screen.window_width() / 2 + 10
    version_y = -screen.window_height() / 2 + 10
    menu_turtle.penup()
    menu_turtle.goto(version_x, version_y)
    menu_turtle.color("black")
    menu_turtle.write(version_text, align="left", font=("Arial", 12, "normal"))

    credits_text = "Timon Scheuer 10/2, Julian Kern 10/2"
    credits_x = screen.window_width() / 2 - 10
    credits_y = -screen.window_height() / 2 + 10
    menu_turtle.penup()
    menu_turtle.goto(credits_x, credits_y)
    menu_turtle.color("black")
    menu_turtle.write(credits_text, align="right", font=("Arial", 12, "normal"))

    screen.update()
    screen.onclick(handle_menu_click)
    screen.getcanvas().bind("<Motion>", canvas_mouse_move_handler)


def handle_menu_click(x, y):
    for button in buttons:
        btn_x, btn_y, width, height = button["x"], button["y"], button["width"], button["height"]
        is_enabled = button.get("enabled", True) 
        if is_enabled and btn_x - width / 2 < x < btn_x + width / 2 and \
           btn_y - height / 2 < y < btn_y + height / 2:
            if button["action"]:
                button["action"]()
            break

def handle_mouse_move(x, y):
    redraw_needed = False
    for button in buttons:
        btn_x, btn_y, width, height = button["x"], button["y"], button["width"], button["height"]
        is_enabled = button.get("enabled", True)
        
        is_hovering = False
        if is_enabled and btn_x - width / 2 < x < btn_x + width / 2 and \
           btn_y - height / 2 < y < btn_y + height / 2:
            is_hovering = True

        current_hover_state = button.get("is_hovering", False)
        if current_hover_state != is_hovering:
            button["is_hovering"] = is_hovering
            redraw_needed = True
            
            current_color = button.get("hover_color") if is_hovering else button.get("color")
            text_color = BUTTON_TEXT_COLOR 
            
            if button.get("is_world_button", False):
                 draw_world_button(button["world_info"], btn_x, btn_y, width, height, color=current_color)
            else:
                 draw_button(button["text"], btn_x, btn_y, width, height, color=current_color, text_color=text_color, enabled=is_enabled)
    
    if redraw_needed:
        screen.update()

def canvas_mouse_move_handler(event):
    canvas = screen.getcanvas()
    x = event.x - canvas.winfo_width() / 2
    y = canvas.winfo_height() / 2 - event.y
    handle_mouse_move(x,y)


if __name__ == "__main__":
    draw_main_menu()
    turtle.done()
