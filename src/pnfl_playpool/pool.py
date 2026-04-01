from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fbpro98_play import InvalidPlayFileError, PlayFile


logger = logging.getLogger(__name__)

RUN_CATEGORIES = {"GLR", "RL", "RM", "RR"}


@dataclass(frozen=True, slots=True)
class PlayRecord:
    name: str
    play_file: PlayFile
    pool_category: str
    play_type: str

    @property
    def file_path(self) -> Path:
        return self.play_file.file_path

    @property
    def play_category(self) -> int:
        return self.play_file.play_category

    @property
    def special_flag(self) -> int:
        return self.play_file.special_flag

    @property
    def user_category(self) -> int:
        return self.play_file.user_category

    def to_dict(self, *, relative_to: Path | None = None) -> dict[str, str | int]:
        file_path = self.file_path
        if relative_to is not None:
            file_path = file_path.relative_to(relative_to)

        return {
            "name": self.name,
            "file_path": file_path.as_posix(),
            "pool_category": self.pool_category,
            "play_type": self.play_type,
            "play_category": self.play_category,
            "special_flag": self.special_flag,
            "user_category": self.user_category,
        }


class PlayPool:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.offensive_categories: dict[str, dict[int, int]] = {}
        self.defensive_categories: dict[str, dict[int, int]] = {}
        self.offensive_plays: list[PlayRecord] = []
        self.defensive_plays: list[PlayRecord] = []
        self.special_teams_plays: list[PlayRecord] = []

    @classmethod
    def from_directory(cls, root_dir: str | Path) -> PlayPool:
        pool = cls(Path(root_dir))
        logger.info("Processing .ply files in '%s'", pool.root_dir)
        for file_path in pool.root_dir.glob("**/*.ply"):
            pool._process_play_file(file_path)
        return pool

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
        if parent_dir == "Screens":
            pool_category = grandparent_dir
            play_type = "Screen"
        elif parent_dir in RUN_CATEGORIES and (
            play_name[1] == "1" or play_name[2] == "1"
        ):
            pool_category = parent_dir
            play_type = "QB draw"
        else:
            pool_category = parent_dir
            play_type = ""

        play = PlayRecord(
            name=play_name,
            play_file=play_file,
            pool_category=pool_category,
            play_type=play_type,
        )
        self.offensive_plays.append(play)
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
        if grandparent_dir == "R&SDefs":
            pool_category = parent_dir
            play_type = "R&S"
        elif parent_dir.startswith("34") or parent_dir.startswith("43"):
            pool_category = parent_dir[2:]
            play_type = "3-4" if parent_dir.startswith("34") else "4-3"
        else:
            pool_category = parent_dir
            play_type = ""

        play = PlayRecord(
            name=play_name,
            play_file=play_file,
            pool_category=pool_category,
            play_type=play_type,
        )
        self.defensive_plays.append(play)
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
        play = PlayRecord(
            name=play_name,
            play_file=play_file,
            pool_category="",
            play_type="",
        )
        self.special_teams_plays.append(play)

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
    ) -> list[dict[str, str | int]]:
        return [
            play.to_dict(relative_to=relative_to)
            for play in sorted(plays, key=sort_key)
        ]


__all__ = [
    "PlayRecord",
    "PlayPool",
]
