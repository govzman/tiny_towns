from conftest import make_main_game
from game import Building, Game


def error_code(result):
    return result['error']['code']


def test_choose_resource_validation():
    game, (alice, bob) = make_main_game()
    assert error_code(game.choose_resource({'player_id': bob, 'resource': 'red'})) == 58
    assert error_code(game.choose_resource({'player_id': alice, 'resource': 'gold'})) == 57
    assert game.choose_resource({'player_id': alice, 'resource': 'red'})['success']
    assert error_code(game.choose_resource({'player_id': alice, 'resource': 'blue'})) == 65


def test_place_resource_validation():
    game, (alice, bob) = make_main_game()

    assert error_code(game.place_resource(
        {'player_id': alice, 'movement': {'0,0': 'red'}, 'turn_num': 1})) == 60

    game.choose_resource({'player_id': alice, 'resource': 'red'})
    assert error_code(game.place_resource(
        {'player_id': alice, 'movement': {'0,0': 'red'}, 'turn_num': 2})) == 59
    assert error_code(game.place_resource(
        {'player_id': alice, 'movement': {'0,0': 'blue'}, 'turn_num': 1})) == 61
    assert error_code(game.place_resource(
        {'player_id': alice, 'movement': {'4,0': 'red'}, 'turn_num': 1})) == 57
    assert error_code(game.place_resource(
        {'player_id': alice, 'movement': {}, 'turn_num': 1})) == 57

    assert game.place_resource(
        {'player_id': alice, 'movement': {'0,0': 'red'}, 'turn_num': 1})['success']
    assert error_code(game.place_resource(
        {'player_id': alice, 'movement': {'1,0': 'red'}, 'turn_num': 1})) == 62

    # Bob completes turn 1; turn advances and Bob becomes master
    assert game.place_resource(
        {'player_id': bob, 'movement': {'0,0': 'red'}, 'turn_num': 1})['success']
    assert game.turn == 2
    assert game.current_resource is False

    # Alice may not place on her occupied (0,0) in turn 2
    game.choose_resource({'player_id': bob, 'resource': 'blue'})
    assert error_code(game.place_resource(
        {'player_id': alice, 'movement': {'0,0': 'blue'}, 'turn_num': 2})) == 63


def test_place_building_validation():
    game, (alice, _) = make_main_game()
    board = game.players[alice]['board']
    # Cottage identity pattern shifted by (1, 1): yellow (2,1), red (1,2), blue (2,2)
    board.setCell('yellow', [2, 1])
    board.setCell('red', [1, 2])
    board.setCell('blue', [2, 2])

    cells = ['2,1', '1,2', '2,2']
    assert error_code(game.place_building(
        {'player_id': alice, 'cells': cells, 'x': 0, 'y': 0, 'name': 'Cottage'})) == 64
    assert error_code(game.place_building(
        {'player_id': alice, 'cells': ['2,1', '2,1'], 'x': 2, 'y': 1, 'name': 'Cottage'})) == 57
    assert error_code(game.place_building(
        {'player_id': alice, 'cells': ['2,1', '9,9', '2,2'], 'x': 2, 'y': 1, 'name': 'Cottage'})) == 57
    assert game.place_building(
        {'player_id': alice, 'cells': cells, 'x': 2, 'y': 2, 'name': 'Farm'}) == {'isSuccess': False}
    assert game.place_building(
        {'player_id': alice, 'cells': ['2,1', '1,2'], 'x': 2, 'y': 1, 'name': 'Cottage'}) == {'isSuccess': False}

    result = game.place_building(
        {'player_id': alice, 'cells': cells, 'x': 2, 'y': 2, 'name': 'Cottage'})
    assert result['isSuccess'] and result['building'] == 'Cottage'
    assert board.getCell([2, 2]) == 'Cottage'
    assert board.getCell([2, 1]) == 'empty'
    assert board.getCell([1, 2]) == 'empty'


def fill_board(board, value='red', skip=((3, 3),)):
    for x in range(4):
        for y in range(4):
            if (x, y) not in skip and board.getCell([x, y]) == 'empty':
                board.setCell(value, [x, y])


