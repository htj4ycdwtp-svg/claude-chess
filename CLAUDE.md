# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an online, two-player, real-time chess game. A Flask + Flask-SocketIO backend hosts authoritative game state; a minimal HTML/CSS/JavaScript frontend renders the board and relays player actions. This is a personal learning project, not production software — decisions favor clarity, small steps, and understanding over speed or completeness.

The full feature set (below) is implemented and tested. See `README.md` for setup, testing, and deployment instructions.

## Learning Goals

Work in this repo should actively support learning in these areas, not just produce working code:
- Using Claude Code as a development tool
- Writing and evolving a `CLAUDE.md`
- Python 3 fundamentals
- Flask
- Real-time multiplayer development (Flask-SocketIO, rooms, server-authoritative state)
- HTML, CSS, and basic JavaScript
- Testing with pytest
- Deployment (to Render)

## Tech Stack

- **Language:** Python 3
- **Web framework:** Flask
- **Real-time layer:** Flask-SocketIO, using Socket.IO rooms so each match is isolated from every other match
- **Frontend:** HTML and CSS, with minimal vanilla JavaScript (no React, no frontend framework)
- **Testing:** pytest
- **Deployment target:** Render, via `gunicorn` + the `eventlet` worker class (Flask-SocketIO's dev server isn't production-suitable)
- No external chess library (e.g. `python-chess`) — all chess rules are implemented by hand. No computer opponent.
- No database — active games live in server memory for this version (see "Known limitations" in `README.md`).

## Architecture

Three concerns stay in separate layers and never bleed into each other:

1. **Chess rules engine** (`chess_logic/`) — pure Python, no Flask, no Socket.IO, no knowledge of HTTP, sessions, or JavaScript. Fully testable without running a server. `Piece` stays a simple immutable data object (color + piece type only) — movement/legality rules live in `MoveValidator`, not in `Piece` subclasses. If subclassing pieces later seems clearly advantageous, explain why before changing this.
2. **Server** (`server/`) — Flask + Socket.IO. Routes and socket event handlers are thin: they pull identity from the signed session cookie, call into `chess_logic` and `GameManager`, and emit results. **Chess rules are never written directly inside a route or a Socket.IO handler.**
3. **Browser** (`templates/`, `static/`) — renders whatever board state the server sends and forwards user actions (clicks, promotion choice) to the server over Socket.IO. **JavaScript never decides whether a move is legal** — it only displays state and emits intent. (It does decide *when to prompt* for a promotion piece — a UX nicety, not a legality decision; the server independently validates and defaults to queen if the client sends nothing usable.)

The server is authoritative at all times: a move is only real once the server validates and applies it. A move arriving from a browser is a *request*, never a fact — and so is any claim about *which* game or color the browser belongs to. `game_code`/`color` identity comes from the server-signed session cookie, never from a client-supplied field, so a compromised client can't claim someone else's seat.

Actual layout:

```
chess_logic/                # pure rules engine, no Flask/Socket.IO dependency
  board.py                  # Board: 8x8 grid, algebraic squares, copy() for check-safety simulation
  pieces.py                 # Piece: immutable data only (color + piece type), Color/PieceType enums
  move_validator.py          # MoveValidator: per-piece movement pattern + path-blocking legality
  game.py                    # Game: turn tracking, castling/en passant/promotion, check/checkmate/stalemate

server/                     # Flask + Socket.IO, imports chess_logic
  app.py                     # Flask + SocketIO app, HTTP routes (/, /api/create, /api/join)
  game_manager.py             # GameSession/GameManager: in-memory games keyed by code, color reservation
  socket_handlers.py          # Socket.IO event handlers (connect/disconnect/make_move/restart_game/get_legal_moves)

static/
  css/style.css               # board + lobby styling, responsive
  js/main.js                  # click-to-move, highlighting, promotion prompt, socket wiring

templates/
  index.html                  # single page: lobby + board, toggled by JS

tests/
  test_board.py
  test_move_validator.py
  test_game.py
  test_game_manager.py
```

