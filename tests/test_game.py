from chess_logic.board import Board
from chess_logic.game import Game
from chess_logic.pieces import Color, Piece, PieceType


# --- Turn enforcement ---

def test_white_moves_first_from_standard_start():
    game = Game()
    result = game.make_move("e2", "e4")
    assert result.success is True
    assert game.turn == Color.BLACK


def test_black_cannot_move_before_white():
    game = Game()
    result = game.make_move("e7", "e5")
    assert result.success is False
    assert result.reason == "not_your_turn"
    assert game.turn == Color.WHITE


def test_white_cannot_move_twice_in_a_row():
    game = Game()
    game.make_move("e2", "e4")
    result = game.make_move("d2", "d4")
    assert result.success is False
    assert result.reason == "not_your_turn"


# --- Basic moves / captures ---

def test_capture_removes_opposing_piece():
    board = Board.empty()
    board.set_piece("e1", Piece(Color.WHITE, PieceType.KING))
    board.set_piece("e8", Piece(Color.BLACK, PieceType.KING))
    board.set_piece("e4", Piece(Color.WHITE, PieceType.PAWN))
    board.set_piece("d5", Piece(Color.BLACK, PieceType.PAWN))
    game = Game(board=board, turn=Color.WHITE)

    result = game.make_move("e4", "d5")

    assert result.success is True
    assert game.board.get_piece("d5") == Piece(Color.WHITE, PieceType.PAWN)
    assert game.board.get_piece("e4") is None


def test_illegal_move_is_rejected_and_state_unchanged():
    game = Game()
    result = game.make_move("e2", "e5")
    assert result.success is False
    assert result.reason == "illegal_move"
    assert game.turn == Color.WHITE
    assert game.board.get_piece("e2") == Piece(Color.WHITE, PieceType.PAWN)


def test_move_from_empty_square_is_rejected():
    game = Game()
    result = game.make_move("e4", "e5")
    assert result.success is False
    assert result.reason == "no_piece"


# --- Check / checkmate / stalemate ---

def test_check_is_detected():
    board = Board.empty()
    board.set_piece("e1", Piece(Color.WHITE, PieceType.KING))
    board.set_piece("h8", Piece(Color.BLACK, PieceType.KING))
    board.set_piece("e8", Piece(Color.BLACK, PieceType.ROOK))
    game = Game(board=board, turn=Color.BLACK)

    result = game.make_move("e8", "e7")

    assert result.success is True
    assert game.status == "check"
    assert game.winner is None


def test_checkmate_is_detected():
    board = Board.empty()
    board.set_piece("h1", Piece(Color.WHITE, PieceType.KING))
    board.set_piece("g2", Piece(Color.WHITE, PieceType.PAWN))
    board.set_piece("h2", Piece(Color.WHITE, PieceType.PAWN))
    board.set_piece("a8", Piece(Color.BLACK, PieceType.KING))
    board.set_piece("a2", Piece(Color.BLACK, PieceType.ROOK))
    game = Game(board=board, turn=Color.BLACK)

    result = game.make_move("a2", "a1")

    assert result.success is True
    assert game.status == "checkmate"
    assert game.winner == Color.BLACK


def test_stalemate_is_detected():
    board = Board.empty()
    board.set_piece("a1", Piece(Color.WHITE, PieceType.KING))
    board.set_piece("c2", Piece(Color.BLACK, PieceType.KING))
    board.set_piece("b5", Piece(Color.BLACK, PieceType.QUEEN))
    game = Game(board=board, turn=Color.BLACK)

    result = game.make_move("b5", "b3")

    assert result.success is True
    assert game.status == "stalemate"
    assert game.winner is None


def test_move_that_would_leave_own_king_in_check_is_illegal():
    board = Board.empty()
    board.set_piece("e1", Piece(Color.WHITE, PieceType.KING))
    board.set_piece("e2", Piece(Color.WHITE, PieceType.PAWN))
    board.set_piece("e8", Piece(Color.BLACK, PieceType.ROOK))
    board.set_piece("h8", Piece(Color.BLACK, PieceType.KING))
    game = Game(board=board, turn=Color.WHITE)

    # Moving the pawn off the e-file would expose the king to the rook.
    result = game.make_move("e2", "d3")

    assert result.success is False
    assert result.reason == "illegal_move"


# --- Castling ---

def _castling_board(white_rook_square, extra=None):
    board = Board.empty()
    board.set_piece("e1", Piece(Color.WHITE, PieceType.KING))
    board.set_piece(white_rook_square, Piece(Color.WHITE, PieceType.ROOK))
    board.set_piece("a8", Piece(Color.BLACK, PieceType.KING))
    if extra:
        for square, piece in extra.items():
            board.set_piece(square, piece)
    return board


def test_kingside_castle_is_legal_and_moves_both_pieces():
    board = _castling_board("h1")
    game = Game(board=board, turn=Color.WHITE)

    result = game.make_move("e1", "g1")

    assert result.success is True
    assert game.board.get_piece("g1") == Piece(Color.WHITE, PieceType.KING)
    assert game.board.get_piece("f1") == Piece(Color.WHITE, PieceType.ROOK)
    assert game.board.get_piece("e1") is None
    assert game.board.get_piece("h1") is None
    assert game.castling_rights[Color.WHITE]["kingside"] is False
    assert game.castling_rights[Color.WHITE]["queenside"] is False


