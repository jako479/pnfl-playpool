# pnfl-playpool

`pnfl-playpool` scans a PNFL play tree and classifies approved plays.

It uses `fbpro98-play` for basic `.ply` metadata, then applies the current
PNFL-specific folder/name heuristics to produce:

- offensive, defensive, and special-teams play lists
- offensive and defensive category counts
- temporary play types such as `Screen`, `QB draw`, `R&S`, `3-4`, and `4-3`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ..\fbpro98-play
pip install -e ".[dev]"
```

## Usage

```python
from pnfl_playpool import PlayPool

play_pool = PlayPool(r"E:\SIERRA\FbPro98\PNFL")
print(len(play_pool.offensive_plays))
print(len(play_pool.defensive_plays))
print(len(play_pool.special_teams_plays))
```

## Testing

```bash
pytest
```

Current tests cover:

- a snapshot of the checked-in PNFL play subset
- heuristic classification behavior
- invalid `.ply` skip/warning behavior
