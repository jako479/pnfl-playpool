# pnfl-playpool — Test Status

**Test Status: Tests Complete**

## Covered by automated tests

- Whole-pool classification against a pinned JSON snapshot of a real fixture play tree
- Offensive, defensive, and special-teams records resolve to the correct typed subclass
- Expected offensive and defensive category sets are exposed
- Play counts and offensive type counts (run, pass, QB draw, screen, rollout, pass type)
- Defensive personnel grouping counts (3-4, 4-3, R&S, none)
- Per-category counts total back to overall play counts
- Representative offensive and defensive fixture plays classify with the expected category and attributes
- Special-teams record shape and `special_category`
- Case-insensitive `find_by_name` lookup, including a missing-name miss
- Invalid `.ply` fixture is skipped with a logged warning

## Needs tests

- Nothing outstanding for the current scope.
