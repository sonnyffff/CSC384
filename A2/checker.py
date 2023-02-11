import copy
from heapq import heappush, heappop
import argparse
from typing import Optional

# ====================================================================================

char_red_king = 'R'
char_red_normal = 'r'
char_black_king = 'B'
char_black_normal = 'b'


class Piece:
    """
    This represents a piece on the checker.
    """

    def __init__(self, is_king, is_red, coord_x, coord_y):
        """
        :param is_king: True if the piece is the king piece and False otherwise.
        :type is_goal: bool
        :param is_red: True if this piece is a red piece and False if it is black.
        :type is_single: bool
        :param coord_x: The x coordinate of the top left corner of the piece.
        :type coord_x: int
        :param coord_y: The y coordinate of the top left corner of the piece.
        :type coord_y: int
        """

        self.is_king = is_king
        self.is_red = is_red
        self.coord_x = coord_x
        self.coord_y = coord_y

    def __repr__(self):
        return '{} {} {} {}'.format(self.is_king, self.is_red, self.coord_x, self.coord_y)

    def __hash__(self):
        return hash((self.is_king, self.is_red, self.coord_x, self.coord_y))


class Board:
    """
    Board class for setting up the playing board.
    """

    def __init__(self, pieces: list[Piece]):
        """
        :param pieces: The list of Pieces
        :type pieces: List[Piece]
        """

        self.width = 8
        self.height = 8

        self.pieces = pieces
        # self.grid is a 2-d (size * size) array automatically generated
        # using the information on the pieces when a board is being created.
        # A grid contains the symbol for representing the pieces on the board.
        self.grid = []
        self.__construct_grid()

    def __hash__(self):
        return hash(frozenset(self.pieces))

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
            if piece.is_king and piece.is_red:
                self.grid[piece.coord_y][piece.coord_x] = char_red_king
            elif piece.is_king and not piece.is_red:
                self.grid[piece.coord_y][piece.coord_x] = char_black_king
            elif not piece.is_king and piece.is_red:
                self.grid[piece.coord_y][piece.coord_x] = char_red_normal
            elif not piece.is_king and not piece.is_red:
                self.grid[piece.coord_y][piece.coord_x] = char_black_normal
            else:
                print("Can't reach here")

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

    def __init__(self, board, utility, depth, alpha, beta, turn, parent=None):
        """
        :param board: The board of the state.
        :type board: Board
        :param utility: The estimated utility value of current state or utility if the state is terminal.
        :type utility: int
        :param depth: The depth of current state in the search tree.
        :type depth: int
        :param alpha: The best of choice so far for red.
        :type alpha: int
        :param beta: The best of choice so far for black.
        :type beta: int
        :param turn: True if it's red turn
        :type turn: bool
        :param parent: The parent of current state.
        :type parent: Optional[State]
        """
        self.board = board
        self.utility = utility
        self.depth = depth
        self.parent = parent
        self.alpha = alpha
        self.beta = beta
        self.red_turn = turn
        self.id = hash(board)  # The id for breaking ties.
        assert(alpha <= beta)

    def __gt__(self, other):
        return self.utility > other.utility

    def __eq__(self, other):
        if self.id == other.id:
            return True
        return False


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

            if ch == char_red_normal:
                pieces.append(Piece(False, True, x, line_index))
            elif ch == char_red_king:
                pieces.append(Piece(True, True, x, line_index))
            elif ch == char_black_normal:
                pieces.append(Piece(False, False, x, line_index))
            elif ch == char_black_king:
                pieces.append(Piece(True, False, x, line_index))
        line_index += 1

    puzzle_file.close()

    board = Board(pieces)

    return board


def write_solution(goal_state: State, filename: str):
    """ Generate solution file base on the goal state.

    """
    f = open(filename, "w+")
    sol = get_solution(goal_state)
    for s in sol:
        for i, line in enumerate(s.board.grid):
            for ch in line:
                f.write(ch)
            f.write('\n')
        f.write("\n")


##########################################
# Helper Functions
##########################################

