from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from pnfl_playpool import (
    DefensivePersonnel,
    DefensivePlayRecord,
    OffensivePlayRecord,
    PlayPool,
    PlayRecord,
    SpecialTeamsPlayRecord,
)


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
EXPECTED_PERSONNEL_GROUPINGS = {
    None,
    DefensivePersonnel.THREE_FOUR,
    DefensivePersonnel.FOUR_THREE,
    DefensivePersonnel.RUN_AND_SHOOT,
}

REPRESENTATIVE_OFFENSIVE_PLAYS = [
    ("Offense/GLP/AFGZoutX.ply", "AFGZOUTX", "GLP", False, False),
    ("Offense/GLR/AF21goal.ply", "AF21GOAL", "GLR", False, False),
    ("Offense/PLR/AF9KflyA.ply", "AF9KFLYA", "PLR", False, False),
    ("Offense/PML/AF4AoutX.ply", "AF4AOUTX", "PML", False, False),
    ("Offense/PMM/Screens/AF5Xscrn.ply", "AF5XSCRN", "PMM", True, False),
    ("Offense/PMR/AF6A02T.ply", "AF6A02T", "PMR", False, False),
    ("Offense/PMR/Screens/AF6Zscrn.ply", "AF6ZSCRN", "PMR", True, False),
    ("Offense/PRD/AF0AouSX.ply", "AF0AOUSX", "PRD", False, False),
    ("Offense/PSL/AF1Ain2T.ply", "AF1AIN2T", "PSL", False, False),
    ("Offense/PSL/Screens/SF1Iscrn.ply", "SF1ISCRN", "PSL", True, False),
    ("Offense/PSM/AF2AshtZ.ply", "AF2ASHTZ", "PSM", False, False),
    ("Offense/PSR/AF3ArshZ.ply", "AF3ARSHZ", "PSR", False, False),
    ("Offense/GLR/WR10GR01.ply", "WR10GR01", "GLR", False, True),
    ("Offense/RL/A21Div20.ply", "A21DIV20", "RL", False, True),
    ("Offense/RM/AF21rm12.ply", "AF21RM12", "RM", False, False),
    ("Offense/RM/PS10qdrw.ply", "PS10QDRW", "RM", False, True),
    ("Offense/RR/AF21rr12.ply", "AF21RR12", "RR", False, False),
    ("Offense/RR/AZ10RRDW.PLY", "AZ10RRDW", "RR", False, True),
]

REPRESENTATIVE_DEFENSIVE_PLAYS = [
    ("Defense/GLpass/AF32gp02.ply", "AF32GP02", "GLpass", None),
    ("Defense/GLrun/AT42glrM.ply", "AT42GLRM", "GLrun", None),
    ("Defense/R&SDefs/PassDazzle/AT2PDBTS.ply", "AT2PDBTS", "PassDazzle", DefensivePersonnel.RUN_AND_SHOOT),
    ("Defense/R&SDefs/PassLong/AF22PL01.ply", "AF22PL01", "PassLong", DefensivePersonnel.RUN_AND_SHOOT),
    ("Defense/R&SDefs/PassMedium/AF22pmDT.ply", "AF22PMDT", "PassMedium", DefensivePersonnel.RUN_AND_SHOOT),
    ("Defense/PassShort/3R04ps01.ply", "3R04PS01", "PassShort", None),
    ("Defense/RunDazzle/ATF4RRD1.ply", "ATF4RRD1", "RunDazzle", None),
    ("Defense/34RunLeft/AF31rl3H.ply", "AF31RL3H", "RunLeft", DefensivePersonnel.THREE_FOUR),
    ("Defense/34RunMiddle/AF31rmBG.ply", "AF31RMBG", "RunMiddle", DefensivePersonnel.THREE_FOUR),
    ("Defense/34RunRight/AF31rrBG.ply", "AF31RRBG", "RunRight", DefensivePersonnel.THREE_FOUR),
    ("Defense/43RunLeft/AF41rl2p.ply", "AF41RL2P", "RunLeft", DefensivePersonnel.FOUR_THREE),
    ("Defense/43RunMiddle/AF41rmBE.ply", "AF41RMBE", "RunMiddle", DefensivePersonnel.FOUR_THREE),
    ("Defense/43RunRight/AF41rr25.ply", "AF41RR25", "RunRight", DefensivePersonnel.FOUR_THREE),
]


@pytest.fixture(scope="module")
def play_pool() -> PlayPool:
    return PlayPool.from_directory(FIXTURE_ROOT)


