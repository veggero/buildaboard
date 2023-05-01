"""
All of the following code was written by me, Niccolò Venerandi.
Rather than a copyright notice, this is an indication of who to blame.
Furthermore, all other files in this folder are also to be blamed on me,
with the only exception of web/PieceEditor.html and its assets.
"""

from __future__ import annotations
from dataclasses import dataclass
from time import sleep, time
from pprint import pprint
from typing import Callable, Optional
from copy import deepcopy
from RestrictedPython import safe_builtins, compile_restricted
from RestrictedPython.Eval import default_guarded_getiter
from RestrictedPython.Guards import guarded_iter_unpack_sequence, safer_getattr
from buildaboard import Range, PieceType, Piece, Move, Board, Clock, king, queen

try:
    import eel
except ModuleNotFoundError:
    print("Please install the module 'eel'!")
    print('python3 -m pip install eel')
    exit()

files, ranks = 'abcdefgh', '12345678'

@dataclass
class GameSituation:
    board: Board
    clock: Clock
    players: [Players] = None

@dataclass
class Player:
    p_setup: Callable
    p_move: Optional[Callable]

    def setup(self):
        return self.verify_setup(self.p_setup())
        try: pass
        except Exception as e:
            return eel.fuck('Python error in custom code: ' + str(e))

    def move(self, board, clock):
        try:
            return self.verify_move(self.p_move(deepcopy(board), deepcopy(clock)), board)
        except Exception as e:
            return eel.fuck('Python error in custom code: ' + str(e))

    def verify_setup(self, setup):
        if any(p.rank > 2 for p in setup):
            eel.fuck('Somebody attempted to put a place further than the first three ranks on setup. That\'s invalid!')
            return []
        elif sum(p.type.price for p in setup if p.type != king) > 200:
            eel.fuck('Somebody attempted to put more than 200 points of pieces! That\'s invalid.')
            return []
        elif not any(p.type == king for p in setup):
            eel.fuck('Somebody did not put a king in their initial configuration!')
            return []
        return setup

    def verify_move(self, move, board):
        if not move: return None
        if not any((p.rank, p.file, p.type) == (move.piece.rank, move.piece.file, move.piece.type) for p in board.player):
            eel.fuck('Invalid move: piece to be moved does not exist / not in the right position')
            return None
        if not board.check_move(move):
            eel.fuck('Invalid move attempted')
            return None
        return move

    @staticmethod
    def fromText(name, info):
        if name == 'Human':
            try:
                exec(info)
            except Exception as e:
                return eel.fuck('Python error in custom code: ' + str(e))
            if not 'setup' in locals():
                return eel.fuck('No setup function defined in custom code!')
            return Player(locals()['setup'], None)

        if name == 'Builtin AI':
            info = open('builtin_ai2.py').read()

        def run_this(function, globalv):
            return lambda *a: eval(function + '(*a)', globalv, {'a': a})

        try:
            binary = compile_restricted(info, filename="<player code>", mode='exec')
            globalv, localv = {'__builtins__': safe_builtins}, {}
            globalv['__builtins__']['__import__'] = __import__
            globalv['__builtins__']['print'] = print
            globalv['__builtins__']['any'] = any
            globalv['__builtins__']['max'] = max
            globalv['__builtins__']['min'] = min
            globalv['__builtins__']['__metaclass__'] = type
            globalv['__builtins__']['__name__'] = 'playercode'
            globalv['__builtins__']['_getiter_'] = default_guarded_getiter
            globalv['__builtins__']['_iter_unpack_sequence_'] = guarded_iter_unpack_sequence
            globalv['__builtins__']['getattr'] = safer_getattr
            globalv['__builtins__']['list'] = list
            exec(info, globalv, localv)
            globalv.update(localv)
        except Exception as e:
            return eel.fuck('Python error in custom code: ' + str(e))
        if not 'setup' in globalv:
            return eel.fuck('No setup function defined in custom code!')
        if not 'move' in globalv:
            return eel.fuck('No move function defined in custom code!')
        return Player(run_this('setup', globalv), run_this('move', globalv))

