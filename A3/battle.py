import math
import argparse
import time
import copy
import filecmp

char_submarine = 'S'
char_water = '.'
char_left = '<'
char_right = '>'
char_top = '^'
char_bottom = 'v'
char_middle = 'M'
CELL_DICT = dict()


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

    def pruneValue(self, value):
        '''Remove value from current domain'''
        try:
            self._curdom.remove(value)
        except:
            print("Error: tried to prune value {} from variable {}'s domain, but value not present!".format(value,
                                                                                                            self._name))
        # dkey = (reasonVar, reasonVal)
        # if not dkey in Variable.undoDict:
        #     Variable.undoDict[dkey] = []
        # Variable.undoDict[dkey].append((self, value))

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
        self.restore = {}
        self.constraint = []

    def __hash__(self):
        return hash((self.name, self.domain, self.x_coord, self.y_coord))

    def __str__(self):
        return "Variable {}{}".format(self.x_coord, self.y_coord)

    def __lt__(self, other):
        if len(self._dom) < len(other._dom):
            return True
        return False

    def add_restore(self, item, domain):
        self.restore[item] = domain
        # self.restore.append(item)

    def add_constraint(self, constraint):
        self.constraint.append(constraint)


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
        flag = 0
        for cell in self._scope:
            if cell.is_ship:
                count += 1
            if cell.getValue() is None:
                flag = 1
        if count == self.limit:
            return 0
        elif flag == 1 and count < self.limit:
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
        flag = 0
        for cell in self._scope:
            if cell.is_ship:
                count += 1
            if cell.getValue() is None:
                flag = 1
        if count == self.limit:
            return 0
        elif flag == 1 and count < self.limit:
            return 1
        else:
            # oversize
            return 2


class ShipConstraint(Constraint):
    def __init__(self, name, scope, submarine, destroyers, cruisers, battleships):
        Constraint.__init__(self, name, scope)
        self.submarine = submarine
        self.destroyers = destroyers
        self.cruisers = cruisers
        self.battleships = battleships

    def check(self):
        submarine = 0
        destroyers = 0
        cruisers = 0
        battleships = 0
        counter1 = 0
        counter2 = 0
        width = math.sqrt(len(self._scope) + 1)
        for cell in self._scope:
            if cell.getValue() != '.':
                if cell.getValue() == char_submarine:
                    submarine += 1
                    if submarine > self.submarine:
                        return 2
                elif cell.getValue() == char_left:
                    counter1 = 0
                elif cell.getValue() == char_middle:
                    counter1 += 1
                elif cell.getValue() == char_right:
                    if counter1 == 0:
                        destroyers += 1
                        if destroyers > self.destroyers:
                            return 2
                    elif counter1 == 1:
                        cruisers += 1
                        if cruisers > self.cruisers:
                            return 2
                    elif counter1 == 2:
                        battleships += 1
                        if battleships > self.battleships:
                            return 2
        for i in range(0, int(width)):
            # for cell in self._scope:
            #     if cell.x_coord == i:
            for j in range(0, int(width)):
                cell = CELL_DICT[(i, j)]
                if cell.getValue() != '.':
                    if cell.getValue() == char_top:
                        counter2 = 0
                    elif cell.getValue() == char_middle:
                        counter2 += 1
                    elif cell.getValue() == char_bottom:
                        if counter2 == 0:
                            destroyers += 1
                            if destroyers > self.destroyers:
                                return 2
                        elif counter2 == 1:
                            cruisers += 1
                            if cruisers > self.cruisers:
                                return 2
                        elif counter2 == 2:
                            battleships += 1
                            if battleships > self.battleships:
                                return 2
        if self.destroyers == destroyers and self.battleships == battleships and self.cruisers == cruisers and \
                self.submarine == submarine:
            return 0
        return 2


def get_cell(x_coord, y_coord) -> Cell:
    return CELL_DICT[(x_coord, y_coord)]


def check_if_spot_valid(width, x_coord, y_coord):
    if 0 <= x_coord <= width - 1:
        if 0 <= y_coord <= width - 1:
            return True
    return False


