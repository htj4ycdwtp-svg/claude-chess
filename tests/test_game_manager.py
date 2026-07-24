from server.game_manager import GameManager
from chess_logic.pieces import Color


def test_create_game_reserves_creator_as_white():
    manager = GameManager()
    session = manager.create_game()

    assert session.players[Color.WHITE]["assigned"] is True
    assert session.players[Color.WHITE]["sid"] is None
    assert session.players[Color.BLACK]["assigned"] is False


def test_join_game_reserves_joiner_as_black():
    manager = GameManager()
    session = manager.create_game()

    result = manager.join_game(session.code)

    assert result.success is True
    assert result.session.players[Color.BLACK]["assigned"] is True


def test_join_unknown_code_is_rejected():
    manager = GameManager()
    result = manager.join_game("ZZZZ")

    assert result.success is False
    assert result.reason == "not_found"


def test_join_full_game_is_rejected():
    manager = GameManager()
    session = manager.create_game()
    manager.join_game(session.code)

    result = manager.join_game(session.code)

    assert result.success is False
    assert result.reason == "full"


def test_generated_game_codes_are_unique():
    manager = GameManager()
    codes = {manager.create_game().code for _ in range(20)}
    assert len(codes) == 20


def test_attach_socket_connects_a_reserved_color():
    manager = GameManager()
    session = manager.create_game()

    attached = manager.attach_socket(session.code, Color.WHITE, "sid-1")

    assert attached is session
    assert session.players[Color.WHITE]["sid"] == "sid-1"
    assert session.players[Color.WHITE]["connected"] is True


def test_attach_socket_rejects_unassigned_color():
    manager = GameManager()
    session = manager.create_game()

    attached = manager.attach_socket(session.code, Color.BLACK, "sid-1")

    assert attached is None
    assert session.players[Color.BLACK]["sid"] is None


def test_attach_socket_rejects_unknown_code():
    manager = GameManager()
    assert manager.attach_socket("ZZZZ", Color.WHITE, "sid-1") is None


def test_games_remain_isolated_from_one_another():
    manager = GameManager()
    session_a = manager.create_game()
    manager.join_game(session_a.code)
    manager.attach_socket(session_a.code, Color.WHITE, "a-white")
    manager.attach_socket(session_a.code, Color.BLACK, "a-black")

    session_b = manager.create_game()
    manager.join_game(session_b.code)
    manager.attach_socket(session_b.code, Color.WHITE, "b-white")
    manager.attach_socket(session_b.code, Color.BLACK, "b-black")

    session_a.game.make_move("e2", "e4")

    assert session_a.game.turn == Color.BLACK
    assert session_b.game.turn == Color.WHITE
    assert session_b.game.board.get_piece("e4") is None


def test_disconnect_marks_player_disconnected_but_keeps_game():
    manager = GameManager()
    session = manager.create_game()
    manager.attach_socket(session.code, Color.WHITE, "sid-1")

    manager.handle_disconnect("sid-1")

    assert manager.get_session(session.code) is not None
    assert session.players[Color.WHITE]["connected"] is False
    assert session.players[Color.WHITE]["assigned"] is True


def test_reconnect_after_disconnect_reattaches_same_color():
    manager = GameManager()
    session = manager.create_game()
    manager.attach_socket(session.code, Color.WHITE, "sid-1")
    manager.handle_disconnect("sid-1")

    reattached = manager.attach_socket(session.code, Color.WHITE, "sid-2")

    assert reattached is session
    assert session.players[Color.WHITE]["sid"] == "sid-2"
    assert session.players[Color.WHITE]["connected"] is True


def test_restart_resets_game_but_keeps_players():
    manager = GameManager()
    session = manager.create_game()
    manager.join_game(session.code)
    manager.attach_socket(session.code, Color.WHITE, "sid-1")
    manager.attach_socket(session.code, Color.BLACK, "sid-2")
    session.game.make_move("e2", "e4")

    manager.restart(session.code)

    assert session.game.turn == Color.WHITE
    assert session.game.board.get_piece("e4") is None
    assert session.players[Color.WHITE]["sid"] == "sid-1"
    assert session.players[Color.BLACK]["sid"] == "sid-2"
