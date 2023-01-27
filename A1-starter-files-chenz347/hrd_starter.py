import copy
from heapq import heappush, heappop
import time
import argparse
import sys
from typing import Optional
import math

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
        # self.id = hash(board)  # The id for breaking ties.

    def __lt__(self, other):
        return self.f < other.f


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


def write_solution(goal: State, filename: str):
    f = open(filename, "w")
    sol = get_solution(goal)
    for s in sol:
        for i, line in enumerate(s.board.grid):
            for ch in line:
                f.write(ch)
            f.write('\n')
        f.write("\n")


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
    for y in range(0, 5):
        for x in range(0, 4):
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


def add_to_successor(new_pieces, state, successor):
    new_board = Board(new_pieces)
    if all(s.board != new_board for s in successor):
        new_state = State(new_board, state.f, state.depth + 1, state)
        successor.append(new_state)



def check_upper(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y, inboard, spot, state, successor,
                is_2: bool):
    if check_spot_valid(spot):
        # goal above empty
        if inboard.grid[spot[1]][spot[0]] == char_goal and not is_2:
            # not on right edge
            if check_spot_valid([spot[0] + 1, spot[1]]):
                if inboard.grid[spot[1]][spot[0] + 1] == char_goal and empty_coord1_x + 1 == empty_coord2_x \
                        and empty_coord2_y == empty_coord1_y:
                    new_pieces = copy.deepcopy(inboard.pieces)
                    for p in new_pieces:
                        if p.is_goal:
                            p.coord_y = p.coord_y + 1
                    add_to_successor(new_pieces, state, successor)
        # horizontal above empty
        if inboard.grid[spot[1]][spot[0]] == '<' and not is_2:
            # not on right edge
            if check_spot_valid([spot[0] + 1, spot[1]]):
                if inboard.grid[spot[1]][spot[0] + 1] == '>' and empty_coord1_x + 1 == empty_coord2_x \
                        and empty_coord2_y == empty_coord1_y:
                    new_pieces = copy.deepcopy(inboard.pieces)
                    for p in new_pieces:
                        if p.coord_x == spot[0] and p.coord_y == spot[1]:
                            p.coord_y = p.coord_y + 1
                    add_to_successor(new_pieces, state, successor)
        # vertical above empty
        if inboard.grid[spot[1]][spot[0]] == 'v':
            new_pieces = copy.deepcopy(inboard.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1] - 1:
                    p.coord_y = p.coord_y + 1
            add_to_successor(new_pieces, state, successor)
        # single above empty
        if inboard.grid[spot[1]][spot[0]] == char_single:
            new_pieces = copy.deepcopy(inboard.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_y = p.coord_y + 1
            add_to_successor(new_pieces, state, successor)

    return


def check_left(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y, inboard, spot, state, successor,
               is_2: bool):
    if check_spot_valid(spot):
        # goal left empty
        if inboard.grid[spot[1]][spot[0]] == char_goal:
            if check_spot_valid([spot[0], spot[1] + 1]):
                if inboard.grid[spot[1] + 1][spot[0]] == char_goal and empty_coord1_x == empty_coord2_x \
                        and empty_coord1_y + 1 == empty_coord2_y:
                    new_pieces = copy.deepcopy(inboard.pieces)
                    for p in new_pieces:
                        if p.is_goal:
                            p.coord_x = p.coord_x + 1
                    add_to_successor(new_pieces, state, successor)
        # horizontal left empty
        if inboard.grid[spot[1]][spot[0]] == '>':
            new_pieces = copy.deepcopy(inboard.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] - 1 and p.coord_y == spot[1]:
                    p.coord_x = p.coord_x + 1
            add_to_successor(new_pieces, state, successor)
        # vertical left empty
        if inboard.grid[spot[1]][spot[0]] == '^' and not is_2:
            if check_spot_valid([spot[0], spot[1] + 1]):
                if inboard.grid[spot[1] + 1][spot[0]] == 'v' and empty_coord1_x == empty_coord2_x \
                        and empty_coord1_y + 1 == empty_coord2_y:
                    new_pieces = copy.deepcopy(inboard.pieces)
                    for p in new_pieces:
                        if p.coord_x == spot[0] and p.coord_y == spot[1]:
                            p.coord_x = p.coord_x + 1
                    add_to_successor(new_pieces, state, successor)
        # single left empty
        if inboard.grid[spot[1]][spot[0]] == char_single:
            new_pieces = copy.deepcopy(inboard.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_x = p.coord_x + 1
            add_to_successor(new_pieces, state, successor)
    return


def check_right(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y, inboard, spot, state, successor,
                is_2: bool):
    if check_spot_valid(spot):
        # goal right empty
        if inboard.grid[spot[1]][spot[0]] == char_goal:
            if check_spot_valid([spot[0], spot[1] + 1]):
                if inboard.grid[spot[1] + 1][spot[0]] == char_goal and empty_coord1_x == empty_coord2_x \
                        and empty_coord1_y + 1 == empty_coord2_y:
                    new_pieces = copy.deepcopy(inboard.pieces)
                    for p in new_pieces:
                        if p.is_goal:
                            p.coord_x = p.coord_x - 1
                    add_to_successor(new_pieces, state, successor)
        # horizontal right empty
        if inboard.grid[spot[1]][spot[0]] == '<':
            new_pieces = copy.deepcopy(inboard.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_x = p.coord_x - 1
            add_to_successor(new_pieces, state, successor)
        # vertical right empty
        if inboard.grid[spot[1]][spot[0]] == '^' and not is_2:
            if check_spot_valid([spot[0], spot[1] + 1]):
                if inboard.grid[spot[1] + 1][spot[0]] == 'v' and empty_coord1_x == empty_coord2_x \
                        and empty_coord1_y + 1 == empty_coord2_y:
                    new_pieces = copy.deepcopy(inboard.pieces)
                    for p in new_pieces:
                        if p.coord_x == spot[0] and p.coord_y == spot[1]:
                            p.coord_x = p.coord_x - 1
                    add_to_successor(new_pieces, state, successor)
        # single right empty
        if inboard.grid[spot[1]][spot[0]] == char_single:
            new_pieces = copy.deepcopy(inboard.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_x = p.coord_x - 1
            add_to_successor(new_pieces, state, successor)
    return


def check_bottom(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y, inboard, spot, state, successor,
                 is_2: bool):
    if check_spot_valid(spot):
        # goal above empty
        if inboard.grid[spot[1]][spot[0]] == char_goal and not is_2:
            # not on right edge
            if check_spot_valid([spot[0] + 1, spot[1]]):
                if inboard.grid[spot[1]][spot[0] + 1] == char_goal and empty_coord1_x + 1 == empty_coord2_x \
                        and empty_coord2_y == empty_coord1_y:
                    new_pieces = copy.deepcopy(inboard.pieces)
                    for p in new_pieces:
                        if p.is_goal:
                            p.coord_y = p.coord_y - 1
                    add_to_successor(new_pieces, state, successor)
        # horizontal above empty
        if inboard.grid[spot[1]][spot[0]] == '<' and not is_2:
            # not on right edge
            if check_spot_valid([spot[0] + 1, spot[1]]):
                if inboard.grid[spot[1]][spot[0] + 1] == '>' and empty_coord1_x + 1 == empty_coord2_x \
                        and empty_coord2_y == empty_coord1_y:
                    new_pieces = copy.deepcopy(inboard.pieces)
                    for p in new_pieces:
                        if p.coord_x == spot[0] and p.coord_y == spot[1]:
                            p.coord_y = p.coord_y - 1
                    add_to_successor(new_pieces, state, successor)
        # vertical under empty
        if inboard.grid[spot[1]][spot[0]] == '^':
            new_pieces = copy.deepcopy(inboard.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_y = p.coord_y - 1
            add_to_successor(new_pieces, state, successor)
        # single under empty
        if inboard.grid[spot[1]][spot[0]] == char_single:
            new_pieces = copy.deepcopy(inboard.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_y = p.coord_y - 1
            add_to_successor(new_pieces, state, successor)

    return


def generate_successors(state: State, empty: list[list]) -> list[State]:
    """ Return a mapping of movable pieces to its movable directions.

    """
    inboard = state.board
    successor = []
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

    check_upper(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                inboard, spot1_0, state, successor, False)
    check_upper(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                inboard, spot2_0, state, successor, True)
    check_left(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
               inboard, spot1_1, state, successor, False)
    check_left(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
               inboard, spot2_1, state, successor, True)
    check_right(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                inboard, spot1_2, state, successor, False)
    check_right(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                inboard, spot2_2, state, successor, True)
    check_bottom(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                 inboard, spot1_3, state, successor, False)
    check_bottom(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                 inboard, spot2_3, state, successor, True)

    return successor


def get_solution(goal: State) -> list[State]:
    """ Given the goal state and back track to solution

    """
    sol = [goal]
    while goal.parent is not None:
        sol.append(goal.parent)
        goal = goal.parent
    sol.reverse()
    return sol


def dfs_search(init_state: State) -> Optional[State]:
    """ Dfs search to find the goal state

    """
    frontier = [init_state]
    explored = []
    while len(frontier) != 0:
        curr = frontier.pop()
        if all(curr.board != e.board for e in explored):
            explored.append(curr)
            if goal_test(curr):
                return curr
            empty_spots = find_empty_spot(curr.board)
            successors = generate_successors(curr, empty_spots)
            for s in successors:
                frontier.append(s)
    print("Should not reach here")
    return None


def manhattan_distance(curr_state: State) -> int:
    goal_x = 1
    goal_y = 3
    if goal_test(curr_state):
        return 0
    for p in curr_state.board.pieces:
        if p.is_goal:
            return abs(p.coord_x - goal_x) + abs(p.coord_y - goal_y)


def euclidean_distance(curr_state: State) -> float:
    goal_x = 1
    goal_y = 3
    if goal_test(curr_state):
        return 0
    for p in curr_state.board.pieces:
        if p.is_goal:
            return math.sqrt(abs(p.coord_x - goal_x)**2 + abs(p.coord_y - goal_y)**2)


def a_star_search(init_state: State) -> Optional[State]:
    """ A* search to find the goal state

    """
    frontier = []
    init_state.f = manhattan_distance(init_state)
    heappush(frontier, init_state)
    explored = []
    while len(frontier) != 0:
        curr = heappop(frontier)
        if all(curr.board != e.board for e in explored):
            explored.append(curr)
            if goal_test(curr):
                return curr
            empty_spots = find_empty_spot(curr.board)
            successors = generate_successors(curr, empty_spots)
            m_curr = manhattan_distance(curr)
            print(curr.f)
            for s in successors:
                s.f = 1 + curr.f - m_curr + manhattan_distance(s)
                heappush(frontier, s)
    print("Should not reach here")
    return None

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
    # board1 = read_from_file('testhrd_easy1.txt')
    board1 = read_from_file('testhrd_hard4.txt')
    # board1.display()
    # pp = copy.deepcopy(board1.pieces)
    # for p in pp:
    #     if p.is_goal:
    #         p.coord_x = p.coord_x + 1
    # board2 = Board(pp)
    #
    # print(board1 == board2)
    # pp2 = copy.deepcopy(board2.pieces)
    # for p in pp2:
    #     if p.is_goal:
    #         p.coord_x = p.coord_x - 1
    # board3 = Board(pp2)
    # print(board1 == board3)

    state = State(board1, 0, 0)
    # successor = []
    # empty = find_empty_spot(state.board)
    # successor = generate_successors(state, empty)
    # print(len(successor))
    # for s in successor:
    #     s.board.display()

    #goal = dfs_search(state)
    goal = a_star_search(state)
    goal.board.display()
    write_solution(goal, 'hrd5sol_dfs.txt')
