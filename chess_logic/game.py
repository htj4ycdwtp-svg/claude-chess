from dataclasses import dataclass
from typing import Optional

from chess_logic.board import Board, index_to_square, square_to_index
from chess_logic.move_validator import (
    MoveValidator,
    is_legal_bishop_move,
    is_legal_king_move,
    is_legal_knight_move,
    is_legal_queen_move,
    is_legal_rook_move,
    is_pawn_attack,
)
from chess_logic.pieces import Color, Piece, PieceType

_PROMOTION_TYPES = {PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT}
_PROMOTION_ROW = {Color.WHITE: 0, Color.BLACK: 7}

_ROOK_HOME_COL = {"kingside": 7, "queenside": 0}
_ROOK_CASTLED_COL = {"kingside": 5, "queenside": 3}
_CASTLE_EMPTY_COLS = {"kingside": [5, 6], "queenside": [1, 2, 3]}
_CASTLE_TRANSIT_COLS = {"kingside": [4, 5, 6], "queenside": [4, 3, 2]}

_CORNER_CASTLING_RIGHTS = {
    "a1": (Color.WHITE, "queenside"),
    "h1": (Color.WHITE, "kingside"),
    "a8": (Color.BLACK, "queenside"),
    "h8": (Color.BLACK, "kingside"),
}


def _opposite(color):
    return Color.BLACK if color == Color.WHITE else Color.WHITE


def _castle_side(special):
    return special.split("_")[1]


@dataclass
class MoveOutcome:
    success: bool
    reason: Optional[str] = None


