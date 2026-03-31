import json
import shlex
import subprocess


BASE_URL = "https://www.notexponential.com/aip2pgaming/api/index.php"
USER_ID = "3750"
API_KEY = "bcbd5d942aa9ce0c92d5"
TEAM_NAME = "team2a-bahruz-elmar"
TEAM_ID = "1498"
SECOND_TEAM_ID = "1499"
MEMBER_USER_ID = "3750"


def base_headers():
    return [
        "Authorization: Basic Og==",
        f"x-api-key: {API_KEY}",
        f"userId: {USER_ID}",
        "Accept: */*",
        "Cache-Control: no-cache",
        "User-Agent: PostmanRuntime/7.43.0",
    ]


def run_curl(args, title):
    print("=" * 80)
    print(title)
    print("COMMAND:")
    print(" ".join(shlex.quote(part) for part in args))

    result = subprocess.run(args, capture_output=True, text=True)
    print(f"EXIT CODE: {result.returncode}")
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)


def test_my_teams():
    cmd = [
        "curl",
        "-sS",
        "-i",
        "-L",
        "-G",
        BASE_URL,
        "-H",
        base_headers()[0],
        "-H",
        base_headers()[1],
        "-H",
        base_headers()[2],
        "-H",
        base_headers()[3],
        "-H",
        base_headers()[4],
        "-H",
        base_headers()[5],
        "--data-urlencode",
        "type=myTeams",
    ]
    run_curl(cmd, "GET myTeams")


def test_create_team_form():
    cmd = [
        "curl",
        "-sS",
        "-i",
        "-L",
        "-X",
        "POST",
        BASE_URL,
        "-H",
        base_headers()[0],
        "-H",
        base_headers()[1],
        "-H",
        base_headers()[2],
        "-H",
        base_headers()[3],
        "-H",
        base_headers()[4],
        "-H",
        base_headers()[5],
        "-F",
        "type=team",
        "-F",
        f"name={TEAM_NAME}",
    ]
    run_curl(cmd, "POST create team with multipart form")


def test_create_team_urlencoded():
    cmd = [
        "curl",
        "-sS",
        "-i",
        "-L",
        "-X",
        "POST",
        BASE_URL,
        "-H",
        base_headers()[0],
        "-H",
        base_headers()[1],
        "-H",
        base_headers()[2],
        "-H",
        base_headers()[3],
        "-H",
        base_headers()[4],
        "-H",
        base_headers()[5],
        "--data-urlencode",
        "type=team",
        "--data-urlencode",
        f"name={TEAM_NAME}",
    ]
    run_curl(cmd, "POST create team with urlencoded form")


def test_add_member():
    cmd = [
        "curl",
        "-sS",
        "-i",
        "-L",
        "-X",
        "POST",
        BASE_URL,
        "-H",
        base_headers()[0],
        "-H",
        base_headers()[1],
        "-H",
        base_headers()[2],
        "-H",
        base_headers()[3],
        "-H",
        base_headers()[4],
        "-H",
        base_headers()[5],
        "-F",
        "type=member",
        "-F",
        f"teamId={TEAM_ID}",
        "-F",
        f"userId={MEMBER_USER_ID}",
    ]
    run_curl(cmd, "POST add member")


def test_team_members():
    cmd = [
        "curl",
        "-sS",
        "-i",
        "-L",
        "-G",
        BASE_URL,
        "-H",
        base_headers()[0],
        "-H",
        base_headers()[1],
        "-H",
        base_headers()[2],
        "-H",
        base_headers()[3],
        "-H",
        base_headers()[4],
        "-H",
        base_headers()[5],
        "--data-urlencode",
        "type=team",
        "--data-urlencode",
        f"teamId={TEAM_ID}",
    ]
    run_curl(cmd, "GET team members")


def test_create_self_game():
    cmd = [
        "curl",
        "-sS",
        "-i",
        "-L",
        "-X",
        "POST",
        BASE_URL,
        "-H",
        base_headers()[0],
        "-H",
        base_headers()[1],
        "-H",
        base_headers()[2],
        "-H",
        base_headers()[3],
        "-H",
        base_headers()[4],
        "-H",
        base_headers()[5],
        "-F",
        f"teamId1={TEAM_ID}",
        "-F",
        f"teamId2={SECOND_TEAM_ID}",
        "-F",
        "type=game",
        "-F",
        "gameType=TTT",
        "-F",
        "boardSize=12",
        "-F",
        "target=6",
    ]
    run_curl(cmd, "POST create self-play game")


if __name__ == "__main__":
    test_my_teams()
    test_add_member()
    test_team_members()
    test_create_self_game()
