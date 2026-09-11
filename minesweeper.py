import time
import keyboard
import pyautogui
import cv2
from pathlib import Path
import threading
from tkinter import *
from functions import *
import settings

configs = {
    'easy': {
        'tile_size': 58,
        'board_x': 10,
        'board_y': 8,
        'top_left': (691, 396), #default value
        'total_mines': 10,
        'surrounding_tiles': {
            'up_left': -11,
            'up': -10,
            'up_right': -9,
            'left': -1,
            'right': +1,
            'down_left': +9,
            'down': +10,
            'down_right': +11
        }
    },
    'medium' : {
        'tile_size': 38,
        'board_x': 18,
        'board_y': 14,
        'top_left': (634, 358), #default value
        'total_mines': 40,
        'surrounding_tiles': {
            'up_left': -19,
            'up': -18,
            'up_right': -17,
            'left': -1,
            'right': +1,
            'down_left': +17,
            'down': +18,
            'down_right': +19
        }
    },
    'hard' : {
        'tile_size': 32,
        'board_x': 24,
        'board_y': 20,
        'top_left': (596, 307), #default value
        'total_mines': 99,
        'surrounding_tiles': {
            'up_left': -25,
            'up': -24,
            'up_right': -23,
            'left': -1,
            'right': +1,
            'down_left': +23,
            'down': +24,
            'down_right': +25
        }
    }
}
stop_game = True

root = Tk()
root.title("Minesweeper Solver")
root.geometry('300x300')
root.attributes("-topmost", True)

def auto():
    BASE_DIR = Path(__file__).parent
    IMAGE_DIR = BASE_DIR / "images"
    og_button_text = btn['text']
    og_button_width = btn['width']
    og_button_fg = btn['fg']

    images = {
        'easy.png': 'easy',
        'medium.png': 'medium',
        'hard.png': 'hard'
    }

    for img in images.keys():
        path = IMAGE_DIR / img
        try:
            pyautogui.locateOnScreen(str(path), confidence=0.95)
            return images[img]
        except pyautogui.ImageNotFoundException:
            continue

    btn.config(text='Auto Did Not Succeed!!', width=20, fg='Red')
    root.after(1000, lambda: btn.config(text=og_button_text, width=og_button_width, fg=og_button_fg))

def manual_calibration(mode):
    overlay = Toplevel(root)
    overlay.overrideredirect(True)
    overlay.wm_attributes("-topmost", True)

    label = Label(
        overlay,
        text="",
        bg="#1e1e1e",
        fg="#ffffff",
        font=("Arial", 10),
        padx=8,
        pady=4
    )
    label.pack()

    def update_position():
        if not overlay.winfo_exists():
            return

        x, y = pyautogui.position()
        label.config(text=f"X: {x}, Y: {y};\nPress 'z' to select position.\nPress 'esc' to exit.")
        overlay.geometry(f"+{x + 15}+{y + 15}")
        overlay.after(10, update_position)

    def mouse_arrows_movement(dir):
        x, y = pyautogui.position()
        if dir == 'up': pyautogui.moveTo(x, y-1)
        elif dir == 'down': pyautogui.moveTo(x, y+1)
        elif dir == 'left': pyautogui.moveTo(x-1, y)
        elif dir == 'right': pyautogui.moveTo(x+1, y)

    def exit_program():
        try:
            keyboard.remove_hotkey('esc')
            keyboard.remove_hotkey('z')
            keyboard.remove_hotkey('up')
            keyboard.remove_hotkey('down')
            keyboard.remove_hotkey('left')
            keyboard.remove_hotkey('right')
        except KeyError:
            pass
        root.after(0, overlay.destroy)

    def calibrate(mode):
        configs[mode]['top_left'] = tuple(pyautogui.position())
        print(f"Updated {mode} top_left:", configs[mode]['top_left'])
        exit_program()

    keyboard.add_hotkey('esc', exit_program)
    keyboard.add_hotkey('z', lambda: calibrate(mode))
    keyboard.add_hotkey('up', lambda: mouse_arrows_movement('up'))
    keyboard.add_hotkey('down', lambda: mouse_arrows_movement('down'))
    keyboard.add_hotkey('left', lambda: mouse_arrows_movement('left'))
    keyboard.add_hotkey('right', lambda: mouse_arrows_movement('right'))

    update_position()

