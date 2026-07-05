"""End-game scoring for Tiny Towns.

Pure module: operates on plain 4x4 grids of strings as produced by
Board.getBoard() — building names, resource colors, or 'empty'.
Coordinates are (x, y) with grid[y][x].
"""

from itertools import combinations

BUILDING_COLORS = {
    'Cottage': 'blue',
    'Farm': 'red', 'Granary': 'red', 'Greenhouse': 'red', 'Orchard': 'red',
    'Fountain': 'grey', 'Millstone': 'grey', 'Shed': 'grey', 'Well': 'grey',
    'Abbey': 'orange', 'Chapel': 'orange', 'Cloister': 'orange', 'Temple': 'orange',
    'Bakery': 'yellow', 'Market': 'yellow', 'Tailor': 'yellow', 'Theater': 'yellow',
    'Bank': 'black', 'Factory': 'black', 'Trading Post': 'black', 'Warehouse': 'black',
    'Almshouse': 'green', 'Feast Hall': 'green', 'Inn': 'green', 'Tavern': 'green',
}

SIZE = 4
CORNERS = {(0, 0), (SIZE - 1, 0), (0, SIZE - 1), (SIZE - 1, SIZE - 1)}
CENTER = {(1, 1), (2, 1), (1, 2), (2, 2)}

TAVERN_POINTS = {0: 0, 1: 2, 2: 5, 3: 9, 4: 14}          # 5+ -> 20
ALMSHOUSE_POINTS = {0: 0, 1: -1, 2: 5, 3: -3, 4: 15, 5: -5}  # 6+ -> 26


def cells(grid):
    for y in range(SIZE):
        for x in range(SIZE):
            yield x, y, grid[y][x]


def find_all(grid, name):
    return [(x, y) for x, y, value in cells(grid) if value == name]


def neighbors(x, y):
    return [(nx, ny) for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            if 0 <= nx < SIZE and 0 <= ny < SIZE]


def as_color_grid(grid):
    """Render building names as '<color>_house' (the client's CSS classes)."""
    return [[BUILDING_COLORS[value] + '_house' if value in BUILDING_COLORS else value
             for value in row] for row in grid]


