from random import randint, shuffle
from time import time
import uuid

import util 

class Game():
    def __init__(self): # , players_count=2, players_names=['player1', 'player2']
        self.game_stage = 'lobby'
        self.game_id = str(uuid.uuid4())
        self.players = {}
        self.monuments = ['Arch_Guild', 'Arch_Age', 'Bar_Cast', 
        'Cath_Cat', 'Fort_Iron', 'Grove_Un', 'Mand_Pal', 'Opal_Wat', 
        'Shr_Tree', 'Sil_For', 'Star', 'Stat_Bond', 'Rodina', 'Sky_Bath', 'Crescent']
        
        # ['Architect`s Guild', 'Archive of the Second Age', 'Barrett Castle', 
        # 'Cathedral of Caterina', 'Fort Ironweed', 'Grove University', 'Mandras Palace', 'Opaleyes Watch', 
        # 'Shrine of the Elder Tree', 'Silva Forum', 'The Starloom', 'Statue of the Bondmaker']
        self.buildingRow = BuildingRow()
        self.buildingRow.generate()
        self.currentTurn = 1

    def get_status(self, params):
        if 'id' not in params:
            id = str(uuid.uuid4())
            if self.game_stage == 'lobby':
                if 'nickname' in params: 
                    self.players[id] = {'nickname': params['nickname'], 
                    'ready': False}
                    return {'id': id}
                else:
                    return util.error(2, 'miss nickname')
            else:
                return util.error(3, 'game is already run')

        id = params['id']
        if id not in self.players:
            return util.error(1, 'bad id')

        self.players[id]['last_response'] = time()

        self.setParam('ready', params)

        if self.game_stage == 'lobby':
            if all(map(lambda x: self.players[x]['ready'], self.players.keys())):
                if len(self.players) >= 1 and len(self.players) <= 6:
                      self.game_stage = 'choose_monument'
                      shuffle(self.monuments)
                      for ids in self.players:
                          self.players[ids]['monuments'] = [self.monuments.pop(), self.monuments.pop()] 
                else:
                    return util.error(4, 'wrong number of players')
        if self.game_stage == 'choose_monument':
            return self.res({'monuments': self.players[id]['monuments']})

        self.checkTTL()
        return self.res({
            'players': list(map(lambda x: self.players[x]['nickname'], self.players.keys())), 
            'isReady': list(map(lambda x: self.players[x]['ready'], self.players.keys())),
            })

    def restart_game(self):
        self.players = {}
        self.game_stage = 'lobby'
        print('RESTART!')
        # return {'game_stage': 'lobby', 'restart_game': True}

    def log_out(self, params):
        if params['id'] in self.players:
            del self.players[params['id']]
            return {'status' : 'ok'}
        else:
            return {'error': {'code': 55, 'msg': 'bad id'}, 'id2': params['id'], 'keys': self.players.keys()}

    def checkTTL(self):
        keys = self.players.keys()
        for player_id in keys:
            if 'last_response' in self.players[player_id]:
                if time() - self.players[player_id]['last_response'] > 10:
                    del self.players[player_id]

    def setParam(self, paramName, params):
        if paramName in params:
            self.players[params['id']][paramName] = params[paramName]
        else:
            # TODO() aux.error(2, 'miss ' + paramName)
            pass

    def res(self, params):
        return {
            'game_id': self.game_id, 
            'game_stage': self.game_stage, 
            'params': params
        }

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