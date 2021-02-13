import numpy as np
import copy

class Board():

    __directions = [(1,0),(-1,0),(0,1),(0,-1)]

    def __init__(self, n):
        "Set up initial board configuration."

        self.n = n
        # Create the empty board array.
        self.stones = [None]*self.n
        for i in range(self.n):
            self.stones[i] = [0]*self.n
        self.prev_stones = np.array(self.stones)
        self.histories = np.array([self.stones])
        self.passCnt = 0
        self.step = 0
        self.last_move = None

    # add [][] indexer syntax to the Board
    def __getitem__(self, index): 
        return self.stones[index]

    def getCopy(self):
      b = Board(self.n)
      b.stones = np.copy(self.stones)
      b.prev_stones = np.copy(self.prev_stones)
      b.histories = self.histories.copy()
      b.passCnt = self.passCnt
      b.step = self.step
      b.last_move = self.last_move
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
                    check_board.stones = np.copy(self.stones)
                    check_board.execute_move((x, y), color)
                    hist = len(np.where((self.histories == check_board.stones).all(axis=1).all(axis=1))[0])
                    kou = hist > 0
                    suicide = check_board[x][y] == 0
                    check_board.stones = np.copy(self.stones)
                    check_board.execute_move((x, y), -color)
                    suicide2 = check_board[x][y] == 0
                    if not kou and not suicide and not suicide2:
                        moves.add((x, y))
        return list(moves)

    def has_legal_moves(self, color):
        moves = self.get_legal_moves(color)
        return len(moves) > 0

    def execute_move(self, move, color):
        """Perform the given move on the board
        """
        self.prev_stones = np.copy(self.stones)
        #self.histories.append(self.prev_stones)
        self.histories = np.append(self.histories, [self.prev_stones], axis=0)
        (x,y) = move
        self.last_move = move
        if self[x][y] != 0:
            print(move)
            print(self.stones)
            print(self.prev_stones)
            print(self.get_legal_moves(color))
            print(self.get_legal_moves(-color))
        assert self[x][y] == 0
        self[x][y] = color
        self.execute_shikatu(-color)
        self.execute_shikatu(color)
        self.step += 1
    
    def execute_shikatu(self, color):
        check_stones = np.array(self.stones)
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
        for y in range(self.n):
            for x in range(self.n):
                if check_stones[x][y] == color:
                    kuten = checker(x, y)
                    if kuten == 0:
                        killer(x, y)
                    
        