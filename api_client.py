import json
import subprocess


class NoteXponentialAPIError(Exception):
    """Raised when the remote API or local parsing fails."""


class NoteXponentialAPI:
    BASE_URL = "https://www.notexponential.com/aip2pgaming/api/index.php"

    def __init__(self, user_id, api_key, timeout=30):
        self.user_id = int(user_id)
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self, include_content_type=False):
        headers = {
            "Authorization": "Basic Og==",
            "x-api-key": self.api_key,
            "userId": str(self.user_id),
            "Accept": "*/*",
            "Cache-Control": "no-cache",
            "User-Agent": "PostmanRuntime/7.43.0",
        }
        return headers

    def _request(self, method, params):
        curl_command = [
            "curl",
            "-sS",
            "-L",
            self.BASE_URL,
        ]

        for key, value in self._headers().items():
            curl_command.extend(["-H", f"{key}: {value}"])

        if method == "GET":
            curl_command.append("-G")
            for key, value in params.items():
                curl_command.extend(["--data-urlencode", f"{key}={value}"])
        elif method == "POST":
            curl_command.extend(["-X", "POST"])
            for key, value in params.items():
                curl_command.extend(["-F", f"{key}={value}"])
        else:
            raise NoteXponentialAPIError(f"Unsupported method: {method}")

        try:
            result = subprocess.run(
                curl_command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except Exception as exc:
            raise NoteXponentialAPIError(f"Request failed: {exc}") from exc

        if result.returncode != 0:
            raise NoteXponentialAPIError(
                f"curl failed with exit code {result.returncode}: {result.stderr.strip()}"
            )

        raw = result.stdout.strip()

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise NoteXponentialAPIError(f"Non-JSON response: {raw}") from exc

        if payload.get("code") != "OK":
            raise NoteXponentialAPIError(payload.get("message", "Unknown API failure"))

        return payload

    @staticmethod
    def _decode_nested_json(value):
        if isinstance(value, str):
            return json.loads(value)
        return value

    @staticmethod
    def _get_first_present(mapping, *keys, default=None):
        for key in keys:
            if key in mapping:
                return mapping[key]
        return default

    @staticmethod
    def _normalize_int_list(values):
        if isinstance(values, str):
            values = [value.strip() for value in values.split(",") if value.strip()]
        normalized = []
        for value in values:
            if isinstance(value, dict):
                extracted = None
                for key in ("teamId", "teamID", "gameId", "gameID", "id"):
                    if key in value:
                        extracted = value[key]
                        break
                if extracted is None and len(value) == 1:
                    extracted = next(iter(value.keys()))
                if extracted is not None:
                    normalized.append(int(extracted))
            else:
                normalized.append(int(value))
        return normalized

    def create_team(self, name):
        return self._request("POST", {"type": "team", "name": name})

    def add_team_member(self, team_id, user_id):
        try:
            return self._request(
                "POST",
                {"type": "member", "teamId": int(team_id), "userId": int(user_id)},
            )
        except NoteXponentialAPIError as exc:
            team_members = self.get_team_members(team_id)
            if int(user_id) in team_members:
                return {"code": "OK", "message": "User already in team."}
            raise exc

    def get_team_members(self, team_id):
        response = self._request("GET", {"type": "team", "teamId": int(team_id)})
        return self._normalize_int_list(
            self._get_first_present(response, "userIds", "userids", default=[])
        )

    def get_my_teams(self):
        response = self._request("GET", {"type": "myTeams"})
        return self._normalize_int_list(
            self._get_first_present(response, "myTeams", "teams", default=[])
        )

    def create_game(self, team_id_1, team_id_2, board_size=12, target=6):
        if target > board_size:
            raise NoteXponentialAPIError("target must be less than or equal to board_size")
        return self._request(
            "POST",
            {
                "type": "game",
                "teamId1": int(team_id_1),
                "teamId2": int(team_id_2),
                "gameType": "TTT",
                "boardSize": int(board_size),
                "target": int(target),
            },
        )

    def get_my_games(self, open_only=False):
        response = self._request("GET", {"type": "myOpenGames" if open_only else "myGames"})
        key = "myOpenGames" if open_only else "myGames"
        return self._normalize_int_list(
            self._get_first_present(response, key, "games", default=[])
        )


    def make_move(self, game_id, team_id, row, col):
        return self._request(
            "POST",
            {
                "type": "move",
                "gameId": int(game_id),
                "teamId": int(team_id),
                "move": f"{int(row)},{int(col)}",
            },
        )

    def get_moves(self, game_id, count=20):
        try:
            response = self._request(
                "GET",
                {"type": "moves", "gameId": int(game_id), "count": int(count)},
            )
            return response.get("moves", [])
        except NoteXponentialAPIError as exc:
            if "No moves" in str(exc):
                return []
            raise exc

    def get_game_details(self, game_id):
        response = self._request("GET", {"type": "gameDetails", "gameId": int(game_id)})
        return self._decode_nested_json(response["game"])

    def get_board_string(self, game_id):
        response = self._request("GET", {"type": "boardString", "gameId": int(game_id)})
        return response.get("output", "")

    def get_board_map(self, game_id):
        response = self._request("GET", {"type": "boardMap", "gameId": int(game_id)})
        board_map = self._decode_nested_json(response.get("output", {}))
        return board_map if isinstance(board_map, dict) else {}

    def render_board(self, game_id):
        details = self.get_game_details(game_id)
        board_size = int(self._get_first_present(details, "boardSize", "boardsize"))
        board_map = self.get_board_map(game_id)
        rows = []

        for row in range(board_size):
            cells = []
            for col in range(board_size):
                cells.append(board_map.get(f"{row},{col}", "-"))
            rows.append(" ".join(cells))

        return "\n".join(rows)
