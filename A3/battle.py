import sys
import copy
import math
from heapq import heappush, heappop
import argparse
import time

char_submarine = 'S'
char_water = '.'
char_left = '<'
char_right = '>'
char_top = '^'
char_bottom = 'v'
char_middle = 'M'


class Variable:
    '''Class for defining CSP variables.

      On initialization the variable object can be given a name and a
      list containing variable's domain of values. You can reset the
      variable's domain if you want to solve a similar problem where
      the domains have changed.

      To support CSP propagation, the class also maintains a current
      domain for the variable. Values pruned from the variable domain
      are removed from the current domain but not from the original
      domain. Values can be also restored.
    '''

    undoDict = dict()  # stores pruned values indexed by a

    # (variable,value) reason pair
    def __init__(self, name, domain):
        '''Create a variable object, specifying its name (a
        string) and domain of values.
        '''
        self._name = name  # text name for variable
        self._dom = list(domain)  # Make a copy of passed domain
        self._curdom = list(domain)  # using list
        self._value = None

    def __str__(self):
        return "Variable {}".format(self._name)

    def domain(self):
        '''return copy of variable domain'''
        return (list(self._dom))

    def domainSize(self):
        '''Return the size of the domain'''
        return (len(self.domain()))

    def resetDomain(self, newdomain):
        '''reset the domain of this variable'''
        self._dom = newdomain

    def getValue(self):
        return self._value

    def setValue(self, value):
        if value != None and not value in self._dom:
            print("Error: tried to assign value {} to variable {} that is not in {}'s domain".format(value, self._name,
                                                                                                     self._name))
        else:
            self._value = value

    def unAssign(self):
        self.setValue(None)

    def isAssigned(self):
        return self.getValue() != None

    def name(self):
        return self._name

    def curDomain(self):
        '''return copy of variable current domain. But if variable is assigned
           return just its assigned value (this makes implementing hasSupport easier'''
        if self.isAssigned():
            return ([self.getValue()])
        return (list(self._curdom))

    def curDomainSize(self):
        '''Return the size of the current domain'''
        if self.isAssigned():
            return (1)
        return (len(self._curdom))

    def inCurDomain(self, value):
        '''check if value is in current domain'''
        if self.isAssigned():
            return (value == self.getValue())
        return (value in self._curdom)

    def pruneValue(self, value, reasonVar, reasonVal):
        '''Remove value from current domain'''
        try:
            self._curdom.remove(value)
        except:
            print("Error: tried to prune value {} from variable {}'s domain, but value not present!".format(value,
                                                                                                            self._name))
        dkey = (reasonVar, reasonVal)
        if not dkey in Variable.undoDict:
            Variable.undoDict[dkey] = []
        Variable.undoDict[dkey].append((self, value))

    def restoreVal(self, value):
        self._curdom.append(value)

    def restoreCurDomain(self):
        self._curdom = self.domain()

    def reset(self):
        self.restoreCurDomain()
        self.unAssign()

    def dumpVar(self):
        print("Variable\"{}={}\": Dom = {}, CurDom = {}".format(self._name, self._value, self._dom, self._curdom))

    @staticmethod
    def clearUndoDict():
        undoDict = dict()

    @staticmethod
    def restoreValues(reasonVar, reasonVal):
        dkey = (reasonVar, reasonVal)
        if dkey in Variable.undoDict:
            for (var, val) in Variable.undoDict[dkey]:
                var.restoreVal(val)
            del Variable.undoDict[dkey]


class Cell(Variable):
    def __init__(self, name, domain, is_ship, x_coord, y_coord):
        Variable.__init__(self, name, domain)
        self.is_ship = is_ship
        self.x_coord = x_coord
        self.y_coord = y_coord

    def __hash__(self):
        return hash((self.name, self.domain, self.x_coord, self.y_coord))


# implement various types of constraints
class Constraint:
    '''Base class for defining constraints. Each constraint can check if
       it has been satisfied, so each type of constraint must be a
       different class. For example a constraint of notEquals(V1,V2)
       must be a different class from a constraint of
       greaterThan(V1,V2), as they must implement different checks of
       satisfaction.

       However one can define a class of general table constraints, as
       below, that can capture many different constraints.

       On initialization the constraint's name can be given as well as
       the constraint's scope. IMPORTANT, the scope is ordered! E.g.,
       the constraint greaterThan(V1,V2) is not the same as the
       contraint greaterThan(V2,V1).
    '''

    def __init__(self, name, scope):
        '''create a constraint object, specify the constraint name (a
        string) and its scope (an ORDERED list of variable
        objects).'''
        self._scope = list(scope)
        self._name = "baseClass_" + name  # override in subconstraint types!

    def scope(self):
        return list(self._scope)

    def arity(self):
        return len(self._scope)

    def numUnassigned(self):
        i = 0
        for var in self._scope:
            if not var.isAssigned():
                i += 1
        return i

    def unAssignedVars(self):
        return [var for var in self.scope() if not var.isAssigned()]

    # def check(self):
    #     util.raiseNotDefined()

    def name(self):
        return self._name

    def __str__(self):
        return "Cnstr_{}({})".format(self.name(), map(lambda var: var.name(), self.scope()))

    def printConstraint(self):
        print("Cons: {} Vars = {}".format(
            self.name(), [v.name() for v in self.scope()]))


