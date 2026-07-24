import pytest

from chess_logic.board import Board
from chess_logic.move_validator import MoveValidator
from chess_logic.pieces import Color, Piece, PieceType


@pytest.fixture
def validator():
    return MoveValidator()


# --- Pawn ---

def test_pawn_single_step_forward_is_legal(validator):
    board = Board.empty()
    board.set_piece("e2", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "e2", "e3") is True


def test_pawn_double_step_from_start_is_legal(validator):
    board = Board.empty()
    board.set_piece("e2", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "e2", "e4") is True


def test_pawn_double_step_not_from_start_is_illegal(validator):
    board = Board.empty()
    board.set_piece("e3", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "e3", "e5") is False


def test_pawn_double_step_blocked_is_illegal(validator):
    board = Board.empty()
    board.set_piece("e2", Piece(Color.WHITE, PieceType.PAWN))
    board.set_piece("e3", Piece(Color.BLACK, PieceType.PAWN))
    assert validator.is_legal_move(board, "e2", "e4") is False


def test_pawn_cannot_move_forward_onto_occupied_square(validator):
    board = Board.empty()
    board.set_piece("e2", Piece(Color.WHITE, PieceType.PAWN))
    board.set_piece("e3", Piece(Color.BLACK, PieceType.PAWN))
    assert validator.is_legal_move(board, "e2", "e3") is False


def test_pawn_diagonal_capture_is_legal(validator):
    board = Board.empty()
    board.set_piece("e4", Piece(Color.WHITE, PieceType.PAWN))
    board.set_piece("d5", Piece(Color.BLACK, PieceType.PAWN))
    assert validator.is_legal_move(board, "e4", "d5") is True


def test_pawn_diagonal_move_onto_empty_square_is_illegal(validator):
    board = Board.empty()
    board.set_piece("e4", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "e4", "d5") is False


def test_black_pawn_advances_toward_increasing_rows(validator):
    board = Board.empty()
    board.set_piece("e7", Piece(Color.BLACK, PieceType.PAWN))
    assert validator.is_legal_move(board, "e7", "e6") is True
    assert validator.is_legal_move(board, "e7", "e5") is True
    assert validator.is_legal_move(board, "e7", "e8") is False


# --- Knight ---

def test_knight_l_shaped_move_is_legal(validator):
    board = Board.empty()
    board.set_piece("b1", Piece(Color.WHITE, PieceType.KNIGHT))
    assert validator.is_legal_move(board, "b1", "c3") is True
    assert validator.is_legal_move(board, "b1", "a3") is True


def test_knight_non_l_move_is_illegal(validator):
    board = Board.empty()
    board.set_piece("b1", Piece(Color.WHITE, PieceType.KNIGHT))
    assert validator.is_legal_move(board, "b1", "b3") is False


