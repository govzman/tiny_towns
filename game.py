from random import randint, shuffle
from time import time
import uuid

import util 

class Game():
    def __init__(self) -> None: # , players_count=2, players_names=['player1', 'player2']
        self.stage = 'lobby' # 'lobby', 'choose_monument', 'main_game', 'end_game'
        self.turn = 1
        self.current_resource = False
        self.game_id = str(uuid.uuid4())
        self.players = {}
        self.events = []
        self.monuments = ['Arch_Guild', 'Arch_Age', 'Bar_Cast', # ['Architect`s Guild', 'Archive of the Second Age', 'Barrett Castle', 
        'Cath_Cat', 'Fort_Iron', 'Grove_Un', 'Mand_Pal', 'Opal_Wat', # 'Cathedral of Caterina', 'Fort Ironweed', 'Grove University', 'Mandras Palace', 'Opaleyes Watch', 
        'Shr_Tree', 'Sil_For', 'Star', 'Stat_Bond', 'Rodina', 'Sky_Bath', 'Crescent'] # 'Shrine of the Elder Tree', 'Silva Forum', 'The Starloom', 'Statue of the Bondmaker']
        
        self.buildingRow = BuildingRow()
        self.buildingRow.generate()
        self.board = Board()
        

    def get_status(self, params : dict) -> dict:
        if 'player_id' not in params:
            player_id = str(uuid.uuid4())
            if self.stage == 'lobby':
                if 'nickname' in params: 
                    self.players[player_id] = {'nickname': params['nickname'], 'board': Board(), 'ready': False, 'isFinish': False}
                    return {
                        'stage': self.stage,
                        'player_id': player_id
                        }
                else:
                    return util.error(2, 'miss nickname')
            else:
                return util.error(3, 'game is already run')

        player_id = params['player_id']
        if player_id not in self.players:
            return util.error(1, 'bad id')

        self.players[player_id]['last_response'] = time()

        if self.stage != 'main_game':
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
                'player': { 'monuments': self.players[player_id]['monuments']},
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
            MasterBuilder = ((self.turn - 1) % len(self.players))
            return self.res({
                'stage': self.stage,
                'player': {
                    'monument': self.players[player_id]['monument']
                },
                'players': list(map(lambda x: self.players[x]['nickname'], self.players.keys())),
                'bulidingRow': self.buildingRow.getRow(),
                'isReady': list(map(lambda x: self.players[x]['ready'], self.players.keys())),
                'events': self.events[-min(5, len(self.events)):],
                'MasterBuilder': MasterBuilder,
                'currentResource': self.current_resource,
                'playersBoards': {list(self.players.keys()).index(key): self.players[key]['board'].getBoard(mode='server') for key in self.players} 
            })

        self.checkTTL()
        return self.res({
            'stage': self.stage,
            'players': list(map(lambda x: self.players[x]['nickname'], self.players.keys())), 
            'isReady': list(map(lambda x: self.players[x]['ready'], self.players.keys())),
            })

    def restart_game(self, params : dict = {}) -> dict:        
        self.players = {}
        self.stage = 'lobby'        
        return {'status':'ok', 'params':{'stage': 'lobby' }}
        
    def log_out(self, params : dict) -> dict:
        if params['player_id'] in self.players:
            del self.players[params['player_id']]
            return {'status' : 'ok'}
        else:
            print(self.players)
            return {'error': {'code': 55, 'msg': 'bad id'}}

    def set_monument(self, params : dict) -> dict:
        if params['player_id'] not in self.players:
            return {'error': {'code': 55, 'msg': 'bad id'}}
        
        if self.stage != 'choose_monument':
            return {'error': {'code': 56, 'msg': 'Wrong game stage'}}

        if 'monument' in params:
            if params['monument'] in self.players[params['player_id']]['monuments']:
                self.players[params['player_id']]['monument'] = params['monument']
                return {'status' : 'ok'}
        else:
            print(params, self.players[params['player_id']])
            return {'error': {'code': 57, 'msg': 'bad request'}}

    def find_patterns(self, params : dict) -> dict:
        if params['player_id'] not in self.players:
            return {'error': {'code': 55, 'msg': 'bad id'}}
        if self.stage != 'main_game':
            return {'error': {'code': 56, 'msg': 'Wrong game stage'}}

        if 'building' in params:
            building = params['building']
        else:
            print(params, self.players[params['player_id']])
            return {'error': {'code': 57, 'msg': 'bad request'}}

        # check patterns
        found_patterns = self.players[params['player_id']]['board'].find_patterns(building)

        if found_patterns == []:
            return {'isPattern': False}

        return {'isPattern': True, 'found_patterns': found_patterns}


    def place_building(self, params : dict) -> dict:
        if params['player_id'] not in self.players:
            return {'error': {'code': 55, 'msg': 'bad id'}}
        if self.stage != 'main_game':
            return {'error': {'code': 56, 'msg': 'Wrong game stage'}}

        if 'cells' in params:
            cells = params['cells']
        else:
            print(params, self.players[params['player_id']])
            return {'error': {'code': 57, 'msg': 'bad request'}}

        cords = {}
        for cell in cells:
            cords[cell.replace(',', ', ')] = self.players[params['player_id']]['board'].getCell(list(map(int, cell.split(','))))

        # check patterns
        answer = self.players[params['player_id']]['board'].check_patterns(cords, self.buildingRow)
        if answer != params['name']:
            return {'isSuccess': False}
        
        for cell in cells:
            self.players[params['player_id']]['board'].setCell('empty', list(map(int, cell.split(','))))
        
        self.players[params['player_id']]['board'].setCell(answer, [params['x'], params['y']])
        
        self.events.append(f"{self.players[params['player_id']]['nickname']} построил {params['name']}")

        return {'isSuccess': True, 'building': answer}

    def place_resource(self, params : dict) -> dict:
        if params['player_id'] not in self.players:
            return {'error': {'code': 55, 'msg': 'bad id'}}
        if self.stage != 'main_game':
            return {'error': {'code': 56, 'msg': 'Wrong game stage'}}

        if 'movement' in params:
            if len(params['movement']) == 1:
                x, y = map(int, list(params['movement'].keys())[0].split(','))
                self.players[params['player_id']]['board'].setCell(list(params['movement'].values())[0], [x, y])
                if params['turn_num'] == self.turn:
                    self.players[params['player_id']]['ready'] = True
                else:
                    return {'error': {'code': 59, 'msg': 'wrong turn'}}
                
                self.events.append(f"{self.players[params['player_id']]['nickname']} поставил(а) ресурс")
                if all(list(map(lambda x: self.players[x]['ready'], self.players.keys()))):
                    self.turn += 1
                    for key in self.players.keys():
                        self.players[key]['ready'] = False
                    self.current_resource = False
                    self.events.append('Следующий ход!')
                return {'success': True, 'cords': params['movement']}
            else:
                return {'error': {'code': 57, 'msg': 'bad request'}}
        else:
            return {'error': {'code': 57, 'msg': 'bad request'}}

    def choose_resource(self, params : dict) -> dict:
        if params['player_id'] not in self.players:
            return {'error': {'code': 55, 'msg': 'bad id'}}
        if self.stage != 'main_game':
            return {'error': {'code': 56, 'msg': 'Wrong game stage'}}
        if params['player_id'] not in self.players:
            return {'error': {'code': 55, 'msg': 'bad id'}}

        isMasterBuilder = ((self.turn - 1) % len(self.players)) == (list(self.players.keys()).index(params['player_id']))
        if not isMasterBuilder:
            return {'error': {'code': 58, 'msg': 'Wrong player choosed resource'}}
        
        self.current_resource = params['resource']
        return {'success': True, 'currentResource': params['resource']}

    def is_game_finished(self) -> bool:
        if self.stage == 'end_game': return True
        if all([lambda player: player['isFinish'] for player in self.players]): 
            self.stage = 'end_game'
            return True 
        return False

    # def place_building(self, params):


    def checkTTL(self):
        try:
            keys = self.players.keys()
            for player_id in keys:
                if 'last_response' in self.players[player_id]:
                    if time() - self.players[player_id]['last_response'] > 10:
                        del self.players[player_id]
        except:
            pass

    def setParam(self, paramName : str, params : dict) -> None:
        if (paramName in params) and ('stage' in params and self.stage == params['stage']):
            self.players[params['player_id']][paramName] = params[paramName]
        else:
            # TODO() aux.error(2, 'miss ' + paramName)
            pass

    def res(self, params : dict) -> dict:
        return {
            'game_id': self.game_id, 
            #'game_stage': self.game_stage,
            'turn': self.turn, 
            'params': params
        }


