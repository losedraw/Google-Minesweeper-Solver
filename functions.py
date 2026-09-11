import pyautogui
import time
import keyboard
from itertools import combinations
import random
from PIL import Image
import inspect
import settings

pyautogui.PAUSE = 0.001

click_on_opened = []
last_read_board_state = {}
game_state = {}

# Map of known tile colors to values
color_definitions = {
    (229, 194, 159): 0,
    (215, 184, 153): 0,
    (162, 209, 73): '-',
    (170, 215, 81): '-',
    (25, 118, 210): 1,
    (56, 142, 60): 2,
    (212, 53, 52): 3,
    (123, 31, 162): 4,
    (255, 143, 0): 5,
    (0, 151, 167): 6,
}

def color_matcher(ref_color: tuple, pixel_color: tuple, tolerance=10):
    return all(abs(c1-c2) <= tolerance for c1, c2 in zip(ref_color, pixel_color))

def read_game_state(what_to_check: tuple): #We make a grid based on board_x and board_y. The first tile is index 0 and last tile is index 79 (for medium).
    time.sleep(0.25)
    screenshot = pyautogui.screenshot(region=(*settings.state.top_left,
                                              settings.state.board_x*settings.state.tile_size,
                                              settings.state.board_y*settings.state.tile_size)) #screenshot the board
    for y in range(settings.state.board_y):
        for x in range(settings.state.board_x):
            unfiltered_input = []
            pos_x = (x * settings.state.tile_size) + settings.state.tile_size//2 #determines the x and y coordinates of each tile
            pos_y = (y * settings.state.tile_size) + settings.state.tile_size//2
            tile_info = game_state.get((pos_x+settings.state.top_left[0], pos_y+settings.state.top_left[1])) #tile_info is the state of the tile (opened, unopened, or number)
            if tile_info in (what_to_check):
                for additional_pixel in range(-13, 13, 1): #this checks to the left and right of each center of the tile to ensure it actually reads the number
                    if len(unfiltered_input) >= 2 or '-' in unfiltered_input: #if it reads as unopened tile, just skip the loop. if it reads at least 2 different values, that is enough
                        break
                    pixel_color = screenshot.getpixel((pos_x+additional_pixel, pos_y))
                    for ref_color, values in color_definitions.items():
                        if color_matcher(ref_color, pixel_color) and values not in unfiltered_input: #matches the pixel colour to a defined dictionary of colors and tile values
                            unfiltered_input.append(values)
                input_filter(unfiltered_input, pos_x, pos_y)

def input_filter(unfiltered_input, pos_x, pos_y):
    try: #if its a flag, dont do anything
        if game_state[(pos_x + settings.state.top_left[0], pos_y + settings.state.top_left[1])] == '⚑':
            return
    except KeyError:
        pass
    if '-' not in unfiltered_input: #if unopened, ignore
        if len(unfiltered_input) == 2: # for a numbered tile, it will read it as a 0 and another number
            #print(unfiltered_input)
            unfiltered_input.remove(0)  # this one will remove the 0, hence providing the actual tile value only

    try: # modifies the game_state with the appropriate tile value
        game_state[(pos_x + settings.state.top_left[0], pos_y + settings.state.top_left[1])] = unfiltered_input[0]
    except IndexError:
        pass

def surroundings_check(index, game_state, list_keys_game_state): #checks the general info of a tile based on surrounding tiles such as unopened, flags, and another special state for tametsi_brain and tametsi_alt
    neighbouring_tile_memory = {}
    unopened_tiles = 0
    flags = 0

    for offset in settings.state.surrounding_tiles.values():
        if is_valid_tile(index, offset):
            try:
                current_coord = list_keys_game_state[index + offset]
            except(IndexError):
                read_game_state(('-', 0, 1, 2, 3, 4, 5, 6, 7, 8, 9))
                return

            val = game_state.get(current_coord)
            neighbouring_tile_memory[current_coord] = val

            if val == '-':
                unopened_tiles += 1
            if val == '⚑':
                flags += 1
            if val == '@':
                flags += 0.5
    return unopened_tiles, flags, neighbouring_tile_memory

