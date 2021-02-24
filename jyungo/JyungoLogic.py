import numpy as np
import hashlib
from scipy import ndimage

HASH_BOARD = {}

def shikatu_filter(x):
    if x[4] != 0:
        return -2 # 空マスでない
    if x[1] * x[3] * x[5] * x[7] == 0:
        return -1 # 周りが１つでも空
    s = x[1] + x[3] + x[5] + x[7]
    if s == 4:
        return 3 # 周り全部が同じ色
    if s == -4:
        return 1 # 周り全部が同じ色
    return 0

HASH_INIT = int.from_bytes(hashlib.sha256('init'.encode()).digest(), 'big')
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
        self.histories = {
            '1': set(),
            '-1': set()
        }
        self.passCnt = 0
        self.step = 0
        self.player = 1
        self.last_move = None
        self.hash = HASH_INIT
        self.prev_hash = self.hash

    # add [][] indexer syntax to the Board
    def __getitem__(self, index):
        stones = self.stones[1:-1, 1:-1]
        return stones[index]

    def getCopy(self):
      b = Board(self.n, np.copy(self.stones))
      b.histories = {
          '1': self.histories['1'].copy(),
          '-1': self.histories['-1'].copy()
      }
      b.passCnt = self.passCnt
      b.step = self.step
      b.last_move = self.last_move
      b.hash = self.hash
      b.player = self.player
      return b
    
    def regular_stones(self):
        return self.stones[1:-1, 1:-1]
    
    def astype(self,t):
        return self.regular_stones().astype(t)

    def countDiff(self, color):
        """Counts the # stones of the given color
        (1 for black, -1 for white, 0 for empty spaces)"""
        count = 0
        stones = self.regular_stones()
        for y in range(self.n):
            for x in range(self.n):
                if stones[x][y]==color:
                    count += 1
                if stones[x][y]==-color:
                    count -= 1
        return count

    def get_legal_moves(self, color):
        """Returns all the legal moves for the given color.
        (1 for black, -1 for white
        """
        moves = set()  # stores the legal moves.
        disboard = ndimage.generic_filter(self.regular_stones(), shikatu_filter, size=(3,3), mode='mirror')
        legal = np.where(disboard == -1)
        for i in range(len(legal[0])):
            moves.add((legal[0][i], legal[1][i]))
        question = np.where(disboard >= 0)
        if len(question[0]) > 0:
            check_board = self.getCopy()
        for i in range(len(question[0])):
            x = question[0][i]
            y = question[1][i]
            check_board.stones = self.stones.copy()
            if disboard[x][y] == color + 2:
                # 周辺が自分色で、相手色を打ってみて死ねば自分の目
                check_board.execute_move((x, y), -color)
                eye = check_board[x][y] == 0
                if eye:
                    continue
                check_board.stones = self.stones.copy()
            # 同じ色を打ってみる
            check_board.execute_move((x, y), color)
            # 死ねば自殺
            suicide = check_board[x][y] == 0
            if suicide:
                continue
            # 同一局面になればコウ
            kou = check_board.hash in self.histories['1']
            if kou:
                continue
            moves.add((x, y))
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
            self.hash = self.get_hash((self.regular_stones()+0).tostring() + bytes(f'pass{self.passCnt}', encoding='utf-8'))
            self.histories['1'].add(self.hash)
            self.histories['-1'].add(self.get_hash((self.regular_stones()*-1+0).tostring()))
            return
        self.passCnt = 0
        self.last_move = move
        if self[x][y] != 0:
            print(move)
            print(self.stones)
            print(self.get_legal_moves(color))
            print(self.get_legal_moves(-color))
            print(self.hash)
        assert self[x][y] == 0
        assert color != 0
        self[x][y] = color + 0
        for d in self.__directions:
            (dx, dy) = d
            vx = x + dx
            vy = y + dy
            self.execute_shikatu(-color, vx+1, vy+1)
        self.execute_shikatu(color, x+1, y+1)
        self.hash =self.get_hash((self.regular_stones()+0).tostring())
        self.histories['1'].add(self.hash)
        self.histories['-1'].add(self.get_hash((self.regular_stones()*-1+0).tostring()))

    def get_hash_kifu(self):
        return self.get_hash((str(self.hash) + str(sorted(self.histories['1']))).encode())
    
    def execute_shikatu(self, color, sx, sy):
        checked = set([f'{sx}-{sy}'])
        def checker(x, y):
            cnt = 0
            for d in self.__directions:
                (dx, dy) = d
                vx = x + dx
                vy = y + dy
                tcolor = self.stones[vx][vy]
                if tcolor == 0:
                    cnt += 1
                elif tcolor == color and not (f'{vx}-{vy}' in checked):
                    checked.add(f'{vx}-{vy}')
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
        if self.stones[sx][sy] == color:
            kuten = checker(sx, sy)
            if kuten == 0:
                killer(sx, sy)
                    
        