class RowConstraint(Constraint):
    def __init__(self, name, scope, limit):
        Constraint.__init__(self, name, scope)
        self.limit = limit

    def check(self):
        count = 0
        for cell in self._scope:
            if cell.is_ship:
                count += 1
        if count == self.limit:
            return 0
        elif count < self.limit:
            return 1
        else:
            # oversize
            return 2


class ColConstraint(Constraint):
    def __init__(self, name, scope, limit):
        Constraint.__init__(self, name, scope)
        self.limit = limit

    def check(self):
        count = 0
        for cell in self._scope:
            if cell.is_ship:
                count += 1
        if count == self.limit:
            return 0
        elif count < self.limit:
            return 1
        else:
            # oversize
            return 2


class ShipConstraint(Constraint):
    def __init__(self, name, scope, state, submarine, destroyers, cruisers, battleships):
        Constraint.__init__(self, name, scope)
        self.state = state
        self.submarine = submarine
        self.destroyers = destroyers
        self.cruisers = cruisers
        self.battleships = battleships

    def check(self):
        submarine = 0
        destroyers = 0
        scruisers = 0
        battleships = 0
        for cell in self._scope:
            if cell.getValue() == char_submarine:
                submarine += 1
            elif cell.getValue() == char_top:
                return
    # TODO


class WaterConstraint(Constraint):
    def __init__(self, name, scope, limit):
        Constraint.__init__(self, name, scope)
        self.limit = limit

    def check(self):
        count = 0
        for cell in self._scope:
            if cell.is_ship:
                count += 1
        if count == self.limit:
            return 0
        elif count < self.limit:
            return 1
        else:
            # oversize
            return 2


# object for holding a constraint problem
class CSP:
    '''CSP class groups together a set of variables and a set of
       constraints to form a CSP problem. Provides a usesful place
       to put some other functions that depend on which variables
       and constraints are active'''

    def __init__(self, name, variables, constraints):
        '''create a CSP problem object passing it a name, a list of
           variable objects, and a list of constraint objects'''
        self._name = name
        self._variables = variables
        self._constraints = constraints

        # some sanity checks
        varsInCnst = set()
        for c in constraints:
            varsInCnst = varsInCnst.union(c.scope())
        for v in variables:
            if v not in varsInCnst:
                print("Warning: variable {} is not in any constraint of the CSP {}".format(v.name(), self.name()))
        for v in varsInCnst:
            if v not in variables:
                print(
                    "Error: variable {} appears in constraint but specified as one of the variables of the CSP {}".format(
                        v.name(), self.name()))

        self.constraints_of = [[] for i in range(len(variables))]
        for c in constraints:
            for v in c.scope():
                i = variables.index(v)
                self.constraints_of[i].append(c)

    def name(self):
        return self._name

    def variables(self):
        return list(self._variables)

    def constraints(self):
        return list(self._constraints)

    def constraintsOf(self, var):
        '''return constraints with var in their scope'''
        try:
            i = self.variables().index(var)
            return list(self.constraints_of[i])
        except:
            print("Error: tried to find constraint of variable {} that isn't in this CSP {}".format(var, self.name()))

    def unAssignAllVars(self):
        '''unassign all variables'''
        for v in self.variables():
            v.unAssign()

    def check(self, solutions):
        '''each solution is a list of (var, value) pairs. Check to see
           if these satisfy all the constraints. Return list of
           erroneous solutions'''

        # save values to restore later
        current_values = [(var, var.getValue()) for var in self.variables()]
        errs = []

        for s in solutions:
            s_vars = [var for (var, val) in s]

            if len(s_vars) != len(self.variables()):
                errs.append([s, "Solution has incorrect number of variables in it"])
                continue

            if len(set(s_vars)) != len(self.variables()):
                errs.append([s, "Solution has duplicate variable assignments"])
                continue

            if set(s_vars) != set(self.variables()):
                errs.append([s, "Solution has incorrect variable in it"])
                continue

            for (var, val) in s:
                var.setValue(val)

            for c in self.constraints():
                if not c.check():
                    errs.append([s, "Solution does not satisfy constraint {}".format(c.name())])
                    break

        for (var, val) in current_values:
            var.setValue(val)

        return errs

    def __str__(self):
        return "CSP {}".format(self.name())


