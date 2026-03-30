import time
from copy import deepcopy
from collections import defaultdict

class agent:
    """
    An agent that plays an m-in-a-row game on an n x n board (a generalized Tic-Tac-Toe).
    Uses iterative-deepening alpha-beta minimax search to determine the best move.

    Players are represented as integers:
        - self.side     : the agent's token (1 = X)
        - 1 - self.side : the opponent's token (0 = O)

    Board state is stored as a dict mapping (row, col) -> player_int.
    Rows and columns are 1-indexed from 1 to n.
    """

    def __init__(self, n, m, side):
        """
        Initialize the agent.

        Args:
            n    (int): Board dimension (n x n grid).
            m    (int): Number of consecutive pieces needed to win.
            side (int): The agent's assigned player: 1 (X) or 0 (O).
        """
        self.n = n
        self.m = m
        self.current_state = {}   # Active board state: {(row, col): player_int}
        self.found_moves = {}     # Reserved for future move caching (currently unused)
        self.time_limit = 1      # Max seconds allowed for alpha-beta search per turn
        self.side = side          # X/1 or O/0

    def terminal_state(self, state):
        """
        Check whether the given state is a terminal (game-over) state.
        A state is terminal if either player has formed a winning line of length m
        in any row, column, or diagonal.

        Returns:
            bool: True if the game is over, False otherwise.
        """
        for player in [self.side, 1 - self.side]:
            if (self.find_longest_row(state, player)[0] == self.m or
            self.find_longest_column(state, player)[0] == self.m or
            self.find_longest_diag(state, player)[0] == self.m):
                return True
        return False

    def find_longest_row(self, state, side):
        """
        Find the longest horizontally consecutive run of `side`'s pieces on the board.

        Iterates over every row that contains at least one of `side`'s pieces,
        scanning columns left-to-right and counting consecutive occupied cells.
        Resets the streak whenever a gap (non-adjacent column or opponents position) is detected.

        Args:
            state (dict): Current board state.
            side  (int) : Player whose pieces to examine.

        Returns:
            tuple: (max_length, path) where max_length is the length of the longest
                   consecutive horizontal run and path is the list of (row, col) cells
                   in that run.
        """
        max_row_length = 0
        # Collect all row indices that contain at least one piece for `side`
        row_ind = set([i for (i, j), k in state.items() if k == side])
        max_row_ind = []
        
        for i in row_ind:
            temp = []       # Cells in the current consecutive streak
            len_temp = 0    # Length of the current streak
            for j in range(self.n):
                if (i, j) not in state:
                    continue
                if state[(i, j)] == side:
                    # If the last recorded cell is not adjacent, reset the streak
                    if len(temp) > 0 and (abs(j - temp[-1][1]) != 1):
                        len_temp = 0
                        temp = []
                    len_temp += 1
                    temp.append((i,j))

                    if len_temp > max_row_length:
                        max_row_length = len_temp
                        max_row_ind = temp.copy()
                
            max_row_length = max(max_row_length, len_temp)

        return max_row_length, max_row_ind
    
    def find_longest_column(self, state, side):
        """
        Find the longest vertically consecutive run of `side`'s pieces on the board.

        Mirrors find_longest_row but scans down each column instead of across each row.

        Args:
            state (dict): Current board state.
            side  (int) : Player whose pieces to examine.

        Returns:
            tuple: (max_length, path) — same structure as find_longest_row.
        """
        max_col_length = 0
        # Collect all column indices that contain at least one piece for `side`
        col_ind = set([j for (i, j), k in state.items() if k == side])
        max_col_ind = []

        for j in col_ind:
            len_temp = 0
            temp = []
            for i in range(self.n):
                if (i, j) not in state:
                    continue
                if state[(i, j)] == side:
                    # If the last recorded cell is not adjacent, reset the streak
                    if len(temp) > 0 and (abs(i - temp[-1][0]) != 1):
                        len_temp = 0
                        temp = []
                    len_temp += 1
                    temp.append((i,j))

                    if len_temp > max_col_length:
                        max_col_length = len_temp
                        max_col_ind = temp.copy()
                
            max_col_length = max(max_col_length, len_temp)

        return max_col_length, max_col_ind
    
    def find_longest_diag(self, state, side):
        """
        Find the longest diagonally consecutive run of `side`'s pieces on the board.

        Checks both main diagonals (top-left to bottom-right, r - c = constant)
        and anti-diagonals (top-right to bottom-left, r + c = constant).
        Resets a diagonal's count when a gap or opponent's position between consecutive pieces is detected.
        Note: The gap-detection logic currently resets both the main and anti-diagonal
        counters for the same cell; in edge cases this may undercount anti-diagonal runs.

        Args:
            state (dict): Current board state.
            side  (int) : Player whose pieces to examine.

        Returns:
            tuple: (max_length, path) where max_length is the longest diagonal run
                   and path is the list of (row, col) cells comprising it.
        """
        main_diag = defaultdict(int)   # Maps (r - c) -> current streak length on that main diagonal
        anti_diag = defaultdict(int)   # Maps (r + c) -> current streak length on that anti-diagonal
        diag_to_ind = {}               # Maps diagonal key -> list of cells in the current streak

        for (r, c), value in state.items():
            if value == side:
                if r-c not in diag_to_ind:
                    diag_to_ind[r-c] = list()
                if r+c not in diag_to_ind:
                    diag_to_ind[r+c] = list()

                # Reset main diagonal streak if current cell is not adjacent to the previous one
                if len(diag_to_ind[r-c]) > 0 and (abs(r - diag_to_ind[r - c][-1][0]) != 1 and abs(c - diag_to_ind[r - c][-1][1]) != 1):
                     main_diag[r - c] = 0
                     diag_to_ind[r - c] = list()
                # Reset anti-diagonal streak if current cell is not adjacent to the previous one
                if len(diag_to_ind[r+c]) > 0 and (abs(r - diag_to_ind[r + c][-1][0]) != 1 and abs(c - diag_to_ind[r + c][-1][1]) != 1):
                    anti_diag[r + c] = 0
                    diag_to_ind[r + c] = list()
                    
                main_diag[r - c] += 1
                anti_diag[r + c] += 1

                diag_to_ind[r - c].append((r,c))
                diag_to_ind[r + c].append((r,c))
            
        # Find the diagonal key with the maximum streak for each diagonal type
        max_key_main = max(main_diag, key=main_diag.get, default= 0)
        max_key_anti = max(anti_diag, key=anti_diag.get, default= 0)
        max_main = main_diag[max_key_main]
        max_anti = anti_diag[max_key_anti]
    
        res = max(max_main, max_anti)
        path = []

        # Retrieve the path of the winning/longest diagonal
        if res == max_main and res != 0:
            path = diag_to_ind[max_key_main].copy()
        elif res == max_anti and res != 0:
            path = diag_to_ind[max_key_anti].copy()
        return res, path
    
    def eval(self, state, side):
        """
        Heuristic evaluation function for a non-terminal board state.

        Computes the longest run for `side` (my) and for the opponent (opp) across
        all three directions. Returns a large positive value if `side` is one move
        away from winning, a large negative value if the opponent is one move away,
        and the simple difference (my - opp) otherwise.

        Args:
            state (dict): Current board state.
            side  (int) : The player from whose perspective to evaluate.

        Returns:
            int: A heuristic score. Higher values favor `side`.
        """
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

        # Heavily penalize states where the opponent is about to win
        if opp == self.m - 1:
            return -10000
        # Heavily reward states where we are about to win
        if my == self.m - 1:
            return 10000
        
        return my - opp

    def actions(self, state): 
        """
        Generate a focused, ordered list of candidate moves for the current state.

        Rather than enumerating all empty cells (which would be too slow on large boards),
        this method identifies the most promising moves by looking at the endpoints of
        the longest existing runs:
          1. Extend the agent's own longest row, column, and diagonal runs.
          2. Block the opponent's longest row, column, and diagonal runs.

        Runs are prioritized by length (longest first) and each generates at most two
        candidate cells (one at each end of the existing streak). Only valid, unoccupied
        cells within board bounds are included.

        Args:
            state (dict): Current board state.

        Returns:
            list: Ordered list of (row, col) candidate move positions.
        """
        actions_list = []

        # Measure the agent's longest streaks and their cell paths in each direction
        max_row_len, path_row = self.find_longest_row(state, self.side)
        max_col_len, path_col = self.find_longest_column(state, self.side)
        max_diag_len, path_diag = self.find_longest_diag(state, self.side)
        # Measure the opponent's longest streaks and their cell paths in each direction
        max_row_len_op, path_row_op = self.find_longest_row(state, 1 - self.side)
        max_col_len_op, path_col_op = self.find_longest_column(state, 1 - self.side)
        max_diag_len_op, path_diag_op = self.find_longest_diag(state, 1 - self.side)

        # Sort directions by streak length so we extend the most threatening lines first
        ord_lengths =sorted({"row": max_row_len, "col": max_col_len, "diag":max_diag_len}.items(), key=lambda x: x[1], reverse= True)
        ord_lengths_op =sorted({"row": max_row_len_op, "col": max_col_len_op, "diag":max_diag_len_op}.items(), key=lambda x: x[1], reverse= True)

        # --- Agent's offensive extension moves ---
        for key, streak_len in ord_lengths:
                if streak_len == 0: 
                    continue   # No pieces placed yet in this direction; skip
                new_start =  new_end = None

                if key == "row":
                    # Extend horizontally: one cell left of the streak start, one right of the end
                    new_start = (path_row[0][0], path_row[0][1]-1)
                    new_end = (path_row[-1][0], path_row[-1][1]+1)
                elif key == "col":
                    # Extend vertically: one cell above the streak start, one below the end
                    new_start = (path_col[0][0]-1, path_col[0][1])
                    new_end = (path_col[-1][0]+1, path_col[-1][1])
                elif key == "diag":
                    # Determine diagonal direction: positive slope vs. negative slope
                    if path_diag[-1][1] - path_diag[0][1] >= 0:
                        # Main diagonal (top-left → bottom-right): extend both ends diagonally
                        new_start = (path_diag[0][0]-1, path_diag[0][1]-1)
                        new_end = (path_diag[-1][0]+1, path_diag[-1][1]+1)
                    else:
                        # Anti-diagonal (top-right → bottom-left): extend in the opposite direction
                        new_start = (path_diag[0][0]-1, path_diag[0][1]+1)
                        new_end = (path_diag[-1][0]+1, path_diag[-1][1]-1)

                # Only add a candidate if it is within the board and not already occupied
                if new_start is not None and new_start[0] in range(self.n) and new_start[1] in range(self.n) and new_start not in state and new_start not in actions_list:
                    actions_list.append(new_start)
                    
                if new_end is not None and new_end[0] in range(self.n) and new_end[1] in range(self.n) and new_end not in state and new_end not in actions_list:
                    actions_list.append(new_end)

        # --- Opponent's defensive blocking moves (same logic, applied to opponent's streaks) ---
        for key, streak_len in ord_lengths_op:
                
                if streak_len == 0: 
                    continue   # Opponent has no pieces in this direction; skip
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

                if new_start is not None and new_start[0] in range(self.n) and new_start[1] in range(self.n) and new_start not in state and new_start not in actions_list:
                    actions_list.append(new_start)
                    
                if new_end is not None and new_end[0] in range(self.n) and new_end[1] in range(self.n) and new_end not in state and new_end not in actions_list:
                    actions_list.append(new_end)
        
        if len(actions_list) > 0:
            return actions_list
        for (r,c) in state.keys():
            for dr in [-1,0,1]:
                for dc in [-1,0,1]:
                    nr = r + dr
                    nc = c + dc

                    if nr in range(self.n) and nc in range(self.n):
                        if (nr,nc) not in state and (nr, nc) not in actions_list:
                            actions_list.append((nr,nc))
        return actions_list

    def min_value(self, state, alpha, beta, depth, max_deth, pos = None):
        """
        Minimax MIN node: the opponent's turn. Tries to minimize the agent's score.

        Applies alpha-beta pruning: stops exploring a branch as soon as the found
        value is <= alpha (the best the MAX player can already guarantee elsewhere).

        Args:
            state    (dict) : Board state at this node.
            alpha    (float): Best score MAX can guarantee so far (lower bound).
            beta     (float): Best score MIN can guarantee so far (upper bound).
            depth    (int)  : Current search depth.
            max_deth (int)  : Maximum depth limit for this iteration.
            pos      (tuple): The move that led to this state (for backtracking).

        Returns:
            tuple: (value, position) — the minimax score and the move that achieves it.
        """
        # Base case: depth limit reached or game is over — return heuristic evaluation
        if depth >= max_deth or self.terminal_state(state):
            return self.eval(state, 1 - self.side), (pos if pos is not None else float("inf")) 
        
        v = float("inf")
        eventual_pos = None

        for pos in self.actions(state):
            new_state = state.copy()
            new_state[pos] = 1 - self.side   # Opponent places their piece
            eventual_pos = pos
            new_val, _ = self.max_value(new_state, alpha, beta, depth + 1, max_deth, pos)
            v = min(v, new_val)

            # Alpha pruning: MAX would never choose this branch, so cut it off
            if v <= alpha:
                return v, pos
            
            beta = min(beta, v)

        return v, eventual_pos

    def max_value(self, state, alpha, beta, depth, max_deth, pos = None):
        """
        Minimax MAX node: the agent's turn. Tries to maximize the agent's score.

        Applies alpha-beta pruning: stops exploring a branch as soon as the found
        value is >= beta (the best the MIN player can already guarantee elsewhere).

        Args:
            state    (dict) : Board state at this node.
            alpha    (float): Best score MAX can guarantee so far (lower bound).
            beta     (float): Best score MIN can guarantee so far (upper bound).
            depth    (int)  : Current search depth.
            max_deth (int)  : Maximum depth limit for this iteration.
            pos      (tuple): The move that led to this state (for backtracking).

        Returns:
            tuple: (value, position) — the minimax score and the move that achieves it.
        """
        # Base case: depth limit reached or game is over — return heuristic evaluation
        if depth >= max_deth or self.terminal_state(state):
            return self.eval(state, self.side), (pos if pos is not None else float("-inf")) 
        
        v = float("-inf")
        eventual_pos = None
        for pos in self.actions(state):
            
            new_state = state.copy()
            new_state[pos] = self.side   # Agent places its piece
            eventual_pos = pos
            new_val, _ = self.min_value(new_state, alpha, beta, depth + 1, max_deth, pos)
            v = max(v, new_val)

            # Beta pruning: MIN would never allow this branch, so cut it off
            if v >= beta:
                return v, pos
            
            alpha = max(alpha, v)
        
        return v, eventual_pos
 
    def is_win(self, state):
        """
        Check if the agent can win immediately on the next move.

        Scans every empty cell and tests whether placing the agent's piece there
        would produce a terminal (winning) state.

        Args:
            state (dict): Current board state.

        Returns:
            tuple or None: The (row, col) of the winning move, or None if no
                           immediate winning move exists.
        """
        temp = state.copy()

        for i in range(self.n):
            for j in range(self.n):
                if (i, j) not in temp:
                    temp[(i,j)] = self.side
                    if self.terminal_state(temp):
                        return (i,j)
                    del temp[(i,j)]
        return None

    def is_break(self, state):
        """
        Check if the opponent can win immediately on their next move (a threat to block).

        Scans every empty cell and tests whether the opponent placing their piece there
        would produce a terminal state. If so, the agent must block that cell.

        Args:
            state (dict): Current board state.

        Returns:
            tuple or None: The (row, col) of the opponent's winning move to block,
                           or None if no immediate threat exists.
        """
        temp = state.copy()

        for i in range(self.n):
            for j in range(self.n):
                if (i, j) not in temp:
                    temp[(i,j)] = 1 - self.side
                    if self.terminal_state(temp):
                        return (i,j)
                    del temp[(i,j)]
                    
        return None
    
    def alpha_beta(self):
        """
        Entry point for the agent's move decision using iterative-deepening alpha-beta search.

        First checks for immediate wins or forced blocks (depth-0 shortcuts). Then runs
        alpha-beta minimax with progressively increasing depth limits until the time budget
        (self.time_limit seconds) is exhausted, always keeping the best action found so far.

        Iterative deepening ensures the agent always has a valid move ready even if time
        runs out mid-search, since each completed depth iteration improves the estimate.

        Returns:
            tuple or None: The best (row, col) action found, or None if the board is
                           nearly full and no move is needed.
        """
        start = time.time()
        action = None
        max_depth = 0
        val = float("-inf")

        # Shortcut 1: play the immediate winning move if one exists
        win_pos = self.is_win(self.current_state)
        # Shortcut 2: block the opponent's immediate winning move if one exists
        break_pos = self.is_break(self.current_state)

        if win_pos is not None:
            return win_pos
        elif break_pos is not None:
            return break_pos
        
        # If only one cell remains, there is no meaningful move to return
        if len(self.current_state) == self.n * self.n - 1:
            return None
        
        # Iterative deepening: keep increasing depth until the time limit is hit
        while(abs(time.time() - start) <= self.time_limit):
            state = deepcopy(self.current_state)
            
            new_val, new_pos = self.max_value(state, float("-inf"), float("inf"), 0, max_depth)
            
            if new_val > val:
                val = new_val
                action = new_pos

            max_depth += 1

        return action
    
    def print_board(self, board):
        """
        Print a human-readable ASCII representation of the board.

        Empty cells are shown as '.', X pieces as 'X', and O pieces as 'O'.

        Args:
            board (dict): Board state to display.
        """
        symbol = {1: 'X', 0: 'O'}
        print("\n")
        for r in range(self.n):
            row = []
            for c in range(self.n):
                val = board.get((r, c))
                row.append(symbol[val] if val in symbol else '.')
            print(" ".join(row))
        print("\n")

    def play(self):
        """
        Run the interactive game loop between the human user and the agent.

        The user plays as the opponent (1 - self.side) and enters moves as
        comma-separated "row,col" coordinates. The agent replies with its
        best move computed by alpha_beta(). The loop ends when either player
        wins or the board is completely filled (draw).
        """
        self.print_board(self.current_state)

        while True: 
            usr_pos = tuple(map(int, input("\nEnter position (x, y): ").split(',')))

            # Re-prompt if the chosen cell is already occupied
            if usr_pos in self.current_state:
                while True:
                    usr_pos = tuple(map(int, input("\nEnter position (x, y): ").split(',')))
                    if usr_pos not in self.current_state:
                        break
            self.current_state[usr_pos] = 1 - self.side   # Record the user's move

            print("User move: ")
            self.print_board(self.current_state)

            if self.terminal_state(self.current_state)  :
                print("\nUser won!")
                break
            elif len(self.current_state) == self.n * self.n:
                print("\nDraw")
                break

            # Agent computes and applies its best move
            action = self.alpha_beta()

            if action is None:
                print("\nDraw")
                break

            self.current_state[action] = self.side

            print("Agent move: ", action)

            self.print_board(self.current_state)

            if self.terminal_state(self.current_state):
                print("\nAgent won!")
                break
            elif len(self.current_state) == self.n * self.n:
                print("\nDraw")
                break