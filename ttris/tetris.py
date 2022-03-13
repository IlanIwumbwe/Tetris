import random
import pygame
from pygame import mixer
from itertools import permutations
import data
import numpy as np
import time

# game assets

I = '....' \
    'xxxx' \
    '....' \
    '....'

S = '....' \
    '.xx.' \
    'xx..' \
    '....'

O = '....' \
    '.xx.' \
    '.xx.' \
    '....'

Z = '....' \
    'xx..' \
    '.xx.' \
    '....'

T = '....' \
    '.x..' \
    'xxx.' \
    '....'

L = '....' \
    '...x' \
    '.xxx' \
    '....'

J = '....' \
    'x...' \
    'xxx.' \
    '....'

CLOCKWISE_MATRIX = [[0, 1], [-1, 0]]
ANTICLOCKWISE_MATRIX = [[0, -1], [1, 0]]

pieces = {'I':I, 'S': S, 'O': O, 'Z': Z, 'T': T, 'L': L, 'J': J}
centres = {'I': (1, 1), 'S': (1, 2), 'O': (1, 1), 'Z': (1, 2), 'T': (1, 2), 'L': (2, 2), 'J': (1, 2)}

CYAN = (51, 255, 255)
BLUE = (255, 255, 100)
PINK = (255, 51, 255)
YELLOW = (0, 0, 255)
ORANGE = (255, 128, 0)
RED = (255, 0, 0)
GREEN = (51, 255, 51)
WHITE = (255, 255, 255)
GREY = (100, 100, 100)
BLACK = (0, 0, 0)
SPAWN_ROWS = (100, 140, 40) #(50, 100, 255)
BG = (128, 128, 128)

colours = {'I': CYAN, 'S': BLUE, 'O': PINK, 'Z': YELLOW, 'T': ORANGE, 'L': GREEN, 'J': RED}

action_space = {pygame.K_DOWN: 'down', pygame.K_RIGHT: 'right', pygame.K_LEFT: 'left', pygame.K_UP: 'cw',
                pygame.K_w: 'ccw', pygame.K_TAB: 'hd', pygame.K_SPACE: 'hold', pygame.K_BACKSPACE: 'unhold'}

BOUNDARY = 1
ROWS = 20 + 2  # 2 extra rows for spawning
COLUMNS = 10

# dimensions
width = 800
height = 650
block_size = 20
play_w = ROWS * block_size
play_h = COLUMNS * block_size

top_left_x = (width - play_w) // 2 - 100
top_left_y = height - play_h - 400

# font and music!
f = 'freesansbold.ttf'

"""
mixer.init()
mixer.music.load('tetris-gameboy-02.ogg')
mixer.music.play(-1)
"""

class SRS:
    def __init__(self, piece):  # piece is an object
        self.piece = piece
        self.centre = self.piece.centre
        self.rot_index = self.piece.rot_index

    def rotation(self, clockwise, piece_string):
        mat = None
        piece = [piece_string[i:i + 4] for i in range(0, len(piece_string), 4)]
        c_x, c_y = self.centre

        global_cords = []
        new_global_cords = []

        relative_cords = []
        new_relative_cords = []

        # get global cords
        for ind_x, row in enumerate(piece):
            for ind_y, col in enumerate(row):
                if col == 'x':
                    global_cords.append((ind_y, ind_x))

        # get relative cords to centre
        for x, y in global_cords:
            relative_cords.append((x - c_x, y - c_y))

        if clockwise:
            mat = CLOCKWISE_MATRIX
        if not clockwise:
            mat = ANTICLOCKWISE_MATRIX

        # calculate new relative cord to centre
        for cord in relative_cords:
            new_r_cord = np.dot(cord, mat)
            new_relative_cords.append(new_r_cord)

        # get new global cords
        for x, y in new_relative_cords:
            new_global_cords.append((x + c_x, y + c_y))

        return new_global_cords


