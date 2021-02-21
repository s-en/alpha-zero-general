from __future__ import print_function
import sys
sys.path.append('..')
from Game import Game
from .JyungoLogic import Board
import numpy as np
import hashlib

class JyungoGame(Game):
    square_content = {
        -1: "X",
        +0: "-",
        +1: "O"
    }

    @staticmethod
    def getSquarePiece(piece):
        return JyungoGame.square_content[piece]

    def __init__(self, n):
        self.n = n

    def getInitBoard(self):
        # return initial board
        b = Board(self.n)
        return b

    def getBoardSize(self):
        # (a,b) tuple
        return (self.n, self.n)

    def getActionSize(self):
        # return number of actions
        return self.n*self.n+1

    def getNextState(self, board, player, action):
        # if player takes action on board, return next (board,player)
        # action must be a valid move
        b = board.getCopy()
        b.execute_move(action, player)
        return (b, -player)

    def getValidMoves(self, board, player):
        # return a fixed size binary vector
        valids = [0]*self.getActionSize()
        #if board.pass_cnt < 2:
        #    valids[-1] = 1 # pass
        legalMoves = board.get_legal_moves(player)
        for i in legalMoves:
            valids[i] = 1
        if len(legalMoves) == 0 and board.double_skipped() == False:
            valids[-1] = 1
        return np.array(valids)

    def getGameEnded(self, board, player):
        # return 0 if not ended, 1 if player 1 won, -1 if player 1 lost
        # player = 1
        if board.double_skipped() == False:
            if board.has_legal_moves(player):
                return 0
            if board.has_legal_moves(-player):
                return 0
        if board.countDiff(player) > 0:
            return 1
        return -1

    def getCanonicalForm(self, board, player):
        # return state if player==1, else return -state if player==-1
        b = board.getCopy()
        if player != b.player:
            b.lpayer = player
            b.stones['1'], b.stones['-1'] = b.stones['-1'], b.stones['1']
            b.groups['1'], b.groups['-1'] = b.groups['-1'], b.groups['1']
            b.history['front'], b.history['back'] = b.history['back'], b.history['front']
            b.cache_hash['front'], b.cache_hash['back'] = b.cache_hash['back'], b.cache_hash['front']
        return b

    def getSymmetries(self, board, pi):
        return [(board,pi)]
        # return [(board,pi)]
        # mirror, rotational
        # assert(len(pi) == self.n**2+1)  # 1 for pass
        # pi_board = np.reshape(pi[:-1], (self.n, self.n))
        # l = []
        # for i in range(1, 5):
        #     for j in [True, False]:
        #         newB = board.getCopy()
        #         newB.stones = np.rot90(newB.stones, i)
        #         newPi = np.rot90(pi_board, i)
        #         if j:
        #             newB = np.fliplr(newB) + 0
        #             newPi = np.fliplr(newPi) + 0
        #         l += [(newB, list(newPi.ravel()) + [pi[-1]])]
        # return l

    def stringRepresentation(self, board):
        return board.get_history_hash()

    def stringRepresentationReadable(self, board):
        return board.get_history_hash

    def getScore(self, board, player):
        return board.countDiff(player)

    @staticmethod
    def display(board):
        n = board.n
        print(board.get_history_hash())
        print(board.get_legal_moves(1))
        print(board.get_legal_moves(-1))
        print("   ", end="")
        for y in range(n):
            print(y, end=" ")
        print("")
        print("-----------------------")
        for y in range(n):
            print(y, "|", end="")    # print the row #
            for x in range(n):
                action = y*n + x
                slide = board.n + 3 + action + int(action / board.n) * 2
                black = (board.stones['1'] >> slide) & 1
                white = (board.stones['-1'] >> slide) & 1
                if black == 1:
                    print('o', end=" ")
                elif white == 1:
                    print('x', end=" ")
                else:
                    print('-', end=" ")
            print("|")

        print("-----------------------")
