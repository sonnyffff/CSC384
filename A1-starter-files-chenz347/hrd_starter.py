import copy
from heapq import heappush, heappop
import time
import argparse
import sys
from typing import Optional

# ====================================================================================

char_goal = '1'
char_single = '2'


class Piece:
    """
    This represents a piece on the Hua Rong Dao puzzle.
    """

    def __init__(self, is_goal, is_single, coord_x, coord_y, orientation: Optional[str]):
        """
        :param is_goal: True if the piece is the goal piece and False otherwise.
        :type is_goal: bool
        :param is_single: True if this piece is a 1x1 piece and False otherwise.
        :type is_single: bool
        :param coord_x: The x coordinate of the top left corner of the piece.
        :type coord_x: int
        :param coord_y: The y coordinate of the top left corner of the piece.
        :type coord_y: int
        :param orientation: The orientation of the piece (one of 'h' or 'v') 
            if the piece is a 1x2 piece. Otherwise, this is None
        :type orientation: str
        """

        self.is_goal = is_goal
        self.is_single = is_single
        self.coord_x = coord_x
        self.coord_y = coord_y
        self.orientation = orientation

    def __repr__(self):
        return '{} {} {} {} {}'.format(self.is_goal, self.is_single, \
                                       self.coord_x, self.coord_y, self.orientation)


class Board:
    """
    Board class for setting up the playing board.
    """

    def __init__(self, pieces: list[Piece]):
        """
        :param pieces: The list of Pieces
        :type pieces: List[Piece]
        """

        self.width = 4
        self.height = 5

        self.pieces = pieces

        # self.grid is a 2-d (size * size) array automatically generated
        # using the information on the pieces when a board is being created.
        # A grid contains the symbol for representing the pieces on the board.
        self.grid = []
        self.__construct_grid()

    def __eq__(self, other):
        if self.grid == other.grid:
            return True
        return False

    def __construct_grid(self):
        """
        Called in __init__ to set up a 2-d grid based on the piece location information.

        """

        for i in range(self.height):
            line = []
            for j in range(self.width):
                line.append('.')
            self.grid.append(line)

        for piece in self.pieces:
            if piece.is_goal:
                self.grid[piece.coord_y][piece.coord_x] = char_goal
                self.grid[piece.coord_y][piece.coord_x + 1] = char_goal
                self.grid[piece.coord_y + 1][piece.coord_x] = char_goal
                self.grid[piece.coord_y + 1][piece.coord_x + 1] = char_goal
            elif piece.is_single:
                self.grid[piece.coord_y][piece.coord_x] = char_single
            else:
                if piece.orientation == 'h':
                    self.grid[piece.coord_y][piece.coord_x] = '<'
                    self.grid[piece.coord_y][piece.coord_x + 1] = '>'
                elif piece.orientation == 'v':
                    self.grid[piece.coord_y][piece.coord_x] = '^'
                    self.grid[piece.coord_y + 1][piece.coord_x] = 'v'

    def display(self):
        """
        Print out the current board.

        """
        for i, line in enumerate(self.grid):
            for ch in line:
                print(ch, end='')
            print()


class State:
    """
    State class wrapping a Board with some extra current state information.
    Note that State and Board are different. Board has the locations of the pieces. 
    State has a Board and some extra information that is relevant to the search: 
    heuristic function, f value, current depth and parent.
    """

    def __init__(self, board, f, depth, parent=None):
        """
        :param board: The board of the state.
        :type board: Board
        :param f: The f value of current state.
        :type f: int
        :param depth: The depth of current state in the search tree.
        :type depth: int
        :param parent: The parent of current state.
        :type parent: Optional[State]
        """
        self.board = board
        self.f = f
        self.depth = depth
        self.parent = parent
        self.id = hash(board)  # The id for breaking ties.


