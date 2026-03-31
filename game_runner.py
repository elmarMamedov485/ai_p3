import time

from agent import agent
from api_client import NoteXponentialAPIError


class TicTacToeMatchRunner:
    def __init__(self, client, game_id, team_id, poll_interval=2.0, search_time=15.0):
        self.client = client
        self.game_id = int(game_id)
        self.team_id = int(team_id)
        self.poll_interval = poll_interval
        self.search_time = float(search_time)

    @staticmethod
    def _api_symbol_to_agent_value(symbol):
        if symbol == "X":
            return 1
        if symbol == "O":
            return 0
        raise NoteXponentialAPIError(f"Unexpected symbol in board data: {symbol}")

    @staticmethod
    def _agent_value_to_api_symbol(value):
        return "X" if value == 1 else "O"

    @staticmethod
    def _api_to_agent_position(row, col):
        return row + 1, col + 1

    @staticmethod
    def _agent_to_api_position(row, col):
        return row - 1, col - 1

    @staticmethod
    def _detail(details, *keys, default=None):
        for key in keys:
            if key in details:
                return details[key]
        return default

    def _infer_my_symbol(self, details, moves):
        for move in moves:
            if int(move["teamId"]) == self.team_id:
                return move["symbol"]

        if not moves:
            turn_team_id = int(self._detail(details, "turnTeamId", "turnteamid"))
            return "X" if turn_team_id == self.team_id else "O"

        only_seen_symbol = moves[0]["symbol"]
        return "O" if only_seen_symbol == "X" else "X"

    def _build_agent(self, details, board_map, moves):
        my_symbol = self._infer_my_symbol(details, moves)
        board_size = int(self._detail(details, "boardSize", "boardsize"))
        target = int(self._detail(details, "target"))
        side = self._api_symbol_to_agent_value(my_symbol)
        bot = agent(board_size, target, side, time_limit=self.search_time)

        converted_state = {}
        for raw_position, symbol in board_map.items():
            row, col = map(int, raw_position.split(","))
            converted_state[self._api_to_agent_position(row, col)] = (
                self._api_symbol_to_agent_value(symbol)
            )

        bot.current_state = converted_state
        return bot, my_symbol

    @staticmethod
    def _default_opening_move(board_size):
        center = (board_size + 1) // 2
        return center, center

    @staticmethod
    def _is_valid_agent_move(move, board_size, occupied_positions):
        if not isinstance(move, tuple) or len(move) != 2:
            return False
        row, col = move
        if not isinstance(row, int) or not isinstance(col, int):
            return False
        if row < 1 or row > board_size or col < 1 or col > board_size:
            return False
        if move in occupied_positions:
            return False
        return True

    @staticmethod
    def _fallback_move(board_size, occupied_positions):
        center = (board_size + 1) // 2
        candidates = []

        for distance in range(board_size):
            for row in range(max(1, center - distance), min(board_size, center + distance) + 1):
                for col in range(max(1, center - distance), min(board_size, center + distance) + 1):
                    candidates.append((row, col))

            for move in candidates:
                if move not in occupied_positions:
                    return move

        for row in range(1, board_size + 1):
            for col in range(1, board_size + 1):
                if (row, col) not in occupied_positions:
                    return row, col

        return None

    def _game_is_over(self, details):
        winner = self._detail(details, "winnerTeamId", "winnerteamid")
        status = self._detail(details, "status")
        return winner not in (None, "null", "") or str(status) == "1"

    def _print_game_summary(self, details):
        winner = self._detail(details, "winnerTeamId", "winnerteamid")
        if winner not in (None, "null", ""):
            if int(winner) == self.team_id:
                print(f"Game {self.game_id} finished. Your team won.")
            else:
                print(f"Game {self.game_id} finished. Team {winner} won.")
        else:
            print(f"Game {self.game_id} is no longer open.")

    def _print_local_terminal_summary(self, bot):
        winner = bot.winner(bot.current_state)
        if winner is None and bot.board_full(bot.current_state):
            print(f"Game {self.game_id} appears to be a draw.")
        elif winner == bot.side:
            print(f"Game {self.game_id} appears to be won by your team.")
        elif winner is not None:
            print(f"Game {self.game_id} appears to be won by the opponent.")
        else:
            print(f"Game {self.game_id} has no legal moves remaining.")

    def play_game(self, make_one_move=False):
        printed_waiting = False

        while True:
            details = self.client.get_game_details(self.game_id)

            if self._game_is_over(details):
                self._print_game_summary(details)
                return

            board_map = self.client.get_board_map(self.game_id)
            move_count = int(self._detail(details, "moves", default=0))
            moves = self.client.get_moves(self.game_id, count=move_count) if move_count > 0 else []
            turn_team_id = int(self._detail(details, "turnTeamId", "turnteamid"))

            if turn_team_id != self.team_id:
                if not printed_waiting:
                    print(
                        f"Waiting for opponent. Current turn belongs to team {turn_team_id}."
                    )
                    printed_waiting = True
                time.sleep(self.poll_interval)
                continue

            printed_waiting = False
            bot, my_symbol = self._build_agent(details, board_map, moves)

            if bot.terminal_state(bot.current_state):
                self._print_local_terminal_summary(bot)
                return

            if not bot.current_state:
                chosen_move = self._default_opening_move(bot.n)
            else:
                chosen_move = bot.alpha_beta()

            if not self._is_valid_agent_move(chosen_move, bot.n, bot.current_state):
                chosen_move = self._fallback_move(bot.n, bot.current_state)

            if chosen_move is None:
                self._print_local_terminal_summary(bot)
                return

            api_row, api_col = self._agent_to_api_position(*chosen_move)
            response = self.client.make_move(
                self.game_id,
                self.team_id,
                api_row,
                api_col,
            )

            print(
                f"Played {my_symbol} at ({api_row}, {api_col}) in game {self.game_id}. "
                f"moveId={response['moveId']}"
            )
            print(self.client.render_board(self.game_id))

            if make_one_move:
                return

            time.sleep(self.poll_interval)
