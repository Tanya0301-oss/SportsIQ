"""
FeatureExtractor — converts raw match state dicts into ML feature vectors.

Written as a stateful class so it works identically during:
  - Training (fit on historical data)
  - Live inference (transform single match state)

This eliminates training-serving skew.

Features produced:
  minute, goal_diff, home_goals, away_goals,
  home_red, away_red, shots_home, shots_away,
  possession_home, time_remaining_frac, is_tied,
  home_form_5, away_form_5
"""
import numpy as np
import pandas as pd
from typing import Any


FEATURE_NAMES = [
    "minute",
    "goal_diff",
    "home_goals",
    "away_goals",
    "home_red",
    "away_red",
    "shots_home",
    "shots_away",
    "possession_home",
    "time_remaining_frac",
    "is_tied",
    "home_form_5",
    "away_form_5",
]


class FeatureExtractor:
    """
    Transforms a raw match-state dict or DataFrame into a feature array.

    fit(df): builds team-level form lookup from historical DataFrame.
    transform(state_dict): returns np.ndarray of shape (1, n_features).
    """

    def __init__(self, full_time_minutes: int = 90):
        self.full_time = full_time_minutes
        self._team_form: dict[str, float] = {}   # team_name → weighted win rate

    # ── Training-time fitting ────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> "FeatureExtractor":
        """
        Build per-team form scores from a historical DataFrame.

        Expected columns: home_team, away_team, result (H/D/A), match_date.
        Uses exponentially weighted average so recent matches matter more.
        """
        teams = set(df["home_team"].unique()) | set(df["away_team"].unique())
        for team in teams:
            self._team_form[team] = self._calc_form(df, team)
        return self

    def _calc_form(self, df: pd.DataFrame, team: str) -> float:
        """Exponentially weighted win rate over last 20 matches."""
        team_matches = df[
            (df["home_team"] == team) | (df["away_team"] == team)
        ].sort_values("match_date").tail(20)

        if team_matches.empty:
            return 0.5

        wins = []
        for _, row in team_matches.iterrows():
            if row["home_team"] == team:
                wins.append(1.0 if row["result"] == "H" else 0.0)
            else:
                wins.append(1.0 if row["result"] == "A" else 0.0)

        if not wins:
            return 0.5

        # Exponential weights (more recent = higher weight)
        weights = np.exp(np.linspace(-1, 0, len(wins)))
        weights /= weights.sum()
        return float(np.average(wins, weights=weights))

    def get_team_form(self, team: str) -> float:
        return self._team_form.get(team, 0.5)

    # ── Inference-time transform ─────────────────────────────────────────────

    def transform(self, state: dict[str, Any]) -> np.ndarray:
        """
        Convert a single match-state dict to a feature vector.

        Required keys: minute, home_goals, away_goals, home_red_cards,
                       away_red_cards, home_shots_on_target,
                       away_shots_on_target, home_possession,
                       home_team (optional), away_team (optional).
        """
        minute = float(state.get("minute", 0))
        home_goals = float(state.get("home_goals", 0))
        away_goals = float(state.get("away_goals", 0))
        home_red = float(state.get("home_red_cards", 0))
        away_red = float(state.get("away_red_cards", 0))
        shots_home = float(state.get("home_shots_on_target", 0))
        shots_away = float(state.get("away_shots_on_target", 0))
        possession = float(state.get("home_possession", 50.0))
        home_team = state.get("home_team", "")
        away_team = state.get("away_team", "")

        goal_diff = home_goals - away_goals
        time_remaining = max(0.0, (self.full_time - minute) / self.full_time)
        is_tied = 1.0 if goal_diff == 0 else 0.0
        home_form = self.get_team_form(home_team)
        away_form = self.get_team_form(away_team)

        return np.array([[
            minute,
            goal_diff,
            home_goals,
            away_goals,
            home_red,
            away_red,
            shots_home,
            shots_away,
            possession,
            time_remaining,
            is_tied,
            home_form,
            away_form,
        ]], dtype=np.float32)

    def transform_df(self, df: pd.DataFrame) -> np.ndarray:
        """
        Batch transform historical match DataFrame for training.
        Each row is assumed to be at half-time snapshot (minute=45).
        """
        rows = []
        for _, row in df.iterrows():
            state = {
                "minute": row.get("ht_minute", 45),
                "home_goals": row.get("ht_home_goals", row.get("home_goals", 0) // 2),
                "away_goals": row.get("ht_away_goals", row.get("away_goals", 0) // 2),
                "home_red_cards": row.get("home_red", 0),
                "away_red_cards": row.get("away_red", 0),
                "home_shots_on_target": row.get("home_shots_on_target", row.get("hst", 0)),
                "away_shots_on_target": row.get("away_shots_on_target", row.get("ast", 0)),
                "home_possession": row.get("home_possession", 50.0),
                "home_team": row.get("home_team", ""),
                "away_team": row.get("away_team", ""),
            }
            rows.append(self.transform(state)[0])
        return np.array(rows, dtype=np.float32)
