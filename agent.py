import time
from copy import deepcopy
from collections import defaultdict
class agent:

    def __init__(self, n, m, side):
        self.n = n
        self.m = m
        self.current_state = {}
        self.found_moves = {}
        self.time_limit = 3
        self.side = side #X/1 or O/0

    def terminal_state(self, state):
        for player in [self.side, 1 - self.side]:
            if (self.find_longest_row(state, player)[0] == self.m or
            self.find_longest_column(state, player)[0] == self.m or
            self.find_longest_diag(state, player)[0] == self.m):
                return True
        return False

    def find_longest_row(self, state, side):
        max_row_length = 0
        row_ind = set([i for (i, j), k in state.items() if k == side])
        max_row_ind = []
        
        for i in row_ind:
            temp = []
            len_temp = 0
            for j in range(1, self.n+1):
                if (i, j) not in state:
                    continue
                if state[(i, j)] == side:
                    if len(temp) > 0 and (abs(j - temp[-1][1]) != 1):
                        len_temp = 0
                        temp = []
                    len_temp += 1
                    temp.append((i,j))

                    if len_temp > max_row_length:
                        max_row_length = len_temp
                        max_row_ind = temp.copy()
                elif state[(i, j)] == abs(side - 1):
                    len_temp = 0
                    temp = []
            
            max_row_length = max(max_row_length, len_temp)

        return max_row_length, max_row_ind
    
    def find_longest_column(self, state, side):
        max_col_length = 0
        col_ind = set([j for (i, j), k in state.items() if k == side])
        max_col_ind = []

        for j in col_ind:
            len_temp = 0
            temp = []
            for i in range(1, self.n+1):
                if (i, j) not in state:
                    continue
                if state[(i, j)] == side:
                    if len(temp) > 0 and (abs(i - temp[-1][0]) != 1):
                        len_temp = 0
                        temp = []
                    len_temp += 1
                    temp.append((i,j))

                    if len_temp > max_col_length:
                        max_col_length = len_temp
                        max_col_ind = temp.copy()
                elif state[(i, j)] == abs(side - 1):
                    len_temp = 0
                    temp = []
            
            max_col_length = max(max_col_length, len_temp)

        return max_col_length, max_col_ind
    
    def find_longest_diag(self, state, side):
        main_diag = defaultdict(int)   # r - c
        anti_diag = defaultdict(int)   # r + c
        diag_to_ind = {}
        for (r, c), value in state.items():
            if value == side:
                if r-c not in diag_to_ind:
                    diag_to_ind[r-c] = list()
                if r+c not in diag_to_ind:
                    diag_to_ind[r+c] = list()

                if len(diag_to_ind[r-c]) > 0 and (abs(r - diag_to_ind[r - c][-1][0]) != 1 and abs(c - diag_to_ind[r - c][-1][1]) != 1):
                     main_diag[r - c] = 0
                     diag_to_ind[r - c] = list()
                if len(diag_to_ind[r+c]) > 0 and (abs(r - diag_to_ind[r + c][-1][0]) != 1 and abs(c - diag_to_ind[r + c][-1][1]) != 1):
                    main_diag[r + c] = 0
                    diag_to_ind[r + c] = list()
                    
                main_diag[r - c] += 1
                anti_diag[r + c] += 1

                
                diag_to_ind[r - c].append((r,c))
                diag_to_ind[r + c].append((r,c))
            else:
                main_diag[r - c] = 0
                anti_diag[r + c] = 0
                diag_to_ind[r - c] = list()
                diag_to_ind[r + c] = list()
    
        max_key_main = max(main_diag, key=main_diag.get, default= 0)
        max_key_anti = max(anti_diag, key=anti_diag.get, default= 0)
        max_main = main_diag[max_key_main]
        max_anti = anti_diag[max_key_anti]
    
        res = max(max_main, max_anti)
        path = []

        if res == max_main and res != 0:
            path = diag_to_ind[max_key_main].copy()
        elif res == max_anti and res != 0:
            path = diag_to_ind[max_key_anti].copy()
        return res, path
    
    def eval(self, state, side):
        my = max(
        self.find_longest_row(state, side)[0],
        self.find_longest_column(state, side)[0],
        self.find_longest_diag(state, side)[0]
        )

        opp = max(
            self.find_longest_row(state, 1-side)[0],
            self.find_longest_column(state, 1-side)[0],
            self.find_longest_diag(state, 1-side)[0]
        )

        if opp == self.m - 1:
            return -10000
        if my == self.m - 1:
            return 10000
        
        return my - opp

    def actions(self, state): #should return ordered list of positions of possible next moves
        actions = []

        max_row_len, path_row = self.find_longest_row(state, self.side)
        max_col_len, path_col = self.find_longest_column(state, self.side)
        max_diag_len, path_diag = self.find_longest_diag(state, self.side)
        max_row_len_op, path_row_op = self.find_longest_row(state, 1 - self.side)
        max_col_len_op, path_col_op = self.find_longest_column(state, 1 - self.side)
        max_diag_len_op, path_diag_op = self.find_longest_diag(state, 1 - self.side)


        ord_lengths =sorted({"row": max_row_len, "col": max_col_len, "diag":max_diag_len}.items(), key=lambda x: x[1], reverse= True)
        ord_lengths_op =sorted({"row": max_row_len_op, "col": max_col_len_op, "diag":max_diag_len_op}.items(), key=lambda x: x[1], reverse= True)

        for key, len in ord_lengths:
                if len == 0: 
                    continue 
                new_start =  new_end = None

                if key == "row":
                    new_start = (path_row[0][0], path_row[0][1]-1)
                    new_end = (path_row[-1][0], path_row[-1][1]+1)
                elif key == "col":
                    new_start = (path_col[0][0]-1, path_col[0][1])
                    new_end = (path_col[-1][0]+1, path_col[-1][1])
                elif key == "diag":
                    
                    if path_diag[-1][1] - path_diag[0][1] >= 0:
                        new_start = (path_diag[0][0]-1, path_diag[0][1]-1)
                        new_end = (path_diag[-1][0]+1, path_diag[-1][1]+1)
                    else:
                        new_start = (path_diag[0][0]-1, path_diag[0][1]+1)
                        new_end = (path_diag[-1][0]+1, path_diag[-1][1]-1)

                
                if new_start is not None and new_start[0] in range(1,self.n + 1) and new_start[1] in range(1,self.n+1) and new_start not in state and new_start not in actions:
                    actions.append(new_start)
                    
                if new_end is not None and new_end[0] in range(1,self.n + 1) and new_end[1] in range(1,self.n+1) and new_end not in state and new_end not in actions:
                    actions.append(new_end)

        for key, len in ord_lengths_op:
                if len == 0: 
                    continue 
                new_start =  new_end = None

                if key == "row":
                    new_start = (path_row_op[0][0], path_row_op[0][1]-1)
                    new_end = (path_row_op[-1][0], path_row_op[-1][1]+1)
                elif key == "col":
                    new_start = (path_col_op[0][0]-1, path_col_op[0][1])
                    new_end = (path_col_op[-1][0]+1, path_col_op[-1][1])
                elif key == "diag":
                    
                    if path_diag_op[-1][1] - path_diag_op[0][1] >= 0:
                        new_start = (path_diag_op[0][0]-1, path_diag_op[0][1]-1)
                        new_end = (path_diag_op[-1][0]+1, path_diag_op[-1][1]+1)
                    else:
                        new_start = (path_diag_op[0][0]-1, path_diag_op[0][1]+1)
                        new_end = (path_diag_op[-1][0]+1, path_diag_op[-1][1]-1)

                
                if new_start is not None and new_start[0] in range(1,self.n + 1) and new_start[1] in range(1,self.n+1) and new_start not in state and new_start not in actions:
                    actions.append(new_start)
                    
                if new_end is not None and new_end[0] in range(1,self.n + 1) and new_end[1] in range(1,self.n+1) and new_end not in state and new_end not in actions:
                    actions.append(new_end)
        return actions

    def min_value(self, state, alpha, beta, depth, max_deth, pos = None):
        if depth >= max_deth or self.terminal_state(state):
            return self.eval(state, 1 - self.side), (pos if pos is not None else float("inf")) 
        
        v = float("inf")
        eventual_pos = None

        for pos in self.actions(state):
            new_state = state.copy()
            new_state[pos] = 1 - self.side
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
            
            new_state = state.copy()
            new_state[pos] = self.side
            eventual_pos = pos
            new_val, _ = self.min_value(new_state, alpha, beta, depth + 1, max_deth, pos)
            v = max(v, new_val)

            if v >= beta:
                return v, pos
            
            alpha = max(alpha, v)
        
        
        return v, eventual_pos
 
    def is_win(self, state):
        temp = state.copy()

        for i in range(1, self.n + 1):
            for j in range(1, self.n +1):
                if (i, j) not in temp:
                    temp[(i,j)] = self.side
                    if self.terminal_state(temp):
                        return (i,j)
                    del temp[(i,j)]
        return None

    def is_break(self, state):
        temp = state.copy()

        for i in range(1, self.n + 1):
            for j in range(1, self.n +1):
                if (i, j) not in temp:
                    temp[(i,j)] = 1 - self.side
                    if self.terminal_state(temp):
                        return (i,j)
                    del temp[(i,j)]
                    
        return None
    
    def alpha_beta(self):
        start = time.time()
        action = None
        max_depth = 0

        win_pos = self.is_win(self.current_state)
        break_pos = self.is_break(self.current_state)

        if win_pos is not None:
            return win_pos
        elif break_pos is not None:
            return break_pos
        
        if len(self.current_state) == self.n * self.n - 1:
            return None
        
        while(abs(time.time() - start) <= self.time_limit):
            state = deepcopy(self.current_state)
            val = float("-inf")
            new_val, new_pos = self.max_value(state, float("-inf"), float("inf"), 0, max_depth)
            
            if new_val > val:
                val = new_val
                action = new_pos

            max_depth += 1

        return action
    
    def print_board(self, board):
        symbol = {1: 'X', 0: 'O'}
        print("\n")
        for r in range(1,self.n+1):
            row = []
            for c in range(1,self.n+1):
                val = board.get((r, c))
                row.append(symbol[val] if val in symbol else '.')
            print(" ".join(row))
        print("\n")

    def play(self):
        self.print_board(self.current_state)

        while True: 
            usr_pos = tuple(map(int, input("\nEnter position (x, y): ").split(',')))

            if usr_pos in self.current_state:
                while True:
                    usr_pos = tuple(map(int, input("\nEnter position (x, y): ").split(',')))
                    if usr_pos not in self.current_state:
                        break
            self.current_state[usr_pos] = 1 - self.side

            print("User move: ")
            self.print_board(self.current_state)

            if self.terminal_state(self.current_state)  :
                print("\nUser won!")
                break
            elif len(self.current_state) == self.n * self.n:
                print("\nDraw")
                break

            action = self.alpha_beta()

            if action is None:
                print("\nDraw")
                break

            self.current_state[action] = self.side

            print("Agent move: ")
            self.print_board(self.current_state)

            if self.terminal_state(self.current_state):
                print("\nAgent won!")
                break
            elif len(self.current_state) == self.n * self.n:
                print("\nDraw")
                break


