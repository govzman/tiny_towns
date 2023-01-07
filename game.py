from random import randint, shuffle
from time import time
import uuid

import util 

class Game():
    def __init__(self): # , players_count=2, players_names=['player1', 'player2']
        self.stage = 'lobby'
        self.game_step = 0
        self.game_id = str(uuid.uuid4())
        self.players = {}
        self.monuments = ['Arch_Guild', 'Arch_Age', 'Bar_Cast', # ['Architect`s Guild', 'Archive of the Second Age', 'Barrett Castle', 
        'Cath_Cat', 'Fort_Iron', 'Grove_Un', 'Mand_Pal', 'Opal_Wat', # 'Cathedral of Caterina', 'Fort Ironweed', 'Grove University', 'Mandras Palace', 'Opaleyes Watch', 
        'Shr_Tree', 'Sil_For', 'Star', 'Stat_Bond', 'Rodina', 'Sky_Bath', 'Crescent'] # 'Shrine of the Elder Tree', 'Silva Forum', 'The Starloom', 'Statue of the Bondmaker']
        
        self.buildingRow = BuildingRow()
        self.buildingRow.generate()
        self.board = Board()
        self.turn = 1

    def get_status(self, params):
        if 'id' not in params:
            id = str(uuid.uuid4())
            if self.stage == 'lobby':
                if 'nickname' in params: 
                    self.players[id] = {'nickname': params['nickname'], 'board': Board(), 'ready': False}
                    return {
                        'stage': self.stage,
                        'id': id
                        }
                else:
                    return util.error(2, 'miss nickname')
            else:
                return util.error(3, 'game is already run')

        id = params['id']
        if id not in self.players:
            return util.error(1, 'bad id')

        self.players[id]['last_response'] = time()

        self.setParam('ready', params)
        
        if self.stage == 'lobby':            
            if all(map(lambda x: self.players[x]['ready'], self.players.keys())):
                if len(self.players) >= 1 and len(self.players) <= 6:
                    self.stage = 'choose_monument'
                    shuffle(self.monuments)
                    for ids in self.players:
                        self.players[ids]['monuments'] = [self.monuments.pop(), self.monuments.pop()]
                        self.players[ids]['ready'] = False
                    # return {
                    #     'stage': self.stage
                    # }
                else:
                    return util.error(4, 'wrong number of players')

        if self.stage == 'choose_monument':
            out = self.res({
                'stage': self.stage,
                'player': { 'monuments': self.players[id]['monuments']},
                'bulidingRow': self.buildingRow.getRow(), 
                'players': list(map(lambda x: self.players[x]['nickname'], self.players.keys())), 
                'isReady': list(map(lambda x: self.players[x]['ready'], self.players.keys()))
            })
            
            if all(map(lambda x: self.players[x]['ready'], self.players.keys())):
                self.stage = 'main_game'
                for ids in self.players:
                    self.players[ids]['ready'] = False

            return out
        
        if self.stage == 'main_game':
            isMasterBuilder =  list(self.players.keys()).index(id) == ((self.turn - 1) % len(self.players))
            return self.res({
                'stage': self.stage,
                'player': {
                    'monument': self.players[id]['monument']
                },
                'players': list(map(lambda x: self.players[x]['nickname'], self.players.keys())),
                'bulidingRow': self.buildingRow.getRow(),
                'isReady': list(map(lambda x: self.players[x]['ready'], self.players.keys())),
                'isMasterBuilder': isMasterBuilder
            })

        self.checkTTL()
        return self.res({
            'stage': self.stage,
            'players': list(map(lambda x: self.players[x]['nickname'], self.players.keys())), 
            'isReady': list(map(lambda x: self.players[x]['ready'], self.players.keys())),
            })

    def restart_game(self):        
        self.players = {}
        self.stage = 'lobby'        
        return {'status':'ok', 'params':{'stage': 'lobby' }}
        
    def log_out(self, params):
        if params['id'] in self.players:
            del self.players[params['id']]
            return {'status' : 'ok'}
        else:
            print(self.players)
            return {'error': {'code': 55, 'msg': 'bad id'}}


    def set_monument(self, params):
        if params['id'] not in self.players:
            return {'error': {'code': 55, 'msg': 'bad id'}}
        
        if self.stage != 'choose_monument':
            return {'error': {'code': 56, 'msg': 'Wrong game stage'}}

        if 'monument' in params:
            if params['monument'] in self.players[params['id']]['monuments']:
                self.players[params['id']]['monument'] = params['monument']
                return {'status' : 'ok'}
        else:
            print(params, self.players[params['id']])
            return {'error': {'code': 57, 'msg': 'bad request'}}

    def check_patterns(self, params):
        if params['id'] not in self.players:
            return {'error': {'code': 55, 'msg': 'bad id'}}
        if self.stage != 'main_game':
            return {'error': {'code': 56, 'msg': 'Wrong game stage'}}

        if 'cords' in params:
            cords = params['cords']
        else:
            print(params, self.players[params['id']])
            return {'error': {'code': 57, 'msg': 'bad request'}}

        # check patterns
        answer = self.players[params['id']]['board'].check_patterns(cords, self.buildingRow)

        if answer == None:
            return {'isPattern': False}
        return {'isPattern': True, 'building': answer}

    def place_resource(self, params):
        if params['id'] not in self.players:
            return {'error': {'code': 55, 'msg': 'bad id'}}
        if self.stage != 'main_game':
            return {'error': {'code': 56, 'msg': 'Wrong game stage'}}
        # print(params)
        if 'movement' in params:
            if len(params['movement']) == 1:
                x, y = map(int, list(params['movement'].keys())[0].split(','))
                self.players[params['id']]['board'].setCell(list(params['movement'].values())[0], [x, y])
                print(self.players[params['id']]['board'])
            else:
                return {'error': {'code': 57, 'msg': 'bad request'}}
        else:
            return {'error': {'code': 57, 'msg': 'bad request'}}

    def checkTTL(self):
        try:
            keys = self.players.keys()
            for player_id in keys:
                if 'last_response' in self.players[player_id]:
                    if time() - self.players[player_id]['last_response'] > 10:
                        del self.players[player_id]
        except:
            pass

    def setParam(self, paramName, params):
        #print('PARAMS',paramName, params, self.players[params['id']][paramName])
        if (paramName in params) and ('stage' in params and self.stage == params['stage']):
            self.players[params['id']][paramName] = params[paramName]
        else:
            # TODO() aux.error(2, 'miss ' + paramName)
            pass

    def res(self, params):
        return {
            'game_id': self.game_id, 
            #'game_stage': self.game_stage,
            'game_step': self.game_step, 
            'params': params
        }