class Resource():
    def __init__(self, name : str) -> None:
        self.name = name

class ResourceOnBoard(Resource):
    def __init__(self, name : str) -> None:
        super().__init__(name)

class Building():
    with open('buildings_patterns.txt') as file:
        lines = file.readlines()
        buildings_patterns = {}
        for i in range(len(lines)):
            buliding, pattern = lines[i].split(' / ')
            buildings_patterns[buliding] = eval(pattern)

    def __init__(self, name : str = 'Cottage', type : str ='blue', id : int = 1):
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

    def add_all_rotations(self) -> None:
        size_x = 1
        size_y = 1
        for cell in self.patterns[0]:
            x, y = map(int, cell.split(', '))
            size_x, size_y = max(size_x, x + 1), max(size_y, y + 1)

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
        for _ in range(3):
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
        for _ in range(3):
            turn90 = {} # right 
            for cell in self.patterns[-1]:
                x, y = map(int, cell.split(', '))
                turn90[f'{size_y - 1 - y}, {x}'] = self.patterns[-1][cell]
            self.patterns.append(turn90)
        

class BuildingRow():
    def __init__(self) -> None:
        self.buildings = []

    # generate row
    def generate(self) -> None: 
        self.buildings = []
        self.buildings.append(Building('Cottage', 'blue', 0))
        builds = {'red': ['Farm', 'Granary', 'Greenhouse', 'Orchard'], 'grey': ['Fountain', 'Millstone', 'Shed', 'Well'], 'orange': ['Abbey', 'Chapel', 'Cloister', 'Temple'], 'yellow': ['Bakery', 'Market', 'Tailor', 'Theater'], 'black': ['Bank', 'Factory', 'Trading Post', 'Warehouse'], 'green': ['Almshouse', 'Feast Hall', 'Inn', 'Tavern']}
        for type in builds.keys():
            id = randint(0, 3)
            self.buildings.append(Building(builds[type][id], type, id))

    def getRow(self) -> list:
        return list(map(lambda x: f"{x.type}:{x.name}", self.buildings))

    def __str__(self) -> str:
        return ', '.join(list(map(lambda x: x.name, self.buildings)))

