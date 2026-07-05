from scoring import compute_final_scores, optimal_feeding, score_board


def make_grid(placements):
    grid = [['empty'] * 4 for _ in range(4)]
    for (x, y), value in placements.items():
        grid[y][x] = value
    return grid


def points_for(result, building):
    for item in result['breakdown']:
        if item['building'] == building:
            return item['points']
    return 0


# --- feeding ---------------------------------------------------------------

def test_no_feeder_no_fed_cottages():
    result = score_board(make_grid({(0, 0): 'Cottage', (1, 0): 'Cottage'}))
    assert result['fed_cottages'] == []
    assert points_for(result, 'Cottage') == 0


def test_farm_feeds_any_four_cottages():
    grid = make_grid({(3, 3): 'Farm', (0, 0): 'Cottage', (1, 0): 'Cottage',
                      (2, 0): 'Cottage', (3, 0): 'Cottage', (0, 1): 'Cottage'})
    fed, split = optimal_feeding(grid)
    assert len(fed) == 4
    assert split['Cottage'] == 12


def test_granary_feeds_surrounding_incl_diagonals():
    grid = make_grid({(1, 1): 'Granary', (0, 0): 'Cottage',  # diagonal -> fed
                      (2, 2): 'Cottage',                     # diagonal -> fed
                      (3, 3): 'Cottage'})                    # out of reach
    fed, _ = optimal_feeding(grid)
    assert fed == {(0, 0), (2, 2)}


def test_orchard_feeds_row_and_column():
    grid = make_grid({(0, 0): 'Orchard', (3, 0): 'Cottage',  # same row -> fed
                      (0, 3): 'Cottage',                     # same column -> fed
                      (1, 1): 'Cottage'})                    # neither -> unfed
    fed, _ = optimal_feeding(grid)
    assert fed == {(3, 0), (0, 3)}


def test_greenhouse_picks_best_component():
    # One contiguous pair next to nothing vs a triple: greenhouse takes the triple.
    grid = make_grid({(0, 0): 'Greenhouse',
                      (0, 2): 'Cottage', (0, 3): 'Cottage',
                      (3, 0): 'Cottage', (3, 1): 'Cottage', (3, 2): 'Cottage'})
    fed, split = optimal_feeding(grid)
    assert fed == {(3, 0), (3, 1), (3, 2)}
    assert split['Cottage'] == 9


def test_farm_picks_temple_adjacent_cottages():
    # 6 cottages, farm capacity 4: any 4 give 12 cottage points, but only a
    # pick containing the two temple-adjacent ones earns the temple's 4.
    grid = make_grid({(1, 1): 'Temple', (2, 2): 'Farm',
                      (1, 0): 'Cottage', (0, 1): 'Cottage',
                      (3, 0): 'Cottage', (3, 1): 'Cottage',
                      (3, 2): 'Cottage', (3, 3): 'Cottage'})
    fed, split = optimal_feeding(grid)
    assert (1, 0) in fed and (0, 1) in fed
    assert split == {'Cottage': 12, 'Chapel': 0, 'Temple': 4}


def test_chapel_scores_per_fed_cottage():
    grid = make_grid({(0, 0): 'Chapel', (1, 0): 'Chapel', (3, 3): 'Farm',
                      (0, 1): 'Cottage', (1, 1): 'Cottage'})
    result = score_board(grid)
    assert points_for(result, 'Chapel') == 4  # 2 chapels x 2 fed cottages


# --- grey ------------------------------------------------------------------

def test_well_scores_adjacent_cottages_fed_or_not():
    grid = make_grid({(1, 1): 'Well', (1, 0): 'Cottage', (0, 1): 'Cottage'})
    assert points_for(score_board(grid), 'Well') == 2


def test_fountains_need_a_neighbor_fountain():
    paired = make_grid({(0, 0): 'Fountain', (1, 0): 'Fountain'})
    assert points_for(score_board(paired), 'Fountain') == 4
    lone = make_grid({(0, 0): 'Fountain', (2, 0): 'Fountain'})
    assert points_for(score_board(lone), 'Fountain') == 0


