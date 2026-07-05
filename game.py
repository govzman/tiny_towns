import os.path
from random import randint, shuffle
from time import time
import uuid

import scoring
import util

class Game():
    TTL_SECONDS = 60
    RESOURCES = ['red', 'blue', 'brown', 'yellow', 'grey']

    def __init__(self) -> None: # , players_count=2, players_names=['player1', 'player2']
        self._reset()

    def _reset(self) -> None:
        self.stage = 'lobby' # 'lobby', 'choose_monument', 'main_game', 'end_game'
        self.turn = 1
        self.current_resource = False
        self.game_id = str(uuid.uuid4())
        self.players = {}
        self.events = []
        self.master_id = None
        self.final_scores = None
        self.monuments = ['Arch_Guild', 'Arch_Age', 'Bar_Cast', # ['Architect`s Guild', 'Archive of the Second Age', 'Barrett Castle',
        'Cath_Cat', 'Fort_Iron', 'Grove_Un', 'Mand_Pal', 'Opal_Wat', # 'Cathedral of Caterina', 'Fort Ironweed', 'Grove University', 'Mandras Palace', 'Opaleyes Watch',
        'Shr_Tree', 'Sil_For', 'Star', 'Stat_Bond', 'Rodina', 'Sky_Bath', 'Crescent'] # 'Shrine of the Elder Tree', 'Silva Forum', 'The Starloom', 'Statue of the Bondmaker']

        self.buildingRow = BuildingRow()
        self.buildingRow.generate()


    def get_status(self, params : dict) -> dict:
        if 'player_id' not in params:
            player_id = str(uuid.uuid4())
            if self.stage == 'lobby':
                if 'nickname' not in params:
                    return util.error(2, 'miss nickname')
                nicknames = [player['nickname'] for player in self.players.values()]
                if params['nickname'] in nicknames:
                    return util.error(5, 'nickname is already taken')
                self.players[player_id] = {'nickname': params['nickname'], 'board': Board(),
                    'ready': False, 'isFinish': False, 'placed': False,
                    'master_turns': 0, 'disconnected': False}
                return {
                    'stage': self.stage,
                    'player_id': player_id
                    }
            else:
                return util.error(3, 'game is already run')

        player_id = params['player_id']
        if player_id not in self.players:
            return util.error(1, 'bad id')

        self.players[player_id]['last_response'] = time()
        self.checkTTL()

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
                    self.players[ids]['placed'] = False
                self._assign_master(list(self.players.keys())[0])

            return out

        if self.stage == 'main_game':
            ids = list(self.players.keys())
            MasterBuilder = ids.index(self.master_id) if self.master_id in self.players else 0
            return self.res({
                'stage': self.stage,
                'player': {
                    'monument': self.players[player_id].get('monument')
                },
                'players': list(map(lambda x: self.players[x]['nickname'], self.players.keys())),
                'bulidingRow': self.buildingRow.getRow(),
                'isReady': list(map(lambda x: self.players[x]['ready'], self.players.keys())),
                'isFinish': list(map(lambda x: self.players[x]['isFinish'], self.players.keys())),
                'events': self.events[-min(5, len(self.events)):],
                'MasterBuilder': MasterBuilder,
                'currentResource': self.current_resource,
                'playersBoards': {list(self.players.keys()).index(key): self.players[key]['board'].getBoard(mode='server') for key in self.players}
            })

        if self.stage == 'end_game':
            payload = {
                'stage': self.stage,
                'players': list(map(lambda x: self.players[x]['nickname'], self.players.keys())),
            }
            payload.update(self.final_scores)
            return self.res(payload)

        return self.res({
            'stage': self.stage,
            'players': list(map(lambda x: self.players[x]['nickname'], self.players.keys())),
            'isReady': list(map(lambda x: self.players[x]['ready'], self.players.keys())),
            })

    def restart_game(self, params : dict = {}) -> dict:
        self._reset()
        return {'status':'ok', 'params':{'stage': 'lobby' }}
        
    def log_out(self, params : dict) -> dict:
        if params.get('player_id') in self.players:
            del self.players[params['player_id']]
            return {'status' : 'ok'}
        else:
            return util.error(55, 'bad id')

    def set_monument(self, params : dict) -> dict:
        player = self.players.get(params.get('player_id'))
        if player is None:
            return util.error(55, 'bad id')

        if self.stage != 'choose_monument':
            return util.error(56, 'Wrong game stage')

        if params.get('monument') not in player['monuments']:
            return util.error(57, 'bad request')

        player['monument'] = params['monument']
        return {'status' : 'ok'}

    def find_patterns(self, params : dict) -> dict:
        player = self.players.get(params.get('player_id'))
        if player is None:
            return util.error(55, 'bad id')
        if self.stage != 'main_game':
            return util.error(56, 'Wrong game stage')

        building = params.get('building')
        if building not in Building.buildings_patterns:
            return util.error(57, 'bad request')

        found_patterns = player['board'].find_patterns(building)

        if found_patterns == []:
            return {'isPattern': False}

        return {'isPattern': True, 'found_patterns': found_patterns}


    def place_building(self, params : dict) -> dict:
        player = self.players.get(params.get('player_id'))
        if player is None:
            return util.error(55, 'bad id')
        if self.stage != 'main_game':
            return util.error(56, 'Wrong game stage')

        if player['isFinish']:
            return util.error(66, 'town is complete')

        cells = params.get('cells')
        if not isinstance(cells, list) or not cells or 'x' not in params or 'y' not in params:
            return util.error(57, 'bad request')

        try:
            coords = [tuple(map(int, cell.split(','))) for cell in cells]
            x, y = int(params['x']), int(params['y'])
        except (ValueError, AttributeError):
            return util.error(57, 'bad request')

        if len(set(coords)) != len(coords):
            return util.error(57, 'bad request')
        if any(not (0 <= cx <= 3 and 0 <= cy <= 3) for cx, cy in [(x, y)] + coords):
            return util.error(57, 'bad request')

        board = player['board']
        cords = {f'{cx}, {cy}': board.getCell([cx, cy]) for cx, cy in coords}

        answer = board.check_patterns(cords, self.buildingRow)
        if answer is None or answer != params.get('name'):
            return {'isSuccess': False}

        if (x, y) not in coords:
            # Shed's card effect: it may be constructed on any empty square
            if not (answer == 'Shed' and board.getCell([x, y]) == 'empty'):
                return util.error(64, 'building must be placed on one of the used cells')

        for cx, cy in coords:
            board.setCell('empty', [cx, cy])

        board.setCell(answer, [x, y])

        self.events.append(f"{player['nickname']} built {answer}")

        return {'isSuccess': True, 'building': answer}

    def place_resource(self, params : dict) -> dict:
        player = self.players.get(params.get('player_id'))
        if player is None:
            return util.error(55, 'bad id')
        if self.stage != 'main_game':
            return util.error(56, 'Wrong game stage')

        if player['isFinish']:
            return util.error(66, 'town is complete')

        movement = params.get('movement')
        if not isinstance(movement, dict) or len(movement) != 1:
            return util.error(57, 'bad request')
        if params.get('turn_num') != self.turn:
            return util.error(59, 'wrong turn')
        if not self.current_resource:
            return util.error(60, 'no resource declared yet')
        if player['placed']:
            return util.error(62, 'resource already placed this turn')

        cell, resource = list(movement.items())[0]
        try:
            x, y = map(int, cell.split(','))
        except (ValueError, AttributeError):
            return util.error(57, 'bad request')
        if not (0 <= x <= 3 and 0 <= y <= 3):
            return util.error(57, 'bad request')
        if resource != self.current_resource:
            return util.error(61, 'wrong resource')
        if player['board'].getCell([x, y]) != 'empty':
            return util.error(63, 'cell is occupied')

        player['board'].setCell(self.current_resource, [x, y])
        player['placed'] = True
        self.events.append(f"{player['nickname']} placed a resource")

        board_full = player['board'].is_full()
        if board_full:
            # Official build window: the player may still construct buildings
            # (freeing cells) before confirming the turn via change_readiness.
            pass
        else:
            player['ready'] = True
            self._advance_turn_if_ready()
        return {'success': True, 'cords': movement, 'boardFull': board_full}

    def change_readiness(self, params : dict) -> dict:
        player = self.players.get(params.get('player_id'))
        if player is None:
            return util.error(55, 'bad id')
        if self.stage != 'main_game':
            return util.error(56, 'Wrong game stage')
        if player['isFinish']:
            return util.error(66, 'town is complete')
        if params.get('turn_num') != self.turn:
            return util.error(59, 'wrong turn')
        if not player['placed']:
            return util.error(67, 'place a resource first')

        player['ready'] = True
        self._advance_turn_if_ready()
        return {'success': True}

    def choose_resource(self, params : dict) -> dict:
        player = self.players.get(params.get('player_id'))
        if player is None:
            return util.error(55, 'bad id')
        if self.stage != 'main_game':
            return util.error(56, 'Wrong game stage')
        if params.get('resource') not in Game.RESOURCES:
            return util.error(57, 'bad request')

        if params['player_id'] != self.master_id:
            return util.error(58, 'Wrong player choosed resource')
        if self.current_resource:
            return util.error(65, 'resource already declared this turn')

        self.current_resource = params['resource']
        self.events.append(f"{player['nickname']} declared {params['resource']}")
        return {'success': True, 'currentResource': params['resource']}

    def _active_players(self) -> list:
        return [player_id for player_id, player in self.players.items() if not player['isFinish']]

    def _assign_master(self, player_id : str) -> None:
        if player_id is None:
            return
        self.master_id = player_id
        self.players[player_id]['master_turns'] += 1
        self.events.append(f"{self.players[player_id]['nickname']} is the Master Builder")

    def _next_master(self) -> str:
        ids = list(self.players.keys())
        start = ids.index(self.master_id) + 1 if self.master_id in self.players else 0
        for offset in range(len(ids)):
            candidate = ids[(start + offset) % len(ids)]
            if not self.players[candidate]['isFinish']:
                return candidate
        return None

    def _advance_turn_if_ready(self) -> None:
        if self.stage != 'main_game':
            return
        active = self._active_players()
        if not active:
            self._finish_game()
            return
        if not all(self.players[player_id]['ready'] for player_id in active):
            return

        # A town that is completely full when the turn ends is finished for good.
        for player_id in active:
            player = self.players[player_id]
            if player['board'].is_full():
                player['isFinish'] = True
                self.events.append(f"{player['nickname']} finished their town!")

        self.current_resource = False
        for player in self.players.values():
            player['ready'] = False
            player['placed'] = False

        if not self._active_players():
            self._finish_game()
            return

        self.turn += 1
        self._assign_master(self._next_master())

    def _finish_game(self) -> None:
        self.stage = 'end_game'
        self.final_scores = scoring.compute_final_scores([
            {'nickname': player['nickname'], 'grid': player['board'].getBoard(),
             'master_turns': player['master_turns']}
            for player in self.players.values()
        ])
        self.events.append('Game over!')

    def checkTTL(self) -> None:
        now = time()
        for player_id, player in list(self.players.items()):
            last = player.get('last_response')
            if last is None or now - last <= self.TTL_SECONDS:
                continue
            if self.stage == 'main_game':
                if not player['isFinish']:
                    player['isFinish'] = True
                    player['disconnected'] = True
                    self.events.append(f"{player['nickname']} disconnected")
            elif self.stage == 'end_game':
                pass  # keep everyone visible on the results screen
            else:
                del self.players[player_id]

        if self.stage == 'main_game' and self.players:
            master = self.players.get(self.master_id)
            if (master is None or master['isFinish']) and not self.current_resource:
                self._assign_master(self._next_master())
            self._advance_turn_if_ready()

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
    with open(os.path.join(os.path.dirname(__file__), 'buildings_patterns.txt')) as file:
        lines = file.readlines()
        buildings_patterns = {}
        for i in range(len(lines)):
            buliding, pattern = lines[i].split(' / ')
            buildings_patterns[buliding] = eval(pattern)

    def __init__(self, name : str = 'Cottage', type : str ='blue', id : int = 1):
        self.name = name
        self.type = type
        self.id = id
        if self.name not in Building.buildings_patterns:
            raise KeyError(f'Unknown building {self.name!r}: not in buildings_patterns.txt')
        self.patterns = [Building.buildings_patterns[self.name]]
        self.add_all_rotations()

    def add_all_rotations(self) -> None:
        # Patterns from buildings_patterns.txt are origin-normalized (min x = min y = 0),
        # and both transforms below preserve that.
        def rotate90(pattern : dict) -> dict:
            height = max(int(cell.split(', ')[1]) for cell in pattern) + 1
            return {f"{height - 1 - int(cell.split(', ')[1])}, {cell.split(', ')[0]}": value
                    for cell, value in pattern.items()}

        def mirror(pattern : dict) -> dict:
            width = max(int(cell.split(', ')[0]) for cell in pattern) + 1
            return {f"{width - 1 - int(cell.split(', ')[0])}, {cell.split(', ')[1]}": value
                    for cell, value in pattern.items()}

        variants = []
        for base in (self.patterns[0], mirror(self.patterns[0])):
            pattern = base
            for _ in range(4):
                if pattern not in variants:
                    variants.append(pattern)
                pattern = rotate90(pattern)
        self.patterns = variants


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

    def is_full(self) -> bool:
        return all(cell.get() != 'empty' for row in self.board for cell in row)

    def getBoard(self, mode : str = '') -> list:
        board = [[self.board[j][i].get() for i in range(4)] for j in range(4)]
        if mode == 'server':
            return scoring.as_color_grid(board)
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
                        if pattern[cell] != self.board[cell_y + y][cell_x + x].get():
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
