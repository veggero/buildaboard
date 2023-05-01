from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True, eq=True)
class Range:
    nw: int
    n: int
    ne: int
    w: int
    e: int
    sw: int
    s: int
    se: int

    @property
    def flipped(s): return Range(s.sw, s.s, s.se, s.w, s.e, s.nw, s.n, s.ne)

movementPrices = Range(3, 4, 3, 2, 2, 1, 1, 1)
attackPrices = Range(4, 5, 4, 3, 3, 2, 2, 2)

def dotProduct(a: Range, b: Range) -> int:
    return sum(getattr(a, property) * getattr(b, property)
        for property in ('n', 'nw', 'ne', 'e', 'w', 's', 'sw', 'se'))

@dataclass(frozen=True, eq=True)
class PieceType:
    attack: Range
    movement: Range

    @property
    def flipped(self):
        return PieceType(self.attack.flipped, self.movement.flipped)

    @property
    def price(self):
        return 10 + dotProduct(attackPrices, self.attack) + \
            dotProduct(movementPrices, self.movement)

queen = PieceType(
    Range(8, 8, 8, 8, 8, 8, 8, 8),
    Range(8, 8, 8, 8, 8, 8, 8, 8)
    )

king = PieceType(
    Range(0, 0, 0, 0, 0, 0, 0, 0),
    Range(1, 1, 1, 1, 1, 1, 1, 1)
    )

@dataclass
class Piece:
    type: PieceType
    rank: int
    file: int

    def __hash__(self): return id(self)
    def __eq__(self, other): return self is other

    @property
    def flipped(self):
        return Piece(self.type.flipped, 7-self.rank, self.file)

@dataclass
class Move:
    piece: Piece
    rank: int
    file: int

    @property
    def flipped(self):
        return Move(self.piece.flipped, 7 - self.rank, self.file)

dirToCoordDelta = {'n': (0, 1), 'nw': (-1, 1), 'ne': (1, 1), 'e': (1, 0),
                   'w': (-1, 0), 's': (0, -1), 'sw': (-1, -1), 'se': (1, -1)}

files, ranks = 'abcdefgh', '12345678'

def pieceAt(pieces, rank, file) -> bool:
    return any(p.file == file and p.rank == rank for p in pieces)

def withinBoard(rank, file):
    return 0 <= rank < 8 and 0 <= file < 8

@dataclass
class Board:
    opponent: list[Piece]
    player: list[Piece]
    player_turn: bool = False

    @property
    def pieces(self): return self.opponent + self.player

    @property
    def all_valid_moves(self): return {
        files[piece.file] + ranks[piece.rank]: [files[file] + ranks[rank]
            for rank, file in self.generateAllowed(piece)]
        for piece in self.pieces
    }

    @property
    def flipped(self): return Board(
            [p.flipped for p in self.player],
            [p.flipped for p in self.opponent],
            player_turn = not self.player_turn
        )

    def generateAllowed(board, piece):
        allowed = []
        for prop in ('n', 'nw', 'ne', 'w', 'e', 'sw', 's', 'se'):
            if board.player_turn != (piece in board.player): continue
            opponents = board.opponent if board.player_turn else board.player
            for i in range(1, 9):
                target_rank = piece.rank + dirToCoordDelta[prop][1] * i
                target_file = piece.file + dirToCoordDelta[prop][0] * i
                if not withinBoard(target_rank, target_file): break
                if (i <= getattr(piece.type.movement, prop) and
                    not pieceAt(board.pieces, target_rank, target_file)) or (
                    i <= getattr(piece.type.attack, prop) and
                    pieceAt(opponents, target_rank, target_file)):
                    allowed.append((target_rank, target_file))
                if pieceAt(board.pieces, target_rank, target_file): break
        return allowed

    def check_move(self, m: Move) -> bool:
        if not withinBoard(m.rank, m.file): return
        source = files[m.piece.file] + ranks[m.piece.rank]
        target = files[m.file] + ranks[m.rank]
        return target in self.all_valid_moves[source]


@dataclass
class Clock:
    plys: int
    time: float
    opponent_time: float
    total_time: int
    increment: int

    last_move_start_time: Optional[int] = None

    @property
    def flipped(self):
        return Clock(self.plys, self.opponent_time, self.time,
                     self.total_time, self.increment)