class Piece:
    def __init__(self, x=None, y=None, str_piece=None):
        self.x = x
        self.y = y
        self.str_id = str_piece
        self.piece = pieces[self.str_id]
        self.rot_index = 0
        self.state = self.piece
        self.clockwise = None
        self.all = [(j, i) for i in range(4) for j in range(4)]
        self.centre = centres[self.str_id]
        self.colour = colours[self.str_id] if self.piece is not None else None
        self.state_cords = data.Data(self.str_id, 0).get_data()

    def rotate(self, dir):
        rotation_data_for_I = data.Data(self.str_id, self.rot_index).get_data()
        srs = SRS(self)
        new_str = ['.' for _ in range(16)]


        if self.str_id != 'I':
            if dir == 'cw':
                self.clockwise = True
            else:
                self.clockwise = False

            self.state_cords = srs.rotation(self.clockwise, self.state)

            for x, y in self.state_cords:
                ind = 4*y + x
                new_str[ind] = 'x'

            self.state = ''.join(new_str)
        else:
            self.state_cords = rotation_data_for_I

            for x, y in self.state_cords:
                ind = 4 * y + x
                new_str[ind] = 'x'

            self.state = ''.join(new_str)

    def current_position(self):  # get grid positions of a passed piece object
        return [(r_x+self.x, r_y+self.y) for r_x, r_y in self.state_cords]

    def get_config(self):
        return self.rot_index, (self.x, self.y), self.current_position(), 0

class Collision:
    def __init__(self):  # piece is an object
        self.boundary = [(row, col) for col in range(1) for row in range(24)] + \
                        [(row, col) for col in range(12) for row in range(1)] + \
                        [(row, col) for col in range(11, 12) for row in range(24)] + \
                        [(row, col) for col in range(12) for row in range(23, 24)]
        self.field = [[0 for _ in range(COLUMNS + 2 * BOUNDARY)] for _ in range(ROWS + 2 * BOUNDARY)]

    def create_field(self, landed):
        self.field = [[0 for _ in range(COLUMNS + 2 * BOUNDARY)] for _ in range(ROWS + 2 * BOUNDARY)]
        # create landed positions
        if landed != {}:
            for (x, y) in landed.keys():
                try:
                    self.field[y+BOUNDARY][x+BOUNDARY] = 1
                except IndexError:
                    print('Error on landed piece placement')
                    pass

        # create boundary
        for x, y in self.boundary:
            try:
                self.field[x][y] = 1
            except IndexError:
                print('Boundary positions are wrong')

    def move_works(self, piece, move):  # collision is an object
        srs = SRS(piece)

        if action_space[move] == 'cw':
            rotation_cords = get_rotation_cords(srs, 'cw', piece)

            print(f'Rotation cords : {rotation_cords}')
            print(f'Current piece : {piece.current_position()}')

            if all([self.field[y + BOUNDARY][x + BOUNDARY] == 0 for x, y in rotation_cords]):
                print('The move is valid')

            try:
                return all([self.field[y + BOUNDARY][x + BOUNDARY] == 0 for x, y in rotation_cords])
            except IndexError:
                print('Will try again')
                pass

        elif action_space[move] == 'ccw':
            rotation_cords = get_rotation_cords(srs, 'ccw', piece)

            try:
                return all([self.field[y + BOUNDARY][x + BOUNDARY] == 0 for x, y in rotation_cords])
            except IndexError:
                print('Will try again')
                pass

        elif action_space[move] == 'down':
            pos = piece.current_position()

            try:
                return all([self.field[y + BOUNDARY + 1][x + BOUNDARY] == 0 for x, y in pos])
            except IndexError:
                print('WIll try again')
                pass

        elif action_space[move] == 'right':
            pos = piece.current_position()

            try:
                return all([self.field[y + BOUNDARY][x + BOUNDARY + 1] == 0 for x, y in pos])
            except IndexError:
                print('Will try again')
                pass

        elif action_space[move] == 'left':
            pos = piece.current_position()

            try:
                return all([self.field[y + BOUNDARY][x + BOUNDARY - 1] == 0 for x, y in pos])
            except IndexError:
                print('Will try again')
                pass

        return False

    def print_f(self):
        for i in self.field:
            print(i)


