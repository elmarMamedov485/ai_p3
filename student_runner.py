import argparse
from pathlib import Path

from api_client import NoteXponentialAPI, NoteXponentialAPIError
from game_runner import TicTacToeMatchRunner
import local_config


def build_client():
    return NoteXponentialAPI(
        user_id=local_config.USER_ID,
        api_key=local_config.API_KEY,
    )


def require_team_id():
    if local_config.TEAM_ID is None:
        raise NoteXponentialAPIError(
            "TEAM_ID is not set in local_config.py. Run setup-team once, then save the returned team ID."
        )
    return int(local_config.TEAM_ID)


def resolve_team_id(team_id_override=None):
    return int(team_id_override) if team_id_override is not None else require_team_id()


def persist_config_value(name, value):
    config_path = Path(__file__).with_name("local_config.py")
    lines = config_path.read_text().splitlines()
    updated = []

    for line in lines:
        if line.startswith(f"{name} = "):
            updated.append(f"{name} = {value}")
        else:
            updated.append(line)

    config_path.write_text("\n".join(updated) + "\n")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Convenience runner for the AI Project 3 API workflow."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup = subparsers.add_parser(
        "setup-team",
        help="One-time operation: create your team and add both members.",
    )
    setup.add_argument("team_name", help="New team name to create.")
    setup.add_argument(
        "--teammate-user-id",
        type=int,
        default=local_config.TEAMMATE_USER_ID,
        help="Your teammate's user ID.",
    )
    setup.add_argument(
        "--skip-self",
        action="store_true",
        help="Skip adding your own user ID to the team.",
    )

    subparsers.add_parser(
        "status",
        help="Show current teams and games for this account.",
    )

    add_member = subparsers.add_parser(
        "add-member",
        help="One-time operation: add a user to your existing team.",
    )
    add_member.add_argument("member_user_id", type=int, help="User ID to add.")

    create_game = subparsers.add_parser(
        "create-game",
        help="Repeated operation: create a game against another team.",
    )
    create_game.add_argument("opponent_team_id", type=int, help="Opponent team ID.")
    create_game.add_argument(
        "--team-id",
        type=int,
        default=None,
        help="Override the local TEAM_ID for this command.",
    )
    create_game.add_argument(
        "--board-size",
        type=int,
        default=local_config.DEFAULT_BOARD_SIZE,
        help="Board size.",
    )
    create_game.add_argument(
        "--target",
        type=int,
        default=local_config.DEFAULT_TARGET,
        help="Target length to win.",
    )

    play = subparsers.add_parser(
        "play",
        help="Repeated operation: run the bot in a game until it ends.",
    )
    play.add_argument("game_id", type=int, help="Game ID.")
    play.add_argument(
        "--team-id",
        type=int,
        default=None,
        help="Override the local TEAM_ID for this command.",
    )
    play.add_argument(
        "--poll-interval",
        type=float,
        default=local_config.DEFAULT_POLL_INTERVAL,
        help="Polling delay in seconds.",
    )
    play.add_argument(
        "--search-time",
        type=float,
        default=local_config.DEFAULT_SEARCH_TIME,
        help="Time limit in seconds for one agent move.",
    )
    play.add_argument(
        "--once",
        action="store_true",
        help="Make one move if it is your turn, then exit.",
    )

    board = subparsers.add_parser(
        "board",
        help="Repeated operation: print the current board for a game.",
    )
    board.add_argument("game_id", type=int, help="Game ID.")

    create_second_team = subparsers.add_parser(
        "create-second-team",
        help="Create another team for self-play testing and add your user to it.",
    )
    create_second_team.add_argument("team_name", help="Name for the second test team.")

    self_game = subparsers.add_parser(
        "create-self-game",
        help="Create a game between TEAM_ID and SECOND_TEAM_ID.",
    )
    self_game.add_argument(
        "--board-size",
        type=int,
        default=local_config.DEFAULT_BOARD_SIZE,
        help="Board size.",
    )
    self_game.add_argument(
        "--target",
        type=int,
        default=local_config.DEFAULT_TARGET,
        help="Target length to win.",
    )

    moves = subparsers.add_parser(
        "moves",
        help="Repeated operation: print recent moves for a game.",
    )
    moves.add_argument("game_id", type=int, help="Game ID.")
    moves.add_argument("--count", type=int, default=20, help="Recent move count.")

    return parser


