from dataclasses import dataclass
from time import sleep, time
from random import choice, random
from pprint import pprint
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
            total += 10000
            total -= piece.rank
        else:
            total += piece.type.price
            total += piece.rank
    for piece in board.opponent:
        if piece.type == king:
            total -= 10000
            total += piece.rank
        else:
            total -= piece.type.flipped.price
            total -= (7 - piece.rank)
    return total

def eval_moves(board, depth, cache, timelimit, cachesize):
    assert board.player_turn, "Something went wrong with turns"
    if not any(p.type == king for p in board.player): return -10000, None, None
    if time() > timelimit: depth = min(depth, 1)
    moves = {}

    if cache:
        for key in list(sorted(cache, key=lambda x: cache[x][0], reverse=True))[:cachesize]:
            if cache[key][0] > 9000: return 10000, cache[key][1], None
            if depth == 0:
                moves[key] = cache[key]
            else:
                topval, _, subm = eval_moves(nb := cache[key][1], depth-1, cache[key][2], timelimit, cachesize)
                moves[key] = (-topval, nb, subm)

    else:
        for piece in board.player:
            allowed = board.generateAllowed(piece)
            for (rank, file) in allowed:
                new_board = apply_move(board, piece, rank, file)

                flag = False
                if rank == 7 and piece.type != king and piece.type != queen and depth == 0:
                    depth += 1
                    flag = True

                if depth == 0:
                    moves[(piece, rank, file)] = (eval_b(new_board), new_board.flipped, None)
                else:
                    topval, _, subm = eval_moves(nb := new_board.flipped, depth-1, None, timelimit, cachesize)
                    moves[(piece, rank, file)] = (-topval, nb, subm)

                if flag:
                    depth -= 1
                    flag = False

    if not moves: return -10000, None, None
    top = max(moves, key=lambda x: moves[x][0])
    return moves[top][0], top, moves

def setup():

    if random() > .5:

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
                Piece(rook, 0, 1),
                Piece(rook, 0, 5),
                Piece(king, 0, 0)
                ]

    else:
        pawn = PieceType(
            Range(0, 1, 0, 0, 0, 0, 0, 0),
            Range(0, 1, 0, 0, 0, 0, 0, 0)
            )
        return [Piece(pawn, 2, 3),
                Piece(pawn, 2, 4),
                Piece(pawn, 1, 0),
                Piece(pawn, 1, 1),
                Piece(pawn, 1, 2),
                Piece(pawn, 1, 3),
                Piece(pawn, 1, 4),
                Piece(pawn, 1, 5),
                Piece(pawn, 1, 6),
                Piece(pawn, 1, 7),
                Piece(king, 0, 3),
                ]


def trace(moves, inv=-1):
    if not moves: return 'xxx'
    piece, rank, file = max(moves, key=lambda x: moves[x][0])
    if m := moves[(piece, rank, file)][2]:
        t, m = trace(m, inv*-1)
    else: t, m = '', None
    return (f'{piece.rank}:{piece.file} → {rank}:{file} ({moves[(piece, rank, file)][0]} - {eval_b(moves[(piece, rank, file)][1])});  ' + t, m if m else repr_board(moves[(piece, rank, file)][1]))

def repr_board(board): return eval_b(board)

def choosemove(board, maxtime):
    moves, oldmoves = None, None
    start = time()
    depth = 2
    cachesize = {1: 9, 2: 8, 3: 7, 4: 6, 5: 5, 6: 5, 7: 4, 8: 4}
    while time() - start < maxtime:
        ev, top, moves = eval_moves(board, depth, moves, start+maxtime, cachesize.get(depth, 3))
        #print('>>>', depth, ev, round(time() - start, 2))
        depth += 1
    return top

def move(board, clock) -> Move:

    #print('Time left:', clock.time)
    allocated = clock.increment * (.2 + 3 * (clock.time / clock.total_time))
    #print('Allocated:', allocated)
    return Move(*choosemove(board, allocated))