class P1Constraint(Constraint):
    def __init__(self, name, scope):
        Constraint.__init__(self, name, scope)

    def check(self):
        x = self.scope()[0].getValue()
        y = self.scope()[1].getValue()
        if y is not None:
            if x in {char_top, char_bottom, char_left, char_right, char_middle, char_submarine}:
                if y != '.':
                    return 2
        return 0


class P2Constraint(Constraint):
    def __init__(self, name, scope):
        Constraint.__init__(self, name, scope)

    def check(self):
        x = self.scope()[0].getValue()
        y = self.scope()[1].getValue()
        if y is not None:
            if x in {char_top, char_left, char_right, char_submarine}:
                if y != '.':
                    return 2
            elif x == char_middle:
                if y not in {char_top, char_water, char_middle}:
                    return 2
            elif x == char_bottom:
                if y not in {char_top, char_middle}:
                    return 2
        return 0


class P3Constraint(Constraint):
    def __init__(self, name, scope):
        Constraint.__init__(self, name, scope)

    def check(self):
        x = self.scope()[0].getValue()
        y = self.scope()[1].getValue()
        if y is not None:
            if x in {char_top, char_bottom, char_left, char_right, char_middle, char_submarine}:
                if y != '.':
                    return 2
        return 0


class P4Constraint(Constraint):
    def __init__(self, name, scope):
        Constraint.__init__(self, name, scope)

    def check(self):
        x = self.scope()[0].getValue()
        y = self.scope()[1].getValue()
        if y is not None:
            if x in {char_top, char_left, char_bottom, char_submarine}:
                if y != '.':
                    return 2
            elif x == char_middle:
                if y not in {char_left, char_water, char_middle}:
                    return 2
            elif x == char_right:
                if y not in {char_left, char_middle}:
                    return 2
        return 0


class P5Constraint(Constraint):
    def __init__(self, name, scope):
        Constraint.__init__(self, name, scope)

    def check(self):
        x = self.scope()[0].getValue()
        y = self.scope()[1].getValue()
        if y is not None:
            if x in {char_top, char_right, char_bottom, char_submarine}:
                if y != '.':
                    return 2
            elif x == char_middle:
                if y not in {char_right, char_water, char_middle}:
                    return 2
            elif x == char_left:
                if y not in {char_right, char_middle}:
                    return 2
        return 0


class P6Constraint(Constraint):
    def __init__(self, name, scope):
        Constraint.__init__(self, name, scope)

    def check(self):
        x = self.scope()[0].getValue()
        y = self.scope()[1].getValue()
        if y is not None:
            if x in {char_top, char_bottom, char_left, char_right, char_middle, char_submarine}:
                if y != '.':
                    return 2
        return 0


class P7Constraint(Constraint):
    def __init__(self, name, scope):
        Constraint.__init__(self, name, scope)

    def check(self):
        x = self.scope()[0].getValue()
        y = self.scope()[1].getValue()
        if y is not None:
            if x in {char_bottom, char_left, char_right, char_submarine}:
                if y != '.':
                    return 2
            elif x == char_middle:
                if y not in {char_bottom, char_water, char_middle}:
                    return 2
            elif x == char_top:
                if y not in {char_bottom, char_middle}:
                    return 2
        return 0


class P8Constraint(Constraint):
    def __init__(self, name, scope):
        Constraint.__init__(self, name, scope)

    def check(self):
        x = self.scope()[0].getValue()
        y = self.scope()[1].getValue()
        if y is not None:
            if x in {char_top, char_bottom, char_left, char_right, char_middle, char_submarine}:
                if y != '.':
                    return 2
        return 0


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

    def __str__(self):
        return "CSP {}".format(self.name())


class Board:
    """
    Board class for setting up the playing board.
    """

    def __init__(self, width, cells: list[Cell]):
        """
        :param width: The width of the board
        :type cells: List[Cell]
        """

        self.width = width
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

        for i in range(self.width):
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

    def update(self):
        for i in range(self.width):
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


