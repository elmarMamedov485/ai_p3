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
        self.early_branching = 34
        self.mid_branching = 26
        self.quiescence_extensions = 1
        self.threat_search_depth = 3
        self.threat_search_width = 14
        self.version = "offensive-threat-space-v5-safe-forcing"
        self.last_search_info = {}
        self.transposition_table = {}
        self.threat_table = {}

    def opponent(self, side):
        """Return the other player's integer label."""
        return 1 - side

    def in_bounds(self, row, col):
        """Check whether a position is inside the board."""
        return 1 <= row <= self.n and 1 <= col <= self.n

    def board_full(self, state):
        """Return True when no empty cells remain."""
        return len(state) >= self.n * self.n

    def _state_key(self, state):
        """Build a hashable key for a sparse board state."""
        return tuple(sorted(state.items()))

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

    def _window_threat_info(self, state, cells):
        """
        Extract simple threat features from one length-m window.

        Returns:
            tuple[str | None, int, int]: (owner, stone_count, open_ends)
            owner is "self", "opp", or None.
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
            return None, 0, 0
        if mine == 0 and opp == 0:
            return None, 0, 0

        open_ends = self._open_ends(state, cells)
        if mine:
            return "self", mine, open_ends
        return "opp", opp, open_ends

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

        phase = len(state) / (self.n * self.n)
        multiplier = max(0.25, 1 - 3 * phase)
        return int(score * multiplier)

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
        my_open_wins = 0
        opp_open_wins = 0
        my_open_builds = 0
        opp_open_builds = 0

        for row in range(1, self.n + 1):
            for col in range(1, self.n + 1):
                for dr, dc in self.directions:
                    cells = self._segment_cells(row, col, dr, dc)
                    if cells is None:
                        continue
                    score += self._window_score(state, cells)
                    owner, count, open_ends = self._window_threat_info(state, cells)
                    if owner == "self":
                        if count == self.m - 1 and open_ends == 2:
                            my_open_wins += 1
                        elif count == self.m - 2 and open_ends == 2:
                            my_open_builds += 1
                    elif owner == "opp":
                        if count == self.m - 1 and open_ends == 2:
                            opp_open_wins += 1
                        elif count == self.m - 2 and open_ends == 2:
                            opp_open_builds += 1

        if my_open_wins >= 2:
            score += 350000
        elif my_open_wins == 1:
            score += 60000

        if opp_open_wins >= 2:
            score -= 420000
        elif opp_open_wins == 1:
            score -= 80000

        if my_open_builds >= 2:
            score += 25000
        if opp_open_builds >= 2:
            score -= 32000

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

    def _branch_limit(self, state):
        """
        Use a wider beam early and a tighter one later.

        On large boards the opening and early midgame need more freedom. Later
        positions are usually tactical enough that a smaller ordered list works
        better.
        """
        occupied = len(state)
        if self.n >= 10:
            if occupied <= self.n:
                return self.early_branching
            if occupied <= 2 * self.n:
                return self.mid_branching
            if occupied <= 3 * self.n:
                return max(self.max_branching, 22)
        elif occupied <= self.n:
            return max(self.max_branching, 24)

        return self.max_branching

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

    def _windows_through_move(self, move, dr, dc):
        """Return all length-m windows in one direction that contain move."""
        row, col = move
        windows = []

        for offset in range(self.m):
            start_row = row - offset * dr
            start_col = col - offset * dc
            cells = self._segment_cells(start_row, start_col, dr, dc)
            if cells is not None and move in cells:
                windows.append(cells)

        return windows

    def _threat_cells_after_move(self, state, move, side):
        """
        Find next-turn winning cells created by a hypothetical move.

        A returned cell means that after playing move, side would be able to
        win on the next turn by playing that cell.
        """
        if move in state:
            return set()

        temp = state.copy()
        temp[move] = side
        if self.winner(temp) == side:
            return {move}

        threats = set()
        opponent = self.opponent(side)

        for dr, dc in self.directions:
            for cells in self._windows_through_move(move, dr, dc):
                side_count = 0
                blocked = False
                empties = []

                for cell in cells:
                    value = temp.get(cell)
                    if value == side:
                        side_count += 1
                    elif value == opponent:
                        blocked = True
                        break
                    else:
                        empties.append(cell)

                if not blocked and side_count == self.m - 1 and len(empties) == 1:
                    threats.add(empties[0])

        return threats

    def _build_threat_count_after_move(self, state, move, side):
        """
        Count strong non-immediate threats created by a hypothetical move.

        This looks for open windows with m-2 stones. They are not winning next
        turn yet, but several of them together are useful pressure.
        """
        if move in state:
            return 0

        temp = state.copy()
        temp[move] = side
        opponent = self.opponent(side)
        count = 0

        for dr, dc in self.directions:
            for cells in self._windows_through_move(move, dr, dc):
                side_count = 0
                blocked = False
                empties = []

                for cell in cells:
                    value = temp.get(cell)
                    if value == side:
                        side_count += 1
                    elif value == opponent:
                        blocked = True
                        break
                    else:
                        empties.append(cell)

                if blocked or side_count != self.m - 2 or len(empties) != 2:
                    continue

                if self._open_ends(temp, cells) > 0:
                    count += 1

        return count

    def _winning_moves(self, state, side):
        """Return all moves that would immediately win for side."""
        wins = set()
        for move in self._candidate_cells(state):
            temp = state.copy()
            temp[move] = side
            if self.winner(temp) == side:
                wins.add(move)
        return wins

    def _has_immediate_tension(self, state):
        """Check whether either player has a one-move win available."""
        return bool(
            self._winning_moves(state, self.side)
            or self._winning_moves(state, self.opponent(self.side))
        )

    def _has_fork_tension(self, state):
        """Check whether any candidate move creates a strong fork threat."""
        for move in self.actions(state):
            if len(self._threat_cells_after_move(state, move, self.side)) >= 2:
                return True
            if len(self._threat_cells_after_move(state, move, self.opponent(self.side))) >= 2:
                return True
            if self._build_threat_count_after_move(state, move, self.side) >= 2:
                return True
            if self._build_threat_count_after_move(state, move, self.opponent(self.side)) >= 2:
                return True
        return False

    def _fork_score_after_move(self, state, move, side):
        """
        Score a true fork move.

        Here "fork" means the move creates at least two immediate winning
        cells for the next turn. A single threat is useful, but it is usually
        blockable, so it should not trigger this shortcut.
        """
        threats = self._threat_cells_after_move(state, move, side)
        builds = self._build_threat_count_after_move(state, move, side)

        if len(threats) >= 2:
            return 2000000 + 200000 * len(threats) + 50000 * builds
        return 0

    def _best_fork_move(self, state, side):
        """
        Return a true double-threat move if one exists.

        This is an aggressive shortcut used after immediate wins and blocks.
        It only accepts moves that create multiple next-turn winning cells.
        """
        best_move = None
        best_score = 0

        for move in self.actions(state, side):
            score = self._fork_score_after_move(state, move, side)
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def _is_forcing_candidate(self, state, move, side):
        """
        Check whether a move is tactical enough for threat-space search.

        Threat search should not scan ordinary positional moves. It is meant
        for moves that create a direct threat, build several strong threats, or
        block a direct opponent win while keeping the attack alive.
        """
        opponent = self.opponent(side)
        threats = self._threat_cells_after_move(state, move, side)
        builds = self._build_threat_count_after_move(state, move, side)

        if threats or builds >= 2:
            return True

        if move in self._winning_moves(state, opponent):
            return True

        for dr, dc in self.directions:
            length, open_ends = self._line_potential(state, move, side, dr, dc)
            if length >= self.m - 2 and open_ends > 0:
                return True

        return False

    def _threat_move_score(self, state, move, side):
        """
        Score forcing moves for threat-space search.

        This is intentionally attack-heavy. It is only used inside the
        dedicated threat search, not as the normal static evaluation.
        """
        opponent = self.opponent(side)
        threats = self._threat_cells_after_move(state, move, side)
        builds = self._build_threat_count_after_move(state, move, side)
        blocks = self._threat_cells_after_move(state, move, opponent)
        score = 0

        if threats:
            score += 400000 * len(threats)
        if len(threats) >= 2:
            score += 1600000
        if builds:
            score += 120000 * builds
        if len(blocks) >= 2:
            score += 500000

        for dr, dc in self.directions:
            length, open_ends = self._line_potential(state, move, side, dr, dc)
            score += 300 * (length ** 3) + 200 * open_ends

        return score

    def _forcing_candidates(self, state, side):
        """
        Candidate moves for threat-space search.

        We only keep moves that create immediate threats, create several build
        threats, or are otherwise among the strongest attacking moves.
        """
        candidates = []
        for move in self.actions(state, side):
            if not self._is_forcing_candidate(state, move, side):
                continue
            score = self._threat_move_score(state, move, side)
            if score > 0:
                candidates.append((score, move))

        candidates.sort(reverse=True)
        return [move for _, move in candidates[: self.threat_search_width]]

    def _attack_move_forces_win(self, state, move, side, depth):
        """
        Test one attacking move in threat-space search.

        After the attack move, it is the defender's turn. The move is accepted
        only if it wins immediately, creates an unblockable double threat, or
        creates a single threat whose forced block still leaves a forced win.
        """
        if move in state:
            return False

        opponent = self.opponent(side)
        next_state = state.copy()
        next_state[move] = side

        if self.winner(next_state) == side:
            return True

        # If the defender can win immediately, this is not a forcing attack.
        if self._winning_moves(next_state, opponent):
            return False

        threats = self._winning_moves(next_state, side)
        if len(threats) >= 2:
            return True
        if len(threats) != 1 or depth <= 0:
            return False

        block = next(iter(threats))
        response = next_state.copy()
        response[block] = opponent

        return self._can_force_win(response, side, depth - 1)

    def _can_force_win(self, state, side, depth):
        """
        Bounded threat-space search.

        This function is called when it is the attacker's turn. A line is only
        accepted when every forced defensive reply still leaves the attacker a
        forced continuation. Single blockable threats are not counted as wins.
        """
        self._check_time()
        if "threat_nodes" in self.last_search_info:
            self.last_search_info["threat_nodes"] += 1

        winner = self.winner(state)
        if winner == side:
            return True
        if winner == self.opponent(side) or self.board_full(state):
            return False

        key = (self._state_key(state), side, depth)
        cached = self.threat_table.get(key)
        if cached is not None:
            if "threat_cache_hits" in self.last_search_info:
                self.last_search_info["threat_cache_hits"] += 1
            return cached

        if self._winning_moves(state, side):
            self.threat_table[key] = True
            return True

        if depth <= 0:
            self.threat_table[key] = False
            return False

        opponent = self.opponent(side)
        opponent_wins = self._winning_moves(state, opponent)
        moves = self._forcing_candidates(state, side)

        if len(opponent_wins) > 1:
            self.threat_table[key] = False
            return False
        if len(opponent_wins) == 1:
            # The attacker must block first; otherwise the line is not sound.
            forced_block = next(iter(opponent_wins))
            moves = [forced_block] if forced_block not in state else []

        for move in moves:
            if self._attack_move_forces_win(state, move, side, depth):
                self.threat_table[key] = True
                return True

        self.threat_table[key] = False
        return False

    def _forcing_attack_move(self, state, side, depth=None):
        """Return an attacking move that starts a bounded forced-win line."""
        if depth is None:
            depth = self.threat_search_depth

        for move in self._forcing_candidates(state, side):
            if self._attack_move_forces_win(state, move, side, depth):
                return move

        return None

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

        own_threats = self._threat_cells_after_move(state, move, side)
        opp_threats = self._threat_cells_after_move(state, move, opponent)
        own_builds = self._build_threat_count_after_move(state, move, side)
        opp_builds = self._build_threat_count_after_move(state, move, opponent)

        if len(own_threats) >= 2:
            score += 1500000
        elif len(own_threats) == 1:
            score += 160000

        if len(opp_threats) >= 2:
            score += 1200000
        elif len(opp_threats) == 1:
            score += 130000

        if own_builds >= 2:
            score += 90000
        if opp_builds >= 2:
            score += 70000

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
        branch_limit = self._branch_limit(state)
        if len(ordered) > branch_limit:
            return ordered[:branch_limit]
        return ordered

    def _immediate_move(self, state, side):
        """Return a direct winning move for the given side, if one exists."""
        wins = self._winning_moves(state, side)
        if not wins:
            return None
        return max(wins, key=lambda move: self._move_priority(state, move, side))

    def is_win(self, state):
        """Check whether this agent has an immediate winning move."""
        return self._immediate_move(state, self.side)

    def is_break(self, state):
        """Check whether the opponent has an immediate winning move to block."""
        return self._immediate_move(state, self.opponent(self.side))

    def _alpha_beta(self, state, depth, alpha, beta, turn_side, extension_left=0):
        """
        Recursive alpha-beta search.

        Args:
            state (dict): Current board state.
            depth (int): Remaining depth for this iteration.
            alpha (float): Best guaranteed lower bound for MAX.
            beta (float): Best guaranteed upper bound for MIN.
            turn_side (int): Side to move at this node.
            extension_left (int): Extra tactical plies still allowed.

        Returns:
            tuple: (score, best_move)
        """
        self._check_time()
        self.last_search_info["nodes"] += 1
        table_key = (self._state_key(state), turn_side, depth, extension_left)
        cached = self.transposition_table.get(table_key)
        if cached is not None:
            self.last_search_info["tt_hits"] += 1
            return cached

        winner = self.winner(state)
        if winner is not None or self.board_full(state):
            self.last_search_info["evals"] += 1
            result = (self.eval(state), None)
            self.transposition_table[table_key] = result
            return result

        if depth == 0:
            if extension_left > 0 and (
                self._has_immediate_tension(state) or self._has_fork_tension(state)
            ):
                depth = 1
                extension_left -= 1
                self.last_search_info["extensions"] += 1
            else:
                self.last_search_info["evals"] += 1
                result = (self.eval(state), None)
                self.transposition_table[table_key] = result
                return result

        moves = self.actions(state, turn_side)
        if not moves:
            result = (self.eval(state), None)
            self.transposition_table[table_key] = result
            return result

        best_move = moves[0]
        pruned = False

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
                    extension_left,
                )
                if child_value > value:
                    value = child_value
                    best_move = move
                alpha = max(alpha, value)
                if alpha >= beta:
                    self.last_search_info["cutoffs"] += 1
                    pruned = True
                    break
            result = (value, best_move)
            if not pruned:
                self.transposition_table[table_key] = result
            return result

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
                extension_left,
            )
            if child_value < value:
                value = child_value
                best_move = move
            beta = min(beta, value)
            if alpha >= beta:
                self.last_search_info["cutoffs"] += 1
                pruned = True
                break
        result = (value, best_move)
        if not pruned:
            self.transposition_table[table_key] = result
        return result

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
            "tt_hits": 0,
            "threat_nodes": 0,
            "threat_cache_hits": 0,
            "threat_timed_out": False,
            "extensions": 0,
            "completed_depth": 0,
            "elapsed": 0.0,
            "move": None,
            "score": None,
            "timed_out": False,
            "candidate_count": 0,
            "shortcut": None,
            "version": self.version,
        }
        self.transposition_table = {}
        self.threat_table = {}
        full_deadline = time.time() + self.time_limit
        self.deadline = full_deadline

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
            self.last_search_info["shortcut"] = "win"
            return win_pos

        break_pos = self.is_break(self.current_state)
        if break_pos is not None:
            self.last_search_info["move"] = break_pos
            self.last_search_info["score"] = self.eval(self.current_state)
            self.last_search_info["elapsed"] = time.time() - start_time
            self.last_search_info["shortcut"] = "block"
            return break_pos

        fork_pos = self._best_fork_move(self.current_state, self.side)
        if fork_pos is not None:
            self.last_search_info["move"] = fork_pos
            self.last_search_info["score"] = self.eval(self.current_state)
            self.last_search_info["elapsed"] = time.time() - start_time
            self.last_search_info["shortcut"] = "attack_fork"
            return fork_pos

        threat_budget = min(3.0, max(0.25, self.time_limit * 0.25))
        self.deadline = min(full_deadline, time.time() + threat_budget)
        try:
            forcing_pos = self._forcing_attack_move(self.current_state, self.side)
        except SearchTimeout:
            forcing_pos = None
            self.last_search_info["threat_timed_out"] = True
        finally:
            self.deadline = full_deadline

        if forcing_pos is not None:
            self.last_search_info["move"] = forcing_pos
            self.last_search_info["score"] = self.eval(self.current_state)
            self.last_search_info["elapsed"] = time.time() - start_time
            self.last_search_info["shortcut"] = "threat_space_attack"
            return forcing_pos

        opponent_fork_pos = self._best_fork_move(
            self.current_state,
            self.opponent(self.side),
        )
        if opponent_fork_pos is not None and opponent_fork_pos not in self.current_state:
            self.last_search_info["move"] = opponent_fork_pos
            self.last_search_info["score"] = self.eval(self.current_state)
            self.last_search_info["elapsed"] = time.time() - start_time
            self.last_search_info["shortcut"] = "block_fork"
            return opponent_fork_pos

        self.deadline = min(full_deadline, time.time() + threat_budget)
        try:
            opponent_forcing_pos = self._forcing_attack_move(
                self.current_state,
                self.opponent(self.side),
                depth=max(1, self.threat_search_depth - 1),
            )
        except SearchTimeout:
            opponent_forcing_pos = None
            self.last_search_info["threat_timed_out"] = True
        finally:
            self.deadline = full_deadline

        if (
            opponent_forcing_pos is not None
            and opponent_forcing_pos not in self.current_state
        ):
            self.last_search_info["move"] = opponent_forcing_pos
            self.last_search_info["score"] = self.eval(self.current_state)
            self.last_search_info["elapsed"] = time.time() - start_time
            self.last_search_info["shortcut"] = "block_threat_space"
            return opponent_forcing_pos

        best_move = moves[0]
        best_value = float("-inf")
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
                    self.quiescence_extensions,
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