class Board:
    def __init__(self, landed, lines, score):
        self.landed = landed
        self.score = score
        self.lines = lines
        self.level = 0

    def create_grid(self):
        # if you want to change colour of grid, change _____ to desired colour! (except tetromino colour)
        GRID = [[WHITE for column in range(COLUMNS)] for row in range(ROWS)]

        for i in range(ROWS):
            for j in range(COLUMNS):
                if (j, i) in self.landed:
                    # set colour if position is landed i.e there is a piece there
                    GRID[i][j] = self.landed[(j, i)]
        return GRID

    @staticmethod
    def show_best_move(grid, best_move):
        if best_move:
            for x, y in best_move[2]:
                try:
                    grid[y][x] = GREY
                except IndexError:
                    print('Problem')

    @staticmethod
    def show_held_piece(surface, held_piece):
        pos_x = top_left_x + play_w - 100
        pos_y = top_left_y

        n_p = [held_piece.piece[i:i + 4] for i in range(0, len(held_piece.piece), 4)]

        # outer rectangle
        # pygame.draw.rect(surface, (100,100,100), (pos_x, pos_y, play_w//2+60, play_h), 3)

        # next piece
        for ind_x, row in enumerate(n_p):
            for ind_y, column in enumerate(row):
                if column == 'x':
                    pygame.draw.rect(surface, held_piece.colour, (
                        pos_x + ind_y * block_size + 20, pos_y + ind_x * block_size + 20, block_size, block_size), 0)
                    pygame.draw.rect(surface, BLACK, (
                        pos_x + ind_y * block_size + 20, pos_y + ind_x * block_size + 20, block_size, block_size), 2)

    @staticmethod
    def show_next_piece(surface, next_piece):
        pos_x = top_left_x + play_w - 220
        pos_y = top_left_y

        n_p = [next_piece.piece[i:i + 4] for i in range(0, len(next_piece.piece), 4)]

        # outer rectangle
        # pygame.draw.rect(surface, (100,100,100), (pos_x, pos_y, play_w//2+60, play_h), 3)

        # next piece
        for ind_x, row in enumerate(n_p):
            for ind_y, column in enumerate(row):
                if column == 'x':
                    pygame.draw.rect(surface, next_piece.colour, (
                        pos_x + ind_y * block_size + 20, pos_y + ind_x * block_size + 20, block_size, block_size), 0)
                    pygame.draw.rect(surface, BLACK, (
                        pos_x + ind_y * block_size + 20, pos_y + ind_x * block_size + 20, block_size, block_size), 2)

    @staticmethod
    def render_grid(surface, grid):
        # boundary
        for i in range(ROWS + BOUNDARY + 1):
            for j in range(COLUMNS + BOUNDARY + 1):
                pygame.draw.rect(surface, GREY, (top_left_x - (BOUNDARY * block_size) + j * block_size,
                                                            top_left_y - (BOUNDARY * block_size) + i * block_size,
                                                            block_size, block_size), 0)
                pygame.draw.rect(surface, BLACK, (top_left_x - (BOUNDARY * block_size) + j * block_size,
                                                      top_left_y - (BOUNDARY * block_size) + i * block_size, block_size,
                                                      block_size), 2)

        # convert grid colours to output onto surface
        for ind_x, rows in enumerate(grid):
            for ind_y, colour in enumerate(rows):
                pygame.draw.rect(surface, colour, (
                    top_left_x + (ind_y * block_size), top_left_y + (ind_x * block_size), block_size, block_size), 0)

        # draw black boundaries
        for i in range(ROWS):
            for j in range(COLUMNS):
                if i == 0 or i == 1:  # first 2 rows are for spawing
                    pygame.draw.rect(surface, SPAWN_ROWS,
                                     (top_left_x + j * block_size, top_left_y + i * block_size, block_size, block_size),
                                     0)
                    pygame.draw.rect(surface, WHITE,
                                     (top_left_x + j * block_size, top_left_y + i * block_size, block_size, block_size),
                                     2)
                if grid[i][j] != WHITE:
                    pygame.draw.rect(surface, BLACK,
                                     (top_left_x + j * block_size, top_left_y + i * block_size, block_size, block_size),
                                     2)

    def clear_rows(self, grid):
        cleared_row = 0
        cleared_rows = 0

        for index in range(ROWS - 1, -1, -1):
            if WHITE not in grid[index]:
                cleared_rows += 1
                cleared_row = index
                for column in range(COLUMNS):
                    try:
                        del self.landed[(column, cleared_row)]  # deletes colours off cleared rows
                    except KeyError:
                        pass

        # sort all landed positions based on the rows in the grid, then reverse that as we are
        # searching grid from below

        for position in sorted(list(self.landed), key=lambda pos: pos[1], reverse=True):
            col, row = position

            if row < cleared_row:  # if row is above index of row that was cleared:
                new_pos = (col, row + cleared_rows)  # make new position that moves itm down by number of cleared rows

                self.landed[new_pos] = self.landed.pop(
                    position)  # .pop here removes colours from all rows above, and places them in their new positions

        self.lines += cleared_rows
        self.score += score_game(cleared_rows, self.level)

        return cleared_rows


