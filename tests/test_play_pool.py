from __future__ import annotations

import json
from pathlib import Path

import pytest

from pnfl_playpool import PlayPool


TESTS_DIR = Path(__file__).resolve().parent
FIXTURE_ROOT = TESTS_DIR / "data" / "plays"
SNAPSHOT_PATH = TESTS_DIR / "expected" / "play_pool_snapshot.json"
INVALID_FIXTURE = FIXTURE_ROOT / "Offense" / "PML" / "PS7Xmids.ply"

EXPECTED_OFFENSIVE_CATEGORIES = {
    "GLP",
    "GLR",
    "PLR",
    "PML",
    "PMM",
    "PMR",
    "PRD",
    "PSL",
    "PSM",
    "PSR",
    "RL",
    "RM",
    "RR",
}
EXPECTED_DEFENSIVE_CATEGORIES = {
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
EXPECTED_OFFENSIVE_TYPES = {"", "QB draw", "Screen"}
EXPECTED_DEFENSIVE_TYPES = {"", "3-4", "4-3", "R&S"}

REPRESENTATIVE_PLAYS = [
    ("Offense/GLP/AFGZoutX.ply", "AFGZOUTX", "GLP", ""),
    ("Offense/GLR/AF21goal.ply", "AF21GOAL", "GLR", ""),
    ("Offense/PLR/AF9KflyA.ply", "AF9KFLYA", "PLR", ""),
    ("Offense/PML/AF4AoutX.ply", "AF4AOUTX", "PML", ""),
    ("Offense/PMM/Screens/AF5Xscrn.ply", "AF5XSCRN", "PMM", "Screen"),
    ("Offense/PMR/AF6A02T.ply", "AF6A02T", "PMR", ""),
    ("Offense/PMR/Screens/AF6Zscrn.ply", "AF6ZSCRN", "PMR", "Screen"),
    ("Offense/PRD/AF0AouSX.ply", "AF0AOUSX", "PRD", ""),
    ("Offense/PSL/AF1Ain2T.ply", "AF1AIN2T", "PSL", ""),
    ("Offense/PSL/Screens/SF1Iscrn.ply", "SF1ISCRN", "PSL", "Screen"),
    ("Offense/PSM/AF2AshtZ.ply", "AF2ASHTZ", "PSM", ""),
    ("Offense/PSR/AF3ArshZ.ply", "AF3ARSHZ", "PSR", ""),
    ("Offense/GLR/WR10GR01.ply", "WR10GR01", "GLR", "QB draw"),
    ("Offense/RL/A21Div20.ply", "A21DIV20", "RL", "QB draw"),
    ("Offense/RM/AF21rm12.ply", "AF21RM12", "RM", ""),
    ("Offense/RM/PS10qdrw.ply", "PS10QDRW", "RM", "QB draw"),
    ("Offense/RR/AF21rr12.ply", "AF21RR12", "RR", ""),
    ("Offense/RR/AZ10RRDW.PLY", "AZ10RRDW", "RR", "QB draw"),
    ("Defense/GLpass/AF32gp02.ply", "AF32GP02", "GLpass", ""),
    ("Defense/GLrun/AT42glrM.ply", "AT42GLRM", "GLrun", ""),
    ("Defense/R&SDefs/PassDazzle/AT2PDBTS.ply", "AT2PDBTS", "PassDazzle", "R&S"),
    ("Defense/R&SDefs/PassLong/AF22PL01.ply", "AF22PL01", "PassLong", "R&S"),
    ("Defense/R&SDefs/PassMedium/AF22pmDT.ply", "AF22PMDT", "PassMedium", "R&S"),
    ("Defense/PassShort/3R04ps01.ply", "3R04PS01", "PassShort", ""),
    ("Defense/RunDazzle/ATF4RRD1.ply", "ATF4RRD1", "RunDazzle", ""),
    ("Defense/34RunLeft/AF31rl3H.ply", "AF31RL3H", "RunLeft", "3-4"),
    ("Defense/34RunMiddle/AF31rmBG.ply", "AF31RMBG", "RunMiddle", "3-4"),
    ("Defense/34RunRight/AF31rrBG.ply", "AF31RRBG", "RunRight", "3-4"),
    ("Defense/43RunLeft/AF41rl2p.ply", "AF41RL2P", "RunLeft", "4-3"),
    ("Defense/43RunMiddle/AF41rmBE.ply", "AF41RMBE", "RunMiddle", "4-3"),
    ("Defense/43RunRight/AF41rr25.ply", "AF41RR25", "RunRight", "4-3"),
]


@pytest.fixture(scope="module")
def play_pool() -> PlayPool:
    return PlayPool(FIXTURE_ROOT)


def play_by_relative_path(play_pool: PlayPool, relative_path: str) -> object:
    relative_posix = Path(relative_path).as_posix()
    for play in (
        play_pool.offensive_plays
        + play_pool.defensive_plays
        + play_pool.special_teams_plays
    ):
        if Path(play.file_path).relative_to(FIXTURE_ROOT).as_posix() == relative_posix:
            return play
    raise AssertionError(f"Play not found for fixture path: {relative_path}")


def test_play_pool_matches_snapshot(play_pool: PlayPool) -> None:
    actual = play_pool.to_dict(relative_to=FIXTURE_ROOT)
    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    assert actual == expected


def test_play_pool_exposes_expected_category_and_type_sets(play_pool: PlayPool) -> None:
    assert set(play_pool.offensive_categories) == EXPECTED_OFFENSIVE_CATEGORIES
    assert set(play_pool.defensive_categories) == EXPECTED_DEFENSIVE_CATEGORIES
    assert {play.play_type for play in play_pool.offensive_plays} == EXPECTED_OFFENSIVE_TYPES
    assert {play.play_type for play in play_pool.defensive_plays} == EXPECTED_DEFENSIVE_TYPES
    assert {play.directory_category for play in play_pool.special_teams_plays} == {""}
    assert {play.play_type for play in play_pool.special_teams_plays} == {""}


def test_category_count_totals_match_play_counts(play_pool: PlayPool) -> None:
    offensive_total = sum(
        count
        for category_counts in play_pool.offensive_categories.values()
        for count in category_counts.values()
    )
    defensive_total = sum(
        count
        for category_counts in play_pool.defensive_categories.values()
        for count in category_counts.values()
    )

    assert offensive_total == len(play_pool.offensive_plays)
    assert defensive_total == len(play_pool.defensive_plays)


@pytest.mark.parametrize(
    ("relative_path", "expected_name", "expected_category", "expected_play_type"),
    REPRESENTATIVE_PLAYS,
)
def test_real_fixture_examples_classify_as_expected(
    play_pool: PlayPool,
    relative_path: str,
    expected_name: str,
    expected_category: str,
    expected_play_type: str,
) -> None:
    play = play_by_relative_path(play_pool, relative_path)

    assert play.name == expected_name
    assert play.directory_category == expected_category
    assert play.play_type == expected_play_type


def test_special_teams_fixture_shape(play_pool: PlayPool) -> None:
    play = play_by_relative_path(play_pool, "Special/AF-KO.ply")

    assert play.name == "AF-KO"
    assert play.directory_category == ""
    assert play.play_type == ""
    assert play.special_flag == 0x02


def test_known_invalid_fixture_is_skipped_with_warning(capsys) -> None:
    play_pool = PlayPool(FIXTURE_ROOT)
    captured = capsys.readouterr()

    assert INVALID_FIXTURE.is_file()
    assert "Warning: skipping invalid play file:" in captured.out
    assert "PS7Xmids.ply" in captured.out
    assert all(
        Path(play.file_path).name != INVALID_FIXTURE.name
        for play in play_pool.offensive_plays
    )
