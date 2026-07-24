import os
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session
from flask_socketio import SocketIO

from chess_logic.pieces import Color
from server.game_manager import GameManager
from server.socket_handlers import register_handlers

BASE_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

socketio = SocketIO(app, async_mode="eventlet")
game_manager = GameManager()
register_handlers(socketio, game_manager)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/create", methods=["POST"])
def create_game_route():
    game_session = game_manager.create_game()
    session["game_code"] = game_session.code
    session["color"] = Color.WHITE.value
    return jsonify({"game_code": game_session.code})


@app.route("/api/join", methods=["POST"])
def join_game_route():
    data = request.get_json(silent=True) or {}
    code = str(data.get("game_code", "")).strip().upper()

    result = game_manager.join_game(code)
    if not result.success:
        status_code = 404 if result.reason == "not_found" else 409
        return jsonify({"error": result.reason}), status_code

    session["game_code"] = code
    session["color"] = Color.BLACK.value
    return jsonify({"game_code": code})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    running_under_debugger = "pydevd" in sys.modules
    socketio.run(app, host="0.0.0.0", port=port, debug=True, use_reloader=not running_under_debugger)