def test_knight_jumps_over_pieces(validator):
    board = Board.empty()
    board.set_piece("b1", Piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece("b2", Piece(Color.WHITE, PieceType.PAWN))
    board.set_piece("c2", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "b1", "c3") is True


def test_knight_cannot_capture_friendly_piece(validator):
    board = Board.empty()
    board.set_piece("b1", Piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece("c3", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "b1", "c3") is False


def test_knight_can_capture_enemy_piece(validator):
    board = Board.empty()
    board.set_piece("b1", Piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece("c3", Piece(Color.BLACK, PieceType.PAWN))
    assert validator.is_legal_move(board, "b1", "c3") is True


# --- Bishop ---

def test_bishop_diagonal_move_is_legal(validator):
    board = Board.empty()
    board.set_piece("d4", Piece(Color.WHITE, PieceType.BISHOP))
    assert validator.is_legal_move(board, "d4", "g7") is True


def test_bishop_straight_move_is_illegal(validator):
    board = Board.empty()
    board.set_piece("d4", Piece(Color.WHITE, PieceType.BISHOP))
    assert validator.is_legal_move(board, "d4", "d7") is False


def test_bishop_blocked_path_is_illegal(validator):
    board = Board.empty()
    board.set_piece("d4", Piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece("f6", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "d4", "g7") is False


# --- Rook ---

def test_rook_straight_move_is_legal(validator):
    board = Board.empty()
    board.set_piece("a1", Piece(Color.WHITE, PieceType.ROOK))
    assert validator.is_legal_move(board, "a1", "a5") is True


def test_rook_diagonal_move_is_illegal(validator):
    board = Board.empty()
    board.set_piece("a1", Piece(Color.WHITE, PieceType.ROOK))
    assert validator.is_legal_move(board, "a1", "b2") is False


def test_rook_blocked_path_is_illegal(validator):
    board = Board.empty()
    board.set_piece("a1", Piece(Color.WHITE, PieceType.ROOK))
    board.set_piece("a3", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "a1", "a5") is False


def test_rook_cannot_capture_friendly_piece(validator):
    board = Board.empty()
    board.set_piece("a1", Piece(Color.WHITE, PieceType.ROOK))
    board.set_piece("a5", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "a1", "a5") is False


def test_rook_can_capture_enemy_piece(validator):
    board = Board.empty()
    board.set_piece("a1", Piece(Color.WHITE, PieceType.ROOK))
    board.set_piece("a5", Piece(Color.BLACK, PieceType.PAWN))
    assert validator.is_legal_move(board, "a1", "a5") is True


# --- Queen ---

def test_queen_diagonal_move_is_legal(validator):
    board = Board.empty()
    board.set_piece("d4", Piece(Color.WHITE, PieceType.QUEEN))
    assert validator.is_legal_move(board, "d4", "a7") is True


def test_queen_straight_move_is_legal(validator):
    board = Board.empty()
    board.set_piece("d4", Piece(Color.WHITE, PieceType.QUEEN))
    assert validator.is_legal_move(board, "d4", "d8") is True


def test_queen_knight_shaped_move_is_illegal(validator):
    board = Board.empty()
    board.set_piece("d4", Piece(Color.WHITE, PieceType.QUEEN))
    assert validator.is_legal_move(board, "d4", "f5") is False


def test_queen_blocked_path_is_illegal(validator):
    board = Board.empty()
    board.set_piece("d4", Piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece("d6", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "d4", "d8") is False


# --- King ---

def test_king_single_step_is_legal(validator):
    board = Board.empty()
    board.set_piece("e1", Piece(Color.WHITE, PieceType.KING))
    assert validator.is_legal_move(board, "e1", "e2") is True
    assert validator.is_legal_move(board, "e1", "d2") is True


def test_king_multi_square_move_is_illegal(validator):
    board = Board.empty()
    board.set_piece("e1", Piece(Color.WHITE, PieceType.KING))
    assert validator.is_legal_move(board, "e1", "e3") is False


def test_king_cannot_capture_friendly_piece(validator):
    board = Board.empty()
    board.set_piece("e1", Piece(Color.WHITE, PieceType.KING))
    board.set_piece("e2", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "e1", "e2") is False


def test_king_can_capture_adjacent_enemy_piece(validator):
    board = Board.empty()
    board.set_piece("e1", Piece(Color.WHITE, PieceType.KING))
    board.set_piece("e2", Piece(Color.BLACK, PieceType.PAWN))
    assert validator.is_legal_move(board, "e1", "e2") is True


# --- General API behavior ---

def test_no_piece_at_source_returns_false(validator):
    board = Board.empty()
    assert validator.is_legal_move(board, "e2", "e4") is False


def test_from_square_equal_to_to_square_is_illegal(validator):
    board = Board.empty()
    board.set_piece("e2", Piece(Color.WHITE, PieceType.PAWN))
    assert validator.is_legal_move(board, "e2", "e2") is False


def test_validator_does_not_mutate_board(validator):
    board = Board.empty()
    pawn = Piece(Color.WHITE, PieceType.PAWN)
    board.set_piece("e2", pawn)

    validator.is_legal_move(board, "e2", "e4")

    assert board.get_piece("e2") == pawn
    assert board.get_piece("e4") is None