def test_full_game_reaches_end_game_with_scores():
    game, (alice, bob) = make_main_game()
    fill_board(game.players[alice]['board'])
    fill_board(game.players[bob]['board'])

    game.choose_resource({'player_id': alice, 'resource': 'blue'})
    result = game.place_resource({'player_id': alice, 'movement': {'3,3': 'blue'}, 'turn_num': 1})
    assert result['success'] and result['boardFull']
    assert game.stage == 'main_game'  # build window still open

    result = game.place_resource({'player_id': bob, 'movement': {'3,3': 'blue'}, 'turn_num': 1})
    assert result['boardFull']

    assert game.change_readiness({'player_id': alice, 'turn_num': 1})['success']
    assert game.stage == 'main_game'  # bob has not confirmed yet
    assert game.change_readiness({'player_id': bob, 'turn_num': 1})['success']
    assert game.stage == 'end_game'

    status = game.get_status({'player_id': alice})
    params = status['params']
    assert params['stage'] == 'end_game'
    assert len(params['scores']) == 2
    # identical boards -> points tie; Alice was master once, Bob never -> Bob wins
    assert params['win_reason'] == 'master_turns'
    assert params['winner'] == [1]
    assert params['scores'][0]['total'] == -16


def test_board_full_build_window_can_unfinish():
    game, (alice, bob) = make_main_game()
    board = game.players[alice]['board']
    fill_board(board)
    # last empty cell (3,3) will complete a Cottage: yellow (3,2), red (2,3), blue (3,3)
    board.setCell('yellow', [3, 2])
    board.setCell('red', [2, 3])

    game.choose_resource({'player_id': alice, 'resource': 'blue'})
    result = game.place_resource({'player_id': alice, 'movement': {'3,3': 'blue'}, 'turn_num': 1})
    assert result['boardFull']

    built = game.place_building({'player_id': alice, 'cells': ['3,2', '2,3', '3,3'],
                                 'x': 3, 'y': 3, 'name': 'Cottage'})
    assert built['isSuccess']
    assert game.change_readiness({'player_id': alice, 'turn_num': 1})['success']

    game.place_resource({'player_id': bob, 'movement': {'0,0': 'blue'}, 'turn_num': 1})
    assert game.turn == 2
    assert not game.players[alice]['isFinish']  # building freed cells again


def test_master_rotation_skips_finished_players():
    game, (alice, bob, carol) = make_main_game(('Alice', 'Bob', 'Carol'))
    fill_board(game.players[alice]['board'])

    assert game.master_id == alice
    game.choose_resource({'player_id': alice, 'resource': 'red'})
    assert game.place_resource({'player_id': alice, 'movement': {'3,3': 'red'}, 'turn_num': 1})['boardFull']
    game.change_readiness({'player_id': alice, 'turn_num': 1})
    game.place_resource({'player_id': bob, 'movement': {'0,0': 'red'}, 'turn_num': 1})
    game.place_resource({'player_id': carol, 'movement': {'0,0': 'red'}, 'turn_num': 1})

    assert game.players[alice]['isFinish']
    assert game.turn == 2
    assert game.master_id == bob

    # finished players cannot act
    assert error_code(game.place_resource(
        {'player_id': alice, 'movement': {'0,0': 'red'}, 'turn_num': 2})) == 66
    assert error_code(game.change_readiness({'player_id': alice, 'turn_num': 2})) == 66
    assert error_code(game.place_building(
        {'player_id': alice, 'cells': ['0,0'], 'x': 0, 'y': 0, 'name': 'Well'})) == 66

    # turn 2: bob and carol continue without alice
    game.choose_resource({'player_id': bob, 'resource': 'red'})
    game.place_resource({'player_id': bob, 'movement': {'0,1': 'red'}, 'turn_num': 2})
    game.place_resource({'player_id': carol, 'movement': {'0,1': 'red'}, 'turn_num': 2})
    assert game.turn == 3
    assert game.master_id == carol

    # turn 4 master wraps around, skipping finished alice
    game.choose_resource({'player_id': carol, 'resource': 'red'})
    game.place_resource({'player_id': bob, 'movement': {'0,2': 'red'}, 'turn_num': 3})
    game.place_resource({'player_id': carol, 'movement': {'0,2': 'red'}, 'turn_num': 3})
    assert game.master_id == bob