**Deviation from the earlier plan:** a single `templates/index.html` is used for both the lobby and the board (toggled by JS) instead of separate `index.html`/`game.html` templates — this avoids threading a game code through URLs/routes for no real benefit, since players share the code out-of-band and type it into a form.

**Why create/join are HTTP routes, not Socket.IO events:** Flask can only set the session cookie (`Set-Cookie`) on an HTTP response. A Socket.IO event has no HTTP response to attach one to, so create/join happen over `POST /api/create` and `POST /api/join` (which reserve a color and set the cookie); the Socket.IO `connect` handler then reads that cookie to attach the live connection to the right game/color. This is also exactly how reconnection works — a reload re-sends the same cookie, and `connect` re-attaches to the same seat.

## Feature Status

All implemented and covered by tests:
- Standard starting position; legal movement (with path-blocking) for every piece; captures
- Turn enforcement; rejecting moves on the opponent's pieces
- Check, checkmate, and stalemate detection
- Castling (both sides, with the occupied-square / in-check / through-check / lost-rights cases enforced)
- En passant (including expiry after one move)
- Pawn promotion (defaults to queen if the client doesn't specify a valid choice)
- Create game with a short code; join by code; creator is White, joiner is Black
- Isolated Socket.IO room per game
- Reconnection to the same game/color after a page reload, via the session cookie
- Restart (resets the board, keeps the same two players)
- Clear rejection of invalid/unknown and full game codes

**Explicitly out of scope:** accounts, matchmaking, rankings, chat, spectators, timers, a computer opponent, React, and a database. Don't add these unless asked, even if they seem like natural next steps.

## Development Workflow

- Build one small stage at a time.
- Before making a significant change, explain the plan and list which files will change.
- Make the smallest useful change that accomplishes the current stage — don't add features outside the requested stage.
- Run the test suite after changing any game logic.
- Ask before deleting files.
- Do not create Git commits unless explicitly requested.
- Since this is a learning project, briefly explain the reasoning behind non-obvious choices (why a class vs. a function, why a room vs. a global game list, why the server re-validates a move) as they come up.

## Commands

**Setup:**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Run the server** (must run as a module, not a script, so `chess_logic`/`server` resolve as packages):
```
python -m server.app
```

**Run tests:**
```
pytest                                   # all tests
pytest tests/test_game.py                # one file
pytest tests/test_game.py::test_name     # one test
pytest -k "castle"                       # by keyword
pytest -v                                # verbose output
```

## Testing Rules

- Test chess rules independently of Flask and the browser (`test_board.py`, `test_move_validator.py`, `test_game.py` — no server needed for legality, check, checkmate, castling, en passant, or promotion).
- Test creating and joining a game, and color assignment (creator White, joiner Black) — `test_game_manager.py`.
- Test turn enforcement and rejecting moves on the opponent's pieces.
- Test invalid/unknown and full game codes are rejected.
- Test that games remain isolated from one another.
- Test reconnection (a disconnected slot can be re-attached to the same color).

## Deployment Notes

Deployed to Render via `Procfile` / `render.yaml`, both already in the repo. See `README.md` for exact settings.

- Runs under `gunicorn --worker-class eventlet -w 1` — **exactly one worker**, not a preference but a hard requirement: game state lives in one process's memory (`GameManager`), so more than one worker/instance would split games across processes that don't share state.
- `SECRET_KEY` must be set via environment variable in production (signs the session cookie that carries game/color identity) — falls back to a dev-only constant otherwise.
- `PORT` is read from the environment, not hardcoded.
- `eventlet` is in upstream maintenance/bugfix mode; it still works correctly here. If it's ever dropped, `gevent` is the drop-in alternative (swap it in `requirements.txt`, `Procfile`, `render.yaml`, and `async_mode` in `server/app.py`).
