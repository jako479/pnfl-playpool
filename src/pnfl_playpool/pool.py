from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from fbpro98_play import InvalidPlyError, PlyFile


RUN_CATEGORIES = {"GLR", "RL", "RM", "RR"}


@dataclass(frozen=True, slots=True)
class Play:
    name: str
    file_path: str
    directory_category: str
    play_type: str
    play_category: int
    special_flag: int
    user_category: int

    def to_dict(self, *, relative_to: Path | None = None) -> dict[str, str | int]:
        file_path = Path(self.file_path)
        if relative_to is not None:
            file_path = file_path.relative_to(relative_to)

        return {
            "name": self.name,
            "file_path": file_path.as_posix(),
            "directory_category": self.directory_category,
            "play_type": self.play_type,
            "play_category": self.play_category,
            "special_flag": self.special_flag,
            "user_category": self.user_category,
        }


class PlayPool:
    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = Path(root_dir)
        self.offensive_categories: dict[str, dict[int, int]] = {}
        self.defensive_categories: dict[str, dict[int, int]] = {}
        self.offensive_plays: list[Play] = []
        self.defensive_plays: list[Play] = []
        self.special_teams_plays: list[Play] = []

        print(f"Processing .ply files in '{self.root_dir}'")
        for file_path in self.root_dir.glob("**/*.ply"):
            self._process_play_file(file_path)

    def _process_play_file(self, file_path: Path) -> None:
        try:
            play_file = PlyFile(file_path)
        except InvalidPlyError as exc:
            print(f"Warning: skipping invalid play file: {exc}")
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
        play_file: PlyFile,
    ) -> None:
        if parent_dir == "Screens":
            directory_category = grandparent_dir
            play_type = "Screen"
        elif parent_dir in RUN_CATEGORIES and (
            play_name[1] == "1" or play_name[2] == "1"
        ):
            directory_category = parent_dir
            play_type = "QB draw"
        else:
            directory_category = parent_dir
            play_type = ""

        play = Play(
            name=play_name,
            file_path=str(play_file.file_path),
            directory_category=directory_category,
            play_type=play_type,
            play_category=play_file.play_category,
            special_flag=play_file.special_flag,
            user_category=play_file.user_category,
        )
        self.offensive_plays.append(play)
        self._increment_user_category_count(
            self.offensive_categories,
            directory_category,
            play_file.user_category,
        )

    def _process_defensive_play(
        self,
        play_name: str,
        parent_dir: str,
        grandparent_dir: str,
        play_file: PlyFile,
    ) -> None:
        if grandparent_dir == "R&SDefs":
            directory_category = parent_dir
            play_type = "R&S"
        elif parent_dir.startswith("34") or parent_dir.startswith("43"):
            directory_category = parent_dir[2:]
            play_type = "3-4" if parent_dir.startswith("34") else "4-3"
        else:
            directory_category = parent_dir
            play_type = ""

        play = Play(
            name=play_name,
            file_path=str(play_file.file_path),
            directory_category=directory_category,
            play_type=play_type,
            play_category=play_file.play_category,
            special_flag=play_file.special_flag,
            user_category=play_file.user_category,
        )
        self.defensive_plays.append(play)
        self._increment_user_category_count(
            self.defensive_categories,
            directory_category,
            play_file.user_category,
        )

    def _process_special_teams_play(
        self,
        play_name: str,
        play_file: PlyFile,
    ) -> None:
        play = Play(
            name=play_name,
            file_path=str(play_file.file_path),
            directory_category="",
            play_type="",
            play_category=play_file.play_category,
            special_flag=play_file.special_flag,
            user_category=play_file.user_category,
        )
        self.special_teams_plays.append(play)

    @staticmethod
    def _increment_user_category_count(
        categories: dict[str, dict[int, int]],
        directory_category: str,
        user_category: int,
    ) -> None:
        category_counts = categories.setdefault(directory_category, {})
        category_counts[user_category] = category_counts.get(user_category, 0) + 1

    def to_dict(self, *, relative_to: str | Path | None = None) -> dict[str, object]:
        base_path = Path(relative_to) if relative_to is not None else None
        return {
            "offensive_plays": self._serialize_plays(
                self.offensive_plays,
                relative_to=base_path,
                sort_key=lambda play: (play.directory_category, play.name),
            ),
            "defensive_plays": self._serialize_plays(
                self.defensive_plays,
                relative_to=base_path,
                sort_key=lambda play: (play.directory_category, play.name),
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
        for directory_category in sorted(categories):
            for user_category in sorted(categories[directory_category]):
                rows.append(
                    {
                        "directory_category": directory_category,
                        "user_category": user_category,
                        "count": categories[directory_category][user_category],
                    }
                )
        return rows

    @staticmethod
    def _serialize_plays(
        plays: Iterable[Play],
        *,
        relative_to: Path | None,
        sort_key: object,
    ) -> list[dict[str, str | int]]:
        return [
            play.to_dict(relative_to=relative_to)
            for play in sorted(plays, key=sort_key)
        ]


__all__ = [
    "Play",
    "PlayPool",
]
