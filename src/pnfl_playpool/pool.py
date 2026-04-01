from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from fbpro98_play import InvalidPlayFileError, PlayFile


logger = logging.getLogger(__name__)

RUN_CATEGORIES = {"GLR", "RL", "RM", "RR"}
PASS_CATEGORIES = {"GLP", "PLR", "PML", "PMM", "PMR", "PRD", "PSL", "PSM", "PSR"}


class PassType(Enum):
    TIMED = "Timed"
    CHECK_RECEIVERS = "Check Receivers"


class DefensivePersonnel(Enum):
    THREE_FOUR = "3-4"
    FOUR_THREE = "4-3"
    RUN_AND_SHOOT = "R&S"


@dataclass(frozen=True)
class PlayRecord:
    name: str
    play_file: PlayFile
    pool_category: str

    @property
    def file_path(self) -> Path:
        return self.play_file.file_path

    @property
    def play_category(self) -> int:
        return self.play_file.play_category

    @property
    def special_category(self) -> int:
        return self.play_file.special_category

    @property
    def user_category(self) -> int:
        return self.play_file.user_category

    def _base_dict(self, *, relative_to: Path | None = None) -> dict[str, object]:
        file_path = self.file_path
        if relative_to is not None:
            file_path = file_path.relative_to(relative_to)

        return {
            "name": self.name,
            "file_path": file_path.as_posix(),
            "pool_category": self.pool_category,
            "play_category": self.play_category,
            "special_category": self.special_category,
            "user_category": self.user_category,
        }

    def to_dict(self, *, relative_to: Path | None = None) -> dict[str, object]:
        return self._base_dict(relative_to=relative_to)


@dataclass(frozen=True)
class OffensivePlayRecord(PlayRecord):
    screen: bool = False
    rollout: bool = False
    qb_draw: bool = False
    pass_type: PassType | None = None

    def to_dict(self, *, relative_to: Path | None = None) -> dict[str, object]:
        result = self._base_dict(relative_to=relative_to)
        result["screen"] = self.screen
        result["rollout"] = self.rollout
        result["qb_draw"] = self.qb_draw
        result["pass_type"] = self.pass_type.value if self.pass_type else None
        return result


@dataclass(frozen=True)
class DefensivePlayRecord(PlayRecord):
    personnel_grouping: DefensivePersonnel | None = None

    def to_dict(self, *, relative_to: Path | None = None) -> dict[str, object]:
        result = self._base_dict(relative_to=relative_to)
        result["personnel_grouping"] = (
            self.personnel_grouping.value if self.personnel_grouping else None
        )
        return result


@dataclass(frozen=True)
class SpecialTeamsPlayRecord(PlayRecord):
    pass


class PlayPool:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.offensive_categories: dict[str, dict[int, int]] = {}
        self.defensive_categories: dict[str, dict[int, int]] = {}
        self.offensive_plays: list[OffensivePlayRecord] = []
        self.defensive_plays: list[DefensivePlayRecord] = []
        self.special_teams_plays: list[SpecialTeamsPlayRecord] = []
        self._plays_by_name: dict[str, PlayRecord] = {}

    @classmethod
    def from_directory(cls, root_dir: str | Path) -> PlayPool:
        pool = cls(Path(root_dir))
        logger.info("Processing .ply files in '%s'", pool.root_dir)
        for file_path in pool.root_dir.glob("**/*.ply"):
            pool._process_play_file(file_path)
        return pool

    def find_by_name(self, name: str) -> PlayRecord | None:
        return self._plays_by_name.get(name.upper())

    def _register_play(self, play: PlayRecord) -> None:
        self._plays_by_name[play.name] = play

    def _process_play_file(self, file_path: Path) -> None:
        try:
            play_file = PlayFile(file_path)
        except InvalidPlayFileError as exc:
            logger.warning("Skipping invalid play file: %s", exc)
            return

        play_name = file_path.stem.upper()
        parent_dir = file_path.parent.name
        grandparent_dir = file_path.parent.parent.name
        file_path_text = str(file_path)

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
        screen = parent_dir == "Screens"
        pool_category = grandparent_dir if screen else parent_dir
        qb_draw = (
            pool_category in RUN_CATEGORIES
            and (play_name[1] == "1" or play_name[2] == "1")
        )

        play = OffensivePlayRecord(
            name=play_name,
            play_file=play_file,
            pool_category=pool_category,
            screen=screen,
            qb_draw=qb_draw,
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
            pool_category="",
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

    def to_dict(self, *, relative_to: str | Path | None = None) -> dict[str, object]:
        base_path = Path(relative_to) if relative_to is not None else None
        return {
            "offensive_plays": self._serialize_plays(
                self.offensive_plays,
                relative_to=base_path,
                sort_key=lambda play: (play.pool_category, play.name),
            ),
            "defensive_plays": self._serialize_plays(
                self.defensive_plays,
                relative_to=base_path,
                sort_key=lambda play: (play.pool_category, play.name),
            ),
            "special_teams_plays": self._serialize_plays(
                self.special_teams_plays,
                relative_to=base_path,
                sort_key=lambda play: play.name,
            ),
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

    @staticmethod
    def _serialize_plays(
        plays: Iterable[PlayRecord],
        *,
        relative_to: Path | None,
        sort_key: Callable[[PlayRecord], Any],
    ) -> list[dict[str, object]]:
        return [
            play.to_dict(relative_to=relative_to)
            for play in sorted(plays, key=sort_key)
        ]


__all__ = [
    "DefensivePersonnel",
    "DefensivePlayRecord",
    "OffensivePlayRecord",
    "PassType",
    "PlayPool",
    "PlayRecord",
    "SpecialTeamsPlayRecord",
]
