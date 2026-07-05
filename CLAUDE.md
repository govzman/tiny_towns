# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A web version of the board game "Tiny Towns". Python Flask backend, vanilla JS frontend, no build step. The base game is playable end-to-end with full scoring; monuments are cosmetic (chosen but no patterns/effects/points) and the black-building in-play effects (Warehouse storage, Factory swap, Bank resource ban, Trading Post wild) are not implemented.

## Running

```bash
uv run python app.py   # serves on PORT env var, default 5000
uv run pytest          # test suite in tests/
uv run pytest tests/test_scoring.py -k tavern   # single test
```

Deps live in `pyproject.toml` (pytest in the dev group); `requirements.txt` is kept only for the Heroku-style `Procfile` deploy.

`test.js` is not part of the test suite — it's a scratchpad for pattern rotation experiments (and uses stale building names).

## Architecture

**Single-endpoint JSON-RPC style API.** `app.py` exposes `POST /api` taking `{"method": ..., "params": ...}`. Method names are whitelisted in `app.py`, then dispatched via `getattr` to a single global `Game` instance — the server hosts exactly one in-memory game per process, no persistence, no sessions. Adding an API method means adding it to the whitelist in `app.py` and implementing it on `Game`.

**Game state machine** (`game.py`, `Game.stage`): `lobby` → `choose_monument` → `main_game` → `end_game`. Pre-game transitions happen inside `get_status` when all players are `ready`; turn advance happens in `_advance_turn_if_ready` (called from `place_resource`/`change_readiness`/`checkTTL`). The Master Builder is tracked explicitly as `Game.master_id` and rotates in join order, skipping finished players; `master_turns` feeds the tiebreaker. A player whose placement fills their board is NOT auto-readied — they get the official build window (`boardFull: true` in the response) and confirm via `change_readiness`; full boards are stamped `isFinish` at turn advance. When everyone is finished, `_finish_game` computes `final_scores` exactly once via `scoring.compute_final_scores`. Players are keyed by server-generated UUID (`player_id`); a player who stops polling for 60 s (`checkTTL`) is deleted in lobby stages but only marked finished/disconnected during `main_game` — never delete main_game players, the client identifies itself and the master by list index.

**Scoring** (`scoring.py`): pure module, no Flask/Game imports; operates on 4×4 grids of strings from `Board.getBoard()` (coords `(x, y)`, `grid[y][x]`). Owns `BUILDING_COLORS` (single source of truth, imported by `Board.getBoard`). Cottage feeding is player-favorable and optimized exhaustively in `optimal_feeding` (Farm/Greenhouse choices matter because Chapel/Temple depend on which cottages are fed). Rules source: `docs/Tiny_Towns_Rules.pdf` + card images in `static/assets/buildings/*.png`.

**Polling client** (`static/js/game.js`): a single-page app served from `static/`. It polls `get_status` every 2 s (`PING_INTERVAL`) and re-renders the page when the stage or boards change. Client state (`game` object) is persisted to `localStorage` under `gameState`; `player_id` survives page reloads. Pages are rendered by `showPage()` switching on stage name.

**Building patterns exist in TWO places and must be kept in sync:**
- Server: `buildings_patterns.txt` — one line per building, `Name / {'x, y': 'color', ...}` coordinate-dict format, parsed with `eval` at `Building` class-body execution time. Rotations/mirrors are generated in `Building.add_all_rotations()`.
- Client: the `buildings` matrix literal at the top of `static/js/game.js` (row/column arrays); rotations generated in `getPatterns()`.

Both sides validate placement: the client finds matching cells to highlight, then the server re-checks in `Board.check_patterns` / `find_patterns` when `place_building` is called. A shape change touches both files.

**Naming pitfalls:** the canonical names are `Theater`, `Feast Hall`, `Trading Post`, and the grey spelling is `grey` — consistent across `buildings_patterns.txt`, `game.py`, and `game.js` (only `test.js` still has stale variants). `Building.__init__` raises `KeyError` on unknown names on purpose: name drift between `BuildingRow.generate()` and the pattern file used to fall back to a silent stub. The API/board use `bulidingRow` (sic) as a key and building types are suffixed `_house` on server-rendered boards. Coordinates are `x, y` strings with the board stored as `board[y][x]` (4×4).

**Errors** are returned as `{'error': {'code': N, 'msg': ...}}` (see `util.error`); success responses are wrapped by `Game.res()` with `game_id` and `turn`.

Deployment: `Procfile` (`web: python app.py`) for Heroku-style hosting.
