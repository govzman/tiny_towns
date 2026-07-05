from game import Game


def join(game, nickname):
    return game.get_status({'nickname': nickname})['player_id']


def make_main_game(nicknames=('Alice', 'Bob')):
    """Drive a fresh Game through lobby and monument choice into main_game.

    Returns (game, player_ids) with player_ids in join order — the first
    player is the Master Builder of turn 1.
    """
    game = Game()
    ids = [join(game, nickname) for nickname in nicknames]
    for player_id in ids:
        game.get_status({'player_id': player_id, 'ready': True, 'stage': 'lobby'})
    assert game.stage == 'choose_monument'
    for player_id in ids:
        monument = game.players[player_id]['monuments'][0]
        game.set_monument({'player_id': player_id, 'stage': 'choose_monument', 'monument': monument})
        game.get_status({'player_id': player_id, 'ready': True, 'stage': 'choose_monument'})
    assert game.stage == 'main_game'
    return game, ids
