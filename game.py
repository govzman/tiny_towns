from random import randint
import uuid


class Game():
    def __init__(self): # , players_count=2, players_names=['player1', 'player2']
        self.game_state = 'lobby'
        self.players_count = 0
        self.players = {}
        self.buildingRow = BuildingRow()
        self.buildingRow.generate()
        self.currentTurn = 1

    def get_status(self, params):
        if self.game_state == 'lobby':
            if 'id' not in params:
                id = str(uuid.uuid4())
                self.players[id] = {'nickname': params['nickname'], 'ready': False, 'id': id}
            else:
                id = params['id']
                if id in self.players:
                    self.players[id]['ready'] = params['ready']
                else:
                    return {
                        'error': {'code': 1, 'msg': 'bad id'}
                    }
        return {
            'game_state': self.game_state, 
            'players': list(map(lambda x: self.players[x]['nickname'], self.players.keys())), 
            'isReady': list(map(lambda x: str(self.players[x]['ready']), self.players.keys())),
            'id': id
            }

    def restart_game(self):
        self.players = {}
        self.game_state = 'lobby'


class Resource():
    def __init__(self, name):
        self.name = name

class ResourceOnBoard(Resource):
    def __init__(self, name):
        super().__init__(name)

class Building():
    def __init__(self, name='Cottage', type='cottage', id=1):
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

    def checkPatterns(self, cords):
        pass


# class Player():
#     def __init__(self, nickname):
#         self.nickname = nickname
#         self.id = 1
#         self.board = Board()
#         self.isReady = False
#         self.monument_id = 0

#     def getBoard(self):
#         self.board.print()



# row = BuildingRow()
# row.generate()
# print(list(map(lambda x: x.name + ' ' + x.type , row.buildings)))

# board = Board()
# board.setCell('1', 0, 3)
# board.print()

# player1 = Player("player1")
# player1.getBoard()

if __name__ == '__main__':
    game = Game()
    print(game.buildingRow.getRow())