def test_ttl_disconnect_marks_finished_without_removal():
    from time import time
    game, (alice, bob) = make_main_game()
    game.players[alice]['last_response'] = time() - Game.TTL_SECONDS - 1

    status = game.get_status({'player_id': bob, 'stage': 'main_game'})
    assert len(game.players) == 2  # no deletion during main_game
    assert game.players[alice]['isFinish'] and game.players[alice]['disconnected']
    assert status['params']['isFinish'] == [True, False]
    # alice was master and had not declared -> master passes to bob
    assert game.master_id == bob

    # bob can finish the game alone
    game.choose_resource({'player_id': bob, 'resource': 'grey'})
    fill_board(game.players[bob]['board'])
    game.place_resource({'player_id': bob, 'movement': {'3,3': 'grey'}, 'turn_num': 1})
    game.change_readiness({'player_id': bob, 'turn_num': 1})
    assert game.stage == 'end_game'


def test_ttl_disconnect_of_all_players_ends_game():
    from time import time
    game, (alice, bob) = make_main_game()
    game.players[alice]['last_response'] = time() - Game.TTL_SECONDS - 1
    game.players[bob]['last_response'] = time() - Game.TTL_SECONDS - 1
    game.checkTTL()
    assert game.stage == 'end_game'
    assert game.final_scores is not None


def test_restart_resets_everything():
    game, (alice, _) = make_main_game()
    old_game_id = game.game_id
    game.choose_resource({'player_id': alice, 'resource': 'red'})
    result = game.restart_game()
    assert result['status'] == 'ok'
    assert game.stage == 'lobby'
    assert game.players == {}
    assert game.turn == 1
    assert game.events == []
    assert game.current_resource is False
    assert game.master_id is None
    assert game.game_id != old_game_id


def test_shed_can_be_built_on_any_empty_cell():
    game, (alice, _) = make_main_game()
    # force Shed to be this game's grey building
    game.buildingRow.buildings = [
        building if building.type != 'grey' else Building('Shed', 'grey', 2)
        for building in game.buildingRow.buildings
    ]
    board = game.players[alice]['board']
    board.setCell('brown', [0, 0])
    board.setCell('grey', [0, 1])

    result = game.place_building({'player_id': alice, 'cells': ['0,0', '0,1'],
                                  'x': 3, 'y': 3, 'name': 'Shed'})
    assert result['isSuccess']
    assert board.getCell([3, 3]) == 'Shed'
    assert board.getCell([0, 0]) == 'empty' and board.getCell([0, 1]) == 'empty'

    # the free-placement target must still be an empty square
    board.setCell('brown', [0, 0])
    board.setCell('grey', [0, 1])
    assert error_code(game.place_building({'player_id': alice, 'cells': ['0,0', '0,1'],
                                           'x': 3, 'y': 3, 'name': 'Shed'})) == 64


def test_duplicate_nickname_rejected():
    game = Game()
    game.get_status({'nickname': 'Alice'})
    assert error_code(game.get_status({'nickname': 'Alice'})) == 5


def test_wrong_stage_rejections():
    from game import Game
    game = Game()
    player_id = game.get_status({'nickname': 'Solo'})['player_id']
    assert error_code(game.choose_resource({'player_id': player_id, 'resource': 'red'})) == 56
    assert error_code(game.place_resource(
        {'player_id': player_id, 'movement': {'0,0': 'red'}, 'turn_num': 1})) == 56
    assert error_code(game.place_building(
        {'player_id': player_id, 'cells': ['0,0'], 'x': 0, 'y': 0, 'name': 'Well'})) == 56
    assert error_code(game.set_monument({'player_id': player_id, 'monument': 'Star'})) == 56