def test_millstone_needs_red_or_yellow_neighbor():
    assert points_for(score_board(make_grid({(0, 0): 'Millstone', (1, 0): 'Farm'})), 'Millstone') == 2
    assert points_for(score_board(make_grid({(0, 0): 'Millstone', (1, 0): 'Bakery'})), 'Millstone') == 2
    assert points_for(score_board(make_grid({(0, 0): 'Millstone', (1, 0): 'Well'})), 'Millstone') == 0


def test_shed_is_flat_one_point():
    assert points_for(score_board(make_grid({(0, 0): 'Shed', (3, 3): 'Shed'})), 'Shed') == 2


# --- orange ----------------------------------------------------------------

def test_abbey_avoids_green_yellow_black():
    assert points_for(score_board(make_grid({(0, 0): 'Abbey', (1, 0): 'Well'})), 'Abbey') == 3
    assert points_for(score_board(make_grid({(0, 0): 'Abbey', (1, 0): 'Tavern'})), 'Abbey') == 0
    assert points_for(score_board(make_grid({(0, 0): 'Abbey', (1, 0): 'Bank'})), 'Abbey') == 0


def test_cloister_corners():
    one_corner = make_grid({(0, 0): 'Cloister'})
    assert points_for(score_board(one_corner), 'Cloister') == 1
    three_corners_one_not = make_grid({(0, 0): 'Cloister', (3, 0): 'Cloister',
                                       (0, 3): 'Cloister', (1, 1): 'Cloister'})
    # 4 cloisters x 3 in corners
    assert points_for(score_board(three_corners_one_not), 'Cloister') == 12


# --- yellow ----------------------------------------------------------------

def test_bakery_needs_red_or_black_neighbor():
    assert points_for(score_board(make_grid({(0, 0): 'Bakery', (1, 0): 'Farm'})), 'Bakery') == 3
    assert points_for(score_board(make_grid({(0, 0): 'Bakery', (1, 0): 'Bank'})), 'Bakery') == 3
    assert points_for(score_board(make_grid({(0, 0): 'Bakery', (1, 0): 'Well'})), 'Bakery') == 0


def test_market_row_or_column():
    same_row = make_grid({(0, 0): 'Market', (2, 0): 'Market'})
    assert points_for(score_board(same_row), 'Market') == 4  # each 1 + 1
    row_and_column = make_grid({(0, 0): 'Market', (2, 0): 'Market', (0, 2): 'Market'})
    # corner market: 1 + max(1 row, 1 col) = 2; others 1 + 1 = 2
    assert points_for(score_board(row_and_column), 'Market') == 6


def test_tailor_counts_center_tailors():
    grid = make_grid({(1, 1): 'Tailor', (0, 0): 'Tailor'})
    # each tailor: 1 + 1 center tailor
    assert points_for(score_board(grid), 'Tailor') == 4
    full_center = make_grid({(1, 1): 'Tailor', (2, 1): 'Tailor', (1, 2): 'Tailor', (2, 2): 'Tailor'})
    assert points_for(score_board(full_center), 'Tailor') == 20  # 4 x (1 + 4)


def test_theater_unique_types_in_row_and_column():
    grid = make_grid({(1, 1): 'Theater',
                      (0, 1): 'Well', (3, 1): 'Well',      # duplicate type counts once
                      (1, 0): 'Cottage', (1, 3): 'Theater',  # other theaters don't count
                      (2, 2): 'Bank'})                       # not in row/column
    # theater (1,1): {Well, Cottage} = 2; theater (1,3): {Cottage} in its column = 1
    assert points_for(score_board(grid), 'Theater') == 3


# --- black -----------------------------------------------------------------

def test_black_buildings_flat_scores():
    grid = make_grid({(0, 0): 'Bank', (1, 0): 'Trading Post',
                      (2, 0): 'Factory', (3, 0): 'Warehouse'})
    result = score_board(grid)
    assert points_for(result, 'Bank') == 4
    assert points_for(result, 'Trading Post') == 1
    assert points_for(result, 'Factory') == 0
    assert points_for(result, 'Warehouse') == 0


# --- green -----------------------------------------------------------------

def test_tavern_table():
    three = make_grid({(0, 0): 'Tavern', (1, 0): 'Tavern', (2, 0): 'Tavern'})
    assert points_for(score_board(three), 'Tavern') == 9
    six = make_grid({(x, 0): 'Tavern' for x in range(4)} | {(0, 1): 'Tavern', (1, 1): 'Tavern'})
    assert points_for(score_board(six), 'Tavern') == 20


