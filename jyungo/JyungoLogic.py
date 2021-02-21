import numpy as np
import hashlib
import re
import random

BLACK = '1'
WHITE = '-1'

BANPEI = {
    '7': 0b111111111100000001100000001100000001100000001100000001100000001100000001111111111,
    '5': 0b1111111100000110000011000001100000110000011111111
}

HASH_INIT = int.from_bytes(hashlib.sha256('init'.encode()).digest(), 'big')
class Board():
    def __init__(self, n):
        "Set up initial board configuration."
        self.player = 1
        self.n = n
        self.size = n*n
        self.padded_size = (n+2)**2
        pad_board = BANPEI[str(self.n)]
        self.stones = {
            BLACK: pad_board, # black
            WHITE: pad_board # white
        }
        self.groups = {
            BLACK: {}, # black
            WHITE: {} # white
        }
        self.history = {
            'front': set(),
            'back': set()
        }
        self.cache_hash = {
            'front': HASH_INIT,
            'back': HASH_INIT
        }
        self.pass_cnt = 0
        self.step = 0

    # add [][] indexer syntax to the Board
    def __getitem__(self, index):
        black = self.has_stone(self.stones[BLACK], index)
        white = self.has_stone(self.stones[WHITE], index)
        return black - white
    
    def astype(self,t):
        stones = []
        for i in range(self.size):
            stones.append(self[i])
        return np.array(stones).astype(t)
    
    def has_stone(self, board, index):
        slide = self.n + 3 + index + int(index / self.n) * 2
        return board >> slide & 1

    def getCopy(self):
        b = Board(self.n)
        b.player = self.player
        b.stones = {
            BLACK: self.stones[BLACK],
            WHITE: self.stones[WHITE]
        }
        b.groups = {
            BLACK: self.groups[BLACK].copy(),
            WHITE: self.groups[WHITE].copy(),
        }
        b.history = {
            'front': self.history['front'].copy(),
            'back': self.history['back'].copy()
        }
        b.cache_hash = {
            'front': self.cache_hash['front'],
            'back': self.cache_hash['back']
        }
        b.pass_cnt = self.pass_cnt
        b.step = self.step
        return b

    def countDiff(self, color):
        """Counts the # stones of the given color
        (1 for black, -1 for white, 0 for empty spaces)"""
        return (bin(self.stones[BLACK]).count('1') - bin(self.stones[WHITE]).count('1')) * color

    def board2actions(self, boardstr):
        actions = []
        n = self.n + 2
        for m in re.finditer('1', boardstr.zfill(self.padded_size)):
            action = self.padded_size - m.start()
            action = action-n-int(action/n)*2
            actions.append(action)
        return actions

    def get_legal_moves(self, color):
        """Returns 
         the legal moves for the given color.
        (1 for black, -1 for white
        """
        moves = set()
        # スキップを除く
        skip_mask = (1 << self.padded_size) - 1
        board = self.stones[str(color)] & skip_mask
        board_opp = self.stones[str(-color)] & skip_mask
        both = board | board_opp
        board_rev = ~board+(1<<self.padded_size)
        both_rev = ~both+(1<<self.padded_size)
        n = self.n + 2
        # 周りが１つでも空ならOK
        kuten = (both_rev & both_rev >> 1) | (both_rev & both_rev << 1) | (both_rev & both_rev >> n) | (both_rev & both_rev << n)
        moves |= set(self.board2actions(bin(kuten)[2:]))
        # 周りが全部同じ色の箇所をチェック
        eye = (board_rev & board >> 1) & (board_rev & board << 1) & (board_rev & board >> n) & (board_rev & board << n)
        # それ以外の空マスは実際に打ってみる
        trial = both_rev & (~kuten)
        trials = self.board2actions(bin(trial)[2:])
        for action in trials:
            b = self.getCopy()
            b.execute_move(action, color)
            if b[action] == 0:
                # 打った石が消えれば自殺手
                continue # 自殺は禁止
            if self.has_stone(eye, action) == 1:
                # 消えないけど自分の色で囲われていれば目
                b2 = self.getCopy()
                b2.execute_move(action, -color)
                if b2[action] == 0:
                    continue # playoutでは禁止手
            if b.get_hash() in self.history['front']:
                # 同一局面禁止
                continue
            moves.add(action)
        return list(moves)

    def has_legal_moves(self, color):
        moves = self.get_legal_moves(color)
        return len(moves) != 0
    
    def double_skipped(self):
        board = self.stones['1']
        board_opp = self.stones['-1']
        return (board >> self.padded_size & 1) & (board_opp >> self.padded_size & 1) == 1
    
    def execute_move(self, action, color):
        """Perform the given move on the board
        """
        if self[action] != 0:
            print('zero action')
            print(action)
            print(self.get_legal_moves(color))
            print(self.get_legal_moves(-color))
            print(self.stones['1'])
            print(self.stones['-1'])
            print(self.get_history_hash())
        assert self[action] == 0
        self.step += 1
        n = self.n + 2
        me = str(color)
        you = str(-color)
        if action == self.size:
            # pass
            self.stones[me] |= 1 << self.padded_size
            self.pass_cnt += 1
            self.save_hash()
            return
        # 石を打つ
        slide = n + 1 + action + int(action / self.n) * 2
        skip_mask = (1 << self.padded_size) - 1 # スキップを除くため
        hit_stone = 1 << slide
        self.stones[me] |= hit_stone
        self.stones[me] &= skip_mask # clear pass
        self.pass_cnt = 0
        
        board = self.stones[me] & skip_mask
        board_opp = self.stones[you] & skip_mask

        mask = 1 << slide + 1 | 1 << slide - 1 | 1 << slide + n | 1 << slide - n # 上下左右
        same_cnt = bin(board & ~board_opp & mask).count('1') # 周囲の同じ色の数
        opp_cnt = bin(board_opp & ~board & mask).count('1') # 周囲の相手色の数
        new_ren = hit_stone
        new_neighbor = ~board & mask
        suspects = [] # 死亡容疑者リスト
        # 同色チェック
        if same_cnt > 0:
            # groupをくっつける
            for ren, neighbor in list(self.groups[me].items()):
                if bin(ren & mask).count('1') > 0:
                    new_ren |= ren
                    new_neighbor |= neighbor
                    del self.groups[me][ren]
        # 新しい連を追加
        self.groups[me][new_ren] = new_neighbor
        # 相手色チェック
        if opp_cnt > 0:
            # 周囲のgroupを調べる
            for ren, neighbor in list(self.groups[you].items()):
                if bin(ren & mask).count('1') > 0:
                    # 死活チェックリストに加える
                    suspects.append({'ren':ren, 'neighbor': neighbor, 'player': you})
        # 打った石は死活チェックリストの最後に加える
        suspects.append({'ren': new_ren, 'neighbor': new_neighbor, 'player': me})
        # 空点が無ければ死亡
        for row in suspects:
            board = self.stones[me] & skip_mask
            board_opp = self.stones[you] & skip_mask
            if bin(row['neighbor'] & ~board & ~board_opp).count('1') == 0:
                self.stones[row['player']] -= row['ren']
                #self.stones[row['player']] |= BANPEI[str(self.n)]
                del self.groups[row['player']][row['ren']]
        self.save_hash()
    
    def get_hash(self, color = 1):
        return int(self.stones[str(color)]) << (self.padded_size + 1) | self.stones[str(-color)]
    
    def save_hash(self):
        h_front = self.get_hash()
        h_back = self.get_hash(-1)
        # self.cache_hash['front'] ^= int.from_bytes(hashlib.sha256(hex(h_front).encode()).digest(), 'big')
        # self.cache_hash['back'] ^= int.from_bytes(hashlib.sha256(hex(h_back).encode()).digest(), 'big')
        self.history['front'].add(h_front)
        self.history['back'].add(h_back)
        self.cache_hash['front'] = str(sorted(self.history['front']))
        self.cache_hash['back'] = str(sorted(self.history['back']))
    
    def get_history_hash(self):
        return self.cache_hash['front']
