import numpy as np
import hashlib

HASH_BOARD = {}
def bitwise_xor_bytes(a, b):
    result_int = int.from_bytes(a, byteorder="big") ^ int.from_bytes(b, byteorder="big")
    return result_int.to_bytes(max(len(a), len(b)), byteorder="big")

HASH_INIT = hashlib.sha256('init'.encode()).digest()
HASH_KIFU = hashlib.sha256('kifu'.encode()).digest()
class Board():

    __directions = [(1,0),(-1,0),(0,1),(0,-1)]

    def __init__(self, n):
        "Set up initial board configuration."

        self.n = n
        if not n in HASH_BOARD:
            HASH_BOARD[n] = [[], []]
            for p in range(2):
                HASH_BOARD[n][p] = [0]*(self.n*self.n+1)
                HASH_BOARD[n][p][-1] = hashlib.sha256(f'pass{p}'.encode()).digest()
                cnt = 0
                for x in range(self.n):
                    for y in range(self.n):
                        addr = str(x) + str(y)
                        hashv = hashlib.sha256(addr.encode()).digest()
                        HASH_BOARD[n][p][cnt] = hashv
                        cnt += 1
        # Create the empty board array.
        self.stones = [None]*self.n
        for i in range(self.n):
            self.stones[i] = [0]*self.n
        self.histories = {}
        self.passCnt = 0
        self.step = 0
        self.last_move = None
        self.hash = HASH_INIT
        self.hash_kifu = HASH_KIFU
        self.prev_hash = self.hash

    # add [][] indexer syntax to the Board
    def __getitem__(self, index): 
        return self.stones[index]

    def getCopy(self):
      b = Board(self.n)
      b.stones = np.copy(self.stones)
      b.histories = self.histories.copy()
      b.passCnt = self.passCnt
      b.step = self.step
      b.last_move = self.last_move
      b.hash = self.hash
      b.hash_kifu = self.hash_kifu
      return b
    
    def astype(self,t):
        return self.stones.astype(t)

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
        check_board = Board(self.n)

        # Get all empty locations
        for y in range(self.n):
            for x in range(self.n):
                if self[x][y] == 0:
                    # check kou
                    check_board = self.getCopy()
                    check_board.execute_move((x, y), color)
                    kou = check_board.hash in self.histories
                    suicide = check_board[x][y] == 0
                    if not kou and not suicide:
                        moves.add((x, y))
        return list(moves)

    def has_legal_moves(self, color):
        moves = self.get_legal_moves(color)
        return len(moves) > 0
    
    def execute_move(self, move, color):
        """Perform the given move on the board
        """
        (x,y) = move
        
        if x >= self.n: # pass
            self.passCnt += 1
            self.step += 1
            self.hash = hashlib.sha256(self.stones.tostring() + bytes(f'pass{self.passCnt}', encoding='utf-8')).digest()
            self.hash_kifu = bitwise_xor_bytes(self.hash_kifu, self.hash)
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
        check_stones = np.array(self.stones)
        for d in self.__directions:
            (dx, dy) = d
            vx = x + dx
            vy = y + dy
            if vx < 0 or vy < 0 or vx >= self.n or vy >= self.n:
                continue
            self.execute_shikatu(-color, check_stones, vx, vy)
        self.execute_shikatu(color, check_stones, x, y)
        self.hash = hashlib.sha256(self.stones.tostring()).digest()
        self.hash_kifu = bitwise_xor_bytes(self.hash_kifu, self.hash)
        self.histories[self.hash] = True
        self.step += 1
    
    def execute_shikatu(self, color, check_stones, x, y):
        def checker(x, y):
            cnt = 0
            if check_stones[x][y] != 0:
                check_stones[x][y] *= 2
            for d in self.__directions:
                (dx, dy) = d
                vx = x + dx
                vy = y + dy
                if vx < 0 or vy < 0 or vx >= self.n or vy >= self.n:
                    continue
                tcolor = check_stones[vx][vy]
                if tcolor == 0:
                    cnt += 1
                elif tcolor == color:
                    cnt += checker(vx, vy)
            return cnt
        def killer(x, y):
            self.stones[x][y] = 0
            for d in self.__directions:
                (dx, dy) = d
                vx = x + dx
                vy = y + dy
                if vx < 0 or vy < 0 or vx >= self.n or vy >= self.n:
                    continue
                tcolor = self.stones[vx][vy]
                if tcolor == color:
                    killer(vx, vy)
        if check_stones[x][y] == color:
            kuten = checker(x, y)
            if kuten == 0:
                killer(x, y)
                    
        