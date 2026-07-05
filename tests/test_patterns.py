import pytest

from game import Building, BuildingRow, Board, Cell

# Cottage + the 4 candidates per color from BuildingRow.generate()
ALL_BUILDING_NAMES = [
    'Cottage',
    'Farm', 'Granary', 'Greenhouse', 'Orchard',
    'Fountain', 'Millstone', 'Shed', 'Well',
    'Abbey', 'Chapel', 'Cloister', 'Temple',
    'Bakery', 'Market', 'Tailor', 'Theater',
    'Bank', 'Factory', 'Trading Post', 'Warehouse',
    'Almshouse', 'Feast Hall', 'Inn', 'Tavern',
]


def make_board(rows):
    board = Board()
    board.setBoard([[Cell(value) for value in row] for row in rows])
    return board


def test_every_row_candidate_has_a_real_pattern():
    for name in ALL_BUILDING_NAMES:
        building = Building(name)
        assert building.patterns[0] == Building.buildings_patterns[name]


def test_unknown_building_raises():
    with pytest.raises(KeyError):
        Building('Palace')


def test_rotations_include_all_orientations():
    tavern = Building('Tavern')  # 1x3 column: red, red, blue
    assert {'0, 0': 'red', '0, 1': 'red', '0, 2': 'blue'} in tavern.patterns
    # rotated 90° right: 3x1 row, blue leftmost
    assert {'2, 0': 'red', '1, 0': 'red', '0, 0': 'blue'} in tavern.patterns
    # vertical mirror: blue on top
    assert {'0, 2': 'red', '0, 1': 'red', '0, 0': 'blue'} in tavern.patterns


def test_chiral_building_has_180_rotation():
    # Temple is chiral and non-square; the old rotation code displaced the
    # 180°/270° variants so they could never match check_patterns.
    temple = Building('Temple')
    r180 = {'1, 0': 'red', '1, 1': 'red', '1, 2': 'grey', '0, 2': 'blue'}
    assert r180 in temple.patterns
    # all variants must be origin-normalized
    for pattern in temple.patterns:
        xs = [int(cell.split(', ')[0]) for cell in pattern]
        ys = [int(cell.split(', ')[1]) for cell in pattern]
        assert min(xs) == 0 and min(ys) == 0, pattern
    # a chiral 2x3 shape has 8 distinct orientations
    assert len(temple.patterns) == 8


def test_find_patterns_on_asymmetric_layout():
    # Bakery identity pattern occupies column 0 (red, blue, red) + yellow at (1, 1)
    board = make_board([
        ['red', 'empty', 'empty', 'empty'],
        ['blue', 'yellow', 'empty', 'empty'],
        ['red', 'empty', 'empty', 'empty'],
        ['empty', 'empty', 'empty', 'empty'],
    ])
    found = board.find_patterns('Bakery')
    assert {'0, 0': 'red', '0, 1': 'blue', '0, 2': 'red', '1, 1': 'yellow'} in found


def test_find_patterns_with_offset():
    # Same Bakery shape shifted by (2, 1)
    board = make_board([
        ['empty', 'empty', 'empty', 'empty'],
        ['empty', 'empty', 'red', 'empty'],
        ['empty', 'empty', 'blue', 'yellow'],
        ['empty', 'empty', 'red', 'empty'],
    ])
    found = board.find_patterns('Bakery')
    assert {'2, 1': 'red', '2, 2': 'blue', '2, 3': 'red', '3, 2': 'yellow'} in found


def test_single_red_cube_builds_nothing():
    board = make_board([
        ['red', 'empty', 'empty', 'empty'],
        ['empty', 'empty', 'empty', 'empty'],
        ['empty', 'empty', 'empty', 'empty'],
        ['empty', 'empty', 'empty', 'empty'],
    ])
    for name in ALL_BUILDING_NAMES:
        assert board.find_patterns(name) == [], name

    row = BuildingRow()
    row.generate()
    assert board.check_patterns({'0, 0': 'red'}, row) is None


def test_check_patterns_matches_row_building():
    row = BuildingRow()
    row.generate()
    # Cottage is always in the row; its identity pattern must match regardless of offset
    cords = {'2, 1': 'yellow', '1, 2': 'red', '2, 2': 'blue'}
    assert row.buildings[0].name == 'Cottage'
    assert Board().check_patterns(cords, row) == 'Cottage'