class Game:
    def __init__(self, board=None, turn=Color.WHITE):
        self.board = board if board is not None else Board()
        self.turn = turn
        self.move_validator = MoveValidator()
        self.en_passant_target = None
        self.castling_rights = {
            Color.WHITE: {"kingside": True, "queenside": True},
            Color.BLACK: {"kingside": True, "queenside": True},
        }
        self.status = "in_progress"
        self.winner = None

    def make_move(self, from_square, to_square, promotion_piece_type=None):
        if self.status in ("checkmate", "stalemate"):
            return MoveOutcome(False, "game_over")

        piece = self.board.get_piece(from_square)
        if piece is None:
            return MoveOutcome(False, "no_piece")
        if piece.color != self.turn:
            return MoveOutcome(False, "not_your_turn")

        special = self._legality(piece, from_square, to_square)
        if special is None:
            return MoveOutcome(False, "illegal_move")

        captured_square = to_square
        if special == "en_passant":
            from_row, _ = square_to_index(from_square)
            _, to_col = square_to_index(to_square)
            captured_square = index_to_square(from_row, to_col)

        self._apply_move_on_board(self.board, piece, from_square, to_square, special, promotion_piece_type)
        self._update_castling_rights(piece, from_square, captured_square)
        self._update_en_passant_target(piece, from_square, to_square)
        self.turn = _opposite(self.turn)
        self._update_status()

        return MoveOutcome(True)

    def piece_at(self, square):
        return self.board.get_piece(square)

    def legal_destinations(self, from_square):
        piece = self.board.get_piece(from_square)
        if piece is None or piece.color != self.turn:
            return []
        destinations = []
        for row, col in self.board.all_squares():
            to_square = index_to_square(row, col)
            if to_square == from_square:
                continue
            if self._legality(piece, from_square, to_square) is not None:
                destinations.append(to_square)
        return destinations

    def reset(self):
        self.__init__()

    def to_dict(self):
        board_state = {
            index_to_square(row, col): {"color": piece.color.value, "type": piece.piece_type.value}
            for (row, col), piece in self.board.occupied_squares()
        }
        return {
            "board": board_state,
            "turn": self.turn.value,
            "status": self.status,
            "winner": self.winner.value if self.winner else None,
        }

    # --- legality ---

    def _legality(self, piece, from_square, to_square):
        special = self._classify_special_move(piece, from_square, to_square)

        if special in ("castle_kingside", "castle_queenside"):
            if not self._is_legal_castle(piece.color, _castle_side(special)):
                return None
        elif special == "en_passant":
            if not self._is_legal_en_passant(piece, from_square, to_square):
                return None
        else:
            if not self.move_validator.is_legal_move(self.board, from_square, to_square):
                return None

        if not self._is_safe_after_move(piece.color, from_square, to_square, special):
            return None

        return special or "normal"

    def _classify_special_move(self, piece, from_square, to_square):
        from_row, from_col = square_to_index(from_square)
        to_row, to_col = square_to_index(to_square)

        if piece.piece_type == PieceType.KING and from_row == to_row and abs(to_col - from_col) == 2:
            return "castle_kingside" if to_col > from_col else "castle_queenside"

        if (
            piece.piece_type == PieceType.PAWN
            and to_col != from_col
            and to_square == self.en_passant_target
        ):
            return "en_passant"

        return None

    def _is_legal_castle(self, color, side):
        if not self.castling_rights[color][side]:
            return False

        home_row = 7 if color == Color.WHITE else 0
        king_square = index_to_square(home_row, 4)
        if self.board.get_piece(king_square) != Piece(color, PieceType.KING):
            return False

        rook_square = index_to_square(home_row, _ROOK_HOME_COL[side])
        if self.board.get_piece(rook_square) != Piece(color, PieceType.ROOK):
            return False

        for col in _CASTLE_EMPTY_COLS[side]:
            if self.board.get_piece(index_to_square(home_row, col)) is not None:
                return False

        opponent = _opposite(color)
        for col in _CASTLE_TRANSIT_COLS[side]:
            if self._is_square_attacked(self.board, index_to_square(home_row, col), opponent):
                return False

        return True

    def _is_legal_en_passant(self, piece, from_square, to_square):
        from_row, from_col = square_to_index(from_square)
        to_row, to_col = square_to_index(to_square)
        if not is_pawn_attack(piece.color, to_row - from_row, to_col - from_col):
            return False
        captured_square = index_to_square(from_row, to_col)
        captured = self.board.get_piece(captured_square)
        return captured is not None and captured.color != piece.color and captured.piece_type == PieceType.PAWN

    def _is_safe_after_move(self, color, from_square, to_square, special):
        piece = self.board.get_piece(from_square)
        simulated = self.board.copy()
        self._apply_move_on_board(simulated, piece, from_square, to_square, special, PieceType.QUEEN)
        king_square = self._find_king_square(simulated, color)
        return not self._is_square_attacked(simulated, king_square, _opposite(color))

    def _has_any_legal_move(self, color):
        for (row, col), piece in self.board.occupied_squares():
            if piece.color != color:
                continue
            from_square = index_to_square(row, col)
            for to_row, to_col in self.board.all_squares():
                to_square = index_to_square(to_row, to_col)
                if from_square == to_square:
                    continue
                if self._legality(piece, from_square, to_square) is not None:
                    return True
        return False

    # --- state mutation ---

    def _apply_move_on_board(self, board, piece, from_square, to_square, special, promotion_piece_type):
        board.set_piece(from_square, None)

        if special == "en_passant":
            from_row, _ = square_to_index(from_square)
            _, to_col = square_to_index(to_square)
            board.set_piece(index_to_square(from_row, to_col), None)
            board.set_piece(to_square, piece)
            return

        if special in ("castle_kingside", "castle_queenside"):
            home_row, _ = square_to_index(from_square)
            board.set_piece(to_square, piece)
            side = _castle_side(special)
            rook_home = index_to_square(home_row, _ROOK_HOME_COL[side])
            rook_dest = index_to_square(home_row, _ROOK_CASTLED_COL[side])
            rook = board.get_piece(rook_home)
            board.set_piece(rook_home, None)
            board.set_piece(rook_dest, rook)
            return

        to_row, _ = square_to_index(to_square)
        if piece.piece_type == PieceType.PAWN and to_row == _PROMOTION_ROW[piece.color]:
            chosen = promotion_piece_type if promotion_piece_type in _PROMOTION_TYPES else PieceType.QUEEN
            board.set_piece(to_square, Piece(piece.color, chosen))
            return

        board.set_piece(to_square, piece)

    def _update_castling_rights(self, piece, from_square, captured_square):
        if piece.piece_type == PieceType.KING:
            self.castling_rights[piece.color]["kingside"] = False
            self.castling_rights[piece.color]["queenside"] = False
        elif piece.piece_type == PieceType.ROOK and from_square in _CORNER_CASTLING_RIGHTS:
            color, side = _CORNER_CASTLING_RIGHTS[from_square]
            if color == piece.color:
                self.castling_rights[color][side] = False

        if captured_square in _CORNER_CASTLING_RIGHTS:
            color, side = _CORNER_CASTLING_RIGHTS[captured_square]
            self.castling_rights[color][side] = False

    def _update_en_passant_target(self, piece, from_square, to_square):
        self.en_passant_target = None
        if piece.piece_type == PieceType.PAWN:
            from_row, _ = square_to_index(from_square)
            to_row, to_col = square_to_index(to_square)
            if abs(to_row - from_row) == 2:
                passed_row = (from_row + to_row) // 2
                self.en_passant_target = index_to_square(passed_row, to_col)

    def _update_status(self):
        color = self.turn
        king_square = self._find_king_square(self.board, color)
        in_check = self._is_square_attacked(self.board, king_square, _opposite(color))
        has_moves = self._has_any_legal_move(color)

        if in_check and not has_moves:
            self.status = "checkmate"
            self.winner = _opposite(color)
        elif not in_check and not has_moves:
            self.status = "stalemate"
            self.winner = None
        elif in_check:
            self.status = "check"
            self.winner = None
        else:
            self.status = "in_progress"
            self.winner = None

    # --- attack detection ---

    def _find_king_square(self, board, color):
        for (row, col), piece in board.occupied_squares():
            if piece.color == color and piece.piece_type == PieceType.KING:
                return index_to_square(row, col)
        return None

    def _is_square_attacked(self, board, square, by_color):
        to_row, to_col = square_to_index(square)
        for (from_row, from_col), attacker in board.occupied_squares():
            if attacker.color != by_color:
                continue
            row_delta = to_row - from_row
            col_delta = to_col - from_col
            if attacker.piece_type == PieceType.PAWN:
                if is_pawn_attack(attacker.color, row_delta, col_delta):
                    return True
            elif attacker.piece_type == PieceType.KNIGHT:
                if is_legal_knight_move(row_delta, col_delta):
                    return True
            elif attacker.piece_type == PieceType.BISHOP:
                if is_legal_bishop_move(board, from_row, from_col, row_delta, col_delta):
                    return True
            elif attacker.piece_type == PieceType.ROOK:
                if is_legal_rook_move(board, from_row, from_col, row_delta, col_delta):
                    return True
            elif attacker.piece_type == PieceType.QUEEN:
                if is_legal_queen_move(board, from_row, from_col, row_delta, col_delta):
                    return True
            elif attacker.piece_type == PieceType.KING:
                if is_legal_king_move(row_delta, col_delta):
                    return True
        return False