class State(CSP):
    """
    State class wrapping a Board with some extra current state information.
    Note that State and Board are different. Board has the locations of the pieces.
    State has a Board and some extra information that is relevant to the search:
    heuristic function, f value, current depth and parent.
    """

    def __init__(self, name, board, depth, constraints, parent=None):
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
        CSP.__init__(self, name, board.cells, constraints)
        self.board = board
        self.depth = depth
        self.parent = parent
        self.id = hash(board)  # The id for breaking ties.

    def __eq__(self, other):
        if self.id == other.id:
            return True
        return False

    def partial_check(self, cell: Cell):
        for c in cell.constraint:
            if c.check() == 2:
                return False
        for c in self.board.cells:
            if c.getValue() == char_middle:
                flag = 0
                tv1 = 0
                tv2 = 0
                tv11 = 0
                tv22 = 0
                if check_if_spot_valid(self.board.width, c.x_coord, c.y_coord - 1):
                    tv1 = get_cell(c.x_coord, c.y_coord - 1).getValue()
                if check_if_spot_valid(self.board.width, c.x_coord - 1, c.y_coord):
                    tv2 = get_cell(c.x_coord - 1, c.y_coord).getValue()
                if check_if_spot_valid(self.board.width, c.x_coord, c.y_coord + 1):
                    tv11 = get_cell(c.x_coord, c.y_coord + 1).getValue()
                if check_if_spot_valid(self.board.width, c.x_coord + 1, c.y_coord):
                    tv22 = get_cell(c.x_coord + 1, c.y_coord).getValue()
                if tv1 == char_top or tv1 == char_middle or tv11 == char_bottom or tv11 == char_middle or tv2 == char_water or tv22 == char_water:
                    flag = 'v'
                elif tv2 == char_left or tv2 == char_middle or tv22 == char_right or tv22 == char_middle or tv1 == char_water or tv11 == char_water:
                    flag = 'h'
                if (c.x_coord == 0 and c.y_coord == 0) or (
                        c.x_coord == self.board.width - 1 and c.y_coord == self.board.width - 1) or \
                        (c.x_coord == 0 and c.y_coord == self.board.width - 1) or (
                        c.x_coord == self.board.width - 1 and c.y_coord == 0):
                    return False
                if flag == 'v':
                    if c.y_coord == 0 or c.y_coord == self.board.width - 1:
                        return False
                    if tv1 is not None:
                        if tv1 not in {char_middle, char_top}:
                            return False
                    if tv11 is not None:
                        if tv11 not in {char_middle, char_bottom}:
                            return False
                elif flag == 'h':
                    if c.x_coord == 0 or c.x_coord == self.board.width - 1:
                        return False
                    if tv2 is not None:
                        if tv2 not in {char_middle, char_left}:
                            return False
                    if tv22 is not None:
                        if tv22 not in {char_middle, char_right}:
                            return False
        return True

    def full_check(self):
        for c in self.constraints():
            if c.check() == 1 or c.check() == 2:
                return False
        for cell in self.board.cells:
            if cell.getValue() is None:
                return False
        return True


