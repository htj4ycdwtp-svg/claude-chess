import random
import string
from dataclasses import dataclass, field
from typing import Optional

from chess_logic.game import Game
from chess_logic.pieces import Color

_CODE_LENGTH = 4
_CODE_ALPHABET = "".join(c for c in string.ascii_uppercase + string.digits if c not in "0O1IL")


def _generate_code():
    return "".join(random.choices(_CODE_ALPHABET, k=_CODE_LENGTH))


def _new_player_slot():
    return {"assigned": False, "sid": None, "connected": False}


@dataclass
class GameSession:
    code: str
    game: Game = field(default_factory=Game)
    players: dict = field(
        default_factory=lambda: {Color.WHITE: _new_player_slot(), Color.BLACK: _new_player_slot()}
    )

    def color_for_sid(self, sid):
        for color, info in self.players.items():
            if info["sid"] == sid:
                return color
        return None


@dataclass
class JoinResult:
    success: bool
    reason: Optional[str] = None
    session: Optional[GameSession] = None


class GameManager:
    """
    Create/join reserve a color slot over HTTP (so Flask can set a session
    cookie). The actual Socket.IO connection attaches to that reservation
    afterward via attach_socket, using the cookie as proof of identity —
    this is also how a reconnect (fresh socket, same browser session) works.
    """

    def __init__(self):
        self._sessions = {}

    def create_game(self):
        code = _generate_code()
        while code in self._sessions:
            code = _generate_code()

        session = GameSession(code=code)
        session.players[Color.WHITE]["assigned"] = True
        self._sessions[code] = session
        return session

    def join_game(self, code):
        session = self._sessions.get(code)
        if session is None:
            return JoinResult(False, "not_found")
        if session.players[Color.BLACK]["assigned"]:
            return JoinResult(False, "full")

        session.players[Color.BLACK]["assigned"] = True
        return JoinResult(True, session=session)

    def get_session(self, code):
        return self._sessions.get(code)

    def attach_socket(self, code, color, sid):
        session = self._sessions.get(code)
        if session is None or not session.players.get(color, {}).get("assigned"):
            return None
        session.players[color]["sid"] = sid
        session.players[color]["connected"] = True
        return session

    def restart(self, code):
        session = self._sessions.get(code)
        if session is None:
            return None
        session.game.reset()
        return session

    def handle_disconnect(self, sid):
        for session in self._sessions.values():
            color = session.color_for_sid(sid)
            if color is not None:
                session.players[color]["sid"] = None
                session.players[color]["connected"] = False
                return session
        return None
