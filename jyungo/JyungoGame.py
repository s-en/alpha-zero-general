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
        return (b, -player)

    def getValidMoves(self, board, player):
        # return a fixed size binary vector
        valids = [0]*self.getActionSize()
        valids[-1] = 1 # pass
        b = board.getCopy()
        legalMoves = b.get_legal_moves(player)
        #if board.step < board.n ** 2:
            #legalMoves = b.get_legal_moves(player)
            #valids[-1] = 1 # pass
        for x, y in legalMoves:
            valids[self.n*x+y]=1
        return np.array(valids)

    def getGameEnded(self, board, player):
        # return 0 if not ended, 1 if player 1 won, -1 if player 1 lost
        # player = 1
        b = board.getCopy()
        if b.passCnt < 2:
            if b.has_legal_moves(player):
                return 0
            if b.has_legal_moves(-player):
                return 0
        if b.countDiff(player) > 0:
            return 1
        return -1

    def getCanonicalForm(self, board, player):
        # return state if player==1, else return -state if player==-1
        b = board.getCopy()
        b.stones = b.stones * player
        return b

    def getSymmetries(self, board, pi):
        # return [(board,pi)]
        # mirror, rotational
        assert(len(pi) == self.n**2+1)  # 1 for pass
        pi_board = np.reshape(pi[:-1], (self.n, self.n))
        l = []
        b = board.getCopy()
        if b.last_move != None:
            (x, y) = b.last_move
            b.stones[x][y] *= 2 # flag last move
        for i in range(1, 5):
            for j in [True, False]:
                #newB = board.getCopy()
                #newB.stones = np.rot90(newB.stones, i)

                newB = np.rot90(b.stones, i)
                newPi = np.rot90(pi_board, i)
                if j:
                    newB = np.fliplr(newB)
                    newPi = np.fliplr(newPi)
                l += [(newB, list(newPi.ravel()) + [pi[-1]])]
        return l

    def stringRepresentation(self, board):
        #s1 = board.stones.tostring()
        #s2 = board.histories.tostring()
        #return s1 + s2 + bytes(board.passCnt)
        return board.hash_kifu

    def stringRepresentationReadable(self, board):
        board_s = "".join(self.square_content[square] for row in board for square in row)
        return board_s

    def getScore(self, board, player):
        b = board.getCopy()
        return b.countDiff(player)

    @staticmethod
    def display(board):
        n = len(board[0])
        print(board.get_legal_moves(1))
        print(board.get_legal_moves(-1))
        print(board.hash_kifu)
        #print(board.hash)
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