def test_queenside_castle_is_legal_and_moves_both_pieces():
    board = _castling_board("a1")
    game = Game(board=board, turn=Color.WHITE)

    result = game.make_move("e1", "c1")

    assert result.success is True
    assert game.board.get_piece("c1") == Piece(Color.WHITE, PieceType.KING)
    assert game.board.get_piece("d1") == Piece(Color.WHITE, PieceType.ROOK)
    assert game.board.get_piece("a1") is None
    assert game.board.get_piece("e1") is None


def test_castle_blocked_by_occupied_square_is_illegal():
    board = _castling_board("h1", extra={"f1": Piece(Color.WHITE, PieceType.BISHOP)})
    game = Game(board=board, turn=Color.WHITE)

    result = game.make_move("e1", "g1")

    assert result.success is False
    assert game.board.get_piece("e1") == Piece(Color.WHITE, PieceType.KING)


def test_castle_while_in_check_is_illegal():
    board = _castling_board("h1", extra={"e8": Piece(Color.BLACK, PieceType.ROOK)})
    board.set_piece("a8", None)
    board.set_piece("h8", Piece(Color.BLACK, PieceType.KING))
    game = Game(board=board, turn=Color.WHITE)

    result = game.make_move("e1", "g1")

    assert result.success is False


def test_castle_through_attacked_square_is_illegal():
    board = _castling_board("h1", extra={"f8": Piece(Color.BLACK, PieceType.ROOK)})
    board.set_piece("a8", None)
    board.set_piece("h8", Piece(Color.BLACK, PieceType.KING))
    game = Game(board=board, turn=Color.WHITE)

    result = game.make_move("e1", "g1")

    assert result.success is False


def test_castle_rejected_once_rights_are_lost():
    board = _castling_board("h1")
    game = Game(board=board, turn=Color.WHITE)
    game.castling_rights[Color.WHITE]["kingside"] = False

    result = game.make_move("e1", "g1")

    assert result.success is False


# --- En passant ---

def _en_passant_board():
    board = Board.empty()
    board.set_piece("a1", Piece(Color.WHITE, PieceType.KING))
    board.set_piece("a8", Piece(Color.BLACK, PieceType.KING))
    board.set_piece("e5", Piece(Color.WHITE, PieceType.PAWN))
    board.set_piece("d7", Piece(Color.BLACK, PieceType.PAWN))
    return board


def test_en_passant_capture_is_legal_immediately_after_double_step():
    board = _en_passant_board()
    game = Game(board=board, turn=Color.BLACK)

    game.make_move("d7", "d5")
    assert game.en_passant_target == "d6"

    result = game.make_move("e5", "d6")

    assert result.success is True
    assert game.board.get_piece("d6") == Piece(Color.WHITE, PieceType.PAWN)
    assert game.board.get_piece("d5") is None
    assert game.board.get_piece("e5") is None


def test_en_passant_expires_after_one_move():
    board = _en_passant_board()
    game = Game(board=board, turn=Color.BLACK)

    game.make_move("d7", "d5")
    game.make_move("a1", "b1")
    game.make_move("a8", "b8")

    result = game.make_move("e5", "d6")

    assert result.success is False


# --- Promotion ---

def _promotion_board():
    board = Board.empty()
    board.set_piece("e1", Piece(Color.WHITE, PieceType.KING))
    board.set_piece("e8", Piece(Color.BLACK, PieceType.KING))
    board.set_piece("a7", Piece(Color.WHITE, PieceType.PAWN))
    return board


def test_pawn_promotes_to_queen_by_default():
    board = _promotion_board()
    game = Game(board=board, turn=Color.WHITE)

    result = game.make_move("a7", "a8")

    assert result.success is True
    assert game.board.get_piece("a8") == Piece(Color.WHITE, PieceType.QUEEN)


def test_pawn_promotes_to_requested_piece_type():
    board = _promotion_board()
    game = Game(board=board, turn=Color.WHITE)

    result = game.make_move("a7", "a8", promotion_piece_type=PieceType.KNIGHT)

    assert result.success is True
    assert game.board.get_piece("a8") == Piece(Color.WHITE, PieceType.KNIGHT)


# --- Restart ---

def test_reset_restores_standard_starting_state():
    game = Game()
    game.make_move("e2", "e4")

    game.reset()

    assert game.turn == Color.WHITE
    assert game.status == "in_progress"
    assert game.board.get_piece("e2") == Piece(Color.WHITE, PieceType.PAWN)
    assert game.board.get_piece("e4") is None


# --- Legal destinations (used for client-side highlighting) ---

def test_legal_destinations_for_opening_pawn():
    game = Game()
    destinations = set(game.legal_destinations("e2"))
    assert destinations == {"e3", "e4"}


def test_legal_destinations_empty_for_opponent_piece():
    game = Game()
    assert game.legal_destinations("e7") == []
