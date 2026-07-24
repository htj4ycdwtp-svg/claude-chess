# Online Chess

A from-scratch, two-player, real-time chess game. Python chess engine (no external chess library), Flask + Flask-SocketIO server, and a minimal HTML/CSS/vanilla-JS frontend. Built as a learning project — see `CLAUDE.md` for the architecture and design rationale.

## Features

- Standard chess rules implemented by hand: legal movement for every piece, captures, check, checkmate, stalemate, castling, en passant, pawn promotion
- Create a game and get a short code; a second player joins with that code
- Creator plays White, joiner plays Black
- Server-authoritative move validation — the browser only sends move *requests*
- Isolated Socket.IO room per game (games never affect each other)
- Reconnection support (reload the page and rejoin your in-progress game)
- Restart button

## Local setup

Requires Python 3.11+.

```
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running locally

```
python server/app.py
```

Then open `http://127.0.0.1:5000` in a browser.

## Running the tests

```
pytest                 # all tests
pytest tests/test_game.py                # one file
pytest tests/test_game.py::test_name     # one test
pytest -k "castle"     # by keyword
pytest -v              # verbose output
```

## Testing multiplayer locally with two browser sessions

Socket.IO identifies a player via a server-side session cookie, so two tabs of the *same* browser will share one cookie and collide. To test both sides at once, use two separate cookie jars, for example:

1. Open `http://127.0.0.1:5000` in a normal window. Click **Create Game** and note the 4-character game code shown.
2. Open a **second, different browser** (or an incognito/private window) and go to the same URL. Enter the game code and click **Join Game**.
3. The first window is White, the second is Black. Moves made in either window update both boards immediately.
4. To test reconnection: reload the page in either window — it should automatically rejoin the same game as the same color.
5. **Restart Game** resets the board for both players without leaving the room.

## Deploying to Render

This repo includes `render.yaml`, so Render can pick up the service configuration automatically ("New +" → "Blueprint", point it at this repo).

**Exact settings** (if configuring a Web Service manually instead of via the blueprint):

- **Environment:** Python 3
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT server.app:app`
- **Instance count / workers: exactly 1.** Game state is kept in server memory (no database) — running more than one worker process or instance would split games across processes that don't share state. Do not scale this service horizontally in its current form.
- **Environment variables:**
  - `SECRET_KEY` — set to a random value (Render's "Generate Value" option works). This signs the session cookie that identifies which game/color a browser belongs to; without it, sessions won't persist correctly across deploys/restarts.
  - `PYTHON_VERSION` — e.g. `3.12.4`, or whatever current Render-supported version you prefer.

Render provides `PORT` automatically; the start command binds to it.

## Known limitations

- **In-memory state only.** All active games live in the server process's memory. A server restart (including a Render redeploy) clears every in-progress game. There is intentionally no database in this version.
- **Single worker only**, for the reason above — this app cannot be horizontally scaled without adding shared storage (e.g. Redis) for game state, which is out of scope here.
- **No move history / no draw offers / no resignation** — only checkmate and stalemate end a game; there's no way to claim a draw or resign.
- **`eventlet` is in maintenance/bugfix mode upstream** (its maintainers now recommend new projects consider alternatives). It still works correctly here; if it's ever dropped, swap `eventlet` for `gevent` in `requirements.txt`, `Procfile`, `render.yaml`, and `async_mode` in `server/app.py`.
- Promotion, if requested, defaults to a queen if the client sends an invalid or missing choice.
