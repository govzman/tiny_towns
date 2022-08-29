from random import randint

class Game():
    def __init__(self, players_count=2, players_names=['player1', 'player2']):
        self.players_count = players_count
        self.players = [Player(name) for name in players_names]
        self.buildingRow = BuildingRow()
        self.buildingRow.generate()
        self.currentTurn = 1

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
        self.buildings.append(Building('Cottage', 'cottage', 0))
        #types = ['red', 'gray', 'orange', 'yellow', 'black', 'green']
        builds = {'red': ['Farm', 'Granary', 'Greenhouse', 'Orchard'], 'gray': ['Fountain', 'Millstone', 'Shed', 'Well'], 'orange': ['Chapel', 'Chapel', 'Cloister', 'Temple'], 'yellow': ['Bakery', 'Market', 'Tailor', 'Theater'], 'black': ['Bank', 'Factory', 'Trading Post', 'Warehouse'], 'green': ['Almshouse', 'Feast Hall', 'Inn', 'Tavern']}
        for type in builds.keys():
            id = randint(0, 3)
            self.buildings.append(Building(builds[type][id], type, id))

    def getRow(self):
        return list(map(lambda x: x.name, self.buildings))


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

# player1 = Player("player1")
# player1.getBoard()

game = Game(2, ['player1', 'player2'])
print(game.buildingRow.getRow())