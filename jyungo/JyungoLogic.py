import numpy as np
import hashlib
from scipy import ndimage

HASH_BOARD = {}

def shikatu_filter(x):
    if x[4] != 0:
        return -2
    if x[1] * x[3] * x[5] * x[7] == 0:
        return -1
    return 0

HASH_INIT = int.from_bytes(hashlib.sha256('init'.encode()).digest(), 'big')
HASH_KIFU = int.from_bytes(hashlib.sha256('kifu'.encode()).digest(), 'big')
class Board():

    __directions = [(1,0),(-1,0),(0,1),(0,-1)]

    def __init__(self, n, stones=None):
        "Set up initial board configuration."

        self.n = n
        if not n in HASH_BOARD:
            HASH_BOARD[n] = [[], []]
            for p in range(2):
                HASH_BOARD[n][p] = [0]*(self.n*self.n+1)
                HASH_BOARD[n][p][-1] = int.from_bytes(hashlib.sha256(f'pass{p}'.encode()).digest(), 'big')
                cnt = 0
                for x in range(self.n):
                    for y in range(self.n):
                        addr = str(x) + str(y)
                        hashv = int.from_bytes(hashlib.sha256(addr.encode()).digest(), 'big')
                        HASH_BOARD[n][p][cnt] = hashv
                        cnt += 1
        # Create the empty board array.
        #self.stones = [None]*self.n
        #for i in range(self.n):
            #self.stones[i] = [0]*self.n
        if stones is None:
            self.stones = np.zeros([self.n+2, self.n+2])
        else:
            self.stones = stones
        self.stones[0,:] = 3
        self.stones[-1,:] = 3
        self.stones[:,0] = 3
        self.stones[:,-1] = 3
        self.histories = {}
        self.passCnt = 0
        self.step = 0
        self.last_move = None
        self.hash = HASH_INIT
        self.hash_kifu = HASH_KIFU
        self.prev_hash = self.hash

    # add [][] indexer syntax to the Board
    def __getitem__(self, index):
        stones = self.stones[1:-1, 1:-1]
        return stones[index]

    def getCopy(self):
      b = Board(self.n, np.copy(self.stones))
      b.histories = self.histories.copy()
      b.passCnt = self.passCnt
      b.step = self.step
      b.last_move = self.last_move
      b.hash = self.hash
      b.hash_kifu = self.hash_kifu
      return b
    
    def regular_stones(self):
        return self.stones[1:-1, 1:-1]
    
    def astype(self,t):
        stones = self.stones[1:-1, 1:-1]
        return stones.astype(t)

    def countDiff(self, color):
        """Counts the # stones of the given color
        (1 for black, -1 for white, 0 for empty spaces)"""
        count = 0
        for y in range(self.n):
            for x in range(self.n):
                if self[x][y]==color:
                    count += 1
                if self[x][y]==-color:
                    count -= 1
        return count

    def get_legal_moves(self, color):
        """Returns all the legal moves for the given color.
        (1 for black, -1 for white
        """
        moves = set()  # stores the legal moves.
        disboard = ndimage.generic_filter(self.regular_stones(), shikatu_filter, size=(3,3), mode='mirror')
        legal = np.where(disboard == -1)
        question = np.where(disboard == 0)
        for i in range(len(legal[0])):
            moves.add((legal[0][i], legal[1][i]))
        if len(question[0]) > 0:
            check_board = self.getCopy()
        for i in range(len(question[0])):
            x = question[0][i]
            y = question[1][i]
            # check kou
            check_board.stones = self.stones.copy()
            check_board.execute_move((x, y), color)
            suicide = check_board[x][y] == 0
            kou = check_board.hash in self.histories
            if not suicide and not kou:
                moves.add((x, y))
        # check_board = self.getCopy()
        # # Get all empty locations
        # for y in range(self.n):
        #     for x in range(self.n):
        #         if self[x][y] == 0:
        #             # １方向でも空いてれば合法手

        #             # check kou
        #             check_board.stones = self.stones.copy()
        #             check_board.execute_move((x, y), color)
        #             suicide = check_board[x][y] == 0
        #             kou = check_board.hash in self.histories
        #             if not suicide and not kou:
        #                 moves.add((x, y))
        return list(moves)

    def has_legal_moves(self, color):
        moves = self.get_legal_moves(color)
        return len(moves) > 0
    
    def get_hash(self, s):
        return int.from_bytes(hashlib.sha256(s).digest(), 'big')
    
    def execute_move(self, move, color):
        """Perform the given move on the board
        """
        (x,y) = move
        
        if x >= self.n: # pass
            self.passCnt += 1
            self.step += 1
            self.hash = self.get_hash(self.stones.tostring() + bytes(f'pass{self.passCnt}', encoding='utf-8'))
            self.hash_kifu = self.get_hash_kifu()
            self.histories[self.hash] = True
            return
        self.passCnt = 0
        self.last_move = move
        if self[x][y] != 0:
            print(move)
            print(self.stones)
            print(self.get_legal_moves(color))
            print(self.get_legal_moves(-color))
        assert self[x][y] == 0
        self[x][y] = color
        for d in self.__directions:
            (dx, dy) = d
            vx = x + dx
            vy = y + dy
            self.execute_shikatu(-color, vx+1, vy+1)
        self.execute_shikatu(color, x+1, y+1)
        self.hash =self.get_hash(self.stones.tostring())
        self.hash_kifu = self.get_hash_kifu()
        self.histories[self.hash] = True
        self.step += 1

    def get_hash_kifu(self):
        return self.hash_kifu ^ self.hash
    
    def execute_shikatu(self, color, x, y):
        checked = {}
        def checker(x, y):
            cnt = 0
            if self.stones[x][y] != 0:
                checked[f'{x}{y}'] = True
            for d in self.__directions:
                (dx, dy) = d
                vx = x + dx
                vy = y + dy
                tcolor = self.stones[vx][vy]
                if tcolor == 0:
                    cnt += 1
                elif tcolor == color and not (f'{x}{y}' in checked):
                    cnt += checker(vx, vy)
            return cnt
        def killer(x, y):
            self.stones[x][y] = 0
            for d in self.__directions:
                (dx, dy) = d
                vx = x + dx
                vy = y + dy
                tcolor = self.stones[vx][vy]
                if tcolor == color:
                    killer(vx, vy)
        if self.stones[x][y] == color:
            kuten = checker(x, y)
            if kuten == 0:
                killer(x, y)
                    
        