class Piece_Gne:
    def __init__(self, bag):
        self.bag = bag
        self.start_ind = 0

    def generator_function(self):
        permu = list(permutations(self.bag))

        while True:
            for piece in random.choice(permu):
                yield piece

    def pop(self, buffer, gen):
        popped = buffer[self.start_ind]
        self.start_ind = (self.start_ind + 1) % len(buffer)
        buffer[self.start_ind] = next(gen)

        return popped

    def get_piece(self):
        gen = self.generator_function()
        buffer = [next(gen) for _ in range(7)]

        popped = self.pop(buffer, gen)

        p = Piece(4, 0, popped)
        return p


def get_rotation_cords(srs, dir, piece):
    data_for_I = data.Data('I', piece.rot_index).get_data()

    if piece.str_id == 'I':
        grid_cords = [(x + piece.x, y+ piece.y) for x, y in data_for_I]
    else:
        ascii_cords = srs.rotation(True, piece.state) if dir == 'cw' else srs.rotation(False, piece.state)

        grid_cords = [(x+ piece.x, y + piece.y) for x, y in ascii_cords]

    return grid_cords


def score_game(cleared, level):
    # more to be done
    if cleared == 1:
        return 40 + (40 * level)
    elif cleared == 2:
        return 100 + (100 * level)
    elif cleared == 3:
        return 300 + (300 * level)
    elif cleared == 4:
        return 1200 + (1200 * level)
    else:
        return 0

def get_data(piece, rot_index):
    return data.Data(piece, rot_index).get_data()