def play_by_relative_path(play_pool: PlayPool, relative_path: str) -> PlayRecord:
    relative_posix = Path(relative_path).as_posix()
    for play in (
        play_pool.offensive_plays
        + play_pool.defensive_plays
        + play_pool.special_teams_plays
    ):
        if play.file_path.relative_to(FIXTURE_ROOT).as_posix() == relative_posix:
            return play
    raise AssertionError(f"Play not found for fixture path: {relative_path}")


def test_play_pool_matches_snapshot(play_pool: PlayPool) -> None:
    actual = play_pool.to_dict(relative_to=FIXTURE_ROOT)
    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    assert actual == expected


def test_play_pool_exposes_expected_category_sets(play_pool: PlayPool) -> None:
    assert set(play_pool.offensive_categories) == EXPECTED_OFFENSIVE_CATEGORIES
    assert set(play_pool.defensive_categories) == EXPECTED_DEFENSIVE_CATEGORIES
    assert {play.pool_category for play in play_pool.special_teams_plays} == {""}


def test_offensive_plays_are_offensive_records(play_pool: PlayPool) -> None:
    assert all(isinstance(play, OffensivePlayRecord) for play in play_pool.offensive_plays)


def test_defensive_plays_are_defensive_records(play_pool: PlayPool) -> None:
    assert all(isinstance(play, DefensivePlayRecord) for play in play_pool.defensive_plays)


def test_special_teams_plays_are_special_teams_records(play_pool: PlayPool) -> None:
    assert all(isinstance(play, SpecialTeamsPlayRecord) for play in play_pool.special_teams_plays)


def test_offensive_plays_have_expected_attribute_sets(play_pool: PlayPool) -> None:
    assert {play.screen for play in play_pool.offensive_plays} == {True, False}
    assert {play.qb_draw for play in play_pool.offensive_plays} == {True, False}


def test_defensive_plays_have_expected_personnel_groupings(play_pool: PlayPool) -> None:
    assert {play.personnel_grouping for play in play_pool.defensive_plays} == EXPECTED_PERSONNEL_GROUPINGS


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
    ("relative_path", "expected_name", "expected_category", "expected_screen", "expected_qb_draw"),
    REPRESENTATIVE_OFFENSIVE_PLAYS,
)
def test_offensive_fixture_examples_classify_as_expected(
    play_pool: PlayPool,
    relative_path: str,
    expected_name: str,
    expected_category: str,
    expected_screen: bool,
    expected_qb_draw: bool,
) -> None:
    play = play_by_relative_path(play_pool, relative_path)
    assert isinstance(play, OffensivePlayRecord)

    assert play.name == expected_name
    assert play.pool_category == expected_category
    assert play.screen == expected_screen
    assert play.qb_draw == expected_qb_draw


@pytest.mark.parametrize(
    ("relative_path", "expected_name", "expected_category", "expected_personnel_grouping"),
    REPRESENTATIVE_DEFENSIVE_PLAYS,
)
def test_defensive_fixture_examples_classify_as_expected(
    play_pool: PlayPool,
    relative_path: str,
    expected_name: str,
    expected_category: str,
    expected_personnel_grouping: DefensivePersonnel | None,
) -> None:
    play = play_by_relative_path(play_pool, relative_path)
    assert isinstance(play, DefensivePlayRecord)

    assert play.name == expected_name
    assert play.pool_category == expected_category
    assert play.personnel_grouping == expected_personnel_grouping


def test_special_teams_fixture_shape(play_pool: PlayPool) -> None:
    play = play_by_relative_path(play_pool, "Special/AF-KO.ply")
    assert isinstance(play, SpecialTeamsPlayRecord)

    assert play.name == "AF-KO"
    assert play.pool_category == ""
    assert play.special_category == 0x02


def test_find_by_name(play_pool: PlayPool) -> None:
    play = play_pool.find_by_name("AFGZOUTX")
    assert play is not None
    assert play.name == "AFGZOUTX"
    assert isinstance(play, OffensivePlayRecord)

    play = play_pool.find_by_name("afgzoutx")
    assert play is not None

    play = play_pool.find_by_name("AF32GP02")
    assert play is not None
    assert isinstance(play, DefensivePlayRecord)

    play = play_pool.find_by_name("AF-KO")
    assert play is not None
    assert isinstance(play, SpecialTeamsPlayRecord)

    assert play_pool.find_by_name("DOESNOTEXIST") is None


def test_known_invalid_fixture_is_skipped_with_warning(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="pnfl_playpool.pool"):
        play_pool = PlayPool.from_directory(FIXTURE_ROOT)

    assert INVALID_FIXTURE.is_file()
    assert "Skipping invalid play file:" in caplog.text
    assert "PS7Xmids.ply" in caplog.text
    assert all(
        play.file_path.name != INVALID_FIXTURE.name
        for play in play_pool.offensive_plays
    )