def test_inn_must_be_alone_in_row_and_column():
    diagonal = make_grid({(0, 0): 'Inn', (1, 1): 'Inn'})
    assert points_for(score_board(diagonal), 'Inn') == 6
    same_row = make_grid({(0, 0): 'Inn', (2, 0): 'Inn'})
    assert points_for(score_board(same_row), 'Inn') == 0


def test_almshouse_table():
    assert points_for(score_board(make_grid({(0, 0): 'Almshouse'})), 'Almshouse') == -1
    five = make_grid({(x, 0): 'Almshouse' for x in range(4)} | {(0, 1): 'Almshouse'})
    assert points_for(score_board(five), 'Almshouse') == -5


def test_feast_hall_depends_on_right_neighbor():
    grid = make_grid({(0, 0): 'Feast Hall', (1, 0): 'Feast Hall'})
    assert points_for(score_board(grid, feast_hall_wins=True), 'Feast Hall') == 6
    assert points_for(score_board(grid, feast_hall_wins=False), 'Feast Hall') == 4


# --- totals and winners ------------------------------------------------------

def test_rulebook_page5_example():
    # The worked example from the rulebook scores 28 including a Warehouse
    # storing 3 cubes (-3). Warehouse storage is out of scope here (0), so
    # the same board totals 31.
    grid = make_grid({
        (0, 0): 'Cottage', (1, 0): 'Well', (2, 0): 'Cottage', (3, 0): 'Tavern',
        (0, 1): 'Cottage', (1, 1): 'Cottage', (2, 1): 'Chapel', (3, 1): 'Tavern',
        (0, 2): 'Well', (1, 2): 'Cottage', (2, 2): 'Farm', (3, 2): 'Tavern',
        (1, 3): 'Warehouse', (2, 3): 'Bakery',
    })
    result = score_board(grid)
    assert points_for(result, 'Well') == 5       # 3 + 2 adjacent cottages
    assert points_for(result, 'Cottage') == 12   # farm feeds 4 of 5
    assert points_for(result, 'Chapel') == 4
    assert points_for(result, 'Tavern') == 9
    assert points_for(result, 'Bakery') == 3     # adjacent to Farm
    assert result['empty_penalty'] == -2
    assert result['total'] == 31


def test_empty_board_scores_minus_16():
    result = score_board(make_grid({}))
    assert result['total'] == -16


def test_resources_count_as_empty():
    result = score_board(make_grid({(0, 0): 'red', (1, 1): 'blue', (2, 2): 'Shed'}))
    assert result['empty_cells'] == 15
    assert result['total'] == 1 - 15


def test_compute_final_scores_feast_hall_and_winner():
    alice_grid = make_grid({(0, 0): 'Feast Hall', (1, 0): 'Feast Hall'})
    bob_grid = make_grid({(0, 0): 'Feast Hall'})
    outcome = compute_final_scores([
        {'nickname': 'Alice', 'grid': alice_grid, 'master_turns': 3},
        {'nickname': 'Bob', 'grid': bob_grid, 'master_turns': 2},
    ])
    alice, bob = outcome['scores']
    assert points_for(alice, 'Feast Hall') == 6  # 2 halls, more than Bob -> 3 each
    assert points_for(bob, 'Feast Hall') == 2    # 1 hall, not more than Alice
    assert outcome['winner'] == [0]
    assert outcome['win_reason'] == 'points'
    assert alice['board'][0][0] == 'green_house'


def test_tiebreaker_master_turns():
    grid = make_grid({(0, 0): 'Shed'})
    outcome = compute_final_scores([
        {'nickname': 'Alice', 'grid': grid, 'master_turns': 3},
        {'nickname': 'Bob', 'grid': [row[:] for row in grid], 'master_turns': 2},
    ])
    assert outcome['winner'] == [1]
    assert outcome['win_reason'] == 'master_turns'


def test_identical_players_share_the_win():
    grid = make_grid({(0, 0): 'Shed'})
    outcome = compute_final_scores([
        {'nickname': 'Alice', 'grid': grid, 'master_turns': 2},
        {'nickname': 'Bob', 'grid': [row[:] for row in grid], 'master_turns': 2},
    ])
    assert outcome['winner'] == [0, 1]
    assert outcome['win_reason'] == 'shared'