def setup_team(client, team_name, teammate_user_id, skip_self):
    response = client.create_team(team_name)
    team_id = int(response["teamId"])
    persist_config_value("TEAM_ID", team_id)
    print(f"Created team {team_id}.")

    if not skip_self:
        client.add_team_member(team_id, local_config.USER_ID)
        print(f"Added your user ID {local_config.USER_ID}.")

    if teammate_user_id is not None:
        client.add_team_member(team_id, int(teammate_user_id))
        print(f"Added teammate user ID {int(teammate_user_id)}.")
    else:
        print("Teammate user ID not provided. Add them later with main.py add-member.")

    print("Saved TEAM_ID in local_config.py.")


def show_status(client):
    teams = client.get_my_teams()
    games = client.get_my_games()
    open_games = client.get_my_games(open_only=True)
    print(f"My teams: {teams}")
    print(f"My games: {games}")
    print(f"My open games: {open_games}")


def create_game(client, opponent_team_id, board_size, target, team_id_override=None):
    team_id = resolve_team_id(team_id_override)
    response = client.create_game(team_id, int(opponent_team_id), board_size, target)
    print(f"Created game {response['gameId']}.")


def play_game(
    client,
    game_id,
    poll_interval,
    make_one_move,
    team_id_override=None,
    search_time=None,
):
    team_id = resolve_team_id(team_id_override)
    runner = TicTacToeMatchRunner(
        client=client,
        game_id=int(game_id),
        team_id=team_id,
        poll_interval=poll_interval,
        search_time=search_time if search_time is not None else local_config.DEFAULT_SEARCH_TIME,
    )
    runner.play_game(make_one_move=make_one_move)


def create_second_team(client, team_name):
    response = client.create_team(team_name)
    team_id = int(response["teamId"])
    client.add_team_member(team_id, local_config.USER_ID)
    persist_config_value("SECOND_TEAM_ID", team_id)
    print(f"Created second team {team_id} and added user {local_config.USER_ID}.")
    print("Saved SECOND_TEAM_ID in local_config.py.")


def create_self_game(client, board_size, target):
    first_team_id = require_team_id()
    if local_config.SECOND_TEAM_ID is None:
        raise NoteXponentialAPIError(
            "SECOND_TEAM_ID is not set in local_config.py. Create a second team first."
        )
    response = client.create_game(
        first_team_id,
        int(local_config.SECOND_TEAM_ID),
        board_size,
        target,
    )
    print(
        f"Created self-play game {response['gameId']} between "
        f"{first_team_id} and {int(local_config.SECOND_TEAM_ID)}."
    )


def main():
    parser = build_parser()
    args = parser.parse_args()
    client = build_client()

    try:
        if args.command == "setup-team":
            setup_team(
                client,
                args.team_name,
                args.teammate_user_id,
                args.skip_self,
            )
        elif args.command == "status":
            show_status(client)
        elif args.command == "add-member":
            team_id = require_team_id()
            client.add_team_member(team_id, args.member_user_id)
            print(f"Added user {args.member_user_id} to team {team_id}.")
        elif args.command == "create-second-team":
            create_second_team(client, args.team_name)
        elif args.command == "create-self-game":
            create_self_game(client, args.board_size, args.target)
        elif args.command == "create-game":
            create_game(
                client,
                args.opponent_team_id,
                args.board_size,
                args.target,
                args.team_id,
            )
        elif args.command == "play":
            play_game(
                client,
                args.game_id,
                args.poll_interval,
                args.once,
                args.team_id,
                args.search_time,
            )
        elif args.command == "board":
            print(client.render_board(args.game_id))
        elif args.command == "moves":
            print(client.get_moves(args.game_id, count=args.count))
    except NoteXponentialAPIError as exc:
        print(f"API error: {exc}")


if __name__ == "__main__":
    main()
