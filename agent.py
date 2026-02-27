import time
from copy import deepcopy
class agent:

    def __init__(self, n, m, side):
        self.n = n
        self.m = m
        self.current_state = {}
        self.found_moves = {}
        self.time_limit = 100
        self.side = side #X or O

    def eval(self, state):
        pass

    def actions(self, state): #should return position of the next move
        pass

    def min_value(self, state, alpha, beta, depth, max_deth):
        if depth <= max_deth:
            return self.eval(state)
        
        v = float("inf")

        for pos in self.actions(state):
            new_state = deepcopy(state)
            new_state[pos] = self.side
            v = max(v, self.min_value(state, alpha, beta, depth + 1, max_deth))

            if v <= alpha:
                return v
            
            beta = min(beta, v)

        return v

    def max_value(self, state, alpha, beta, depth, max_deth):
        if depth <= max_deth:
            return self.eval(state)
        
        v = float("-inf")

        for pos in self.actions(state):
            new_state = deepcopy(state)
            new_state[pos] = self.side
            v = max(v, self.min_value(state, alpha, beta, depth + 1, max_deth))

            if v >= beta:
                return v
            
            alpha = max(alpha, v)
        
        return v
        
    def alpha_beta(self):
        start = time.time

        while(abs(time.time - start) <= self.time_limit):
            max_depth = 0

            state = deepcopy(self.current_state)
            val = float("-inf")
            val = max(val, self.max_value(state, float("-inf"), float("inf"), 0, max_depth))

            max_depth += 1
        


    
        
    
