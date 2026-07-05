# RECOMMENDATIONS — code, design, and architecture improvements

Ordered by how much they matter, not by how easy they are. File sizes for context: `game.js` ~735 lines, `game.py` ~560 lines.

## 1. Security

- **Nickname XSS (real vulnerability).** Nicknames are user input and are rendered via `innerHTML` in `updatePlayersList` and in the end-screen score columns (`game.js`). A nickname like `<img src=x onerror=...>` executes in every player's browser. Fix: build those nodes with `textContent`/`createElement`, or add one `escapeHtml()` helper and use it at every interpolation of server data into `innerHTML`. The events log is safe (`innerText`), which shows the codebase already knows the right pattern — apply it consistently.
- **`eval()` on the pattern file.** `Building` evals every line of `buildings_patterns.txt` at import. It's repo-controlled today, but it's a fragile parser and a habit worth dropping: convert the file to JSON (`buildings_patterns.json`) and `json.load` it. This also unlocks serving the same file to the client (see §2).
- **`player_id` is a bearer token** in `localStorage` with no expiry or binding. Acceptable for a friends-game, but don't build anything more on top of it without sessions.

## 2. Architecture

- **One source of truth for building patterns.** The same shapes live in `buildings_patterns.txt` (server) and the `buildings` matrix at the top of `game.js` (client), with two independent rotation implementations. This already caused a real bug (`Theatre` vs `Theater`) and monuments will double the data. Serve the patterns as JSON (static file or endpoint), have the client fetch them at load, and delete the client-side copy. Rotation logic can stay client-side (it's needed for instant highlighting) but should consume the same base data.
- **Make `Game` injectable instead of a module-level singleton.** `app.py` holds `myGame` at import time; tests already construct `Game()` directly, and rooms (TODO P5) will need a `{room_code: Game}` registry. A `create_app(game_factory)` application-factory is the standard Flask shape and costs ~20 lines now.
- **Consistent response envelope.** `get_status` wraps in `res()` (`{game_id, turn, params}`), while other methods return bare `{status}`/`{success}`/`{isSuccess}` (three different success keys!). Pick one envelope: `{ok: true, data: ...}` / `{ok: false, error: {code, msg}}`, and give the client one place that unwraps it.
- **Error codes are magic numbers** (55, 56, 57, …) duplicated across `game.py` and implicitly known by tests. Define them once (`enum.IntEnum` in `util.py` — e.g. `Err.BAD_ID`, `Err.WRONG_STAGE`) and use names everywhere.
- **Separate domain from transport.** `Game` methods return HTTP-ish error dicts, mixing rule logic with API shape. Cleaner: domain methods raise `GameError(code, msg)`; `app.py` catches and serializes. `game.py` then reads as rules, not as an API handler.
- **The single-threaded assumption is invisible.** Turn advance runs synchronously inside request handlers and is only safe because the Werkzeug dev server is single-threaded. Document it loudly, or better: a `threading.Lock` around mutating API methods (`with game.lock:` in the dispatcher — one line in `app.py`). Mandatory before gunicorn/threads.
- **Polling → SSE.** Every client polls `get_status` every 2 s; the E2E showed real (if minor) stale-state races, and the log endpoint noise is constant. Server-Sent Events fit this app perfectly (server→client push, no client→server channel needed beyond the existing POSTs) and are ~30 lines in Flask.

## 3. Backend code quality

- **Model the domain with types.** Players are stringly-keyed dicts (`player['isFinish']`, `player['placed']`, …) — typos are runtime bugs. A `@dataclass Player` (nickname, board, ready, placed, finished, disconnected, master_turns, monument, last_response) plus `Stage(str, Enum)` would let pyright/mypy catch most of the mistakes this codebase historically had.
- **Kill the `Cell` class.** It's a get/set wrapper around a string; `Board` can store `list[list[str]]` directly and lose ~15 lines and one indirection.
- **One coordinate convention.** Today: `'x, y'` strings (pattern keys), `'x,y'` strings (API cells), `[x, y]` lists (`getCell`), `(x, y)` tuples (scoring), with `board[y][x]` indexing throughout — plus `updateBoard` in JS iterating with `x` as the row. It works, but every new feature pays a tax. Introduce helpers (`parse_cell`, `cell_key`) and a short "coordinates" note in CLAUDE.md; rename the JS loop variables to `row`/`col`.
- **PEP 8 + tooling.** Mixed naming (`checkTTL`, `setParam`, `getRow` vs snake_case), `params : dict` spacing, commented-out code blocks. Adopt `ruff` (lint + format) — the codebase is small enough to clean in one pass — and wire it into pre-commit.
- **Unbounded `events` list** grows for the whole game; only the last 5 are ever sent. Use `collections.deque(maxlen=50)`.
- **Inject the clock.** `checkTTL` calls `time()` directly; tests fake timestamps by rewriting `last_response`. A `now` parameter (or `Game.clock` attribute) makes TTL tests direct.
- **Dependency drift.** `requirements.txt` pins Flask 2.2.5 while `uv.lock` resolves Flask 3.1.3 — the deployed app and the dev app are different majors. Generate `requirements.txt` from the lock (`uv export --no-dev > requirements.txt`) or switch the Procfile to `uv run python app.py` and delete it.
- **Logging noise.** `logging.basicConfig(level=DEBUG)` plus logging every request body means each client produces a log line every 2 s. Log at INFO, and skip bodies for `get_status`.

## 4. Frontend code quality

- **Split `game.js`.** 735 lines of top-level `const`s in one module: split into `api.js` (fetch + envelope), `state.js` (game state + localStorage), `patterns.js` (matching), `render/` (per-page). It's already `type="module"`, so this needs no build step.
- **`api()` swallows errors.** On network failure it logs and returns `undefined`, so every caller that does `res.success`/`res.error` can throw. Return `{ok: false, error}` from the catch, or let it throw and handle at call sites.
- **Brittle DOM access.** `qs('#myboard').childNodes[3]` depends on whitespace text nodes in a template string — one reformat breaks the board. Use `qs('#myboard table')`. Same for `children[1].rows[y].cells[x]`.
- **Dialog listener leak.** Each multi-pattern build re-adds a click listener to `#dialog` (`addEventListener(..., true)`), so old handlers accumulate and re-fire. Use `{once: true}` or build the dialog nodes fresh with delegation.
- **Render-on-diff via `JSON.stringify` comparisons** (the code's own comment: "WTF! TODO!"). It mostly works, but the contract is fragile (key order, `undefined`s). Since state is tiny, simplest robust fix: re-render deterministically from state every poll, and keep DOM writes idempotent.
- **Persist a schema, not the world.** `setState()` dumps the entire `game` object (including transient turn state) to `localStorage`; on reload half of it is stale. Persist only `{player_id, nickname, game_id}` and rebuild the rest from `get_status`.
- **Replace `prompt()`/`alert()`** with in-page UI. Blocking dialogs freeze the poll loop, break on mobile, and can't be styled. The `#dialog` overlay already exists — generalize it.
- **`test.js` should be deleted** (or moved to `docs/scratch/`): it duplicates pattern logic with stale building names (`Theatre`, `Feast hall`, `gray`) and will mislead the next reader.

## 5. Testing & tooling

- **CI.** A GitHub Actions workflow: `uv run pytest` + a JS syntax/lint check. The suite runs in ~0.2 s; there's no excuse not to gate PRs on it.
- **Check the E2E into the repo.** The Playwright two-player script that verified this work lives in `/tmp` — move it to `e2e/` with a `bun`/`node` runner and a README line; it's the only test of the actual UI seams (polling, dialogs, end screen).
- **Property-based tests for patterns.** `add_all_rotations` is exactly the kind of code Hypothesis is for: for random patterns, assert all variants are origin-normalized, closed under rotation, and count ≤ 8 distinct.
- **JS lint/format.** `biome` (single fast tool, works well with bun) or eslint+prettier; the current file mixes quote styles, semicolons, and dead commented code.
- **Coverage** on `scoring.py` and `game.py` (`pytest-cov`); scoring rules are the highest-value lines to keep at ~100%.

## 6. Repo hygiene

- **`.gitignore` contradicts the repo:** it lists `docs/`, yet `docs/Tiny_Towns_Rules.pdf` and `docs/map.drawio` are tracked (added before the ignore rule). Either stop ignoring `docs/` (the rulebook is a load-bearing reference — recommended) or untrack it deliberately.
- **Asset cleanup:** `board.jpg` + `board.png` duplicates, an `_draft/` folder, mixed webp/png. Pick one board image, move drafts out of `static/`.
- **README refresh:** it still says "some features may not be fully functional" with a stale preview; document the actual state, the run/test commands, and the rules scope.