def preprocessing(state: State):
    for c in state.constraints():
        if isinstance(c, RowConstraint) or isinstance(c, ColConstraint):
            if c.check() == 0:
                for cell in c.scope():
                    if cell.getValue() is None:
                        cell.setValue(char_water)
                        cell.resetDomain(['.'])
                        cell._curdom = ['.']
    for cell in state.board.cells:
        if cell.getValue() is not None:
            if cell.getValue() == char_top:
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord + 2):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord + 2)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord + 2):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord + 2)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
            if cell.getValue() == char_bottom:
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord - 2):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord - 2)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord - 2):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord - 2)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
            if cell.getValue() == char_left:
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 2, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord + 2, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 2, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord + 2, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
            if cell.getValue() == char_right:
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 2, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord - 2, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 2, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord - 2, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
            if cell.getValue() == char_middle:
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
            if cell.getValue() == char_submarine:
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord - 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord - 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']
                if check_if_spot_valid(state.board.width, cell.x_coord + 1, cell.y_coord + 1):
                    temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
                    temp.setValue(char_water)
                    temp.resetDomain(['.'])
                    temp._curdom = ['.']


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
            sc = ShipConstraint("ShipC", [], 0, 0, 0, 0)
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
    for line in puzzle_file:
        for x, ch in enumerate(line):
            if ch == '0':
                cell = Cell('Cell', [char_water, char_middle, char_top, char_bottom, char_left,
                                     char_right, char_submarine], False, x, line_index)
                cells.append(cell)
                CELL_DICT[(x, line_index)] = cell
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
                cell.add_constraint(temp_lookup_cc[x])
                cell.add_constraint(temp_lookup_rc[line_index])
            elif ch == char_submarine:
                cell = Cell('Cell', [char_submarine], True, x, line_index)
                cell.setValue(char_submarine)
                cells.append(cell)
                CELL_DICT[(x, line_index)] = cell
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
                cell.add_constraint(temp_lookup_cc[x])
                cell.add_constraint(temp_lookup_rc[line_index])
            elif ch == char_water:
                cell = Cell('Cell', [char_water], False, x, line_index)
                cell.setValue(char_water)
                cells.append(cell)
                CELL_DICT[(x, line_index)] = cell
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
                cell.add_constraint(temp_lookup_cc[x])
                cell.add_constraint(temp_lookup_rc[line_index])
            elif ch == char_top:
                cell = Cell('Cell', [char_top], True, x, line_index)
                cell.setValue(char_top)
                cells.append(cell)
                CELL_DICT[(x, line_index)] = cell
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
                cell.add_constraint(temp_lookup_cc[x])
                cell.add_constraint(temp_lookup_rc[line_index])
            elif ch == char_bottom:
                cell = Cell('Cell', [char_bottom], True, x, line_index)
                cell.setValue(char_bottom)
                cells.append(cell)
                CELL_DICT[(x, line_index)] = cell
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
                cell.add_constraint(temp_lookup_cc[x])
                cell.add_constraint(temp_lookup_rc[line_index])
            elif ch == char_left:
                cell = Cell('Cell', [char_left], True, x, line_index)
                cell.setValue(char_left)
                cells.append(cell)
                CELL_DICT[(x, line_index)] = cell
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
                cell.add_constraint(temp_lookup_cc[x])
                cell.add_constraint(temp_lookup_rc[line_index])
            elif ch == char_right:
                cell = Cell('Cell', [char_right], True, x, line_index)
                cell.setValue(char_right)
                cells.append(cell)
                CELL_DICT[(x, line_index)] = cell
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
                cell.add_constraint(temp_lookup_cc[x])
                cell.add_constraint(temp_lookup_rc[line_index])
            elif ch == char_middle:
                cell = Cell('Cell', [char_middle], True, x, line_index)
                cell.setValue(char_middle)
                cells.append(cell)
                CELL_DICT[(x, line_index)] = cell
                temp_lookup_cc[x]._scope.append(cell)
                temp_lookup_rc[line_index]._scope.append(cell)
                cell.add_constraint(temp_lookup_cc[x])
                cell.add_constraint(temp_lookup_rc[line_index])
        line_index += 1
    for cell in cells:
        if check_if_spot_valid(line_index, cell.x_coord - 1, cell.y_coord - 1):
            tempc = P1Constraint('p1', [cell, get_cell(cell.x_coord - 1, cell.y_coord - 1)])
            cell.add_constraint(tempc)
        if check_if_spot_valid(line_index, cell.x_coord, cell.y_coord - 1):
            tempc = P2Constraint('p2', [cell, get_cell(cell.x_coord, cell.y_coord - 1)])
            cell.add_constraint(tempc)
        if check_if_spot_valid(line_index, cell.x_coord + 1, cell.y_coord - 1):
            tempc = P3Constraint('p3', [cell, get_cell(cell.x_coord + 1, cell.y_coord - 1)])
            cell.add_constraint(tempc)
        if check_if_spot_valid(line_index, cell.x_coord - 1, cell.y_coord):
            tempc = P4Constraint('p4', [cell, get_cell(cell.x_coord - 1, cell.y_coord)])
            cell.add_constraint(tempc)
        if check_if_spot_valid(line_index, cell.x_coord + 1, cell.y_coord):
            tempc = P5Constraint('p5', [cell, get_cell(cell.x_coord + 1, cell.y_coord)])
            cell.add_constraint(tempc)
        if check_if_spot_valid(line_index, cell.x_coord - 1, cell.y_coord + 1):
            tempc = P6Constraint('p6', [cell, get_cell(cell.x_coord - 1, cell.y_coord + 1)])
            cell.add_constraint(tempc)
        if check_if_spot_valid(line_index, cell.x_coord, cell.y_coord + 1):
            tempc = P7Constraint('p7', [cell, get_cell(cell.x_coord, cell.y_coord + 1)])
            cell.add_constraint(tempc)
        if check_if_spot_valid(line_index, cell.x_coord + 1, cell.y_coord + 1):
            tempc = P8Constraint('p8', [cell, get_cell(cell.x_coord + 1, cell.y_coord + 1)])
            cell.add_constraint(tempc)

    board = Board(line_index, cells)
    for c in constraints:
        if isinstance(c, ShipConstraint):
            c._scope = cells
    state = State("State", board, 0, constraints)
    puzzle_file.close()

    return state


