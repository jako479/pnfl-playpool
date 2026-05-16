# pnfl-playpool — Architecture

Library that walks a PNFL play-pool directory tree, parses every `.ply` file, and classifies each play into a typed `PlayRecord` subclass enriched with PNFL-specific metadata.

For system-level context (how this fits with `fbpro98-play` and `pnfl-playcatalog`), see [pnfl-docs/Design/play-architecture.md](../pnfl-docs/Design/play-architecture.md).

## Module layout

```
src/pnfl_playpool/
├── __init__.py    # public API re-exports
└── pool.py        # PlayPool, PlayRecord (Offensive | Defensive | SpecialTeams), read_play_pool
```

## What this package does

- Provides `read_play_pool(root)` → `PlayPool`
- Walks the PNFL convention directory layout (`Offense/CATEGORY/...`, `Defense/CATEGORY/...`, `Special/...`) under the pool root
- Parses every `.ply` via `fbpro98_play.read_play()`
- Classifies each play into one of three subclasses:
  - `OffensivePlayRecord` — adds `pool_category`, `pass_type`, `is_screen`, `is_rollout`, `is_qb_draw`
  - `DefensivePlayRecord` — adds `pool_category`, `defensive_personnel`
  - `SpecialTeamsPlayRecord` — wraps the underlying play file with the resolved name
- Indexes plays by name for O(1) lookup (`pool.get(name)`, `pool[name]`)
- Exposes filtered views: `offensive_plays`, `defensive_plays`, `special_teams_plays`

## What this package assumes

- The pool root follows the PNFL directory convention: top-level `Offense/`, `Defense/`, `Special/` folders, with inner per-category subfolders for offense and defense
- `.ply` files inside those folders are well-formed FbPro '98 play files
- A play's directory determines its side and pool category; the file's own `play_category` / `special_category` integers are *not* re-derived from the path

## What this package enforces

- Unknown / malformed `.ply` files raise `InvalidPlayFileError` from the underlying library
- Empty pool roots produce an empty `PlayPool` (callers can detect via `len(pool)`)
- Duplicate names across the pool: last-loaded wins; a warning is logged

## What this package does NOT do

- Parse `.ply` bytes (delegates to `fbpro98-play`)
- Read or write `.pln` game plans (lives in `fbpro98-gameplan` / `fbpro98-gameplanwriter`)
- Produce a workbook export (lives in `pnfl-playcatalog`)
- Modify any file — `read_play_pool` is purely a reader

## Classification rules

Side and pool category come from the directory layout:

- `Offense/<CATEGORY>/...` where category ∈ `RUN_CATEGORIES ∪ PASS_CATEGORIES`
- `Defense/<CATEGORY>/...` where category ∈ `DEFENSE_CATEGORIES`
- `Special/...` — any depth, all `.ply` files become `SpecialTeamsPlayRecord`

Offensive metadata is derived from the filename:

- `pass_type` — `TIMED` if the suffix matches `TIMED_SUFFIXES` (and is not in `TIMED_EXCLUSIONS`), else `CHECK_RECEIVERS`
- `is_screen` — substring `screen`
- `is_rollout` — suffix in `ROLLOUT_SUFFIXES` (with exclusions)
- `is_qb_draw` — substring `QBdraw` / `QBDraw`

Defensive metadata:

- `defensive_personnel` — derived from intermediate path segments (`3-4`, `4-3`, `R&SDefs`)

## Testing

- `tests/test_play_pool.py` — classification on a real fixture pool in `tests/data/`, asserted against pinned outputs in `tests/expected/`
