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
    read_play_pool,
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
    ("Offense/GLP/AFGZoutX.ply", "AFGZoutX", "GLP", False, False),
    ("Offense/GLR/AF21goal.ply", "AF21goal", "GLR", False, False),
    ("Offense/PLR/AF9KflyA.ply", "AF9KflyA", "PLR", False, False),
    ("Offense/PML/AF4AoutX.ply", "AF4AoutX", "PML", False, False),
    ("Offense/PMM/Screens/AF5Xscrn.ply", "AF5Xscrn", "PMM", True, False),
    ("Offense/PMR/AF6A02T.ply", "AF6A02T", "PMR", False, False),
    ("Offense/PMR/Screens/AF6Zscrn.ply", "AF6Zscrn", "PMR", True, False),
    ("Offense/PRD/AF0AouSX.ply", "AF0AouSX", "PRD", False, False),
    ("Offense/PSL/AF1Ain2T.ply", "AF1Ain2T", "PSL", False, False),
    ("Offense/PSL/Screens/SF1Iscrn.ply", "SF1Iscrn", "PSL", True, False),
    ("Offense/PSM/AF2AshtZ.ply", "AF2AshtZ", "PSM", False, False),
    ("Offense/PSR/AF3ArshZ.ply", "AF3ArshZ", "PSR", False, False),
    ("Offense/GLR/WR10GR01.ply", "WR10GR01", "GLR", False, True),
    ("Offense/RL/A21Div20.ply", "A21Div20", "RL", False, True),
    ("Offense/RM/AF21rm12.ply", "AF21rm12", "RM", False, False),
    ("Offense/RM/PS10qdrw.ply", "PS10qdrw", "RM", False, True),
    ("Offense/RR/AF21rr12.ply", "AF21rr12", "RR", False, False),
    ("Offense/RR/AZ10RRDW.PLY", "AZ10RRDW", "RR", False, True),
]

REPRESENTATIVE_DEFENSIVE_PLAYS = [
    ("Defense/GLpass/AF32gp02.ply", "AF32gp02", "GLpass", None),
    ("Defense/GLrun/AT42glrM.ply", "AT42glrM", "GLrun", None),
    ("Defense/R&SDefs/PassDazzle/AT2PDBTS.ply", "AT2PDBTS", "PassDazzle", DefensivePersonnel.RUN_AND_SHOOT),
    ("Defense/R&SDefs/PassLong/AF22PL01.ply", "AF22PL01", "PassLong", DefensivePersonnel.RUN_AND_SHOOT),
    ("Defense/R&SDefs/PassMedium/AF22pmDT.ply", "AF22pmDT", "PassMedium", DefensivePersonnel.RUN_AND_SHOOT),
    ("Defense/PassShort/3R04ps01.ply", "3R04ps01", "PassShort", None),
    ("Defense/RunDazzle/ATF4RRD1.ply", "ATF4RRD1", "RunDazzle", None),
    ("Defense/34RunLeft/AF31rl3H.ply", "AF31rl3H", "RunLeft", DefensivePersonnel.THREE_FOUR),
    ("Defense/34RunMiddle/AF31rmBG.ply", "AF31rmBG", "RunMiddle", DefensivePersonnel.THREE_FOUR),
    ("Defense/34RunRight/AF31rrBG.ply", "AF31rrBG", "RunRight", DefensivePersonnel.THREE_FOUR),
    ("Defense/43RunLeft/AF41rl2p.ply", "AF41rl2p", "RunLeft", DefensivePersonnel.FOUR_THREE),
    ("Defense/43RunMiddle/AF41rmBE.ply", "AF41rmBE", "RunMiddle", DefensivePersonnel.FOUR_THREE),
    ("Defense/43RunRight/AF41rr25.ply", "AF41rr25", "RunRight", DefensivePersonnel.FOUR_THREE),
]


@pytest.fixture(scope="module")
def play_pool() -> PlayPool:
    return read_play_pool(FIXTURE_ROOT)


def play_by_relative_path(play_pool: PlayPool, relative_path: str) -> PlayRecord:
    relative_posix = Path(relative_path).as_posix()
    for play in play_pool.offensive_plays + play_pool.defensive_plays + play_pool.special_teams_plays:
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


def test_offensive_plays_are_offensive_records(play_pool: PlayPool) -> None:
    assert all(isinstance(play, OffensivePlayRecord) for play in play_pool.offensive_plays)


def test_defensive_plays_are_defensive_records(play_pool: PlayPool) -> None:
    assert all(isinstance(play, DefensivePlayRecord) for play in play_pool.defensive_plays)


def test_special_teams_plays_are_special_teams_records(play_pool: PlayPool) -> None:
    assert all(isinstance(play, SpecialTeamsPlayRecord) for play in play_pool.special_teams_plays)


def test_play_counts(play_pool: PlayPool) -> None:
    assert len(play_pool.offensive_plays) == 2461
    assert len(play_pool.defensive_plays) == 2186
    assert len(play_pool.special_teams_plays) == 308


def test_offensive_play_type_counts(play_pool: PlayPool) -> None:
    plays = play_pool.offensive_plays
    assert sum(1 for p in plays if p.is_run) == 660
    assert sum(1 for p in plays if p.is_pass) == 1801
    assert sum(1 for p in plays if p.qb_draw) == 52
    assert sum(1 for p in plays if p.screen) == 57
    assert sum(1 for p in plays if p.pass_type is not None) == 388
    assert sum(1 for p in plays if p.rollout) == 189


def test_defensive_play_personnel_counts(play_pool: PlayPool) -> None:
    plays = play_pool.defensive_plays
    assert sum(1 for p in plays if p.personnel_grouping == DefensivePersonnel.THREE_FOUR) == 697
    assert sum(1 for p in plays if p.personnel_grouping == DefensivePersonnel.FOUR_THREE) == 184
    assert sum(1 for p in plays if p.personnel_grouping == DefensivePersonnel.RUN_AND_SHOOT) == 219
    assert sum(1 for p in plays if p.personnel_grouping is None) == 1086


def test_category_count_totals_match_play_counts(play_pool: PlayPool) -> None:
    offensive_total = sum(
        count for category_counts in play_pool.offensive_categories.values() for count in category_counts.values()
    )
    defensive_total = sum(
        count for category_counts in play_pool.defensive_categories.values() for count in category_counts.values()
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
    assert play.special_category == 0x02


def test_find_by_name(play_pool: PlayPool) -> None:
    play = play_pool.find_by_name("AFGZOUTX")
    assert play is not None
    assert play.name == "AFGZoutX"
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
        play_pool = read_play_pool(FIXTURE_ROOT)

    assert INVALID_FIXTURE.is_file()
    assert "Skipping invalid play file:" in caplog.text
    assert "PS7Xmids.ply" in caplog.text
    assert all(play.file_path.name != INVALID_FIXTURE.name for play in play_pool.offensive_plays)
