import time
from copy import deepcopy
class agent:

    def __init__(self, n, m, side):
        self.n = n
        self.m = m
        self.current_state = {}
        self.found_moves = {}
        self.time_limit = 100
        self.side = side #X/1 or O/0

    def eval(self, state, side):
        max_row_length = 0
        max_col_length = 0
        max_diag_length = 0
        row_ind = set([i for (i, j), k in state.items() if k == side])
        col_ind = set([j for (i, j), k in state.items() if k == side])


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

        first_row = [(1, i) for i in range(1, self.n)]
        first_col = [(i, 1) for i in range(1, self.n)]
        last_col = [(i, self.n) for i in range(1, self.n)]

        #change self.n + 1
        '''for pos in first_row:
            len_temp = 0
            new_pos = (pos[0] + 1, pos[1] + 1)
            while  new_pos[0] <= self.n and  new_pos[0]<= self.n:
                if (i, j) not in state:
                    continue
                if state[(i, j)] == side:
                    len_temp += 1
                elif state[(i, j)] == abs(side - 1):
                    len_temp = 0

                new_pos += (1,1)

            max_diag_length = max(max_diag_length, len_temp)

        for pos in first_row:
            len_temp = 0
            new_pos = (pos[0] - 1, pos[1] - 1)
            while  new_pos[0] >= 1 and  new_pos[0] >= 1:
                if (i, j) not in state:
                    continue
                if state[(i, j)] == side:
                    len_temp += 1
                elif state[(i, j)] == abs(side - 1):
                    len_temp = 0

                new_pos -= (1,1)

            max_diag_length = max(max_diag_length, len_temp)

        for pos in first_col:
            len_temp = 0
            new_pos = (pos[0] + 1, pos[1] + 1)
            while  new_pos[0] <= self.n and  new_pos[0]<= self.n:
                if (i, j) not in state:
                    continue
                if state[(i, j)] == side:
                    len_temp += 1
                elif state[(i, j)] == abs(side - 1):
                    len_temp = 0

                new_pos += (1,1)

            max_diag_length = max(max_diag_length, len_temp)

        for pos in last_col:
            len_temp = 0
            new_pos = (pos[0] - 1, pos[1] - 1)
            while  new_pos[0] >= 1 and  new_pos[0] >= 1:
                if (i, j) not in state:
                    continue
                if state[(i, j)] == side:
                    len_temp += 1
                elif state[(i, j)] == abs(side - 1):
                    len_temp = 0

                new_pos -= (1,1)

            max_diag_length = max(max_diag_length, len_temp)
'''

        for pos, key in state.items():
            if key != side:
                continue
            explored = set()
            len_temp = 0
            for pos2, key2 in state.items():
                if key2 != side:
                    continue
                if pos2 in explored:
                    explored.add(pos2)
                    continue
                if pos == pos2:
                    explored.add(pos2)
                    continue
                if abs(pos[0] - pos2[0]) == 1 and abs(pos[1] - pos2[1]) == 1 and key == key2:
                    len_temp += 1
                    explored.add(pos2)
                    max_diag_length = max(max_diag_length, len_temp)
            max_diag_length = max(max_diag_length, len_temp)

        print("diag: ", max_diag_length)
        print("row: ", max_row_length)
        print("col: ", max_col_length)

        return max_diag_length + max_row_length + max_col_length


    def actions(self, state): #should return ordered list of positions of possible next moves
        pass

    def min_value(self, state, alpha, beta, depth, max_deth):
        if depth <= max_deth:
            return self.eval(state)
        
        v = float("inf")
        eventual_pos = None

        for pos in self.actions(state):
            new_state = deepcopy(state)
            new_state[pos] = self.side
            eventual_pos = pos
            new_val, _ = self.min_value(state, alpha, beta, depth + 1, max_deth)
            v = max(v, new_val)

            if v <= alpha:
                return v, pos
            
            beta = min(beta, v)

        return v, eventual_pos

    def max_value(self, state, alpha, beta, depth, max_deth):
        if depth <= max_deth:
            return self.eval(state)
        
        v = float("-inf")
        eventual_pos = None
        for pos in self.actions(state):
            new_state = deepcopy(state)
            new_state[pos] = self.side
            eventual_pos = pos
            new_val, _ = self.min_value(state, alpha, beta, depth + 1, max_deth)
            v = max(v, new_val)

            if v >= beta:
                return v, pos
            
            alpha = max(alpha, v)
        
        return v, eventual_pos
        
    def alpha_beta(self):
        start = time.time
        action = None

        while(abs(time.time - start) <= self.time_limit):
            max_depth = 0

            state = deepcopy(self.current_state)
            val = float("-inf")
            new_val, new_pos = self.max_value(state, float("-inf"), float("inf"), 0, max_depth)
            
            if new_val < val:
                val = new_val
                action = new_pos

            max_depth += 1

        return action