class Tetris:
    def __init__(self):
        self.win = pygame.display.set_mode((width, height))
        # piece generation setup
        self.generate = Piece_Gne(['I', 'S', 'O', 'Z', 'T', 'L', 'J'])

        # get starting piece object
        self.current_piece = self.generate.get_piece()

        # control parameters
        self.run = True
        self.show_piece = True
        self.held_piece = None
        self.change_piece = False
        self.hold_piece = False
        self.unhold_piece = False

        # get next piece
        self.next_piece = self.generate.get_piece()

        # game board setup
        self.landed = {}
        self.lines = 0
        self.score = 0
        self.board = Board(self.landed, self.lines, self.score)
        self.collision = Collision()
        self.collision.create_field(self.landed)
        self.tetrises = 0
        self.grid = self.board.create_grid()

        # gravity setup
        self.fall_time = 0
        self.fall_speed = 0.2

        # game clock
        self.clock = pygame.time.Clock()

        self.best_move = None

    def draw_window(self):  # pass instance of board
        pygame.font.init()

        font = pygame.font.Font(f, 15)

        pos_x = top_left_x + play_w
        pos_y = top_left_y + play_h // 2

        score = font.render(f'Score: {self.board.score}', True, BLACK)
        lines = font.render(f'Lines: {self.board.lines}', True, BLACK)
        level = font.render(f'Level: {self.board.level}', True, BLACK)
        next_text = font.render('NEXT PIECE', True, BLACK)
        hold_text = font.render('HOLD PIECE', True, BLACK)

        self.win.blit(score, (pos_x - 200, pos_y + 50))
        self.win.blit(lines, (pos_x - 200, pos_y + 80))
        self.win.blit(level, (pos_x - 200, pos_y + 110))
        self.win.blit(next_text, (pos_x - 200, pos_y - 90))
        self.win.blit(hold_text, (pos_x - 90, pos_y - 90))

        self.board.show_next_piece(self.win, self.next_piece)
        self.board.render_grid(self.win, self.grid)
        if self.held_piece is not None: self.board.show_held_piece(self.win, self.held_piece)
        pygame.display.update()

    def update_scores(self):
        with open('tetris_champs.txt', 'a') as file:
            file.write(f'\nScore: {self.score} ......  Lines: {self.lines}')

    def lost(self):
        # if piece touches top of grid, its a loss
        for pos in self.landed:
            if pos[1] <= 2:
                return True

        return False

    def change_state(self):
        # lock position
        for i in self.current_piece.current_position():
            self.landed[i] = self.current_piece.colour

        # clear rows
        cleared = self.board.clear_rows(self.grid)

        if cleared == 4:
            self.tetrises += 1

        # update game level
        self.board.level = self.lines // 10

        self.collision.create_field(self.landed)
        # self.collision.print_f()

        self.board.show_next_piece(self.win, self.next_piece)

        self.lines, self.score = self.board.lines, self.board.score  # maybe set self.lines = cleared ?

        self.current_piece = self.next_piece

        if [WHITE] * 10 == self.grid[1] and [WHITE] * 10 == self.grid[0] and [WHITE] * 10 == self.grid[2]:
            self.next_piece = self.generate.get_piece()
            self.change_piece = False

    def game_logic(self):
        self.grid = self.board.create_grid()

        self.fall_time += self.clock.get_rawtime()
        self.clock.tick()

        if self.fall_time / 1000 > self.fall_speed:
            self.fall_time = 0

            if self.collision.move_works(self.current_piece, pygame.K_DOWN):
                self.current_piece.y += 1
            else:
                self.board.score += 1
                self.change_piece = True

        self.win.fill(BG)

        pygame.display.set_caption('Tetris')

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.run = False
            if event.type == pygame.KEYDOWN:
                try:
                    self.collision.create_field(self.landed)
                    self.make_move(event.key)

                    if action_space[event.key] == 'hold':
                        self.hold_piece = True if self.held_piece is None else False

                    if action_space[event.key] == 'unhold':
                        self.unhold_piece = True if self.held_piece is not None else False
                except KeyError:
                    print('WRONG KEY!')

        piece_positions = self.current_piece.current_position()

        # render on board
        if self.show_piece:
            for x, y in piece_positions:
                if (x, y) not in self.landed:
                    try:
                        self.grid[y][x] = self.current_piece.colour
                    except IndexError:
                        # crushes through the wall
                        # print('wef')
                        self.run = False

        '''
        user wants to hold piece, store it in held piece, change current to next,
        generate new piece to replace next piece

        set hold piece back to false
        '''
        if self.hold_piece:
            self.held_piece = self.current_piece
            self.current_piece = self.next_piece
            self.next_piece = self.generate.get_piece()
            self.hold_piece = False

        '''
        user wants to unhold, piece, set hold pressed back to 0, so we reset state
        make it spawn exactly where current piece was
        make swap
        '''
        if self.unhold_piece:
            self.held_piece.x, self.held_piece.y = self.current_piece.x, self.current_piece.y
            self.current_piece = self.held_piece

            self.held_piece = None
            self.unhold_piece = False

        self.draw_window()

        if self.lost():
            self.run = False

    def make_move(self, move):
        if action_space[move] == 'down':
            if self.collision.move_works(self.current_piece, move):
                self.current_piece.y += 1

        elif action_space[move] == 'right':
            if self.collision.move_works(self.current_piece, move):
                self.current_piece.x += 1

        elif action_space[move] == 'left':
            if self.collision.move_works(self.current_piece, move):
                self.current_piece.x -= 1

        elif action_space[move] == 'cw':
            if self.collision.move_works(self.current_piece, move) != False and not self.current_piece.piece == O:
                self.current_piece.rotate('cw')
                self.current_piece.rot_index = (self.current_piece.rot_index + 1) % 4

        elif action_space[move] == 'ccw':
            if self.collision.move_works(self.current_piece, move) != False and not self.current_piece.piece == O:
                self.current_piece.rotate('ccw')
                self.current_piece.rot_index = (self.current_piece.rot_index - 1) % 4

        elif action_space[move] == 'hd':
            works = True

            while works:
                self.current_piece.y += 1
                works = self.collision.move_works(self.current_piece, pygame.K_DOWN)

                if not works:
                    break

tetris_game = Tetris()

while tetris_game.run:
    tetris_game.game_logic()

    if tetris_game.change_piece:
        tetris_game.change_state()