def logic(): #this is the whole logic of the solver
    global last_read_board_state
    print(settings.state.total_mines, settings.state.surrounding_tiles, settings.state.tile_size)
    indexed_game_state_tile_info = list(enumerate(game_state.values()))
    list_keys_game_state = list(game_state.keys())

    for index, tile_info in indexed_game_state_tile_info:
        try:
            unopened_tiles, flags, neighbouring_tile_memory = surroundings_check(index, game_state, list_keys_game_state)
        except(TypeError):
            print(f"[DEBUG CRASH] Index {index} failed in surroundings_check!")
            print(list(game_state.keys())[index])
            print(list(game_state.keys())[0])
            raise ValueError(f"surroundings_check returned None for index {index}")
        if unopened_tiles == 0:
            continue
        if tile_info == 0 and (unopened_tiles > 0 or list(neighbouring_tile_memory.values()).count('o') > 0 or flags > 0):
            read_game_state(('-', 0, 1, 2, 3, 4, 5, 6, 7, 8, 9))
            print('NEW GAME STATE')
            #show_game_state(game_state)
            try:
                if flags > tile_info: #sanity check
                    for coord, tile in game_state.items():
                        if tile != '⚑':
                            continue
                        unflag_tile(coord, game_state)
                break
            except TypeError:
                pass
        basic_logic(neighbouring_tile_memory, flags, unopened_tiles, tile_info, game_state)
        pattern_logic(game_state, index, tile_info)
        open_remaining_tiles(game_state)
        #show_game_state(game_state)
    if last_read_board_state == game_state:
        tametsi_brain(game_state)
        #show_game_state(game_state)
        last_read_board_state == game_state.copy()
        if last_read_board_state == game_state:
            bruteforce(game_state)
            #show_game_state(game_state)
            if last_read_board_state == game_state:
                tametsi_alt(game_state)
                for index, tile_info in indexed_game_state_tile_info:
                    unopened_tiles, flags, neighbouring_tile_memory = surroundings_check(index, game_state, list_keys_game_state)
                    neighbouring_memory_values = list(neighbouring_tile_memory.values())
                    if neighbouring_memory_values.count('@') + neighbouring_memory_values.count('-') < 5:
                        continue
                    basic_logic(neighbouring_tile_memory, flags, unopened_tiles, tile_info, game_state)
                show_game_state(game_state)
                unchunk(game_state)
                if last_read_board_state == game_state:
                    game_end_sequence()
    else:
        last_read_board_state = game_state.copy()

def is_valid_tile(index, offset): #This exists bc otherwise, will think the left of index 10 is 9
    if not (settings.state.board_x * settings.state.board_y - 1) >= index + offset >= 0: #handles the corners
        return False
    if not (index % settings.state.board_x != 0 or (index + offset) % settings.state.board_x != (settings.state.board_x - 1)): #handles left edge
        return False
    if not (index % settings.state.board_x != settings.state.board_x-1 or (index + offset) % settings.state.board_x != 0): #handles right edge
        return False
    return True

def basic_logic(neighbouring_tile_memory, flags, unopened_tiles, tile_info, game_state):
    for coord, tile in neighbouring_tile_memory.items():
        if unopened_tiles + flags == tile_info and tile == '-' and game_state[coord] != '⚑':  # ensures it doesnt click on a flag again:
            flag_tile(coord, game_state)
        if flags == tile_info and tile == '-' and game_state[coord] != 'o':  # avoids clicking on opened tile
            open_tile(coord, game_state)

def bruteforce(game_state):
    print('bruteforcin it')
    indexed_game_state_tile_info = list(enumerate(game_state.values()))
    list_keys_game_state = list(game_state.keys())

    if list(game_state.values()).count('-')/(settings.state.board_x*settings.state.board_y) > 0.05: #makes sure there is no premature bruteforcing
        return

    for index, tile_info in indexed_game_state_tile_info:
        unopened_tiles, flags, neighbouring_tile_memory = surroundings_check(index, game_state, list_keys_game_state)
        banned_permute = []
        unopened_tiles_list = []

        if type(tile_info) != int:
            continue
        if tile_info-flags in (0, 1):
            continue
        for coord, tile in neighbouring_tile_memory.items():
            if tile != '-':
                continue
            neighbours_unopened, neighbours_flags, neighbours_tile_memory = surroundings_check(list(game_state).index(coord), game_state, list_keys_game_state)
            if list(neighbours_tile_memory.values()).count('-') >= 5:
                banned_permute.append(list(game_state).index(coord))
        if index in banned_permute:
            continue

        for coord, tile in neighbouring_tile_memory.items():
            if tile == '-':
                unopened_tiles_list.append(coord)
        try:
            all_mines_combo = list(combinations(unopened_tiles_list, tile_info-flags))
        except(ValueError):
            return

        for combo in all_mines_combo:
            valid_check = True
            for coord in combo:
                flag_tile(coord, game_state)
            for coord, tile in game_state.items():  # checks if combination is valid
                if type(tile) != int:
                    continue
                _, flags, _ = surroundings_check(list(game_state.keys()).index(coord), game_state, list_keys_game_state)
                if tile - flags < 0:
                    valid_check = False
                    for pos in combo:
                        unflag_tile(pos, game_state)
                    break
            if valid_check == True:
                print(combo)
                for index, tile_info in indexed_game_state_tile_info:
                    unopened_tiles, flags, neighbouring_tile_memory = surroundings_check(index, game_state, list_keys_game_state)
                    basic_logic(neighbouring_tile_memory, flags, unopened_tiles, tile_info, game_state)
                return