def read_from_file(filename):
    """
    Load initial board from a given file.

    :param filename: The name of the given file.
    :type filename: str
    :return: A loaded board
    :rtype: Board
    """

    puzzle_file = open(filename, "r")

    line_index = 0
    pieces = []
    g_found = False

    for line in puzzle_file:

        for x, ch in enumerate(line):

            if ch == '^':  # found vertical piece
                pieces.append(Piece(False, False, x, line_index, 'v'))
            elif ch == '<':  # found horizontal piece
                pieces.append(Piece(False, False, x, line_index, 'h'))
            elif ch == char_single:
                pieces.append(Piece(False, True, x, line_index, None))
            elif ch == char_goal:
                if g_found == False:
                    pieces.append(Piece(True, False, x, line_index, None))
                    g_found = True
        line_index += 1

    puzzle_file.close()

    board = Board(pieces)

    return board


##########################################
# Helper Functions
##########################################

def goal_test(state: State):
    """ Test whether the given state is goal state.

    """
    if state.board.grid[3][1] == char_goal:
        if state.board.grid[3][2] == char_goal:
            if state.board.grid[4][1] == char_goal:
                if state.board.grid[4][2] == char_goal:
                    return True
    return False


def heuristic(state: State):
    """ Return the heuristic value of the given state.

    可能两个
    """


def find_empty_spot(inboard: Board):
    """ Return the coordinates of the two empty spots on the board.

    """
    empty_spots = []
    for y in range(0, 4):
        for x in range(0, 5):
            if inboard.grid[y][x] == '.':
                empty_spots.append([x, y])
    return empty_spots


def check_spot_valid(spot: list):
    """ Check if given coordinate a valid spot on the chess board.

    """
    if 3 >= spot[0] >= 0:
        if 4 >= spot[1] >= 0:
            return True
    return False


def movable_pieces(inboard: Board, empty: list[list]):
    """ Return a mapping of movable pieces to its movable directions.

    """
    successor = {}
    empty_coord1_x, empty_coord1_y = empty[0][0], empty[0][1]
    empty_coord2_x, empty_coord2_y = empty[1][0], empty[1][1]

    spot1_0 = [empty_coord1_x, empty_coord1_y - 1]
    spot1_1 = [empty_coord1_x - 1, empty_coord1_y]
    spot1_2 = [empty_coord1_x + 1, empty_coord1_y]
    spot1_3 = [empty_coord1_x, empty_coord1_y + 1]

    spot2_0 = [empty_coord2_x, empty_coord2_y - 1]
    spot2_1 = [empty_coord2_x - 1, empty_coord2_y]
    spot2_2 = [empty_coord2_x + 1, empty_coord2_y]
    spot2_3 = [empty_coord2_x, empty_coord2_y + 1]

    if check_spot_valid(spot1_0):
        if inboard.grid[spot1_0[1]][spot1_0[0]] == char_goal:
            if inboard.grid[spot1_0[1]][spot1_0[0] + 1] == char_goal and empty_coord1_x + 1 == empty_coord2_x \
                    and empty_coord2_y == empty_coord1_y:
                return


def generate_successors(state: State):
    """ Return list of its possible successors of the given states.

    """


def get_solution():
    """

    """


def dfs_search(init_board):
    # init_state = State(init_board, f)
    # list of frontier states
    frontier = [board]
    # while(len(frontier) != 0):

    # with open('hrd5sol_dfs.txt', 'w') as f:


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "--inputfile",
    #     type=str,
    #     required=True,
    #     help="The input file that contains the puzzle."
    # )
    # parser.add_argument(
    #     "--outputfile",
    #     type=str,
    #     required=True,
    #     help="The output file that contains the solution."
    # )
    # parser.add_argument(
    #     "--algo",
    #     type=str,
    #     required=True,
    #     choices=['astar', 'dfs'],
    #     help="The searching algorithm."
    # )
    # args = parser.parse_args()

    # read the board from the file
    # board = read_from_file(args.inputfile)
    board1 = read_from_file('testhrd_easy1.txt')
    board1.display()
    pp = copy.deepcopy(board1.pieces)
    for p in pp:
        if p.is_goal:
            p.coord_x = p.coord_x + 1
    board2 = Board(pp)

    print(board1 == board2)
    pp2 = copy.deepcopy(board2.pieces)
    for p in pp2:
        if p.is_goal:
            p.coord_x = p.coord_x - 1
    board3 = Board(pp2)
    print(board1 == board3)