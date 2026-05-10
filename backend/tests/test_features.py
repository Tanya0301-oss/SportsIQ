"""Tests for FeatureExtractor."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from ml.feature_extractor import FeatureExtractor, FEATURE_NAMES


@pytest.fixture
def extractor():
    """FeatureExtractor fitted on minimal synthetic data."""
    df = pd.DataFrame({
        "home_team": ["Arsenal", "Liverpool", "Arsenal"],
        "away_team": ["Chelsea", "Arsenal",   "Liverpool"],
        "result":    ["H",       "D",          "A"],
        "match_date": pd.to_datetime(["2023-01-01", "2023-01-08", "2023-01-15"]),
    })
    ex = FeatureExtractor()
    ex.fit(df)
    return ex


def test_transform_output_shape(extractor):
    state = {
        "minute": 45, "home_goals": 1, "away_goals": 0,
        "home_red_cards": 0, "away_red_cards": 0,
        "home_shots_on_target": 4, "away_shots_on_target": 2,
        "home_possession": 55.0,
        "home_team": "Arsenal", "away_team": "Chelsea",
    }
    X = extractor.transform(state)
    assert X.shape == (1, len(FEATURE_NAMES))


def test_goal_diff_feature(extractor):
    state = {
        "minute": 60, "home_goals": 2, "away_goals": 1,
        "home_red_cards": 0, "away_red_cards": 0,
        "home_shots_on_target": 5, "away_shots_on_target": 3,
        "home_possession": 52.0,
    }
    X = extractor.transform(state)
    goal_diff_idx = FEATURE_NAMES.index("goal_diff")
    assert X[0, goal_diff_idx] == pytest.approx(1.0)


def test_time_remaining_at_minute_zero(extractor):
    state = {
        "minute": 0, "home_goals": 0, "away_goals": 0,
        "home_red_cards": 0, "away_red_cards": 0,
        "home_shots_on_target": 0, "away_shots_on_target": 0,
        "home_possession": 50.0,
    }
    X = extractor.transform(state)
    tr_idx = FEATURE_NAMES.index("time_remaining_frac")
    assert X[0, tr_idx] == pytest.approx(1.0)


def test_is_tied_when_level(extractor):
    state = {
        "minute": 45, "home_goals": 1, "away_goals": 1,
        "home_red_cards": 0, "away_red_cards": 0,
        "home_shots_on_target": 3, "away_shots_on_target": 3,
        "home_possession": 50.0,
    }
    X = extractor.transform(state)
    tied_idx = FEATURE_NAMES.index("is_tied")
    assert X[0, tied_idx] == pytest.approx(1.0)


def test_team_form_fallback(extractor):
    """Unknown team should return default form of 0.5."""
    form = extractor.get_team_form("Unknown FC")
    assert form == pytest.approx(0.5)


def test_transform_df_shape(extractor):
    df = pd.DataFrame({
        "home_team": ["Arsenal", "Chelsea"],
        "away_team": ["Liverpool", "Arsenal"],
        "home_goals": [1, 0],
        "away_goals": [0, 2],
        "result": ["H", "A"],
        "match_date": pd.to_datetime(["2023-01-01", "2023-01-08"]),
        "hst": [4, 2],
        "ast": [2, 5],
    })
    X = extractor.transform_df(df)
    assert X.shape == (2, len(FEATURE_NAMES))