class Resource():
    def __init__(self, name):
        self.name = name

class ResourceOnBoard(Resource):
    def __init__(self, name):
        super().__init__(name)

class Building():

    with open('buildings_patterns.txt') as file:
        lines = file.readlines()
        buildings_patterns = {}
        # print('!', lines)
        for i in range(len(lines)):
            buliding, pattern = lines[i].split(' / ')
            buildings_patterns[buliding] = eval(pattern)
        print(buildings_patterns)

    def __init__(self, name='Cottage', type='cottage', id=1):
        self.name = name
        self.type = type
        self.id = id
        # self.patterns = []
        if self.name in Building.buildings_patterns:
        # if self.name == 'Cottage':
            # self.patterns = [{'1, 1': 'blue', '0, 1': 'red', '1, 0': 'yellow'}]
            self.patterns = [Building.buildings_patterns[self.name]]
            self.add_all_rotations()
            # print(*self.patterns, sep='\n')
        else:
            self.patterns = [{'0, 0': 'red'}] # заглушка

    def add_all_rotations(self):
        size_x = 1
        size_y = 1
        # print('^', self.patterns)
        for cell in self.patterns[0]:
            x, y = map(int, cell.split(', '))
            size_x, size_y = max(size_x, x + 1), max(size_y, y + 1)
        # print(size_x, size_y)

        # base rotations
        for _ in range(3):
            turn90 = {} # right 
            for cell in self.patterns[-1]:
                x, y = map(int, cell.split(', '))
                turn90[f'{size_y - 1 - y}, {x}'] = self.patterns[-1][cell]
            self.patterns.append(turn90)
        
        # add horizontal symmetric 
        horizontal = {} 
        for cell in self.patterns[0]:
            x, y = map(int, cell.split(', '))
            horizontal[f'{size_x - 1 - x}, {y}'] = self.patterns[0][cell]
        self.patterns.append(horizontal)

        # horizontal symmetrical rotations

        for i in range(3):
            turn90 = {} # right 
            for cell in self.patterns[-1]:
                x, y = map(int, cell.split(', '))
                turn90[f'{size_y - 1 - y}, {x}'] = self.patterns[-1][cell]
            self.patterns.append(turn90)

        # add vertical symmetric 
        vertical = {} 
        for cell in self.patterns[0]:
            x, y = map(int, cell.split(', '))
            vertical[f'{x}, {size_y - y - 1}'] = self.patterns[0][cell]
        self.patterns.append(vertical)

        # horizontal symmetrical rotations

        for i in range(3):
            turn90 = {} # right 
            for cell in self.patterns[-1]:
                x, y = map(int, cell.split(', '))
                turn90[f'{size_y - 1 - y}, {x}'] = self.patterns[-1][cell]
            self.patterns.append(turn90)
        

    # def __call__(self):
    #     return self.name

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

    def __str__(self):
        return ', '.join(list(map(lambda x: x.name, self.buildings)))

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
        self.board = [
            [Cell(), Cell(), Cell(), Cell()],
            [Cell(), Cell(), Cell(), Cell()], 
            [Cell(), Cell(), Cell(), Cell()], 
            [Cell(), Cell(), Cell(), Cell()]
            ]

    def getCell(self, cord):
        return self.board[cord[1]][cord[0]].get()

    def setCell(self, build, cord): 
        self.board[cord[1]][cord[0]].set(build)

    def __str__(self):
        string = ''
        for i in self.board:
            string += '\t'.join(list(map(lambda x: x.get(), i))) + '\n'
        return string
    
    def check_patterns(self, cords, building_row):
        min_cord_x = min(map(lambda x: int(x.split(', ')[0]), cords.keys()))
        min_cord_y = min(map(lambda x: int(x.split(', ')[1]), cords.keys()))
        # print(min_cord_x, min_cord_y)
        cords = {f"{int(cord.split(', ')[0]) - min_cord_x}, {int(cord.split(', ')[1]) - min_cord_y}": cords[cord] for cord in cords}
        # print(cords)
        isFound = False
        for building in building_row.buildings: # 1 потому что ТЕСТ для первого здания (коттеджа)
            if cords in building.patterns:
                isFound = True
                return building.name
        if not isFound:
            return None
            
        # for cord in cords:
        #     print(building_row.buildings[0].patterns[0][str(cord[0]) + ', ' + str(cord[1])])
            # print(cord)
            # print(self.getCell(cord))
        # print(str(cord))
        



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
    # print(game.buildingRow.getRow())
    # input_cells = {'3, 3': 'blue', '2, 3': 'red', '3, 2': 'yellow'}
    # input_cells = {'0, 0': 'blue', '1, 0': 'yellow', '0, 1': 'red'}
    print(game.buildingRow)
    input_cells = {'3, 2': 'gray', '2, 2': 'brown'}
    game.board.check_patterns(input_cells, game.buildingRow)
