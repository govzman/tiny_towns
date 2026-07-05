# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A web version of the board game "Tiny Towns" (in development). Python Flask backend, vanilla JS frontend, no build step, no test suite.

## Running

```bash
uv pip install -r requirements.txt   # Flask only
python app.py                        # serves on PORT env var, default 5000
```

Must be run from the repo root: `game.py` loads `buildings_patterns.txt` by relative path at import time.

`test.js` is not a test suite — it's a scratchpad for experimenting with pattern rotation logic (run with `bun test.js` if needed).

## Architecture

**Single-endpoint JSON-RPC style API.** `app.py` exposes `POST /api` taking `{"method": ..., "params": ...}`. Method names are whitelisted in `app.py`, then dispatched via `getattr` to a single global `Game` instance — the server hosts exactly one in-memory game per process, no persistence, no sessions. Adding an API method means adding it to the whitelist in `app.py` and implementing it on `Game`.

**Game state machine** (`game.py`, `Game.stage`): `lobby` → `choose_monument` → `main_game` → `end_game`. Transitions happen inside `get_status` when all players are `ready`; readiness flags are reset on each transition and each turn. Players are keyed by server-generated UUID (`player_id`); a player is dropped if they don't poll `get_status` for 10 s (`checkTTL`). The "Master Builder" (who picks the turn's resource) rotates as `(turn - 1) % len(players)`.

**Polling client** (`static/js/game.js`): a single-page app served from `static/`. It polls `get_status` every 2 s (`PING_INTERVAL`) and re-renders the page when the stage or boards change. Client state (`game` object) is persisted to `localStorage` under `gameState`; `player_id` survives page reloads. Pages are rendered by `showPage()` switching on stage name.

**Building patterns exist in TWO places and must be kept in sync:**
- Server: `buildings_patterns.txt` — one line per building, `Name / {'x, y': 'color', ...}` coordinate-dict format, parsed with `eval` at `Building` class-body execution time. Rotations/mirrors are generated in `Building.add_all_rotations()`.
- Client: the `buildings` matrix literal at the top of `static/js/game.js` (row/column arrays); rotations generated in `getPatterns()`.

Both sides validate placement: the client finds matching cells to highlight, then the server re-checks in `Board.check_patterns` / `find_patterns` when `place_building` is called. A shape change touches both files.

**Naming pitfalls:** the canonical grey spelling is `grey` (server and game.js) — `test.js` uses `gray` and stale names like `Theatre`/`Feast hall` vs `Theater`/`Feast Hall` used elsewhere; the API/board use `bulidingRow` (sic) as a key and building types are suffixed `_house` on server-rendered boards. Coordinates are `x, y` strings with the board stored as `board[y][x]` (4×4).

**Errors** are returned as `{'error': {'code': N, 'msg': ...}}` (see `util.error`); success responses are wrapped by `Game.res()` with `game_id` and `turn`.

Deployment: `Procfile` (`web: python app.py`) for Heroku-style hosting.