def select_unassigned_var(state: State):
    # MRV
    ret = 0
    minv = math.inf
    for c in state.board.cells:
        if c.getValue() is None:
            # temp.append(c)
            if len(c._curdom) < minv:
                minv = len(c._curdom)
                ret = c
    if ret != 0:
        return ret
    else:
        return False


def backtracking_search(state: State):
    return backtrack(state)


def recover_var(restore):
    if len(restore) != 0:
        for c in restore:
            c._curdom = restore[c]


def forward_checking(cell, state: State, restore):
    width = state.board.width
    if cell.getValue() == '.':
        return True
    for c in cell.constraint:
        if isinstance(c, RowConstraint) or isinstance(c, ColConstraint):
            if c.check() == 0:
                for ce in c.scope():
                    if ce.getValue() is None:
                        restore[ce] = copy.copy(ce._curdom)
                        for dom in ce.curDomain():
                            if dom != '.':
                                ce.pruneValue(dom)
                        if len(ce._curdom) == 0:
                            return False
    if cell.getValue() == char_top:
        # position 1
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 2
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord - 1):
            temp = get_cell(cell.x_coord, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 3
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 4
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord):
            temp = get_cell(cell.x_coord - 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 5
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord):
            temp = get_cell(cell.x_coord + 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 6
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 7
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord + 1):
            temp = get_cell(cell.x_coord, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != char_middle and dom != char_bottom:
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 8
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
    if cell.getValue() == char_bottom:
        # position 1
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 2
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord - 1):
            temp = get_cell(cell.x_coord, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != char_middle and dom != char_top:
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 3
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 4
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord):
            temp = get_cell(cell.x_coord - 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 5
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord):
            temp = get_cell(cell.x_coord + 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 6
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 7
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord + 1):
            temp = get_cell(cell.x_coord, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 8
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
    if cell.getValue() == char_left:
        # position 1
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 2
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord - 1):
            temp = get_cell(cell.x_coord, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 3
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 4
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord):
            temp = get_cell(cell.x_coord - 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 5
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord):
            temp = get_cell(cell.x_coord + 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != char_middle and dom != char_right:
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 6
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 7
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord + 1):
            temp = get_cell(cell.x_coord, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 8
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
    if cell.getValue() == char_right:
        # position 1
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 2
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord - 1):
            temp = get_cell(cell.x_coord, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 3
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 4
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord):
            temp = get_cell(cell.x_coord - 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != char_middle and dom != char_left:
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 5
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord):
            temp = get_cell(cell.x_coord + 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 6
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 7
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord + 1):
            temp = get_cell(cell.x_coord, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 8
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
    if cell.getValue() == char_middle:
        flag = 0
        tv1 = 0
        tv2 = 0
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord - 1):
            tv1 = get_cell(cell.x_coord, cell.y_coord - 1).getValue()
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord):
            tv2 = get_cell(cell.x_coord - 1, cell.y_coord).getValue()
        if tv1 == char_top or tv1 == char_middle:
            flag = 'v'
        elif tv2 == char_left or tv2 == char_middle:
            flag = 'h'
        # position 1
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 2
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord - 1):
            temp = get_cell(cell.x_coord, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                if flag == 'h':
                    for dom in temp.curDomain():
                        if dom != '.':
                            temp.pruneValue(dom)
                    if len(temp._curdom) == 0:
                        return False
                else:
                    for dom in temp.curDomain():
                        if dom != char_middle and dom != char_top:
                            temp.pruneValue(dom)
                    if len(temp._curdom) == 0:
                        return False
        # position 3
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 4
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord):
            temp = get_cell(cell.x_coord - 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                if flag == 'v':
                    for dom in temp.curDomain():
                        if dom != '.':
                            temp.pruneValue(dom)
                    if len(temp._curdom) == 0:
                        return False
                else:
                    for dom in temp.curDomain():
                        if dom != char_middle and dom != char_left:
                            temp.pruneValue(dom)
                    if len(temp._curdom) == 0:
                        return False
        # position 5
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord):
            temp = get_cell(cell.x_coord + 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                if flag == 'v':
                    for dom in temp.curDomain():
                        if dom != '.':
                            temp.pruneValue(dom)
                    if len(temp._curdom) == 0:
                        return False
                else:
                    for dom in temp.curDomain():
                        if dom != char_middle and dom != char_right:
                            temp.pruneValue(dom)
                    if len(temp._curdom) == 0:
                        return False
        # position 6
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 7
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord + 1):
            temp = get_cell(cell.x_coord, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                if flag == 'h':
                    for dom in temp.curDomain():
                        if dom != '.':
                            temp.pruneValue(dom)
                    if len(temp._curdom) == 0:
                        return False
                else:
                    for dom in temp.curDomain():
                        if dom != char_middle and dom != char_bottom:
                            temp.pruneValue(dom)
                    if len(temp._curdom) == 0:
                        return False
        # position 8
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
    if cell.getValue() == char_submarine:
        # position 1
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 2
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord - 1):
            temp = get_cell(cell.x_coord, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 3
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord - 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord - 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 4
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord):
            temp = get_cell(cell.x_coord - 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 5
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord):
            temp = get_cell(cell.x_coord + 1, cell.y_coord)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 6
        if check_if_spot_valid(width, cell.x_coord - 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord - 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 7
        if check_if_spot_valid(width, cell.x_coord, cell.y_coord + 1):
            temp = get_cell(cell.x_coord, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
        # position 8
        if check_if_spot_valid(width, cell.x_coord + 1, cell.y_coord + 1):
            temp = get_cell(cell.x_coord + 1, cell.y_coord + 1)
            if temp.getValue() is None:
                if temp not in restore:
                    restore[temp] = copy.copy(temp._curdom)
                for dom in temp.curDomain():
                    if dom != '.':
                        temp.pruneValue(dom)
                if len(temp._curdom) == 0:
                    return False
    return True


def backtrack(state: State):
    if state.full_check():
        return [([c.x_coord, c.y_coord], c.getValue()) for c in state.board.cells]
    var = select_unassigned_var(state)
    if var is not False:
        for value in var.curDomain():
            var.setValue(value)
            if value != '.':
                var.is_ship = True
            else:
                var.is_ship = False
            if state.partial_check(var):
                restore = dict()
                if forward_checking(var, state, restore):
                    result = backtrack(state)
                    if len(result) != 0:
                        return result
                recover_var(restore)
    else:
        return []
    # reset var
    var._value = None
    var.is_ship = None
    return []


def write_solution(state: State, filename: str):
    """ Generate solution file base on the goal state.

    """
    f = open(filename, "w+")
    sol = backtracking_search(state)
    count = 0
    for s in sol:
        f.write(s[1])
        if state.board.width - 1 == count:
            f.write('\n')
            count = -1
        count += 1


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
    # instate = read_from_file(args.inputfile)
    # preprocessing(instate)
    # write_solution(instate, args.outputfile)

    start = time.time()
    instate = read_from_file('test_input88_3.txt')
    preprocessing(instate)
    write_solution(instate, 'sol.txt')
    end = time.time()
    print(end - start)
