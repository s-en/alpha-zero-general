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
        #if action == self.n*self.n: # pass
        #    b.passCnt += 1
        #    return (b, -player)
        #b.passCnt = 0
        move = (int(action/self.n), action%self.n)
        b.execute_move(move, player)
        b.step += 1
        return (b, -player)

    def getValidMoves(self, board, player):
        # return a fixed size binary vector
        valids = [0]*self.getActionSize()
        legalMoves = board.get_legal_moves(player)
        if len(legalMoves) == 0:
            valids[-1] = 1 # pass
        for x, y in legalMoves:
            valids[self.n*x+y]=1
        return np.array(valids)

    def getGameEnded(self, board, player):
        # return 0 if not ended, 1 if player 1 won, -1 if player 1 lost
        # player = 1
        if board.passCnt < 2:
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
            b.player = player
            b.stones = (b.stones * -1) + 0
            np.place(b.stones, b.stones == -3, 3)
            b.histories['1'], b.histories['-1'] = b.histories['-1'], b.histories['1']
            if b.passCnt == 0:
                b.hash = b.get_hash((b.stones+0).tostring())
            else:
                b.hash = b.get_hash((b.stones+0).tostring() + bytes(f'pass{b.passCnt}', encoding='utf-8'))
        return b

    def getSymmetries(self, board, pi):
        # return [(board,pi)]
        # mirror, rotational
        assert(len(pi) == self.n**2+1)  # 1 for pass
        pi_board = np.reshape(pi[:-1], (self.n, self.n))
        l = []
        for i in range(1, 5):
            for j in [True, False]:
                newB = board.getCopy()
                newB.stones = np.rot90(newB.stones, i)
                newPi = np.rot90(pi_board, i)
                if j:
                    newB.stones = np.fliplr(newB.stones) + 0
                    newPi = np.fliplr(newPi) + 0
                l += [(newB, list(newPi.ravel()) + [pi[-1]])]
        return l

    def stringRepresentation(self, board):
        return board.get_hash_kifu()

    def stringRepresentationReadable(self, board):
        board_s = "".join(self.square_content[square] for row in board for square in row)
        return board_s

    def getScore(self, board, player):
        return board.countDiff(player)

    @staticmethod
    def display(board):
        n = len(board[0])
        # print(board.get_legal_moves(1))
        # print(board.get_legal_moves(-1))
        print(board.get_hash_kifu())
        #print(board.histories)
        print("   ", end="")
        for y in range(n):
            print(y, end=" ")
        print("")
        print("-----------------------")
        for y in range(n):
            print(y, "|", end="")    # print the row #
            for x in range(n):
                piece = board[y][x]    # get the piece to print
                print(JyungoGame.square_content[piece], end=" ")
            print("|")

        print("-----------------------")