class Board:
    """
    Board class for setting up the playing board.
    """

    def __init__(self, width, height, cells: list[Cell]):
        """
        :param pieces: The list of Pieces
        :type pieces: List[Variable]
        """

        self.width = width
        self.height = height

        self.cells = cells
        # self.grid is a 2-d (size * size) array automatically generated
        # using the information on the pieces when a board is being created.
        # A grid contains the symbol for representing the pieces on the board.
        self.grid = []
        self.__construct_grid()

    def __hash__(self):
        return hash(frozenset(self.cells))

    def __construct_grid(self):
        """
        Called in __init__ to set up a 2-d grid based on the piece location information.

        """

        for i in range(self.height):
            line = []
            for j in range(self.width):
                line.append('0')
            self.grid.append(line)

        for cell in self.cells:
            if cell.getValue() is not None:
                if cell.getValue() == char_submarine:
                    self.grid[cell.y_coord][cell.x_coord] = char_submarine
                elif cell.getValue() == char_water:
                    self.grid[cell.y_coord][cell.x_coord] = char_water
                elif cell.getValue() == char_top:
                    self.grid[cell.y_coord][cell.x_coord] = char_top
                elif cell.getValue() == char_left:
                    self.grid[cell.y_coord][cell.x_coord] = char_left
                elif cell.getValue() == char_bottom:
                    self.grid[cell.y_coord][cell.x_coord] = char_bottom
                elif cell.getValue() == char_right:
                    self.grid[cell.y_coord][cell.x_coord] = char_right
                elif cell.getValue() == char_middle:
                    self.grid[cell.y_coord][cell.x_coord] = char_middle
                else:
                    print("Can't reach here!")

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

    def __init__(self, board, depth, constraints, parent=None):
        """
        :param board: The board of the state.
        :type board: Board
        :param depth: The depth of current state in the search tree.
        :type depth: int
        :param parent: The parent of current state.
        :type parent: State
        :param constraints: The constraints of current state
        :type constraints: list
        """
        self.board = board
        self.depth = depth
        self.parent = parent
        self.constraints = constraints
        self.id = hash(board)  # The id for breaking ties.

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
    :rtype: State
    """

    puzzle_file = open(filename, "r")

    line_index = 0
    word_index = 0
    cells = []
    constraints = []
    temp_lookup_rc = dict()
    temp_lookup_cc = dict()
    for line in puzzle_file:
        if line_index == 0:
            for x, ch in enumerate(line):
                if ch != '\n':
                    rc = RowConstraint("RowC", [], int(ch))
                    constraints.append(rc)
                    temp_lookup_rc[x] = rc
        elif line_index == 1:
            for x, ch in enumerate(line):
                if ch != '\n':
                    cc = ColConstraint("ColC", [], int(ch))
                    constraints.append(cc)
                    temp_lookup_cc[x] = cc
        elif line_index == 2:
            sc = ShipConstraint("ShipC", [], None, 0, 0, 0, 0)
            for x, ch in enumerate(line):
                if ch != '\n':
                    if x == 0:
                        sc.submarine = int(ch)
                    elif x == 1:
                        sc.destroyers = int(ch)
                    elif x == 2:
                        sc.cruisers = int(ch)
                    elif x == 3:
                        sc.battleships = int(ch)
                    else:
                        print("Can't get here! No ship")
            constraints.append(sc)
            break
        line_index += 1

    line_index = 0
    line_index2 = 0
    for line in puzzle_file:
        word_index = len(line)
        for x, ch in enumerate(line):
            if ch == '0':
                cell = Cell('Cell', [char_top, char_submarine, char_bottom, char_water, char_middle, char_left,
                                     char_right], False, x, line_index)
                cells.append(cell)
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
            elif ch == char_submarine:
                cell = Cell('Cell', [char_submarine], True, x, line_index)
                cell.setValue(char_submarine)
                cells.append(cell)
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
            elif ch == char_water:
                cell = Cell('Cell', [char_water], False, x, line_index)
                cell.setValue(char_water)
                cells.append(cell)
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
            elif ch == char_top:
                cell = Cell('Cell', [char_top], True, x, line_index)
                cell.setValue(char_top)
                cells.append(cell)
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
            elif ch == char_bottom:
                cell = Cell('Cell', [char_bottom], True, x, line_index)
                cell.setValue(char_bottom)
                cells.append(cell)
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
            elif ch == char_left:
                cell = Cell('Cell', [char_left], True, x, line_index)
                cell.setValue(char_left)
                cells.append(cell)
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
            elif ch == char_right:
                cell = Cell('Cell', [char_right], True, x, line_index)
                cell.setValue(char_right)
                cells.append(cell)
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
            elif ch == char_middle:
                cell = Cell('Cell', [char_middle], True, x, line_index)
                cell.setValue(char_middle)
                cells.append(cell)
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
        line_index += 1
    board = Board(word_index, line_index, cells)

    state = State(board, 0, constraints)
    puzzle_file.close()

    return state


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
    # args = parser.parse_args()

    # read the board from the file
    instate = read_from_file('test_input.txt')
    instate.board.display()
    # generate state base on the board
    # inboard = read_from_file('test_successor_red.txt')
    # start = time.time()
    # print(end - start)

    # write solution base on algo choice
    # write_solution(state, args.outputfile)