def terminal_test(curr_state: State):
    """ Test whether the given state is a terminal state.

    """
    if all(p.is_red for p in curr_state.board.pieces):
        return True
    return False


def find_empty_spot(curr_board: Board):
    """ Return the coordinates of the two empty spots on the board.

    """
    empty_spots = []
    for y in range(0, 8):
        for x in range(0, 8):
            if curr_board.grid[y][x] == '.':
                empty_spots.append([x, y])
    return empty_spots


def check_spot_valid(spot: list):
    """ Check if given coordinate a valid spot on the chess board.

    """
    if 8 >= spot[0] >= 0:
        if 8 >= spot[1] >= 0:
            return True
    return False


def add_to_successor(new_pieces: list[Piece], curr, successor: list, m_curr: int):
    """

    """
    new_board = Board(new_pieces)
    new_state = State(new_board, 0, curr.depth + 1, curr)
    new_f = 1 + curr.f - m_curr + manhattan_distance(new_state)
    new_state.f = new_f
    heappush(successor, new_state)


def check_upper(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y, curr_board, spot, curr_state, successor,
                is_2: bool, m_curr):
    if check_spot_valid(spot):
        # goal above empty
        if curr_board.grid[spot[1]][spot[0]] == char_goal and not is_2:
            if check_spot_valid([spot[0] + 1, spot[1]]):
                if curr_board.grid[spot[1]][spot[0] + 1] == char_goal and empty_coord1_x + 1 == empty_coord2_x \
                        and empty_coord2_y == empty_coord1_y:
                    new_pieces = copy.deepcopy(curr_board.pieces)
                    for p in new_pieces:
                        if p.is_goal:
                            p.coord_y = p.coord_y + 1
                    add_to_successor(new_pieces, curr_state, successor, m_curr)
        # horizontal above empty
        if curr_board.grid[spot[1]][spot[0]] == '<' and not is_2:
            if check_spot_valid([spot[0] + 1, spot[1]]):
                if curr_board.grid[spot[1]][spot[0] + 1] == '>' and empty_coord1_x + 1 == empty_coord2_x \
                        and empty_coord2_y == empty_coord1_y:
                    new_pieces = copy.deepcopy(curr_board.pieces)
                    for p in new_pieces:
                        if p.coord_x == spot[0] and p.coord_y == spot[1]:
                            p.coord_y = p.coord_y + 1
                    add_to_successor(new_pieces, curr_state, successor, m_curr)
        # vertical above empty
        if curr_board.grid[spot[1]][spot[0]] == 'v':
            new_pieces = copy.deepcopy(curr_board.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1] - 1:
                    p.coord_y = p.coord_y + 1
            add_to_successor(new_pieces, curr_state, successor, m_curr)
        # single above empty
        if curr_board.grid[spot[1]][spot[0]] == char_single:
            new_pieces = copy.deepcopy(curr_board.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_y = p.coord_y + 1
            add_to_successor(new_pieces, curr_state, successor, m_curr)

    return


def check_left(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y, curr_board, spot, curr_state, successor,
               is_2: bool, m_curr):
    if check_spot_valid(spot):
        # goal left empty
        if curr_board.grid[spot[1]][spot[0]] == char_goal and not is_2:
            if check_spot_valid([spot[0], spot[1] + 1]):
                if curr_board.grid[spot[1] + 1][spot[0]] == char_goal and empty_coord1_x == empty_coord2_x \
                        and empty_coord1_y + 1 == empty_coord2_y:
                    new_pieces = copy.deepcopy(curr_board.pieces)
                    for p in new_pieces:
                        if p.is_goal:
                            p.coord_x = p.coord_x + 1
                    add_to_successor(new_pieces, curr_state, successor, m_curr)
        # horizontal left empty
        if curr_board.grid[spot[1]][spot[0]] == '>':
            new_pieces = copy.deepcopy(curr_board.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] - 1 and p.coord_y == spot[1]:
                    p.coord_x = p.coord_x + 1
            add_to_successor(new_pieces, curr_state, successor, m_curr)
        # vertical left empty
        if curr_board.grid[spot[1]][spot[0]] == '^' and not is_2:
            if check_spot_valid([spot[0], spot[1] + 1]):
                if curr_board.grid[spot[1] + 1][spot[0]] == 'v' and empty_coord1_x == empty_coord2_x \
                        and empty_coord1_y + 1 == empty_coord2_y:
                    new_pieces = copy.deepcopy(curr_board.pieces)
                    for p in new_pieces:
                        if p.coord_x == spot[0] and p.coord_y == spot[1]:
                            p.coord_x = p.coord_x + 1
                    add_to_successor(new_pieces, curr_state, successor, m_curr)
        # single left empty
        if curr_board.grid[spot[1]][spot[0]] == char_single:
            new_pieces = copy.deepcopy(curr_board.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_x = p.coord_x + 1
            add_to_successor(new_pieces, curr_state, successor, m_curr)
    return


def check_right(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y, curr_board, spot, curr_state, successor,
                is_2: bool, m_curr):
    if check_spot_valid(spot):
        # goal right empty
        if curr_board.grid[spot[1]][spot[0]] == char_goal and not is_2:
            if check_spot_valid([spot[0], spot[1] + 1]):
                if curr_board.grid[spot[1] + 1][spot[0]] == char_goal and empty_coord1_x == empty_coord2_x \
                        and empty_coord1_y + 1 == empty_coord2_y:
                    new_pieces = copy.deepcopy(curr_board.pieces)
                    for p in new_pieces:
                        if p.is_goal:
                            p.coord_x = p.coord_x - 1
                    add_to_successor(new_pieces, curr_state, successor, m_curr)
        # horizontal right empty
        if curr_board.grid[spot[1]][spot[0]] == '<':
            new_pieces = copy.deepcopy(curr_board.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_x = p.coord_x - 1
            add_to_successor(new_pieces, curr_state, successor, m_curr)
        # vertical right empty
        if curr_board.grid[spot[1]][spot[0]] == '^' and not is_2:
            if check_spot_valid([spot[0], spot[1] + 1]):
                if curr_board.grid[spot[1] + 1][spot[0]] == 'v' and empty_coord1_x == empty_coord2_x \
                        and empty_coord1_y + 1 == empty_coord2_y:
                    new_pieces = copy.deepcopy(curr_board.pieces)
                    for p in new_pieces:
                        if p.coord_x == spot[0] and p.coord_y == spot[1]:
                            p.coord_x = p.coord_x - 1
                    add_to_successor(new_pieces, curr_state, successor, m_curr)
        # single right empty
        if curr_board.grid[spot[1]][spot[0]] == char_single:
            new_pieces = copy.deepcopy(curr_board.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_x = p.coord_x - 1
            add_to_successor(new_pieces, curr_state, successor, m_curr)
    return


def check_bottom(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y, curr_board, spot, curr_state,
                 successor, is_2: bool, m_curr):
    if check_spot_valid(spot):
        # goal under empty
        if curr_board.grid[spot[1]][spot[0]] == char_goal and not is_2:
            if check_spot_valid([spot[0] + 1, spot[1]]):
                if curr_board.grid[spot[1]][spot[0] + 1] == char_goal and empty_coord1_x + 1 == empty_coord2_x \
                        and empty_coord2_y == empty_coord1_y:
                    new_pieces = copy.deepcopy(curr_board.pieces)
                    for p in new_pieces:
                        if p.is_goal:
                            p.coord_y = p.coord_y - 1
                    add_to_successor(new_pieces, curr_state, successor, m_curr)
        # horizontal under empty
        if curr_board.grid[spot[1]][spot[0]] == '<' and not is_2:
            if check_spot_valid([spot[0] + 1, spot[1]]):
                if curr_board.grid[spot[1]][spot[0] + 1] == '>' and empty_coord1_x + 1 == empty_coord2_x \
                        and empty_coord2_y == empty_coord1_y:
                    new_pieces = copy.deepcopy(curr_board.pieces)
                    for p in new_pieces:
                        if p.coord_x == spot[0] and p.coord_y == spot[1]:
                            p.coord_y = p.coord_y - 1
                    add_to_successor(new_pieces, curr_state, successor, m_curr)
        # vertical under empty
        if curr_board.grid[spot[1]][spot[0]] == '^':
            new_pieces = copy.deepcopy(curr_board.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_y = p.coord_y - 1
            add_to_successor(new_pieces, curr_state, successor, m_curr)
        # single under empty
        if curr_board.grid[spot[1]][spot[0]] == char_single:
            new_pieces = copy.deepcopy(curr_board.pieces)
            for p in new_pieces:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    p.coord_y = p.coord_y - 1
            add_to_successor(new_pieces, curr_state, successor, m_curr)

    return


def generate_successors(curr: State, empty: list[list], successor: list):
    """ Generate successors of the given state and put into successor list

    with given list of empty spots
    """
    curr_board = curr.board

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

    m_curr = manhattan_distance(curr)
    check_upper(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                curr_board, spot1_0, curr, successor, False, m_curr)
    check_upper(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                curr_board, spot2_0, curr, successor, True, m_curr)
    check_left(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
               curr_board, spot1_1, curr, successor, False, m_curr)
    check_left(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
               curr_board, spot2_1, curr, successor, True, m_curr)
    check_right(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                curr_board, spot1_2, curr, successor, False, m_curr)
    check_right(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                curr_board, spot2_2, curr, successor, True, m_curr)
    check_bottom(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                 curr_board, spot1_3, curr, successor, False, m_curr)
    check_bottom(empty_coord1_x, empty_coord1_y, empty_coord2_x, empty_coord2_y,
                 curr_board, spot2_3, curr, successor, True, m_curr)

    return


def get_solution(goal_state: State) -> list[State]:
    """ Given the goal state and back track to solution

    """
    sol = [goal_state]
    while goal_state.parent is not None:
        sol.append(goal_state.parent)
        goal_state = goal_state.parent
    sol.reverse()
    return sol


def dfs_search(init_state: State) -> Optional[State]:
    """ Dfs search to find the goal state

    """
    frontier = [init_state]
    explored = set()
    while len(frontier) != 0:
        curr = frontier.pop()
        if curr.id not in explored:
            explored.add(curr.id)
            if goal_test(curr):
                return curr
            empty_spots = find_empty_spot(curr.board)
            generate_successors(curr, empty_spots, frontier)
    print("Should not reach here")
    return None


def manhattan_distance(curr_state: State) -> int:
    """ Calculate Manhattan distance for the given state

    """
    goal_x = 1
    goal_y = 3
    if goal_test(curr_state):
        return 0
    for p in curr_state.board.pieces:
        if p.is_goal:
            return abs(p.coord_x - goal_x) + abs(p.coord_y - goal_y)


def a_star_search(init_state: State) -> Optional[State]:
    """ A* search to find the goal state

    """
    frontier = []
    init_state.f = manhattan_distance(init_state)
    heappush(frontier, init_state)
    explored = set()
    while len(frontier) != 0:
        curr = heappop(frontier)
        if curr.id not in explored:
            explored.add(curr.id)
            if goal_test(curr):
                return curr
            empty_spots = find_empty_spot(curr.board)
            generate_successors(curr, empty_spots, frontier)
    print("Should not reach here")
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzle."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    parser.add_argument(
        "--algo",
        type=str,
        required=True,
        choices=['astar', 'dfs'],
        help="The searching algorithm."
    )
    args = parser.parse_args()

    # read the board from the file
    inboard = read_from_file(args.inputfile)
    # generate state base on the board
    state = State(inboard, 0, 0)
    # write solution base on algo choice
    if args.algo == 'dfs':
        goal = dfs_search(state)
        write_solution(goal, args.outputfile)
    elif args.algo == 'astar':
        goal = a_star_search(state)
        write_solution(goal, args.outputfile)
