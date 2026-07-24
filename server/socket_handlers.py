from flask import request, session
from flask_socketio import emit, join_room

from chess_logic.pieces import Color, PieceType

_PROMOTION_BY_NAME = {
    "queen": PieceType.QUEEN,
    "rook": PieceType.ROOK,
    "bishop": PieceType.BISHOP,
    "knight": PieceType.KNIGHT,
}


def _is_valid_square(square):
    return (
        isinstance(square, str)
        and len(square) == 2
        and square[0] in "abcdefgh"
        and square[1] in "12345678"
    )


def _opponent(color):
    return Color.BLACK if color == Color.WHITE else Color.WHITE


def register_handlers(socketio, game_manager):
    def _current_game_session():
        code = session.get("game_code")
        if not code:
            return None, None
        color_name = session.get("color")
        color = Color(color_name) if color_name else None
        return game_manager.get_session(code), color

    @socketio.on("connect")
    def handle_connect():
        code = session.get("game_code")
        color_name = session.get("color")
        if not code or not color_name:
            return

        color = Color(color_name)
        game_session = game_manager.attach_socket(code, color, request.sid)
        if game_session is None:
            return

        join_room(code)
        payload = game_session.game.to_dict()
        payload["your_color"] = color.value
        payload["game_code"] = code
        payload["opponent_connected"] = game_session.players[_opponent(color)]["connected"]
        emit("state_update", payload)
        emit("opponent_status", {"connected": True}, room=code, include_self=False)

    @socketio.on("disconnect")
    def handle_disconnect():
        game_session = game_manager.handle_disconnect(request.sid)
        if game_session is not None:
            emit("opponent_status", {"connected": False}, room=game_session.code, include_self=False)

    @socketio.on("get_legal_moves")
    def handle_get_legal_moves(data):
        game_session, _ = _current_game_session()
        if game_session is None:
            return {"destinations": []}

        square = (data or {}).get("square")
        if not _is_valid_square(square):
            return {"destinations": []}

        return {"destinations": game_session.game.legal_destinations(square)}

    @socketio.on("make_move")
    def handle_make_move(data):
        game_session, color = _current_game_session()
        if game_session is None or color is None:
            emit("move_rejected", {"reason": "not_in_game"})
            return

        if game_session.game.turn != color:
            emit("move_rejected", {"reason": "not_your_turn"})
            return

        data = data or {}
        from_square = data.get("from")
        to_square = data.get("to")
        if not _is_valid_square(from_square) or not _is_valid_square(to_square):
            emit("move_rejected", {"reason": "invalid_square"})
            return

        promotion_piece_type = _PROMOTION_BY_NAME.get(data.get("promotion"))

        piece = game_session.game.piece_at(from_square)
        if piece is None or piece.color != color:
            emit("move_rejected", {"reason": "not_your_piece"})
            return

        result = game_session.game.make_move(from_square, to_square, promotion_piece_type=promotion_piece_type)
        if not result.success:
            emit("move_rejected", {"reason": result.reason})
            return

        emit("state_update", game_session.game.to_dict(), room=game_session.code)

    @socketio.on("restart_game")
    def handle_restart_game():
        code = session.get("game_code")
        if not code:
            return
        game_session = game_manager.restart(code)
        if game_session is not None:
            emit("state_update", game_session.game.to_dict(), room=code)
