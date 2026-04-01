# pnfl-playpool
`pnfl-playpool` scans a PNFL play tree and classifies approved plays.
It uses `fbpro98-play` for basic `.ply` metadata, then applies the current
PNFL-specific folder/name heuristics to produce:
- offensive, defensive, and special-teams play lists
- offensive and defensive category counts
- play types such as `Screen`, `QB draw`, `R&S`, `3-4`, and `4-3`
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

pool = PlayPool.from_directory(r"E:\SIERRA\FbPro98\PNFL")
print(len(pool.offensive_plays))
print(len(pool.defensive_plays))
print(len(pool.special_teams_plays))
```
Each play is a `PlayRecord` containing a `PlayFile` (composition) plus PNFL
classification fields (`pool_category`, `play_type`).
## Testing
```bash
pytest
```
Current tests cover:
- a snapshot of the checked-in PNFL play subset
- all offensive and defensive pool categories in the checked-in corpus
- all current derived play types: `Screen`, `QB draw`, `R&S`, `3-4`, and `4-3`
- category-count totals against the classified play lists
- invalid `.ply` skip/warning behavior
