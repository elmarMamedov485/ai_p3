import time
from copy import deepcopy
from collections import defaultdict
class agent:

    def __init__(self, n, m, side):
        self.n = n
        self.m = m
        self.current_state = {}
        self.found_moves = {}
        self.time_limit = 10
        self.side = side #X/1 or O/0

    def terminal_state(self, state):
        max_row_length = self.find_longest_row(state, self.side)
        max_col_length = self.find_longest_column(state, self.side)
        max_diag_length = self.find_longest_diag(state, self.side)

        if max_col_length == self.n or max_row_length == self.n or max_diag_length == self.n:
            return True
        else:
            return False

    def find_longest_row(self, state, side):
        max_row_length = 0
        row_ind = set([i for (i, j), k in state.items() if k == side])
        
        for i in row_ind:
            len_temp = 0
            for j in range(1, self.n+1):
                if (i, j) not in state:
                    continue
                if state[(i, j)] == side:
                    len_temp += 1
                    max_row_length = max(max_row_length, len_temp)
                elif state[(i, j)] == abs(side - 1):
                    len_temp = 0
            
            max_row_length = max(max_row_length, len_temp)

        return max_row_length
    
    def find_longest_column(self, state, side):
        max_col_length = 0
        col_ind = set([j for (i, j), k in state.items() if k == side])

        for j in col_ind:
            len_temp = 0
            for i in range(1, self.n+1):
                if (i, j) not in state:
                    continue
                if state[(i, j)] == side:
                    len_temp += 1
                    max_col_length = max(max_col_length, len_temp)
                elif state[(i, j)] == abs(side - 1):
                    len_temp = 0
            
            max_col_length = max(max_col_length, len_temp)

        return max_col_length
    
    def find_longest_diag(self, state, side):
        main_diag = defaultdict(int)   # r - c
        anti_diag = defaultdict(int)   # r + c
    
        for (r, c), value in state.items():
            if value == side:
                main_diag[r - c] += 1
                anti_diag[r + c] += 1
    
        max_main = max(main_diag.values(), default=0)
        max_anti = max(anti_diag.values(), default=0)
    
        return max(max_main, max_anti)
    def eval(self, state, side):
        max_row_length = self.find_longest_row(state,side)
        max_col_length = self.find_longest_column(state, side)
        max_diag_length = self.find_longest_diag(state, side)

        #print("diag: ", max_diag_length)
        #print("row: ", max_row_length)
        #print("col: ", max_col_length)

        return max_diag_length + max_row_length + max_col_length

    def actions(self, state): #should return ordered list of positions of possible next moves
        actions = []
        for i in range(1, self.n+1):
            for j in range(1, self.n+1):
                if (i, j) not in state:
                    actions.append((i,j))

        return actions


    def min_value(self, state, alpha, beta, depth, max_deth, pos = None):
        if depth >= max_deth or self.terminal_state(state):
            return self.eval(state, self.side), (pos if pos is not None else float("inf")) 
        
        v = float("inf")
        eventual_pos = None

        for pos in self.actions(state):
            new_state = deepcopy(state)
            new_state[pos] = self.side
            eventual_pos = pos
            new_val, _ = self.max_value(new_state, alpha, beta, depth + 1, max_deth, pos)
            v = min(v, new_val)

            if v <= alpha:
                return v, pos
            
            beta = min(beta, v)

        return v, eventual_pos

    def max_value(self, state, alpha, beta, depth, max_deth, pos = None):
        if depth >= max_deth or self.terminal_state(state):
            return self.eval(state, self.side), (pos if pos is not None else float("-inf")) 
        
        v = float("-inf")
        eventual_pos = None
        for pos in self.actions(state):
            
            new_state = deepcopy(state)
            new_state[pos] = self.side
            eventual_pos = pos
            new_val, _ = self.min_value(new_state, alpha, beta, depth + 1, max_deth, pos)
            v = max(v, new_val)

            if v >= beta:
                return v, pos
            
            alpha = max(alpha, v)
        
        
        return v, eventual_pos
        
    def alpha_beta(self):
        start = time.time()
        action = None
        max_depth = 0

        while(abs(time.time() - start) <= self.time_limit):
            state = deepcopy(self.current_state)
            val = float("-inf")
            new_val, new_pos = self.max_value(state, float("-inf"), float("inf"), 0, max_depth)
            
            if new_val > val:
                val = new_val
                action = new_pos

            max_depth += 1

        return action