@dataclass
class Players:
    white: Player
    black: Player

    def move(self, board):
        move = None
        gs.clock.last_move_start_time = time()
        if board.player_turn and self.white.p_move:
            move = self.white.move(board, gs.clock)
            if not move:
                eel.pySetMoves({})
                return eel.fuck('White lost!')
        elif not board.player_turn and self.black.p_move:
            move = self.black.move(board.flipped, gs.clock.flipped)
            if not move:
                eel.pySetMoves({})
                return eel.fuck('Black lost!')
            if move: move = move.flipped
        if move:
            source = files[move.piece.file] + ranks[move.piece.rank]
            target = files[move.file] + ranks[move.rank]
            eel.receiveMove(source + '-' + target)
            moveDone(source, target)

correspondingPieces = {queen: 'Q', king: 'K'}

gs = GameSituation(Board([], [], None), Clock(0, 0, 0, 10, 1))

def setup():
    gs.board.player_turn = False
    gs.board.player = gs.players.white.setup()
    gs.board.opponent = [p.flipped for p in gs.players.black.setup()]
    if not gs.board.player or not gs.board.opponent: return
    whiteTypes = set(piece.type for piece in gs.board.player if piece.type != king)
    blackTypes = set(piece.type for piece in gs.board.opponent if piece.type != king)
    correspondingPieces.update({a: b for a, b in zip(whiteTypes, 'NBR')})
    correspondingPieces.update({a: b for a, b in zip(blackTypes, 'NBR')})

@eel.expose
def newGame(playera, playerb, infoa, infob):
    white = Player.fromText(playera, infoa)
    black = Player.fromText(playerb, infob)
    if not isinstance(white, Player) or not isinstance(black, Player): return
    gs.players = Players(white, black)
    setup()
    gs.clock.opponent_time = gs.clock.time = gs.clock.total_time
    setGamePosition()
    gs.players.move(gs.board)

@eel.expose
def setGamePosition():
    eel.pySetPosition({
            files[piece.file] + ranks[piece.rank]: 'w' + correspondingPieces[piece.type]
            for piece in gs.board.player
        } | {
            files[piece.file] + ranks[piece.rank]: 'b' + correspondingPieces[piece.type]
            for piece in gs.board.opponent
        }, gs.board.all_valid_moves)

@eel.expose
def moveDone(source, target):
    file, rank = files.index(source[0]), ranks.index(source[1])
    target_file, target_rank = files.index(target[0]), ranks.index(target[1])
    board = gs.board

    # Updates the clock
    gs.clock.plys += 1
    if board.player_turn:
        gs.clock.time -= time() - gs.clock.last_move_start_time
        if gs.clock.time < 0:
            eel.pySetMoves({})
            return eel.fuck('White lost on time!')
        gs.clock.time += gs.clock.increment
    else:
        gs.clock.opponent_time -= time() - gs.clock.last_move_start_time
        if gs.clock.opponent_time < 0:
            eel.pySetMoves({})
            return eel.fuck('Black lost on time!')
        gs.clock.opponent_time += gs.clock.increment

    # Updates the board
    for piece in board.pieces:
        if piece.file == target_file and piece.rank == target_rank:
            if piece.type == king:
                eel.pySetMoves({})
                if piece in board.opponent:
                    return eel.fuck('Black lost their king! Game over.')
                else: return eel.fuck('White lost their king! Game over.')
            if piece in board.opponent: board.opponent.remove(piece)
            else: board.player.remove(piece)
    for piece in board.pieces:
        if piece.file == file and piece.rank == rank:
            piece.file, piece.rank = target_file, target_rank
            if ((board.player_turn and piece.rank == 7) or
                (not board.player_turn and piece.rank == 0)) and \
                    piece.type != king:
                piece.type = queen
                setGamePosition()
            board.player_turn = not board.player_turn
            eel.pySetMoves(board.all_valid_moves)
            break

    # Triggers following move
    gs.players.move(board)


eel.init('web')
eel.start('index.html', size=(1280, 720))

