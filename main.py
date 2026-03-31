import argparse
import os
import sys

from api_client import NoteXponentialAPI, NoteXponentialAPIError
from game_runner import TicTacToeMatchRunner
import local_config


def build_parser():
    parser = argparse.ArgumentParser(
        description="CLI for the AI Project 3 generalized Tic-Tac-Toe API."
    )
    parser.add_argument(
        "--user-id",
        type=int,
        default=int(os.getenv("AIP2P_USER_ID", "0")) or local_config.USER_ID,
        help="Your NoteXponential user ID. Defaults to AIP2P_USER_ID.",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("AIP2P_API_KEY") or local_config.API_KEY,
        help="Your NoteXponential API key. Defaults to AIP2P_API_KEY.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    create_team = subparsers.add_parser("create-team", help="Create a new team.")
    create_team.add_argument("name", help="Team name to create.")

    add_member = subparsers.add_parser("add-member", help="Add a user to a team.")
    add_member.add_argument("team_id", type=int, help="Target team ID.")
    add_member.add_argument("member_user_id", type=int, help="User ID to add.")

    subparsers.add_parser("my-teams", help="List your team IDs.")

    team_members = subparsers.add_parser(
        "team-members", help="List member user IDs for a team."
    )
    team_members.add_argument("team_id", type=int, help="Team ID to inspect.")

    create_game = subparsers.add_parser("create-game", help="Create a new game.")
    create_game.add_argument("team_id", type=int, help="Your team ID.")
    create_game.add_argument("opponent_team_id", type=int, help="Opponent team ID.")
    create_game.add_argument(
        "--board-size",
        type=int,
        default=12,
        help="Board size n for an n x n board.",
    )
    create_game.add_argument(
        "--target",
        type=int,
        default=6,
        help="Target m for m-in-a-row.",
    )

    subparsers.add_parser("my-games", help="List your game IDs.")
    subparsers.add_parser("my-open-games", help="List your open game IDs.")

    game_details = subparsers.add_parser(
        "game-details", help="Show parsed game details."
    )
    game_details.add_argument("game_id", type=int, help="Game ID to inspect.")

    board = subparsers.add_parser("board", help="Show the current board.")
    board.add_argument("game_id", type=int, help="Game ID to inspect.")

    moves = subparsers.add_parser("moves", help="Show recent moves.")
    moves.add_argument("game_id", type=int, help="Game ID to inspect.")
    moves.add_argument(
        "--count",
        type=int,
        default=20,
        help="How many recent moves to fetch.",
    )

    move = subparsers.add_parser("move", help="Submit one move manually.")
    move.add_argument("game_id", type=int, help="Game ID to play in.")
    move.add_argument("team_id", type=int, help="Your team ID.")
    move.add_argument("row", type=int, help="0-indexed move row.")
    move.add_argument("col", type=int, help="0-indexed move column.")

    bot = subparsers.add_parser(
        "play",
        help="Run the bot for one game, polling until the game ends.",
    )
    bot.add_argument("game_id", type=int, help="Game ID to play.")
    bot.add_argument("team_id", type=int, help="Your team ID in that game.")
    bot.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="Seconds to wait between server polls.",
    )
    bot.add_argument(
        "--search-time",
        type=float,
        default=local_config.DEFAULT_SEARCH_TIME,
        help="Time limit in seconds for one agent move.",
    )
    bot.add_argument(
        "--once",
        action="store_true",
        help="Only make at most one move, then exit.",
    )

    return parser


def require_credentials(args):
    if args.user_id is None or not args.api_key:
        raise NoteXponentialAPIError(
            "Missing credentials. Provide --user-id and --api-key, or set "
            "AIP2P_USER_ID and AIP2P_API_KEY."
        )


def create_client(args):
    require_credentials(args)
    return NoteXponentialAPI(user_id=args.user_id, api_key=args.api_key)


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        client = create_client(args)

        if args.command == "create-team":
            response = client.create_team(args.name)
            print(f"Created team {response['teamId']}")

        elif args.command == "add-member":
            client.add_team_member(args.team_id, args.member_user_id)
            print("Team member added.")

        elif args.command == "my-teams":
            print(client.get_my_teams())

        elif args.command == "team-members":
            print(client.get_team_members(args.team_id))

        elif args.command == "create-game":
            response = client.create_game(
                team_id_1=args.team_id,
                team_id_2=args.opponent_team_id,
                board_size=args.board_size,
                target=args.target,
            )
            print(f"Created game {response['gameId']}")

        elif args.command == "my-games":
            print(client.get_my_games())

        elif args.command == "my-open-games":
            print(client.get_my_games(open_only=True))

        elif args.command == "game-details":
            print(client.get_game_details(args.game_id))

        elif args.command == "board":
            print(client.render_board(args.game_id))

        elif args.command == "moves":
            print(client.get_moves(args.game_id, count=args.count))

        elif args.command == "move":
            response = client.make_move(args.game_id, args.team_id, args.row, args.col)
            print(f"Move submitted with moveId {response['moveId']}")

        elif args.command == "play":
            runner = TicTacToeMatchRunner(
                client=client,
                game_id=args.game_id,
                team_id=args.team_id,
                poll_interval=args.poll_interval,
                search_time=args.search_time,
            )
            runner.play_game(make_one_move=args.once)

    except NoteXponentialAPIError as exc:
        print(f"API error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
