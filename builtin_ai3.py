from dataclasses import dataclass
from time import sleep, time
from random import choice
from buildaboard import Range, PieceType, Piece, Move, Board, Clock, king, queen, files, ranks

def hash_board(board):
    return hash(tuple((p.type, p.file, p.rank) for p in b.pieces))

def apply_move(board, piece, rank, file):
    return Board(
        [p for p in board.opponent if (p.rank, p.file) != (rank, file)],
        [(Piece(queen if (piece.type != king and rank == 7) else piece.type, rank, file) if p == piece else p) for p in board.player],
        player_turn = not board.player_turn
        )

def eval_b(board):
    total = 0
    for piece in board.player:
        if piece.type == king:
            total += 1000
            total -= piece.rank
        else:
            total += piece.type.price
            total += piece.rank
    for piece in board.opponent:
        if piece.type == king:
            total -= 1000
            total += piece.rank
        else:
            total -= piece.type.flipped.price
            total -= (7 - piece.rank)
    return total

def f(x):
    if x > 0: return x
    else: return 10*x

def play(board, depth):
    if depth == 0: return eval_b(board)
    if not any(p.type == king for p in board.player): return -1000
    moves = [(piece, rank, file) for piece in board.player for (rank, file) in board.generateAllowed(piece)]
    if not moves: return -1000
    move = choice(moves)
    return -play(apply_move(board, *move).flipped, depth-1)

def choosemove(board):
    moves = {}
    for piece in board.player:
        for (rank, file) in board.generateAllowed(piece):
            score = sum(f(-play(apply_move(board, piece, rank, file).flipped, d))/100 for d in range(7) for i in range(40))
            moves[(piece, rank, file)] = score
    top = max(moves, key=moves.get)
    return top

def setup():

    pawn = PieceType(
        Range(0, 1, 0, 0, 0, 0, 0, 0),
        Range(0, 2, 1, 0, 0, 0, 0, 0)
        )
    bishop = PieceType(
        Range(1, 1, 1, 0, 0, 0, 0, 0),
        Range(0, 1, 0, 0, 0, 0, 0, 0)
        )
    rook = PieceType(
        Range(0, 0, 0, 1, 2, 0, 0, 0),
        Range(0, 0, 0, 1, 0, 0, 0, 0)
        )

    return [Piece(pawn, 2, 0),
            Piece(pawn, 2, 1),
            Piece(pawn, 2, 2),
            Piece(pawn, 2, 3),
            Piece(bishop, 1, 1),
            Piece(bishop, 1, 3),
            Piece(rook, 0, 2),
            Piece(rook, 0, 6),
            Piece(king, 0, 0)
            ]

def move(board, clock) -> Move:
    return Move(*choosemove(board))
