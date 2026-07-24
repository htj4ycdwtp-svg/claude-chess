from chess_logic.pieces import Color, Piece, PieceType

SIZE = 8

_BACK_RANK_ORDER = [
    PieceType.ROOK,
    PieceType.KNIGHT,
    PieceType.BISHOP,
    PieceType.QUEEN,
    PieceType.KING,
    PieceType.BISHOP,
    PieceType.KNIGHT,
    PieceType.ROOK,
]


def square_to_index(square):
    file_char, rank_char = square[0], square[1]
    col = ord(file_char) - ord("a")
    row = SIZE - int(rank_char)
    return row, col


def index_to_square(row, col):
    file_char = chr(ord("a") + col)
    rank = SIZE - row
    return f"{file_char}{rank}"


class Board:
    def __init__(self, populate_standard_position=True):
        self._grid = [[None] * SIZE for _ in range(SIZE)]
        if populate_standard_position:
            self._place_starting_position()

    @classmethod
    def empty(cls):
        return cls(populate_standard_position=False)

    def get_piece(self, square):
        row, col = square_to_index(square)
        return self._grid[row][col]

    def set_piece(self, square, piece):
        row, col = square_to_index(square)
        self._grid[row][col] = piece

    def copy(self):
        new_board = Board.empty()
        new_board._grid = [row[:] for row in self._grid]
        return new_board

    def all_squares(self):
        for row in range(SIZE):
            for col in range(SIZE):
                yield row, col

    def occupied_squares(self):
        for row, col in self.all_squares():
            piece = self._grid[row][col]
            if piece is not None:
                yield (row, col), piece

    def _place_starting_position(self):
        for col, piece_type in enumerate(_BACK_RANK_ORDER):
            self._grid[0][col] = Piece(Color.BLACK, piece_type)
            self._grid[7][col] = Piece(Color.WHITE, piece_type)
        for col in range(SIZE):
            self._grid[1][col] = Piece(Color.BLACK, PieceType.PAWN)
            self._grid[6][col] = Piece(Color.WHITE, PieceType.PAWN)
