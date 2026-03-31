# Generalized Tic-Tac-Toe Agent

Generalized Tic-Tac-Toe competition. The team plays through the NoteXponential API and uses a local search agent to choose moves.
The current code is organized in a way that the API integration stays separate from the game logic:

- `agent.py`: search, move generation, evaluation, and board utilities
- `api_client.py`: working NoteXponential API client using `curl`
- `game_runner.py`: converts API board state into the agent format and submits moves
- `student_runner.py`: main workflow for setup, game creation, and playing
- `main.py`: lower-level CLI that is still usable, but not the main entry point
- `local_config.py`: local defaults for credentials, team IDs, and repeated settings
- `local_diagnostics.py`: local tactical tests and self-play checks

## Important Notes

- Internal board coordinates in `agent.py` are `1`-indexed.
- API move coordinates are `0`-indexed.
- The conversion is already handled in `game_runner.py`; do not change it casually.
- The API path is intentionally implemented with `curl`, not `requests`.
- GET calls use query parameters.
- POST calls use multipart form fields.
- This is deliberate because that path already works in real games.

## Environment

The project was tested with the Conda base environment for better compatibility.

Before running commands:

```bash
conda activate
```

## Local Configuration

Edit `local_config.py` for local defaults:

- `USER_ID`
- `API_KEY`
- `TEAM_ID`
- `TEAMMATE_USER_ID`
- `SECOND_TEAM_ID`
- `DEFAULT_BOARD_SIZE`
- `DEFAULT_TARGET`
- `DEFAULT_POLL_INTERVAL`
- `DEFAULT_SEARCH_TIME`

These are defaults only. Most important game parameters can also be overridden from the command line.

## Main Workflow

Use `student_runner.py` for regular work.

### 1. Create your team

```bash
python student_runner.py setup-team "My Team Name" --teammate-user-id 1234
```

This creates the team and stores the returned `TEAM_ID` in `local_config.py`.

### 2. Check current status

```bash
python student_runner.py status
```

This prints:

- your teams
- your games
- your open games

### 3. Add a team member later

```bash
python student_runner.py add-member 1234
```

### 4. Create a game against another team

```bash
python student_runner.py create-game 1499
```

Override board settings when needed:

```bash
python student_runner.py create-game 1499 --board-size 8 --target 5
python student_runner.py create-game 1499 --board-size 10 --target 5 --team-id 1498
```

### 5. Play a live game

```bash
python student_runner.py play 12345
```

Useful options:

```bash
python student_runner.py play 12345 --once
python student_runner.py play 12345 --poll-interval 1.0
python student_runner.py play 12345 --search-time 12
python student_runner.py play 12345 --team-id 1498 --search-time 8
```

### 6. Inspect a live board or recent moves

```bash
python student_runner.py board 12345
python student_runner.py moves 12345 --count 30
```

## Self-Play Setup

You can create a second team for local API testing:

```bash
python student_runner.py create-second-team "My Second Team"
```

Then create a game between your two saved team IDs:

```bash
python student_runner.py create-self-game
python student_runner.py create-self-game --board-size 8 --target 5
```

## Lower-Level CLI

`main.py` provides a more direct CLI. It is still useful if you want full control over credentials from the command line:

```bash
python main.py --user-id 3750 --api-key YOUR_KEY my-teams
python main.py --user-id 3750 --api-key YOUR_KEY create-game 1498 1499 --board-size 8 --target 5
python main.py --user-id 3750 --api-key YOUR_KEY play 12345 1498 --search-time 10
```

## Local Diagnostics

Use `local_diagnostics.py` to test the agent without the live API.

### Tactical checks

This runs a small set of forced-win and forced-block positions:

```bash
python local_diagnostics.py tactical
python local_diagnostics.py tactical --search-time 0.2
python local_diagnostics.py tactical --search-time 0.2 --show-board
```

This is useful after changing:

- move generation
- heuristic weights
- alpha-beta behavior
- time limit settings

### Self-play checks

This runs local agent-vs-agent games:

```bash
python local_diagnostics.py self-play
python local_diagnostics.py self-play --games 10 --board-size 8 --target 5 --search-time 0.2
python local_diagnostics.py self-play --games 20 --board-size 6 --target 4 --search-time 0.1 --max-moves 100
```

Self-play is helpful for:

- catching invalid move bugs
- checking whether the agent gets stuck in draws
- comparing search-time settings
- rough sanity checks after tuning

Do not treat self-play as the only measure of strength. Real games against other teams matter more.

## What the Agent Currently Does

The search agent in `agent.py` uses:

- alpha-beta minimax
- iterative deepening
- a time limit per move
- candidate move filtering near existing stones
- move ordering to search promising moves first
- a heuristic based on windows of length `m`

The evaluation favors:

- immediate wins
- blocking immediate losses
- longer open-ended runs
- preventing the opponent from building open threats
- central influence when the board is still sparse

The search also stores simple diagnostics in `last_search_info`, such as:

- searched nodes
- number of evaluations
- alpha-beta cutoffs
- deepest completed search depth
- elapsed time
- candidate move count

## Common Checks

Syntax check:

```bash
python -m py_compile agent.py api_client.py game_runner.py student_runner.py main.py local_diagnostics.py
```

Show play command help:

```bash
python student_runner.py play --help
python main.py play --help
```

Quick tactical sanity check:

```bash
python local_diagnostics.py tactical --search-time 0.2
```

## Safe Editing Guidelines

If you continue improving the project, keep these constraints in mind:

- Do not casually replace the `curl` API client with `requests` or `urllib`.
- Do not change the board indexing convention without checking both the agent and runner.
- Keep `agent.py` returning legal `1`-indexed moves.
- If changing the heuristic, rerun tactical checks first.
- If changing search depth, move ordering, or time management, rerun both tactical checks and self-play.

## Suggested Demo Commands

These are good commands to keep ready:

```bash
python student_runner.py status
python student_runner.py create-game 1499 --board-size 8 --target 5
python student_runner.py play 12345 --search-time 10
python local_diagnostics.py tactical --search-time 0.2
python local_diagnostics.py self-play --games 10 --board-size 8 --target 5 --search-time 0.2
```

## Current Recommendation

For normal competition use:

- use `student_runner.py`
- keep the API code unchanged unless a real bug appears
- test agent changes locally before trying them in live games
- use command-line overrides instead of editing code whenever possible