def tametsi_brain(game_state):
    print('tametsin it')
    list_keys_game_state = list(game_state.keys())

    for coord, tile_info in game_state.items():
        index = list(game_state.keys()).index(coord)
        unopened_tiles, flags, neighbouring_memory = surroundings_check(index, game_state, list_keys_game_state)
        if type(tile_info) != int: #ensures tile is a number
            continue
        if tile_info-flags != 1: #ensures its an effective 1
            continue
        if unopened_tiles != 2: #ensures theres only 2 open spaces for chunking
            continue
        for pos, tile in neighbouring_memory.items():
            if tile == '-':
                chunk_flag(pos, game_state)
        #if list(game_state.values()).count('@') > 0:
         #   show_game_state(game_state)
        for co, ti in game_state.items():
            idx = list(game_state.keys()).index(co)
            unop_ti, flg, neighbouring_mem = surroundings_check(idx, game_state, list_keys_game_state)
            basic_logic(neighbouring_mem, flg, unop_ti, ti, game_state)
        unchunk(game_state)

def tametsi_alt(game_state): #this method is not 100%, supposed to catch cases where more than 1 chunk needs to be accounted for to solve
    print('tametsin it')
    indexed_game_state_tile_info = list(enumerate(game_state.values()))
    list_keys_game_state = list(game_state.keys())
    chunk_memory = []

    for coord, tile_info in game_state.items():
        index = list(game_state.keys()).index(coord)
        unopened_tiles, flags, neighbouring_memory = surroundings_check(index, game_state, list_keys_game_state)
        if type(tile_info) != int: #ensures tile is a number
            continue
        if tile_info-flags != 1: #ensures its an effective 1
            continue
        for adjacent_tile_offset in (1, settings.state.board_x):
            unopened_tiles_around_adjacent_tile, flags_around_adjacent_tile, neighbouring_memory_around_adjacent_tile = surroundings_check(index+adjacent_tile_offset, game_state, list_keys_game_state)
            if is_valid_tile(index, adjacent_tile_offset) == False:
                continue
            if type(indexed_game_state_tile_info[index + adjacent_tile_offset][1]) != int: #ensures pair is a number
                continue
            if indexed_game_state_tile_info[index+adjacent_tile_offset][1]-flags_around_adjacent_tile != 1: #ensures the other part of the pair is a 1
                continue
            if unopened_tiles+unopened_tiles_around_adjacent_tile > 4: #4 bc 2 opened each, they see it independently of each other
                continue
            for pos, tile in (neighbouring_memory | neighbouring_memory_around_adjacent_tile).items():
                if tile == '-':
                    chunk_memory.append(pos)
    for coord in chunk_memory:
        chunk_flag(coord, game_state)

def unchunk(game_state):
    for coord, tile_info in game_state.items():
        if tile_info == '@':
            game_state[coord] = '-'

def find_non_flagged_neighbours(game_state, offset_of_b, index):
    non_flagged_neigbours_a = []
    non_flagged_neigbours_b = []
    index_b = index + offset_of_b
    indexed_game_state_tile_info = list(enumerate(game_state.values()))

    for offset_a in settings.state.surrounding_tiles.values():
        if is_valid_tile(index, offset_a) and indexed_game_state_tile_info[index+offset_a][1] == '-':
            if index+offset_a not in non_flagged_neigbours_a:
                non_flagged_neigbours_a.append(index+offset_a)
    for offset_b in settings.state.surrounding_tiles.values():
        if is_valid_tile(index_b, offset_b) and indexed_game_state_tile_info[index_b+offset_b][1] == '-':
            if index_b+offset_b not in non_flagged_neigbours_b:
                non_flagged_neigbours_b.append(index_b+offset_b)

    return non_flagged_neigbours_a, non_flagged_neigbours_b