def _cottage_components(cottages):
    remaining = set(cottages)
    components = []
    while remaining:
        stack = [remaining.pop()]
        component = set(stack)
        while stack:
            x, y = stack.pop()
            for neighbor in neighbors(x, y):
                if neighbor in remaining:
                    remaining.discard(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(frozenset(component))
    return components


def optimal_feeding(grid):
    """Choose which Cottages are fed, in the player's favor.

    Feeding is monotone (a fed cottage never lowers the score), so Granary
    (8 surrounding cells) and Orchard (row + column) always feed everything
    they can. The only real choices are which contiguous cottage group each
    Greenhouse feeds and which cottages the Farms (4 each) feed — both
    matter because Temple needs >= 2 fed cottages adjacent to it. Boards are
    4x4, so exhaustive search is cheap and exact.

    Returns (fed_coords, {'Cottage': pts, 'Chapel': pts, 'Temple': pts}).
    """
    cottages = find_all(grid, 'Cottage')
    n_chapels = len(find_all(grid, 'Chapel'))
    temples = find_all(grid, 'Temple')

    def split(fed):
        temple_pts = sum(4 for tx, ty in temples
                         if sum(1 for n in neighbors(tx, ty) if n in fed) >= 2)
        return {'Cottage': 3 * len(fed), 'Chapel': n_chapels * len(fed), 'Temple': temple_pts}

    if not cottages:
        return frozenset(), split(frozenset())

    cottage_set = set(cottages)
    base_fed = set()
    for gx, gy in find_all(grid, 'Granary'):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if (dx or dy) and (gx + dx, gy + dy) in cottage_set:
                    base_fed.add((gx + dx, gy + dy))
    for ox, oy in find_all(grid, 'Orchard'):
        for cx, cy in cottages:
            if cx == ox or cy == oy:
                base_fed.add((cx, cy))

    farm_capacity = 4 * len(find_all(grid, 'Farm'))
    n_greenhouses = len(find_all(grid, 'Greenhouse'))
    components = _cottage_components(cottages)

    def points(fed):
        parts = split(fed)
        return parts['Cottage'] + parts['Chapel'] + parts['Temple']

    best_fed, best_pts = None, None
    # WLOG each Greenhouse feeds one whole, distinct component (monotonicity).
    for chosen in combinations(components, min(n_greenhouses, len(components))):
        greenhouse_fed = set(base_fed)
        for component in chosen:
            greenhouse_fed |= component
        remaining = [c for c in cottages if c not in greenhouse_fed]
        for pick in combinations(remaining, min(len(remaining), farm_capacity)):
            fed = frozenset(greenhouse_fed | set(pick))
            pts = points(fed)
            if best_pts is None or pts > best_pts:
                best_fed, best_pts = fed, pts

    return best_fed, split(best_fed)


def score_board(grid, feast_hall_wins=False):
    """Score one town. feast_hall_wins: this player has more Feast Halls
    than the player on their right (rulebook comparison, decided by caller)."""
    fed, fed_split = optimal_feeding(grid)

    buildings = {}
    for x, y, value in cells(grid):
        if value in BUILDING_COLORS:
            buildings.setdefault(value, []).append((x, y))

    def coords(name):
        return buildings.get(name, [])

    def adjacent_values(x, y):
        return [grid[ny][nx] for nx, ny in neighbors(x, y)]

    def adjacent_to_color(x, y, colors):
        return any(BUILDING_COLORS.get(value) in colors for value in adjacent_values(x, y))

    breakdown = []

    def add(name, points):
        count = len(coords(name))
        if count:
            breakdown.append({'building': name, 'count': count, 'points': points})

    add('Cottage', fed_split['Cottage'])

    for feeder in ('Farm', 'Granary', 'Greenhouse', 'Orchard'):
        add(feeder, 0)

    add('Well', sum(1 for wx, wy in coords('Well')
                    for value in adjacent_values(wx, wy) if value == 'Cottage'))
    add('Fountain', sum(2 for fx, fy in coords('Fountain')
                        if 'Fountain' in adjacent_values(fx, fy)))
    add('Millstone', sum(2 for mx, my in coords('Millstone')
                         if adjacent_to_color(mx, my, ('red', 'yellow'))))
    add('Shed', len(coords('Shed')))

    add('Abbey', sum(3 for ax, ay in coords('Abbey')
                     if not adjacent_to_color(ax, ay, ('green', 'yellow', 'black'))))
    add('Chapel', fed_split['Chapel'])
    corner_cloisters = sum(1 for cloister in coords('Cloister') if cloister in CORNERS)
    add('Cloister', len(coords('Cloister')) * corner_cloisters)
    add('Temple', fed_split['Temple'])

    add('Bakery', sum(3 for bx, by in coords('Bakery')
                      if adjacent_to_color(bx, by, ('red', 'black'))))
    markets = coords('Market')
    add('Market', sum(1 + max(sum(1 for other in markets if other != market and other[1] == market[1]),
                              sum(1 for other in markets if other != market and other[0] == market[0]))
                      for market in markets))
    center_tailors = sum(1 for tailor in coords('Tailor') if tailor in CENTER)
    add('Tailor', sum(1 + center_tailors for _ in coords('Tailor')))
    theater_points = 0
    for tx, ty in coords('Theater'):
        seen = set()
        for x, y, value in cells(grid):
            if (x == tx or y == ty) and (x, y) != (tx, ty):
                if value in BUILDING_COLORS and value != 'Theater':
                    seen.add(value)
        theater_points += len(seen)
    add('Theater', theater_points)

    add('Bank', 4 * len(coords('Bank')))
    add('Trading Post', len(coords('Trading Post')))
    add('Factory', 0)    # effect-only card, no end-game points
    add('Warehouse', 0)  # -1 per stored resource; storage is out of scope

    n_taverns = len(coords('Tavern'))
    add('Tavern', TAVERN_POINTS[n_taverns] if n_taverns <= 4 else 20)
    inns = coords('Inn')
    add('Inn', sum(3 for inn in inns
                   if not any(other[0] == inn[0] or other[1] == inn[1]
                              for other in inns if other != inn)))
    add('Feast Hall', len(coords('Feast Hall')) * (3 if feast_hall_wins else 2))
    n_almshouses = len(coords('Almshouse'))
    add('Almshouse', ALMSHOUSE_POINTS[n_almshouses] if n_almshouses <= 5 else 26)

    # Remaining resources are removed at game end; every cell without a
    # building scores -1.
    empty_cells = sum(1 for x, y, value in cells(grid) if value not in BUILDING_COLORS)

    return {
        'total': sum(item['points'] for item in breakdown) - empty_cells,
        'breakdown': breakdown,
        'empty_cells': empty_cells,
        'empty_penalty': -empty_cells,
        'fed_cottages': [f'{x},{y}' for x, y in sorted(fed)],
        'cottages': len(coords('Cottage')),
    }


def compute_final_scores(players):
    """players: [{'nickname', 'grid', 'master_turns'}] in join order.
    The 'player on your right' for Feast Hall is the next player, wrapping.
    Solo game: no opponent, Feast Halls score 2 each (rulebook's solo mode
    removes the card entirely; this is the closest sensible reading)."""
    feast_halls = [len(find_all(player['grid'], 'Feast Hall')) for player in players]

    scores = []
    for i, player in enumerate(players):
        wins = len(players) > 1 and feast_halls[i] > feast_halls[(i + 1) % len(players)]
        score = score_board(player['grid'], feast_hall_wins=wins)
        score['nickname'] = player['nickname']
        score['master_turns'] = player.get('master_turns', 0)
        score['board'] = as_color_grid(player['grid'])
        scores.append(score)

    candidates = list(range(len(scores)))
    win_reason = 'shared'
    for reason, key in (('points', lambda s: -s['total']),
                        ('master_turns', lambda s: s['master_turns']),
                        ('empty_cells', lambda s: s['empty_cells']),
                        ('cottages', lambda s: -s['cottages'])):
        best = min(key(scores[i]) for i in candidates)
        candidates = [i for i in candidates if key(scores[i]) == best]
        if len(candidates) == 1:
            win_reason = reason
            break

    return {'winner': candidates, 'win_reason': win_reason, 'scores': scores}