class BuildingOnBoard():
    def __init__(self, name) -> None:
        super().__init__(name)

class Cell():
    def __init__(self, type : str = 'empty'):
        self.type = type

    def set(self, type : str) -> None:
        self.type = type

    def get(self) -> str:
        return self.type

class Board():
    def __init__(self) -> None:
        self.board = [
            [Cell(), Cell(), Cell(), Cell()],
            [Cell(), Cell(), Cell(), Cell()], 
            [Cell(), Cell(), Cell(), Cell()], 
            [Cell(), Cell(), Cell(), Cell()]
            ]

    def getCell(self, cord : list) -> list:
        return self.board[cord[1]][cord[0]].get()

    def setCell(self, build : str, cord : list) -> None: 
        self.board[cord[1]][cord[0]].set(build)

    def getBoard(self, mode : str = '') -> list:
        board = [[self.board[j][i].get() for i in range(4)] for j in range(4)]
        if mode == 'server':
            builds = {'Cottage': 'blue', 'Farm': 'red', 'Granary': 'red', 'Greenhouse': 'red', 'Orchard': 'red', 'Fountain': 'grey', 'Millstone': 'grey', 'Shed': 'grey', 'Well': 'grey', 'Abbey': 'orange', 'Chapel': 'orange', 'Cloister': 'orange', 'Temple': 'orange', 'Bakery': 'yellow', 'Market': 'yellow', 'Tailor': 'yellow', 'Theater': 'yellow',  'Bank': 'black', 'Factory': 'black', 'Trading Post': 'black', 'Warehouse': 'black', 'Almshouse': 'green', 'Feast Hall': 'green', 'Inn': 'green', 'Tavern': 'green'}  
            for i in range(4):
                for j in range(4):
                    if board[i][j] in builds:
                        board[i][j] = builds[board[i][j]] + '_house'
        return board

    def setBoard(self, board : list) -> None:
        self.board = board

    def __str__(self) -> str:
        string = ''
        for i in self.board:
            string += '\t'.join(list(map(lambda x: x.get(), i))) + '\n'
        return string
    
    def check_patterns(self, cords : dict, building_row : list) -> str:
        min_cord_x = min(map(lambda x: int(x.split(', ')[0]), cords.keys()))
        min_cord_y = min(map(lambda x: int(x.split(', ')[1]), cords.keys()))
        cords = {f"{int(cord.split(', ')[0]) - min_cord_x}, {int(cord.split(', ')[1]) - min_cord_y}": cords[cord] for cord in cords}
        isFound = False
        for building in building_row.buildings:
            if cords in building.patterns:
                isFound = True
                return building.name
        if not isFound:
            return None

    def find_patterns(self, building : str) -> list:
        found_patterns = []
        
        building_patterns = Building(building).patterns

        for pattern in building_patterns:
            max_cord_x = max(map(lambda x: int(x.split(', ')[0]), pattern.keys()))
            max_cord_y = max(map(lambda x: int(x.split(', ')[1]), pattern.keys()))
            for x in range(4 - max_cord_x):
                for y in range(4 - max_cord_y):
                    isPattern = True
                    for cell in pattern:
                        cell_x, cell_y = map(int, cell.split(', '))
                        if pattern[cell] != self.board[cell_x + x][cell_y + y].get():
                            isPattern = False
                            break
                    if isPattern:
                        new_pattern = {f"{int(cell.split(', ')[0]) + x}, {int(cell.split(', ')[1]) + y}": pattern[cell] for cell in pattern}
                        if new_pattern not in found_patterns:
                            found_patterns.append(new_pattern)
        return found_patterns    



# class Player():
#     def __init__(self, nickname):
#         self.nickname = nickname
#         self.id = 1
#         self.board = Board()
#         self.isReady = False
#         self.monument_id = 0

#     def getBoard(self):
#         self.board.print()



if __name__ == '__main__':
    # game = Game()
    board = Board()
    board.setBoard([
            [Cell(), Cell('yellow'), Cell(), Cell()],
            [Cell('red'), Cell('blue'), Cell('red'), Cell()], 
            [Cell(), Cell('yellow'), Cell(), Cell()], 
            [Cell(), Cell(), Cell(), Cell()]
            ])
