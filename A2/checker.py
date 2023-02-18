import copy
import math
from heapq import heappush, heappop
import argparse

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
        :param is_red: True if this piece is a red piece and False if it is black.
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

    def __eq__(self, other):
        return hash(self) == hash(other)


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

    def __init__(self, board, utility, depth, alpha, beta, is_red_turn, parent=None):
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
        :param is_red_turn: True if it's red turn
        :type is_red_turn: bool
        :param parent: The parent of current state.
        :type parent: State
        """
        self.board = board
        self.utility = utility
        self.depth = depth
        self.parent = parent
        self.alpha = alpha
        self.beta = beta
        self.red_turn = is_red_turn
        self.id = hash(board)  # The id for breaking ties.
        assert (alpha <= beta)

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
    TODO
    """
    if all(p.is_red for p in curr_state.board.pieces):
        return ['T', 'r']
    elif all(not p.is_red for p in curr_state.board.pieces):
        return ['T', 'b']
    return ['F']


def utility_function(curr_state: State):
    flag = terminal_test(curr_state)
    if flag[0] == 'T':
        if flag[1] == 'r':
            curr_state.utility = math.inf
        elif flag[1] == 'b':
            curr_state.utility = -math.inf
    elif curr_state.depth == 10:
        # estimate utility if not terminal TODO
        curr_state.utility = calculate_estimate_utility(curr_state)
    else:
        curr_state.utility = None


def calculate_estimate_utility(curr_state: State) -> int:
    red_point = 0
    black_point = 0
    for p in curr_state.board.pieces:
        if p.is_red and p.is_king:
            red_point += 2
        elif p.is_red and not p.is_king:
            red_point += 1
        elif not p.is_red and p.is_king:
            black_point += 2
        elif not p.is_red and not p.is_king:
            black_point += 1
    return red_point - black_point


