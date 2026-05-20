"""PNFL play pool: classifies FbPro98 .ply files into offensive/defensive/special records.

Walks a PNFL play-pool root directory, parses each .ply via fbpro98_play, and
classifies plays by directory layout (Offense/Defense/Special and inner
category folders) into typed PlayRecord subclasses with metadata like
pool_category, screen/rollout/QB-draw flags, and personnel grouping.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from os import PathLike
from pathlib import Path

from fbpro98_play import InvalidPlayFileError, PlayFile, read_play

StrPath = str | PathLike[str]

logger = logging.getLogger(__name__)

RUN_CATEGORIES = {"GLR", "RL", "RM", "RR"}
PASS_CATEGORIES = {"GLP", "PLR", "PML", "PMM", "PMR", "PRD", "PSL", "PSM", "PSR"}
DEFENSE_CATEGORIES = {
    "GLpass",
    "GLrun",
    "PassDazzle",
    "PassLong",
    "PassMedium",
    "PassShort",
    "RunDazzle",
    "RunLeft",
    "RunMiddle",
    "RunRight",
}

TIMED_SUFFIXES = {"T", "T1", "T2", "TR", "RT", "Ty", "T01", "T01R", "T02", "Top"}
TIMED_EXCLUSIONS = {"OUT", "SLT1", "FLT1", "OUT1"}
TIMED_LOB_PATTERN = re.compile(r"lob.$", re.I)

ROLLOUT_SUFFIXES = {"R", "RT", "TR", "wagL", "rolL"}
ROLLOUT_EXCLUSIONS = {"CR", "WR", "scrR", "trpR", "nRT", "NRT"}


class PassType(Enum):
    """How a pass play handles its receivers — timed routes vs. progression reads."""

    TIMED = "Timed"
    CHECK_RECEIVERS = "Check Receivers"


class DefensivePersonnel(Enum):
    """Defensive front grouping — 3-4, 4-3, or Run-and-Shoot package."""

    THREE_FOUR = "3-4"
    FOUR_THREE = "4-3"
    RUN_AND_SHOOT = "R&S"


@dataclass(frozen=True)
class PlayRecord:
    """Base record for any play in the pool.

    Pairs a display name with the parsed .ply file behind it, and exposes
    convenience passthrough properties for the most-used PlayFile fields.
    Subclasses add classification-specific fields (pool_category, personnel
    grouping, pass-type flags, etc.).
    """

    name: str
    """Display name of the play (the .ply file's stem, e.g. `MYPLAY`)."""

    play_file: PlayFile
    """Parsed .ply file backing this record. The source of truth for
    file_path, play_category, special_category, and user_category."""

    @property
    def file_path(self) -> Path:
        """Convenience passthrough to `play_file.file_path`."""
        return self.play_file.file_path

    @property
    def play_category(self) -> int:
        """Convenience passthrough to `play_file.play_category`."""
        return self.play_file.play_category

    @property
    def special_category(self) -> int:
        """Convenience passthrough to `play_file.special_category`."""
        return self.play_file.special_category

    @property
    def user_category(self) -> int:
        """Convenience passthrough to `play_file.user_category`."""
        return self.play_file.user_category

    def _base_dict(self, *, relative_to: Path | None = None) -> dict[str, object]:
        file_path = self.file_path
        if relative_to is not None:
            file_path = file_path.relative_to(relative_to)

        return {
            "name": self.name,
            "file_path": file_path.as_posix(),
            "play_category": self.play_category,
            "special_category": self.special_category,
            "user_category": self.user_category,
        }

    def to_dict(self, *, relative_to: Path | None = None) -> dict[str, object]:
        """Serialize this record to a JSON-friendly dict.

        Args:
            relative_to: If given, `file_path` is emitted relative to this base
                directory (POSIX-style). If None, `file_path` is absolute.

        Returns:
            Dict with keys: `name`, `file_path`, `play_category`,
            `special_category`, `user_category`. Subclasses may add fields.
        """
        return self._base_dict(relative_to=relative_to)


@dataclass(frozen=True)
class OffensivePlayRecord(PlayRecord):
    """An offensive play with derived classification from its pool directory.

    `pool_category` comes from the directory structure (e.g. RR, PSL, GLP),
    not the .ply file's bytes. Screen / rollout / QB-draw flags and `pass_type`
    are derived from play-name suffix conventions.
    """

    pool_category: str
    """Pool directory short code (e.g. RR, PSL, GLP, PSR). Member of
    RUN_CATEGORIES or PASS_CATEGORIES."""

    screen: bool = False
    """True if this play lives under a Screens subdirectory."""

    rollout: bool = False
    """True if this pass play's name matches the rollout suffix convention."""

    qb_draw: bool = False
    """True if this run play is a QB draw (detected by name digits)."""

    pass_type: PassType | None = None
    """For pass plays only: TIMED if the name matches the timed-route
    convention, else None (treated as CHECK_RECEIVERS by consumers)."""

    @property
    def is_run(self) -> bool:
        """True if `pool_category` is a run category (member of RUN_CATEGORIES)."""
        return self.pool_category in RUN_CATEGORIES

    @property
    def is_pass(self) -> bool:
        """True if `pool_category` is a pass category (member of PASS_CATEGORIES)."""
        return self.pool_category in PASS_CATEGORIES

    def to_dict(self, *, relative_to: Path | None = None) -> dict[str, object]:
        """Serialize to a JSON-friendly dict.

        Returns:
            The base PlayRecord keys plus `pool_category`, `screen`, `rollout`,
            `qb_draw`, and `pass_type` (the PassType's string value, or None).
        """
        result = self._base_dict(relative_to=relative_to)
        result["pool_category"] = self.pool_category
        result["screen"] = self.screen
        result["rollout"] = self.rollout
        result["qb_draw"] = self.qb_draw
        result["pass_type"] = self.pass_type.value if self.pass_type else None
        return result


@dataclass(frozen=True)
class DefensivePlayRecord(PlayRecord):
    """A defensive play with derived classification from its pool directory.

    `pool_category` and `personnel_grouping` come from the directory structure,
    not the .ply file's bytes. Personnel is inferred from parent directory
    prefix (34/43) or grandparent directory name (R&SDefs).
    """

    pool_category: str
    """Pool directory category (e.g. RunLeft, PassShort, GLrun). Member of
    DEFENSE_CATEGORIES."""

    personnel_grouping: DefensivePersonnel | None = None
    """Defensive front grouping derived from directory layout, or None when
    the directory layout doesn't specify one."""

    def to_dict(self, *, relative_to: Path | None = None) -> dict[str, object]:
        """Serialize to a JSON-friendly dict.

        Returns:
            The base PlayRecord keys plus `pool_category` and
            `personnel_grouping` (the DefensivePersonnel's string value, or None).
        """
        result = self._base_dict(relative_to=relative_to)
        result["pool_category"] = self.pool_category
        result["personnel_grouping"] = self.personnel_grouping.value if self.personnel_grouping else None
        return result


@dataclass(frozen=True)
class SpecialTeamsPlayRecord(PlayRecord):
    """A special-teams play.

    Categorization comes from the .ply file's `special_category` byte, not
    from a pool directory; this record adds no extra fields beyond the base.
    """

    def to_dict(self, *, relative_to: Path | None = None) -> dict[str, object]:
        """Serialize to a JSON-friendly dict. Same keys as the base PlayRecord."""
        return self._base_dict(relative_to=relative_to)


def _is_timed(play_name: str) -> bool:
    for excl in TIMED_EXCLUSIONS:
        if play_name.endswith(excl):
            return False
    if TIMED_LOB_PATTERN.search(play_name):
        return True
    return any(play_name.endswith(sfx) for sfx in TIMED_SUFFIXES)


def _is_rollout(play_name: str) -> bool:
    for excl in ROLLOUT_EXCLUSIONS:
        if play_name.endswith(excl):
            return False
    return any(play_name.endswith(sfx) for sfx in ROLLOUT_SUFFIXES)


class PlayPool:
    """The PNFL play pool — all plays under a root directory, indexed by name and category.

    Construct an empty pool with `PlayPool(root_dir)`, or use the top-level
    `read_play_pool(root_dir)` function to build and populate one in one call.

    Attributes:
        root_dir: The root directory the pool was built from.
        offensive_plays: All classified offensive plays, in discovery order.
        defensive_plays: All classified defensive plays, in discovery order.
        special_teams_plays: All classified special-teams plays, in discovery order.
        offensive_categories: Per-pool-category counts of `user_category` byte
            values, shaped as `{pool_category: {user_category: count}}`.
        defensive_categories: Same shape as `offensive_categories`, for defense.
    """

    def __init__(self, root_dir: StrPath) -> None:
        """Create an empty PlayPool rooted at `root_dir`.

        Args:
            root_dir: The directory the pool will be (or has been) built from.
                Stored as `self.root_dir` (a Path); not scanned by this
                constructor. Use `read_play_pool` to populate.
        """
        self.root_dir = Path(root_dir)
        self.offensive_categories: dict[str, dict[int, int]] = {}
        self.defensive_categories: dict[str, dict[int, int]] = {}
        self.offensive_plays: list[OffensivePlayRecord] = []
        self.defensive_plays: list[DefensivePlayRecord] = []
        self.special_teams_plays: list[SpecialTeamsPlayRecord] = []
        self._plays_by_name: dict[str, PlayRecord] = {}

    def find_by_name(self, name: str) -> PlayRecord | None:
        """Look up a play by name, case-insensitive.

        Args:
            name: Play name (matched against each record's `name` field,
                compared in uppercase).

        Returns:
            The matching PlayRecord, or None if no play with that name was
            found in this pool.
        """
        return self._plays_by_name.get(name.upper())

    def _register_play(self, play: PlayRecord) -> None:
        self._plays_by_name[play.name.upper()] = play

    def _process_play_file(self, file_path: Path) -> None:
        try:
            play_file = read_play(file_path)
        except InvalidPlayFileError as exc:
            logger.warning("Skipping invalid play file: %s", exc)
            return

        play_name = file_path.stem
        parent_dir = file_path.parent.name
        grandparent_dir = file_path.parent.parent.name
        file_path_text = str(file_path)

        # TODO: Validate play belongs in correct pool directory; log warning when misplaced.
        if "Offense" in file_path_text:
            self._process_offensive_play(
                play_name,
                parent_dir,
                grandparent_dir,
                play_file,
            )
        elif "Defense" in file_path_text:
            self._process_defensive_play(
                play_name,
                parent_dir,
                grandparent_dir,
                play_file,
            )
        elif "Special" in file_path_text:
            self._process_special_teams_play(play_name, play_file)

    def _process_offensive_play(
        self,
        play_name: str,
        parent_dir: str,
        grandparent_dir: str,
        play_file: PlayFile,
    ) -> None:
        if play_file.category_name is None:
            logger.warning("Unrecognized category for offensive play '%s', skipping", play_name)
            return

        screen = parent_dir == "Screens"
        pool_category = grandparent_dir if screen else parent_dir
        is_pass = pool_category in PASS_CATEGORIES
        qb_draw = pool_category in RUN_CATEGORIES and (play_name[1] == "1" or play_name[2] == "1")
        rollout = is_pass and _is_rollout(play_name)
        pass_type = PassType.TIMED if is_pass and _is_timed(play_name) else None

        play = OffensivePlayRecord(
            name=play_name,
            play_file=play_file,
            pool_category=pool_category,
            screen=screen,
            qb_draw=qb_draw,
            rollout=rollout,
            pass_type=pass_type,
        )
        self.offensive_plays.append(play)
        self._register_play(play)
        self._increment_user_category_count(
            self.offensive_categories,
            pool_category,
            play_file.user_category,
        )

    def _process_defensive_play(
        self,
        play_name: str,
        parent_dir: str,
        grandparent_dir: str,
        play_file: PlayFile,
    ) -> None:
        if play_file.category_name is None:
            logger.warning("Unrecognized category for defensive play '%s', skipping", play_name)
            return

        personnel_grouping: DefensivePersonnel | None = None
        if grandparent_dir == "R&SDefs":
            pool_category = parent_dir
            personnel_grouping = DefensivePersonnel.RUN_AND_SHOOT
        elif parent_dir.startswith("34"):
            pool_category = parent_dir[2:]
            personnel_grouping = DefensivePersonnel.THREE_FOUR
        elif parent_dir.startswith("43"):
            pool_category = parent_dir[2:]
            personnel_grouping = DefensivePersonnel.FOUR_THREE
        else:
            pool_category = parent_dir

        play = DefensivePlayRecord(
            name=play_name,
            play_file=play_file,
            pool_category=pool_category,
            personnel_grouping=personnel_grouping,
        )
        self.defensive_plays.append(play)
        self._register_play(play)
        self._increment_user_category_count(
            self.defensive_categories,
            pool_category,
            play_file.user_category,
        )

    def _process_special_teams_play(
        self,
        play_name: str,
        play_file: PlayFile,
    ) -> None:
        play = SpecialTeamsPlayRecord(
            name=play_name,
            play_file=play_file,
        )
        self.special_teams_plays.append(play)
        self._register_play(play)

    @staticmethod
    def _increment_user_category_count(
        categories: dict[str, dict[int, int]],
        pool_category: str,
        user_category: int,
    ) -> None:
        category_counts = categories.setdefault(pool_category, {})
        category_counts[user_category] = category_counts.get(user_category, 0) + 1

    def to_dict(self, *, relative_to: StrPath | None = None) -> dict[str, object]:
        """Serialize the pool to a JSON-friendly dict.

        Plays are sorted (by pool_category then name for offense/defense,
        by name only for special teams). When `relative_to` is given, file
        paths are emitted relative to it (POSIX-style); otherwise absolute.

        Args:
            relative_to: If given, every play's `file_path` is emitted relative
                to this base directory. If None, paths are absolute.

        Returns:
            Dict with keys `offensive_plays`, `defensive_plays`,
            `special_teams_plays` (lists of per-play dicts), plus
            `offensive_categories` and `defensive_categories` (lists of
            `{pool_category, user_category, count}` rows).
        """
        base_path = Path(relative_to) if relative_to is not None else None
        return {
            "offensive_plays": [
                p.to_dict(relative_to=base_path)
                for p in sorted(self.offensive_plays, key=lambda p: (p.pool_category, p.name))
            ],
            "defensive_plays": [
                p.to_dict(relative_to=base_path)
                for p in sorted(self.defensive_plays, key=lambda p: (p.pool_category, p.name))
            ],
            "special_teams_plays": [
                p.to_dict(relative_to=base_path) for p in sorted(self.special_teams_plays, key=lambda p: p.name)
            ],
            "offensive_categories": self._serialize_categories(self.offensive_categories),
            "defensive_categories": self._serialize_categories(self.defensive_categories),
        }

    @staticmethod
    def _serialize_categories(
        categories: dict[str, dict[int, int]],
    ) -> list[dict[str, int | str]]:
        rows: list[dict[str, int | str]] = []
        for pool_category in sorted(categories):
            for user_category in sorted(categories[pool_category]):
                rows.append(
                    {
                        "pool_category": pool_category,
                        "user_category": user_category,
                        "count": categories[pool_category][user_category],
                    }
                )
        return rows


def read_play_pool(root_dir: StrPath) -> PlayPool:
    """Build a PlayPool by recursively scanning `root_dir` for .ply files.

    Files are classified by their path: any "Offense" segment routes to
    offensive processing, "Defense" to defensive, "Special" to special teams.
    Invalid .ply files (`InvalidPlayFileError` from fbpro98_play) are logged
    at WARNING and skipped, not raised.

    Args:
        root_dir: Root directory of the PNFL play pool to scan.

    Returns:
        A populated PlayPool containing every valid .ply file found under
        `root_dir`, classified into offensive_plays, defensive_plays, or
        special_teams_plays.
    """
    pool = PlayPool(root_dir)
    logger.info("Processing .ply files in '%s'", pool.root_dir)
    for file_path in pool.root_dir.glob("**/*.ply"):
        pool._process_play_file(file_path)
    return pool
