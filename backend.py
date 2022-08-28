from random import randint


class Resource():
    def __init__(self, name):
        self.name = name
    

class ResourceOnBoard(Resource):
    def __init__(self, name):
        super().__init__(name)

class Building():
    def __init__(self, name='cottage', type='cottage', id=1):
        self.name = name
        self.type = type
        self.id = id

class BuildingRow():
    def __init__(self):
        self.buildings = []

    def generate(self): # generate row
        self.buildings = []
        self.buildings.append(Building('cottage', 'cottage', 0))
        #types = ['red', 'gray', 'orange', 'yellow', 'black', 'green']
        builds = {'red': ['1', '2', '3', '4'], 'gray': ['1', '2', '3', '4'], 'orange': ['1', '2', '3', '4'], 'yellow': ['1', '2', '3', '4'], 'black': ['1', '2', '3', '4'], 'green': ['1', '2', '3', '4']}
        for type in builds.keys():
            id = randint(0, 3)
            self.buildings.append(Building(builds[type][id], type, id))


class BuildingOnBoard():
    def __init__(self, name):
        super().__init__(name)

class Cell():
    def __init__(self, type='empty'):
        self.type = type

    def set(self, type):
        self.type = type

    def get(self):
        return self.type

class Board():
    def __init__(self):
        self.board = [[Cell(), Cell(), Cell(), Cell()], [Cell(), Cell(), Cell(), Cell()], [Cell(), Cell(), Cell(), Cell()], [Cell(), Cell(), Cell(), Cell()]]

    def getCell(self, x, y):
        return self.board[y][x].get()

    def setCell(self, build, x, y): 
        self.board[y][x].set(build)

    def print(self):
        for i in self.board:
            print(' '.join(list(map(lambda x: x.get(), i))))

class Player():
    def __init__(self, name):
        self.name = name
        self.id = 1
        self.board = Board()

    def getBoard(self):
        self.board.print()

# row = BuildingRow()
# row.generate()
# print(list(map(lambda x: x.name + ' ' + x.type , row.buildings)))

# board = Board()
# board.setCell('1', 0, 3)
# board.print()

player1 = Player("player1")
player1.getBoard()