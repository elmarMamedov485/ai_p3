import time


class SearchTimeout(Exception):
    """Raised when the current move search runs out of time."""

    pass


class agent:
    """
    An agent for generalized Tic-Tac-Toe on an n x n board.

    The agent uses iterative-deepening alpha-beta search with a heuristic
    evaluation function to choose moves under a fixed time limit.

    Players are represented as integers:
        - self.side     : the agent's token (1 = X)
        - 1 - self.side : the opponent's token (0 = O)

    Board states are stored as dictionaries:
        {(row, col): player}

    Rows and columns are 1-indexed inside the agent.
    """

    def __init__(self, n, m, side, time_limit=15):
        """
        Initialize the agent.

        Args:
            n (int): Board size.
            m (int): Number of consecutive marks needed to win.
            side (int): The side controlled by this agent, 1 for X or 0 for O.
            time_limit (float): Time budget in seconds for one move.
        """
        self.n = n
        self.m = m
        self.side = side
        self.current_state = {}
        self.time_limit = time_limit
        self.deadline = None
        self.directions = ((0, 1), (1, 0), (1, 1), (1, -1))
        # Keep the move list small enough for deeper search on larger boards.
        self.max_branching = 18
        self.last_search_info = {}

    def opponent(self, side):
        """Return the other player's integer label."""
        return 1 - side

    def in_bounds(self, row, col):
        """Check whether a position is inside the board."""
        return 1 <= row <= self.n and 1 <= col <= self.n

    def board_full(self, state):
        """Return True when no empty cells remain."""
        return len(state) >= self.n * self.n

    def _check_time(self):
        """Stop the current search branch if the move timer has expired."""
        if self.deadline is not None and time.time() >= self.deadline:
            raise SearchTimeout

    def _run_length_from(self, state, row, col, dr, dc):
        """
        Measure the full contiguous line length through one occupied cell.

        Starting from (row, col), this walks in both directions along (dr, dc)
        and counts how many consecutive stones of the same side are connected.
        """
        side = state.get((row, col))
        if side is None:
            return 0

        length = 1

        next_row = row + dr
        next_col = col + dc
        while state.get((next_row, next_col)) == side:
            length += 1
            next_row += dr
            next_col += dc

        prev_row = row - dr
        prev_col = col - dc
        while state.get((prev_row, prev_col)) == side:
            length += 1
            prev_row -= dr
            prev_col -= dc

        return length

    def winner(self, state):
        """
        Return the winning side for a state, or None if there is no winner.

        A win is any row, column, or diagonal run of length at least m.
        """
        for (row, col), side in state.items():
            for dr, dc in self.directions:
                prev_row = row - dr
                prev_col = col - dc
                if state.get((prev_row, prev_col)) == side:
                    continue

                length = 1
                next_row = row + dr
                next_col = col + dc
                while state.get((next_row, next_col)) == side:
                    length += 1
                    if length >= self.m:
                        return side
                    next_row += dr
                    next_col += dc

        return None

    def terminal_state(self, state):
        """Check whether the position is a win for either side or a draw."""
        return self.winner(state) is not None or self.board_full(state)

    def _segment_cells(self, start_row, start_col, dr, dc):
        """
        Build one length-m segment on the board.

        Returns:
            list[tuple[int, int]] | None: The cells in the segment, or None
            if the segment would extend beyond the board.
        """
        cells = []
        for step in range(self.m):
            row = start_row + step * dr
            col = start_col + step * dc
            if not self.in_bounds(row, col):
                return None
            cells.append((row, col))
        return cells

    def _open_ends(self, state, cells):
        """
        Count how many ends of a segment are still open.

        An open end is an in-bounds empty cell immediately before or after the
        segment along the same direction.
        """
        start_row, start_col = cells[0]
        end_row, end_col = cells[-1]
        dr = end_row - cells[-2][0] if len(cells) > 1 else 0
        dc = end_col - cells[-2][1] if len(cells) > 1 else 0

        open_ends = 0
        before = (start_row - dr, start_col - dc)
        after = (end_row + dr, end_col + dc)

        if self.in_bounds(*before) and before not in state:
            open_ends += 1
        if self.in_bounds(*after) and after not in state:
            open_ends += 1

        return open_ends

    def _window_score(self, state, cells):
        """
        Score one length-m segment for the evaluation function.

        Segments containing both sides are treated as neutral. Open-ended
        threats and near-wins receive much larger weights than isolated stones.
        """
        mine = 0
        opp = 0

        for row, col in cells:
            value = state.get((row, col))
            if value == self.side:
                mine += 1
            elif value == self.opponent(self.side):
                opp += 1

        if mine and opp:
            return 0
        if mine == 0 and opp == 0:
            return 0

        if mine:
            open_ends = self._open_ends(state, cells)
            if mine == self.m - 1:
                return 200000 if open_ends == 2 else 90000
            if mine == self.m - 2:
                return 12000 if open_ends == 2 else 4000
            if mine == 1:
                return 12
            return (10 ** mine) * max(1, open_ends)

        open_ends = self._open_ends(state, cells)
        if opp == self.m - 1:
            return -260000 if open_ends == 2 else -120000
        if opp == self.m - 2:
            return -18000 if open_ends == 2 else -6000
        if opp == 1:
            return -12
        return -((10 ** opp) * max(1, open_ends))

    def _center_score(self, state):
        """Give a small bonus for occupying the central area of the board."""
        middle = (self.n + 1) / 2
        score = 0

        for (row, col), side in state.items():
            bonus = self.n - (abs(row - middle) + abs(col - middle))
            if side == self.side:
                score += bonus
            else:
                score -= bonus

        return int(score)

    def eval(self, state):
        """
        Heuristic evaluation from this agent's point of view.

        The evaluation combines:
            - terminal win/loss checks
            - central control
            - scores for all length-m row/column/diagonal segments

        Higher values are better for self.side.
        """
        winner = self.winner(state)
        if winner == self.side:
            return 10 ** (self.m + 2)
        if winner == self.opponent(self.side):
            return -(10 ** (self.m + 2))
        if self.board_full(state):
            return 0

        score = self._center_score(state)
        for row in range(1, self.n + 1):
            for col in range(1, self.n + 1):
                for dr, dc in self.directions:
                    cells = self._segment_cells(row, col, dr, dc)
                    if cells is None:
                        continue
                    score += self._window_score(state, cells)

        return score

    def _all_empty_cells(self, state):
        """Return every empty board position."""
        moves = []
        for row in range(1, self.n + 1):
            for col in range(1, self.n + 1):
                if (row, col) not in state:
                    moves.append((row, col))
        return moves

    def _has_neighbor(self, state, row, col, radius):
        """Check whether a cell is near any existing stone."""
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr == 0 and dc == 0:
                    continue
                if (row + dr, col + dc) in state:
                    return True
        return False

    def _candidate_cells(self, state):
        """
        Build a reduced move list for search.

        Instead of searching every empty square, prefer cells within one or two
        steps of existing stones. This keeps the branching factor manageable on
        larger boards.
        """
        if not state:
            center = (self.n + 1) // 2
            return [(center, center)]

        candidates = {}

        for row in range(1, self.n + 1):
            for col in range(1, self.n + 1):
                if (row, col) in state:
                    continue
                if self._has_neighbor(state, row, col, 1):
                    candidates[(row, col)] = 3
                elif self._has_neighbor(state, row, col, 2):
                    candidates[(row, col)] = 2

        if candidates:
            return list(candidates)
        return self._all_empty_cells(state)

    def _count_neighbors(self, state, row, col, side=None, radius=1):
        """Count nearby occupied cells, optionally filtered by side."""
        count = 0
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr == 0 and dc == 0:
                    continue
                value = state.get((row + dr, col + dc))
                if value is None:
                    continue
                if side is None or value == side:
                    count += 1
        return count

    def _line_potential(self, state, move, side, dr, dc):
        """
        Estimate the line strength created by one hypothetical move.

        Returns:
            tuple[int, int]: (run_length, open_ends)
        """
        row, col = move
        temp = state.copy()
        temp[move] = side
        length = self._run_length_from(temp, row, col, dr, dc)

        next_row = row + dr
        next_col = col + dc
        while temp.get((next_row, next_col)) == side:
            next_row += dr
            next_col += dc

        prev_row = row - dr
        prev_col = col - dc
        while temp.get((prev_row, prev_col)) == side:
            prev_row -= dr
            prev_col -= dc

        open_ends = 0
        if self.in_bounds(next_row, next_col) and (next_row, next_col) not in temp:
            open_ends += 1
        if self.in_bounds(prev_row, prev_col) and (prev_row, prev_col) not in temp:
            open_ends += 1

        return length, open_ends

    def _move_priority(self, state, move, side):
        """
        Score one candidate move for move ordering.

        This is not the full evaluation function. It is a cheaper tactical
        estimate used only to search promising moves first.
        """
        row, col = move
        opponent = self.opponent(side)
        score = 0

        temp = state.copy()
        temp[move] = side
        if self.winner(temp) == side:
            return 10 ** (self.m + 3)

        temp[move] = opponent
        if self.winner(temp) == opponent:
            score += 10 ** (self.m + 2)

        for dr, dc in self.directions:
            own_length, own_open = self._line_potential(state, move, side, dr, dc)
            opp_length, opp_open = self._line_potential(state, move, opponent, dr, dc)

            score += 120 * (own_length ** 3) + 90 * own_open
            score += 95 * (opp_length ** 3) + 70 * opp_open

            if own_length >= self.m - 1:
                score += 250000
            elif own_length == self.m - 2 and own_open == 2:
                score += 35000

            if opp_length >= self.m - 1:
                score += 220000
            elif opp_length == self.m - 2 and opp_open == 2:
                score += 28000

        score += 30 * self._count_neighbors(state, row, col, side)
        score += 20 * self._count_neighbors(state, row, col, opponent)

        center = (self.n + 1) / 2
        score -= int(abs(row - center) + abs(col - center))
        return score

    def actions(self, state, side=None):
        """
        Return an ordered list of candidate moves.

        Candidate moves are sorted by tactical priority, then trimmed to a
        fixed maximum branching factor for alpha-beta search.
        """
        if side is None:
            side = self.side

        moves = self._candidate_cells(state)
        # Good move ordering matters more than raw depth for this project.
        ordered = sorted(
            moves,
            key=lambda move: self._move_priority(state, move, side),
            reverse=True,
        )
        if len(ordered) > self.max_branching:
            return ordered[: self.max_branching]
        return ordered

    def _immediate_move(self, state, side):
        """Return a direct winning move for the given side, if one exists."""
        for move in self.actions(state, side):
            temp = state.copy()
            temp[move] = side
            if self.winner(temp) == side:
                return move
        return None

    def is_win(self, state):
        """Check whether this agent has an immediate winning move."""
        return self._immediate_move(state, self.side)

    def is_break(self, state):
        """Check whether the opponent has an immediate winning move to block."""
        return self._immediate_move(state, self.opponent(self.side))

    def _alpha_beta(self, state, depth, alpha, beta, turn_side):
        """
        Recursive alpha-beta search.

        Args:
            state (dict): Current board state.
            depth (int): Remaining depth for this iteration.
            alpha (float): Best guaranteed lower bound for MAX.
            beta (float): Best guaranteed upper bound for MIN.
            turn_side (int): Side to move at this node.

        Returns:
            tuple: (score, best_move)
        """
        self._check_time()
        self.last_search_info["nodes"] += 1

        winner = self.winner(state)
        if winner is not None or depth == 0 or self.board_full(state):
            self.last_search_info["evals"] += 1
            return self.eval(state), None

        moves = self.actions(state, turn_side)
        if not moves:
            return self.eval(state), None

        best_move = moves[0]

        if turn_side == self.side:
            value = float("-inf")
            for move in moves:
                next_state = state.copy()
                next_state[move] = turn_side
                child_value, _ = self._alpha_beta(
                    next_state,
                    depth - 1,
                    alpha,
                    beta,
                    self.opponent(turn_side),
                )
                if child_value > value:
                    value = child_value
                    best_move = move
                alpha = max(alpha, value)
                if alpha >= beta:
                    self.last_search_info["cutoffs"] += 1
                    break
            return value, best_move

        value = float("inf")
        for move in moves:
            next_state = state.copy()
            next_state[move] = turn_side
            child_value, _ = self._alpha_beta(
                next_state,
                depth - 1,
                alpha,
                beta,
                self.opponent(turn_side),
            )
            if child_value < value:
                value = child_value
                best_move = move
            beta = min(beta, value)
            if alpha >= beta:
                self.last_search_info["cutoffs"] += 1
                break
        return value, best_move

    def alpha_beta(self):
        """
        Choose a move with iterative-deepening alpha-beta search.

        The method first looks for an immediate win or a forced block. If
        neither exists, it keeps deepening the search until the move timer
        expires, always keeping the best completed result found so far.

        Returns:
            tuple[int, int] | None: The selected move in 1-indexed coordinates.
        """
        start_time = time.time()
        self.last_search_info = {
            "nodes": 0,
            "evals": 0,
            "cutoffs": 0,
            "completed_depth": 0,
            "elapsed": 0.0,
            "move": None,
            "score": None,
            "timed_out": False,
            "candidate_count": 0,
        }

        if self.board_full(self.current_state):
            self.last_search_info["elapsed"] = time.time() - start_time
            return None

        moves = self.actions(self.current_state, self.side)
        self.last_search_info["candidate_count"] = len(moves)
        if not moves:
            self.last_search_info["elapsed"] = time.time() - start_time
            return None

        win_pos = self.is_win(self.current_state)
        if win_pos is not None:
            self.last_search_info["move"] = win_pos
            self.last_search_info["score"] = self.eval(self.current_state)
            self.last_search_info["elapsed"] = time.time() - start_time
            return win_pos

        break_pos = self.is_break(self.current_state)
        if break_pos is not None:
            self.last_search_info["move"] = break_pos
            self.last_search_info["score"] = self.eval(self.current_state)
            self.last_search_info["elapsed"] = time.time() - start_time
            return break_pos

        best_move = moves[0]
        best_value = float("-inf")
        self.deadline = time.time() + self.time_limit
        depth = 1

        try:
            # Iterative deepening gives us a legal move even when the clock cuts search off.
            while True:
                value, move = self._alpha_beta(
                    self.current_state,
                    depth,
                    float("-inf"),
                    float("inf"),
                    self.side,
                )
                if move is not None:
                    best_move = move
                    best_value = value
                    self.last_search_info["move"] = best_move
                    self.last_search_info["score"] = best_value
                    self.last_search_info["completed_depth"] = depth
                depth += 1
        except SearchTimeout:
            self.last_search_info["timed_out"] = True

        if best_move is None and best_value == float("-inf"):
            legal_moves = self._all_empty_cells(self.current_state)
            best_move = legal_moves[0] if legal_moves else None

        self.last_search_info["move"] = best_move
        self.last_search_info["score"] = best_value if best_value != float("-inf") else None
        self.last_search_info["elapsed"] = time.time() - start_time

        return best_move

    def print_board(self, board):
        """Print a simple text version of a board state."""
        symbols = {1: "X", 0: "O"}
        for row in range(1, self.n + 1):
            values = []
            for col in range(1, self.n + 1):
                values.append(symbols.get(board.get((row, col)), "."))
            print(" ".join(values))
