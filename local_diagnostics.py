import argparse

from agent import agent


TACTICAL_CASES = [
    {
        "name": "empty-board-center",
        "n": 5,
        "m": 4,
        "side": 1,
        "state": {},
        "expected": {(3, 3)},
    },
    {
        "name": "finish-horizontal-win",
        "n": 5,
        "m": 4,
        "side": 1,
        "state": {(2, 1): 1, (2, 2): 1, (2, 3): 1},
        "expected": {(2, 4)},
    },
    {
        "name": "block-horizontal-loss",
        "n": 5,
        "m": 4,
        "side": 1,
        "state": {(3, 1): 0, (3, 2): 0, (3, 3): 0},
        "expected": {(3, 4)},
    },
    {
        "name": "block-diagonal-loss",
        "n": 5,
        "m": 4,
        "side": 1,
        "state": {(1, 1): 0, (2, 2): 0, (3, 3): 0},
        "expected": {(4, 4)},
    },
    {
        "name": "finish-vertical-win",
        "n": 6,
        "m": 4,
        "side": 0,
        "state": {(2, 5): 0, (3, 5): 0, (4, 5): 0, (2, 2): 1},
        "expected": {(5, 5), (1, 5)},
    },
    {
        "name": "block-open-three",
        "n": 6,
        "m": 4,
        "side": 1,
        "state": {(4, 2): 0, (4, 3): 0, (4, 4): 0, (3, 3): 1},
        "expected": {(4, 1), (4, 5)},
    },
]


def build_parser():
    parser = argparse.ArgumentParser(
        description="Local checks for the generalized Tic-Tac-Toe agent."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    tactical = subparsers.add_parser(
        "tactical",
        help="Run a small suite of tactical positions.",
    )
    tactical.add_argument(
        "--search-time",
        type=float,
        default=1.0,
        help="Seconds allowed per move.",
    )
    tactical.add_argument(
        "--show-board",
        action="store_true",
        help="Print each tactical position.",
    )

    selfplay = subparsers.add_parser(
        "self-play",
        help="Run local self-play games between two copies of the agent.",
    )
    selfplay.add_argument("--games", type=int, default=2, help="Number of games.")
    selfplay.add_argument("--board-size", type=int, default=8, help="Board size.")
    selfplay.add_argument("--target", type=int, default=5, help="Target to win.")
    selfplay.add_argument(
        "--search-time",
        type=float,
        default=0.5,
        help="Seconds allowed per move.",
    )
    selfplay.add_argument(
        "--max-moves",
        type=int,
        default=200,
        help="Stop a local game if it gets too long.",
    )

    return parser


def print_board(n, state):
    symbols = {1: "X", 0: "O"}
    for row in range(1, n + 1):
        values = []
        for col in range(1, n + 1):
            values.append(symbols.get(state.get((row, col)), "."))
        print(" ".join(values))


def run_tactical(search_time, show_board):
    passed = 0

    for case in TACTICAL_CASES:
        bot = agent(case["n"], case["m"], case["side"], time_limit=search_time)
        bot.current_state = case["state"].copy()
        move = bot.alpha_beta()
        ok = move in case["expected"]

        print(f"{case['name']}: move={move} expected={sorted(case['expected'])} pass={ok}")
        print(f"  stats={bot.last_search_info}")
        if show_board:
            print_board(case["n"], case["state"])
            print()

        if ok:
            passed += 1

    print(f"Passed {passed}/{len(TACTICAL_CASES)} tactical checks.")


def choose_opening(board_size, game_index):
    center = (board_size + 1) // 2
    openings = [
        (center, center),
        (center, min(board_size, center + 1)),
        (min(board_size, center + 1), center),
        (max(1, center - 1), center),
    ]
    return openings[game_index % len(openings)]


def run_one_self_play(game_index, board_size, target, search_time, max_moves):
    state = {}
    opening = choose_opening(board_size, game_index)
    state[opening] = 1
    side = 0
    move_count = 1
    history = [("X", opening)]

    while move_count < max_moves:
        bot = agent(board_size, target, side, time_limit=search_time)
        bot.current_state = state.copy()
        move = bot.alpha_beta()

        if move is None or move in state or not bot.in_bounds(*move):
            return {
                "winner": 1 - side,
                "moves": move_count,
                "reason": f"invalid move by {'X' if side == 1 else 'O'}",
                "history": history,
            }

        state[move] = side
        history.append(("X" if side == 1 else "O", move))
        move_count += 1

        winner = bot.winner(state)
        if winner is not None:
            return {
                "winner": winner,
                "moves": move_count,
                "reason": "win",
                "history": history,
            }

        if bot.board_full(state):
            return {
                "winner": None,
                "moves": move_count,
                "reason": "draw",
                "history": history,
            }

        side = 1 - side

    return {
        "winner": None,
        "moves": move_count,
        "reason": "move limit",
        "history": history,
    }


def run_self_play(games, board_size, target, search_time, max_moves):
    x_wins = 0
    o_wins = 0
    draws = 0

    for game_index in range(games):
        result = run_one_self_play(
            game_index,
            board_size,
            target,
            search_time,
            max_moves,
        )

        winner = result["winner"]
        if winner == 1:
            x_wins += 1
            winner_label = "X"
        elif winner == 0:
            o_wins += 1
            winner_label = "O"
        else:
            draws += 1
            winner_label = "draw"

        print(
            f"game {game_index + 1}: winner={winner_label} moves={result['moves']} "
            f"reason={result['reason']} opening={result['history'][0][1]}"
        )

    print(f"summary: X={x_wins} O={o_wins} draw={draws}")


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "tactical":
        run_tactical(args.search_time, args.show_board)
    elif args.command == "self-play":
        run_self_play(
            args.games,
            args.board_size,
            args.target,
            args.search_time,
            args.max_moves,
        )


if __name__ == "__main__":
    main()
