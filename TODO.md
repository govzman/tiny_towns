# TODO — road to a 100% complete game

Where we are today: the base game is playable end-to-end — lobby, monument pick, turn loop with server-side validation, finished-player handling, full scoring for all 24 base buildings, end screen with breakdown and tiebreakers, 55 tests. What's still missing to call it "100%", in priority order.

Effort: **S** = hours, **M** = about a day, **L** = several days.

## P1 — Monuments (the biggest missing rule) — L

Monuments are currently cosmetic: a card is chosen and displayed, but has no construction pattern, no effect, and no points. Rules: `docs/Tiny_Towns_Rules.pdf` p.3 & p.8; the card images in `static/assets/cards/*.webp` are the authority for exact point values and effect text — read each card before implementing it.

Groundwork (do first):

- [ ] Add monument construction patterns to `buildings_patterns.txt` and give `Building` a notion of "owner-only" cards (a monument is buildable only by its owner, exactly once — `Board.check_patterns` currently only knows the shared `BuildingRow`).
- [ ] Ship pattern data to the client instead of duplicating it in the `buildings` matrix in `game.js` (see RECOMMENDATIONS — this becomes unavoidable here, since monument patterns are per-player).
- [ ] Scoring plumbing: `scoring.score_board` needs the player's monument name and its effect hooks; Theater must count a monument as a unique type — except Barrett Castle, which counts as 2 Cottages (rulebook p.7).
- [ ] End screen: show the (un)built monument card and its points.
- [ ] Tests per card: pattern buildable, effect applies, scoring correct.

The 15 cards, grouped by what they touch:

| Card (code)                              | Touches              | Implementation notes                                                                                             |
| ---------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Archive of the Second Age (`Arch_Age`)   | scoring only         | points per unique building type; placement-independent                                                           |
| Silva Forum (`Sil_For`)                  | scoring only         | points per building in your largest contiguous group                                                             |
| The Sky Baths (`Sky_Bath`)               | scoring only         | verify effect from card                                                                                          |
| The Starloom (`Star`)                    | scoring only         | verify effect from card                                                                                          |
| Mandras Palace (`Mand_Pal`)              | scoring only         | orthogonal-adjacency based; verify from card                                                                     |
| Shrine of the Elder Tree (`Shr_Tree`)    | scoring only         | scores by building count at construction time — needs a snapshot, not end-state                                  |
| Cathedral of Caterina (`Cath_Cat`)       | scoring modifier     | empty squares score 0 instead of −1 (own board only)                                                             |
| Barrett Castle (`Bar_Cast`)              | scoring + feeding    | counts as 2 fed-able Cottages — extend `optimal_feeding`                                                         |
| Fort Ironweed (`Fort_Iron`)              | turn flow            | owner can no longer be Master Builder while others remain — `_next_master`                                       |
| Opaleyes Watch (`Opal_Wat`)              | turn flow            | timing restriction from the round after construction; verify from card                                           |
| Statue of the Bondmaker (`Stat_Bond`)    | placement validation | resources on Cottage squares can't be used for construction                                                      |
| Obelisk of the Crescent (`Crescent`)     | placement validation | placement freedom effect; verify from card                                                                       |
| Architects' Guild (`Arch_Guild`)         | interactive UI       | on construction: replace up to 2 of your buildings with any from supply — needs a new client dialog + API method |
| Grove University (`Grove_Un`)            | interactive UI       | on-construction building choice; verify from card                                                                |
| Grand Mausoleum of the Rodina (`Rodina`) | verify               | verify effect from card                                                                                          |

Suggested order: scoring-only cards first (pure `scoring.py` work), then flow/validation cards, interactive-UI cards last.

## P2 — Black building in-play effects — M/L

Currently Bank/Trading Post/Factory/Warehouse only score flat points. Their effects are real gameplay:

- [ ] **Trading Post** (M): acts as a wild resource square for construction patterns. Touches pattern matching on both server (`Board.check_patterns`/`find_patterns`) and client (`game.js` matching); a cell with a Trading Post must match any color in a pattern without being consumed.
- [ ] **Bank** (S/M): on construction, declare a resource type not already on another Bank; the owner can never name it as Master Builder (`choose_resource` validation + a small pick dialog + show the banned cube on the card).
- [ ] **Warehouse** (M/L): store up to 3 resources — when a resource is named you may put it on the Warehouse instead of the board, or swap a stored cube with the named one. Needs per-warehouse storage state, two new moves in `place_resource`, storage UI, and the −1/stored-cube end scoring (`scoring.py` already documents this deviation; the rulebook p.5 example fixture in `tests/test_scoring.py` asserts 31 instead of the official 28 — restore it to 28 once storage exists).
- [ ] **Factory** (M): on construction place 1 resource on it; when *another player* names that type, the owner may take a different resource instead. Asymmetric per-player resource for a turn — `current_resource` becomes per-player; client needs a choice prompt.

## P3 — Rule-fidelity gaps in the current loop — S each

- [ ] Building is allowed any time during `main_game`; the official window is *after placing your resource, before the next declaration*. Enforce `player['placed']` in `place_building` (decide: strict rules vs current leniency).
- [ ] A player who *can't or doesn't want to* build may declare their town done even with free squares ("не хотите строить" — rulebook p.5). Today finishing requires a literally full board. Add a voluntary "finish my town" action.
- [ ] Disconnect = permanently finished after 60 s. Add reconnection: reclaim a seat by nickname while the game runs (`get_status` lobby path already rejects duplicate nicknames — extend it to hand back the old `player_id` for a disconnected player).
- [ ] Feast Hall in solo play scores 2 (documented deviation) — official solo mode removes the card entirely; fold into P4 solo work.
- [ ] Optional "Cave rule" (rulebook p.4): up to 2 named resources per game may be set aside instead of placed; they score nothing. Small state + one button.

## P4 — Game variants — M/L

- [ ] **Solo mode** (rulebook p.6): 15-resource-card deck instead of a Master Builder, removes Tavern/Bank/Fort Ironweed/Opaleyes Watch; mastery table (38+ = Great Architect …) on the end screen.
- [ ] **Town Hall rule** (rulebook p.6): mayor draws resource cards; every 3rd round players choose freely.

## P5 — Product & infrastructure (not rules, but needed for real play) — L

- [ ] Multiple concurrent games: room codes, `Game` registry instead of the single module-level instance (see RECOMMENDATIONS — the groundwork is an injectable `Game`).
- [ ] Persistence across server restarts (a running game currently lives only in memory) — serialize `Game` to disk/SQLite on mutation.
- [ ] Replace 2 s polling with SSE (or WebSockets) — removes the stale-poll races the E2E surfaced ("wrong turn" alerts on fast actions) and cuts request volume ~10×.
- [ ] Production server: the Procfile runs the Werkzeug dev server; move to gunicorn with **exactly one worker** until rooms/persistence land (shared in-memory state breaks with >1 worker).
- [ ] Mobile layout (the board/cards don't fit small screens), replace `prompt()`/`alert()` with in-page UI.
- [ ] i18n if a Russian UI is ever wanted back (strings are now English-only, hardcoded).
- [ ] README refresh: screenshots, how to run (`uv run python app.py`, `uv run pytest`), rules scope.
