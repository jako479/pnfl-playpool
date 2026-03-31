from __future__ import annotations

import json
from pathlib import Path
from struct import Struct

from pnfl_playpool import PlayPool


TESTS_DIR = Path(__file__).resolve().parent
FIXTURE_ROOT = TESTS_DIR / "data" / "plays"
SNAPSHOT_PATH = TESTS_DIR / "expected" / "play_pool_snapshot.json"
PLY_HEADER = Struct("<4si")


def write_ply_file(
    file_path: Path,
    *,
    play_category: int = 0x82,
    special_flag: int = 0x00,
    user_category: int = 0x02,
) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(
        PLY_HEADER.pack(b"P95:", 25)
        + bytes(22)
        + bytes([play_category, special_flag, user_category])
    )


def test_play_pool_matches_snapshot() -> None:
    play_pool = PlayPool(FIXTURE_ROOT)
    actual = play_pool.to_dict(relative_to=FIXTURE_ROOT)
    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    assert actual == expected


def test_play_pool_classifies_and_counts_plays(tmp_path: Path, capsys) -> None:
    offense_screen = tmp_path / "Offense" / "PSL" / "Screens" / "scrn1.ply"
    offense_qb_draw = tmp_path / "Offense" / "RM" / "A1DRAW.ply"
    defense_rs = tmp_path / "Defense" / "R&SDefs" / "PassShort" / "rsdef.ply"
    defense_34 = tmp_path / "Defense" / "34RunLeft" / "front.ply"
    special = tmp_path / "Special" / "kick.ply"

    write_ply_file(offense_screen, user_category=0x10)
    write_ply_file(offense_qb_draw, user_category=0x20)
    write_ply_file(defense_rs, user_category=0x30)
    write_ply_file(defense_34, user_category=0x40)
    write_ply_file(special, special_flag=0x01, user_category=0x50)

    play_pool = PlayPool(tmp_path)
    captured = capsys.readouterr()

    offensive_plays = {play.name: play for play in play_pool.offensive_plays}
    defensive_plays = {play.name: play for play in play_pool.defensive_plays}

    assert "Processing .ply files" in captured.out
    assert set(offensive_plays) == {"SCRN1", "A1DRAW"}
    assert offensive_plays["SCRN1"].directory_category == "PSL"
    assert offensive_plays["SCRN1"].play_type == "Screen"
    assert offensive_plays["A1DRAW"].directory_category == "RM"
    assert offensive_plays["A1DRAW"].play_type == "QB draw"
    assert defensive_plays["RSDEF"].directory_category == "PassShort"
    assert defensive_plays["RSDEF"].play_type == "R&S"
    assert defensive_plays["FRONT"].directory_category == "RunLeft"
    assert defensive_plays["FRONT"].play_type == "3-4"
    assert play_pool.special_teams_plays[0].name == "KICK"
    assert play_pool.special_teams_plays[0].special_flag == 0x01
    assert play_pool.offensive_categories == {"PSL": {0x10: 1}, "RM": {0x20: 1}}
    assert play_pool.defensive_categories == {
        "PassShort": {0x30: 1},
        "RunLeft": {0x40: 1},
    }


def test_invalid_ply_file_is_skipped(tmp_path: Path, capsys) -> None:
    invalid_file = tmp_path / "Offense" / "GLR" / "bad.ply"
    invalid_file.parent.mkdir(parents=True)
    invalid_file.write_bytes(b"")

    play_pool = PlayPool(tmp_path)
    captured = capsys.readouterr()

    assert play_pool.offensive_plays == []
    assert play_pool.defensive_plays == []
    assert play_pool.special_teams_plays == []
    assert "Warning: skipping invalid play file:" in captured.out
