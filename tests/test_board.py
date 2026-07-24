from chess_logic.board import Board
from chess_logic.pieces import Color, Piece, PieceType


def test_board_has_64_squares():
    board = Board()
    assert len(list(board.all_squares())) == 64


def test_each_side_has_16_pieces():
    board = Board()
    white = [p for _, p in board.occupied_squares() if p.color == Color.WHITE]
    black = [p for _, p in board.occupied_squares() if p.color == Color.BLACK]
    assert len(white) == 16
    assert len(black) == 16


def test_each_side_has_8_pawns():
    board = Board()
    for color in (Color.WHITE, Color.BLACK):
        pawns = [
            p
            for _, p in board.occupied_squares()
            if p.color == color and p.piece_type == PieceType.PAWN
        ]
        assert len(pawns) == 8


def test_both_kings_exist():
    board = Board()
    for color in (Color.WHITE, Color.BLACK):
        kings = [
            p
            for _, p in board.occupied_squares()
            if p.color == color and p.piece_type == PieceType.KING
        ]
        assert len(kings) == 1


def test_starting_positions_are_correct():
    board = Board()

    assert board.get_piece("e1") == Piece(Color.WHITE, PieceType.KING)
    assert board.get_piece("e8") == Piece(Color.BLACK, PieceType.KING)
    assert board.get_piece("d1") == Piece(Color.WHITE, PieceType.QUEEN)
    assert board.get_piece("d8") == Piece(Color.BLACK, PieceType.QUEEN)
    assert board.get_piece("a1") == Piece(Color.WHITE, PieceType.ROOK)
    assert board.get_piece("h1") == Piece(Color.WHITE, PieceType.ROOK)
    assert board.get_piece("a8") == Piece(Color.BLACK, PieceType.ROOK)
    assert board.get_piece("h8") == Piece(Color.BLACK, PieceType.ROOK)
    assert board.get_piece("a2") == Piece(Color.WHITE, PieceType.PAWN)
    assert board.get_piece("a7") == Piece(Color.BLACK, PieceType.PAWN)
    assert board.get_piece("e4") is None
    assert board.get_piece("e5") is None