def tool_assisted_calibration(mode):
    og_button_text = btn['text']
    og_button_width = btn['width']
    og_button_fg = btn['fg']
    root.iconify()

    base_dir = Path(__file__).parent
    image_loc = base_dir / "images" / "top_left_tile.png"
    try:
        location = pyautogui.locateOnScreen(str(image_loc), confidence=0.95)
        pyautogui.moveTo(location[0], location[1])
        configs[mode]['top_left'] = (location[0], location[1])
    except(pyautogui.ImageNotFoundException):
        btn.config(text='Auto Did Not Succeed!!', width=20, fg='Red')
        root.after(1000, lambda: btn.config(text=og_button_text, width=og_button_width, fg=og_button_fg))
        pass
    root.deiconify()

menu = Menu(root)
calibrate_menu = Menu(menu)
menu.add_cascade(label='Calibrate', menu=calibrate_menu)

tool_assisted_submenu = Menu(calibrate_menu)
tool_assisted_submenu.add_command(label='Easy', command=lambda: tool_assisted_calibration('easy'))
tool_assisted_submenu.add_command(label='Medium', command=lambda: tool_assisted_calibration('medium'))
tool_assisted_submenu.add_command(label='Hard', command=lambda: tool_assisted_calibration('hard'))
calibrate_menu.add_cascade(label='Tool-assisted', menu=tool_assisted_submenu)

manual_submenu = Menu(calibrate_menu)
manual_submenu.add_command(label='Easy', command=lambda: manual_calibration('easy'))
manual_submenu.add_command(label='Medium', command=lambda: manual_calibration('medium'))
manual_submenu.add_command(label='Hard', command=lambda: manual_calibration('hard'))
calibrate_menu.add_cascade(label='Manual', menu=manual_submenu)
root.config(menu=menu)

difficulty = StringVar(value="auto")
rd1 = Radiobutton(root, text="Easy", value="easy", variable=difficulty).pack()
rd2 = Radiobutton(root, text="Medium", value="medium", variable=difficulty).pack()
rd3 = Radiobutton(root, text="Hard", value="hard", variable=difficulty).pack()
rd4 = Radiobutton(root, text="Auto", value="auto", variable=difficulty).pack()

def game_loop():
    global stop_game
    game_state.clear()

    while not stop_game:
        pyautogui.moveTo(settings.state.top_left[0]-50,settings.state.top_left[1]-50)
        read_game_state(('o', '-',None))  # None should be added in 'what_to_check' bc game_state is initially empty; game_state.get() would return None
        start_and_end_check()
        # show_game_state(game_state)
        logic()

def bot_toggle(): #make this toggle
    global stop_game
    if not stop_game:
        stop_game = True
        btn.configure(text="'q' to Start", fg='Green')
        return

    choice = difficulty.get()
    if choice == 'auto':
        choice = auto()

    config = configs[choice]
    settings.state.tile_size = int(config['tile_size'])
    settings.state.board_x = int(config['board_x'])
    settings.state.board_y = int(config['board_y'])
    settings.state.top_left = tuple(config['top_left'])
    settings.state.total_mines = int(config['total_mines'])
    settings.state.surrounding_tiles = dict(config['surrounding_tiles'])

    stop_game = False
    btn.configure(text="'q' to Stop", fg='Red')
    threading.Thread(target=game_loop, daemon=True).start()

keyboard.add_hotkey('q', lambda: root.after(0, bot_toggle))

btn = Button(root, text='Start', fg='Green', command=bot_toggle, width=10, height=2)
btn.pack()
root.mainloop()