def pattern_logic(game_state, index, tile_info):
    indexed_game_state_tile_info = list(enumerate(game_state.values()))
    indexed_game_state_coords = list(enumerate(game_state.keys()))
    list_keys_game_state = list(game_state.keys())
    str_check = [0, 1, settings.state.board_x]
    try:
        if type(indexed_game_state_tile_info[index][1]) != int:
            return
        for check in str_check[:]:
            if type(indexed_game_state_tile_info[index+check][1]) != int:
                str_check.remove(check)
        _, flags_a, _ = surroundings_check(index, game_state, list_keys_game_state)
        value_a = indexed_game_state_tile_info[index][1] - flags_a
        for offset_b in str_check[::-1]:
            if is_valid_tile(index, offset_b):
                _, flags_b, _ = surroundings_check(index+offset_b, game_state, list_keys_game_state)
                value_b = indexed_game_state_tile_info[index+offset_b][1] - flags_b
                offset_of_b = offset_b
                if value_b != 0:
                    break

        non_flagged_neigbours_a, non_flagged_neigbours_b = find_non_flagged_neighbours(game_state, offset_of_b, index)
        a_not_b = [a for a in non_flagged_neigbours_a if a not in non_flagged_neigbours_b]
        b_not_a = [b for b in non_flagged_neigbours_b if b not in non_flagged_neigbours_a]
        a_and_b = [a for a in non_flagged_neigbours_a if a in non_flagged_neigbours_b]

        if value_a-value_b == len(a_not_b):
            for idx in a_not_b:
                flag_tile(indexed_game_state_coords[idx][1], game_state)
            for idx in b_not_a:
                open_tile(indexed_game_state_coords[idx][1], game_state)
        elif value_b-value_a == len(b_not_a):
            for idx in b_not_a:
                flag_tile(indexed_game_state_coords[idx][1], game_state)
            for idx in a_not_b:
                open_tile(indexed_game_state_coords[idx][1], game_state)
    except (IndexError, TypeError):
        pass

def chunk_flag(coord: tuple, game_state):
    game_state[coord] = "@"

def unflag_tile(coord: tuple, game_state):
    #pyautogui.rightClick(*coord)
    game_state[coord] = '-'

def flag_tile(coord: tuple, game_state):
    #pyautogui.rightClick(*coord)
    game_state[coord] = '⚑'

def open_tile(coord: tuple, game_state):
    pyautogui.leftClick(*coord)
    caller = inspect.currentframe().f_back.f_code.co_name
    print(f"open_tile() was called by {caller}")
    print(f'index: {list(game_state).index(coord)}')
    game_state[coord] = 'o'

def open_remaining_tiles(game_state):
    if list(game_state.values()).count('⚑') == settings.state.total_mines:
        for coord, tile_info in game_state.items():
            if tile_info == '-':
                open_tile(coord, game_state)

def cycle_repeat():
    for i in range(4):
        pyautogui.click(944, 735)
    time.sleep(0.5)
    pyautogui.click(944, 735)
    time.sleep(0.7)

def final_game_state_cleaner(game_state):
    list_keys_game_state = list(game_state.keys())
    coord = list(game_state.keys())
    tile_info = list(game_state.values())

    for index, coord in enumerate(coord):
        if tile_info[index] == 'o':
            _, flags, _ = surroundings_check(index, game_state, list_keys_game_state)
            game_state[coord] = flags
    #show_game_state(game_state)

def game_end_sequence():
    print('Game End')
    final_game_state_cleaner(game_state)
    game_state.clear()
    cycle_repeat()

def start_and_end_check(): #make end game checks better
    list_value_game_state = list(game_state.values())
    list_keys_game_state = list(game_state.keys())
    if list_value_game_state.count('⚑') == settings.state.total_mines:
        game_end_sequence()
    if list_value_game_state.count('-') == settings.state.board_x * settings.state.board_y:
        open_tile(list_keys_game_state[0], game_state)
        time.sleep(1)

def show_game_state(game_state):
    for index, tile_info in enumerate(game_state.values()):
        print(tile_info, end=' ')
        if (index + 1) % settings.state.board_x == 0:
            print('')
    print('')

