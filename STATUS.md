# pnfl-playpool — Status

**Status: Complete**

Library that scans a PNFL play tree and classifies approved `.ply` plays into typed, metadata-enriched play records.

## Implemented

- Recursive scan of a PNFL play-pool root (`read_play_pool`), parsing every `.ply` via `fbpro98-play`
- Typed play records: `OffensivePlayRecord`, `DefensivePlayRecord`, `SpecialTeamsPlayRecord`
- Offensive classification from folder/name heuristics: pool category, screen, rollout, QB draw, pass type
- Defensive classification: pool category and personnel grouping (3-4, 4-3, R&S)
- Offensive and defensive per-category user-category counts
- O(1) case-insensitive play lookup by name and filtered offense/defense/special views
- JSON-friendly serialization via `to_dict`
- Invalid `.ply` files logged and skipped rather than aborting the scan

## Remaining

- Validate that each play resides in the correct pool directory and warn when a play is misplaced
