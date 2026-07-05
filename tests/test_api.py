import json

import pytest

import app as app_module
from game import Game


@pytest.fixture
def client():
    app_module.myGame = Game()  # fresh game per test
    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as client:
        yield client


def call(client, method, params=None):
    response = client.post('/api', json={'method': method, 'params': params or {}})
    assert response.status_code == 200
    return json.loads(response.data)


def test_unknown_method_is_rejected(client):
    assert call(client, 'is_game_finished')['error']['code'] == 100
    assert call(client, 'checkTTL')['error']['code'] == 100


def test_missing_method_is_rejected(client):
    response = client.post('/api', json={'params': {}})
    assert json.loads(response.data)['error']['code'] == 100


def test_every_method_returns_json_for_bad_id(client):
    for method in ['log_out', 'set_monument', 'place_resource', 'choose_resource',
                   'place_building', 'find_patterns']:
        result = call(client, method, {'player_id': 'no-such-id'})
        assert result['error']['code'] in (55, 56), method


def test_lobby_join_and_status(client):
    joined = call(client, 'get_status', {'nickname': 'Alice'})
    assert joined['stage'] == 'lobby'
    player_id = joined['player_id']

    status = call(client, 'get_status', {'player_id': player_id, 'ready': False, 'stage': 'lobby'})
    assert status['params']['stage'] == 'lobby'
    assert status['params']['players'] == ['Alice']


def test_get_status_without_nickname_is_rejected(client):
    assert call(client, 'get_status', {})['error']['code'] == 2


def test_restart_game(client):
    assert call(client, 'restart_game')['status'] == 'ok'


def test_full_solo_game_over_http(client):
    player_id = call(client, 'get_status', {'nickname': 'Solo'})['player_id']

    status = call(client, 'get_status', {'player_id': player_id, 'ready': True, 'stage': 'lobby'})
    assert status['params']['stage'] == 'choose_monument'
    monument = status['params']['player']['monuments'][0]
    call(client, 'set_monument', {'player_id': player_id, 'stage': 'choose_monument', 'monument': monument})
    call(client, 'get_status', {'player_id': player_id, 'ready': True, 'stage': 'choose_monument'})

    status = call(client, 'get_status', {'player_id': player_id, 'stage': 'main_game'})
    assert status['params']['stage'] == 'main_game'
    assert status['params']['MasterBuilder'] == 0

    for turn in range(1, 17):
        assert call(client, 'choose_resource',
                    {'player_id': player_id, 'resource': 'red'}).get('success')
        x, y = (turn - 1) % 4, (turn - 1) // 4
        result = call(client, 'place_resource',
                      {'player_id': player_id, 'movement': {f'{x},{y}': 'red'}, 'turn_num': turn})
        assert result.get('success'), result

    assert result['boardFull']
    assert call(client, 'change_readiness', {'player_id': player_id, 'turn_num': 16}).get('success')

    status = call(client, 'get_status', {'player_id': player_id})
    params = status['params']
    assert params['stage'] == 'end_game'
    assert params['winner'] == [0]
    assert params['scores'][0]['total'] == -16  # 16 unbuilt squares
    assert params['scores'][0]['board'][0][0] == 'red'
