# pnfl-playpool
`pnfl-playpool` scans a PNFL play tree and classifies approved plays.
It uses `fbpro98-play` for basic `.ply` metadata, then applies the current
PNFL-specific folder/name heuristics to produce:
- typed play records: `OffensivePlayRecord`, `DefensivePlayRecord`, `SpecialTeamsPlayRecord`
- offensive attributes: screen, rollout, QB draw, pass type
- defensive attributes: personnel grouping (3-4, 4-3, R&S)
- offensive and defensive category counts
- O(1) play lookup by name
## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ..\fbpro98-play
pip install -e ".[dev]"
```
## Usage
```python
from pnfl_playpool import PlayPool, OffensivePlayRecord

pool = PlayPool.from_directory(r"E:\SIERRA\FbPro98\PNFL")
print(len(pool.offensive_plays))
print(len(pool.defensive_plays))

play = pool.find_by_name("AF3ArshZ")
if isinstance(play, OffensivePlayRecord):
    print(play.pool_category, play.screen, play.qb_draw)
```
## Testing
```bash
pytest
```