def find_empty_spot(curr_board: Board):
    """ Return the coordinates of the two empty spots on the board.
    TODO
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
    if 7 >= spot[0] >= 0:
        if 7 >= spot[1] >= 0:
            return True
    return False


def check_neighbor_color(curr: State, is_red: bool, spot: list) -> list:
    if is_red:
        for p in curr.board.pieces:
            if not p.is_red:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    return [True, p]
        return [False]
    else:
        for p in curr.board.pieces:
            if p.is_red:
                if p.coord_x == spot[0] and p.coord_y == spot[1]:
                    return [True, p]
        return [False]


def generate_possible_spots(p: Piece) -> list[list]:
    spot_1 = [p.coord_x - 1, p.coord_y - 1]
    spot_2 = [p.coord_x + 1, p.coord_y - 1]
    spot_3 = [p.coord_x - 1, p.coord_y + 1]
    spot_4 = [p.coord_x + 1, p.coord_y + 1]
    spots = [spot_1, spot_2, spot_3, spot_4]
    return spots


def check_jump(curr: State, prev_jump=None) -> dict[Piece: list[list]]:
    """

    :param curr: current state
    :param prev_jump: a piece that previously jumps
    :return: a dictionary maps to piece and its jump locations (as a list).
    """
    jump_map = dict()
    empty_spots = find_empty_spot(curr.board)
    # there is a previous jump (multi jumps)
    if prev_jump is not None:
        p = prev_jump
        if p.is_red:
            spots = generate_possible_spots(p)
            for s in spots:
                if check_spot_valid(s):
                    # black neighbor
                    n_list = check_neighbor_color(curr, True, s)
                    if n_list[0]:
                        if p.is_king:
                            # top left
                            if [2 * s[0] - p.coord_x, 2 * s[1] - p.coord_y] in empty_spots:
                                if jump_map.setdefault(p) is None:
                                    jump_map[p] = []
                                jump_map[p].append(n_list[1])
                        else:
                            # top left
                            if 2 * s[1] - p.coord_y < p.coord_y:
                                if [2 * s[0] - p.coord_x, 2 * s[1] - p.coord_y] in empty_spots:
                                    if jump_map.setdefault(p) is None:
                                        jump_map[p] = []
                                    jump_map[p].append(n_list[1])
        else:
            spots = generate_possible_spots(p)
            for s in spots:
                if check_spot_valid(s):
                    # red neighbor
                    n_list = check_neighbor_color(curr, False, s)
                    if n_list[0]:
                        if p.is_king:
                            # top left
                            if [2 * s[0] - p.coord_x, 2 * s[1] - p.coord_y] in empty_spots:
                                if jump_map.setdefault(p) is None:
                                    jump_map[p] = []
                                jump_map[p].append(n_list[1])
                        else:
                            # top left
                            if 2 * s[1] - p.coord_y > p.coord_y:
                                if [2 * s[0] - p.coord_x, 2 * s[1] - p.coord_y] in empty_spots:
                                    if jump_map.setdefault(p) is None:
                                        jump_map[p] = []
                                    jump_map[p].append(n_list[1])
        return jump_map
    if curr.red_turn:
        for p in curr.board.pieces:
            # red pieces
            if p.is_red:
                spots = generate_possible_spots(p)
                for s in spots:
                    if check_spot_valid(s):
                        # black neighbor
                        n_list = check_neighbor_color(curr, True, s)
                        if n_list[0]:
                            if p.is_king:
                                # top left
                                if [2 * s[0] - p.coord_x, 2 * s[1] - p.coord_y] in empty_spots:
                                    if jump_map.setdefault(p) is None:
                                        jump_map[p] = []
                                    jump_map[p].append(n_list[1])
                            else:
                                # top left
                                if 2 * s[1] - p.coord_y < p.coord_y:
                                    if [2 * s[0] - p.coord_x, 2 * s[1] - p.coord_y] in empty_spots:
                                        if jump_map.setdefault(p) is None:
                                            jump_map[p] = []
                                        jump_map[p].append(n_list[1])
    else:
        for p in curr.board.pieces:
            # black pieces
            if not p.is_red:
                spots = generate_possible_spots(p)
                for s in spots:
                    if check_spot_valid(s):
                        # red neighbor
                        n_list = check_neighbor_color(curr, False, s)
                        if n_list[0]:
                            if p.is_king:
                                # top left
                                if [2 * s[0] - p.coord_x, 2 * s[1] - p.coord_y] in empty_spots:
                                    if jump_map.setdefault(p) is None:
                                        jump_map[p] = []
                                    jump_map[p].append(n_list[1])
                            else:
                                # top left
                                if 2 * s[1] - p.coord_y > p.coord_y:
                                    if [2 * s[0] - p.coord_x, 2 * s[1] - p.coord_y] in empty_spots:
                                        if jump_map.setdefault(p) is None:
                                            jump_map[p] = []
                                        jump_map[p].append(n_list[1])
    return jump_map


def jump(curr, piece: Piece) -> list[State]:
    """
    Perform jump

    :param piece:
    :param curr:
    :return:
    """
    flag_state = curr
    jump_map = check_jump(flag_state, piece)
    if len(jump_map) == 0:
        return [flag_state]
    else:
        ret = []
        for capture in jump_map[piece]:
            new_pieces = copy.deepcopy(flag_state.board.pieces)
            for p in new_pieces:
                if p == piece:
                    # update new position
                    p.coord_x = 2 * capture.coord_x - p.coord_x
                    p.coord_y = 2 * capture.coord_y - p.coord_y
                    # remove captured piece
                    new_pieces.remove(capture)
                    new_state = State(Board(new_pieces), 0, 0, 0, 0, curr.red_turn, flag_state)
                    # update flag, for recursion
                    flag_state = new_state
                    j_states = jump(flag_state, p)
                    for js in j_states:
                        ret.append(js)
                    # set back flag for next iteration
                    flag_state = curr
                    break
        for s in ret:
            s.depth = curr.depth + 1
            utility_function(s)
        return ret


def move(curr: State) -> list[State]:
    ret = []
    new_piece = copy.deepcopy(curr.board.pieces)
    if curr.red_turn:
        for p in new_piece:
            if p.is_red:
                spots = generate_possible_spots(p)
                count = 1
                for s in spots:
                    if check_spot_valid(s):
                        if p.is_king:
                            p.coord_x = s[0]
                            p.coord_y = s[1]
                            temp = State(Board(new_piece), 0, curr.depth + 1, 0, 0, True, curr)
                            utility_function(temp)
                            ret.append(temp)

                        else:
                            # top left
                            if count == 1 or count == 2:
                                p.coord_x = s[0]
                                p.coord_y = s[1]
                                temp = State(Board(new_piece), 0, curr.depth + 1, 0, 0, True, curr)
                                utility_function(temp)
                                ret.append(temp)
                    count += 1
    else:
        for p in new_piece:
            if not p.is_red:
                spots = generate_possible_spots(p)
                count = 1
                for s in spots:
                    if check_spot_valid(s):
                        if p.is_king:
                            p.coord_x = s[0]
                            p.coord_y = s[1]
                            temp = State(Board(new_piece), 0, curr.depth + 1, 0, 0, True, curr)
                            utility_function(temp)
                            ret.append(temp)
                        else:
                            # top left
                            if count == 3 or count == 4:
                                p.coord_x = s[0]
                                p.coord_y = s[1]
                                temp = State(Board(new_piece), 0, curr.depth + 1, 0, 0, True, curr)
                                utility_function(temp)
                                ret.append(temp)
                    count += 1
    return ret


def generate_successors(curr: State, successor: list):
    """ Generate successors of the given state and put into successor list

    with given list of empty spots
    """
    jump_map = check_jump(curr)
    if len(jump_map) != 0:
        # must jump
        for piece in jump_map:
            jumps = jump(curr, piece)
            for j in jumps:
                successor.append(j)
    else:
        moves = move(curr)
        for m in moves:
            successor.append(m)


def get_solution(goal_state: State) -> list[State]:
    """ Given the goal state and back track to solution

    """
    sol = [goal_state]
    while goal_state.parent is not None:
        sol.append(goal_state.parent)
        goal_state = goal_state.parent
    sol.reverse()
    return sol


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
    inboard = read_from_file("test_successor_red.txt")
    # generate state base on the board
    state = State(inboard, 0, 0, 0, 0, False)
    sucessor = []
    generate_successors(state, sucessor)
    for s in sucessor:
        s.board.display()
        print(s.utility)
        print('\n')
    # for p in state.board.pieces:
    #     if p.coord_x == 2 and p.coord_y == 1:
    #         dict = check_jump(state, p)
    #         for k in dict:
    #             print(k)

    # write solution base on algo choice
    # if args.algo == 'dfs':
    #     goal = dfs_search(state)
    #     write_solution(goal, args.outputfile)
    # elif args.algo == 'astar':
    #     goal = a_star_search(state)
    #     write_solution(goal, args.outputfile)
