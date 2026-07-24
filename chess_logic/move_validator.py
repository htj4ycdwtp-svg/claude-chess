from chess_logic.board import index_to_square, square_to_index
from chess_logic.pieces import Color, PieceType

_PAWN_DIRECTION = {
    Color.WHITE: -1,
    Color.BLACK: 1,
}

_PAWN_START_ROW = {
    Color.WHITE: 6,
    Color.BLACK: 1,
}

_KNIGHT_DELTAS = {
    (1, 2), (1, -2), (-1, 2), (-1, -2),
    (2, 1), (2, -1), (-2, 1), (-2, -1),
}


def _sign(n):
    return (n > 0) - (n < 0)


def _is_path_clear(board, from_row, from_col, row_delta, col_delta):
    row_step = _sign(row_delta)
    col_step = _sign(col_delta)
    distance = max(abs(row_delta), abs(col_delta))

    row, col = from_row + row_step, from_col + col_step
    for _ in range(distance - 1):
        if board.get_piece(index_to_square(row, col)) is not None:
            return False
        row += row_step
        col += col_step
    return True


def _is_legal_pawn_move(board, piece, from_row, from_col, row_delta, col_delta, destination):
    direction = _PAWN_DIRECTION[piece.color]

    if col_delta == 0:
        if destination is not None:
            return False
        if row_delta == direction:
            return True
        if from_row == _PAWN_START_ROW[piece.color] and row_delta == 2 * direction:
            mid_square = index_to_square(from_row + direction, from_col)
            return board.get_piece(mid_square) is None
        return False

    if abs(col_delta) == 1 and row_delta == direction:
        return destination is not None

    return False


def is_pawn_attack(color, row_delta, col_delta):
    return row_delta == _PAWN_DIRECTION[color] and abs(col_delta) == 1


def is_legal_knight_move(row_delta, col_delta):
    return (row_delta, col_delta) in _KNIGHT_DELTAS


def is_legal_bishop_move(board, from_row, from_col, row_delta, col_delta):
    if row_delta == 0 or abs(row_delta) != abs(col_delta):
        return False
    return _is_path_clear(board, from_row, from_col, row_delta, col_delta)


def is_legal_rook_move(board, from_row, from_col, row_delta, col_delta):
    if (row_delta == 0) == (col_delta == 0):
        return False
    return _is_path_clear(board, from_row, from_col, row_delta, col_delta)


def is_legal_queen_move(board, from_row, from_col, row_delta, col_delta):
    is_diagonal = row_delta != 0 and abs(row_delta) == abs(col_delta)
    is_straight = (row_delta == 0) != (col_delta == 0)
    if not (is_diagonal or is_straight):
        return False
    return _is_path_clear(board, from_row, from_col, row_delta, col_delta)


def is_legal_king_move(row_delta, col_delta):
    return max(abs(row_delta), abs(col_delta)) == 1


class MoveValidator:
    def is_legal_move(self, board, from_square, to_square):
        if from_square == to_square:
            return False

        piece = board.get_piece(from_square)
        if piece is None:
            return False

        destination = board.get_piece(to_square)
        if destination is not None and destination.color == piece.color:
            return False

        from_row, from_col = square_to_index(from_square)
        to_row, to_col = square_to_index(to_square)
        row_delta = to_row - from_row
        col_delta = to_col - from_col

        if piece.piece_type == PieceType.PAWN:
            return _is_legal_pawn_move(
                board, piece, from_row, from_col, row_delta, col_delta, destination
            )
        if piece.piece_type == PieceType.KNIGHT:
            return is_legal_knight_move(row_delta, col_delta)
        if piece.piece_type == PieceType.BISHOP:
            return is_legal_bishop_move(board, from_row, from_col, row_delta, col_delta)
        if piece.piece_type == PieceType.ROOK:
            return is_legal_rook_move(board, from_row, from_col, row_delta, col_delta)
        if piece.piece_type == PieceType.QUEEN:
            return is_legal_queen_move(board, from_row, from_col, row_delta, col_delta)
        if piece.piece_type == PieceType.KING:
            return is_legal_king_move(row_delta, col_delta)

        return False
