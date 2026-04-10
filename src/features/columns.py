"""Shared feature/label definitions used across training, evaluation, and serving."""

from __future__ import annotations

from typing import Dict, List

# Convention used across the project:
# - Away win: 0
# - Draw: 1
# - Home win: 2
TARGET_MAP: Dict[str, int] = {"A": 0, "D": 1, "H": 2}

# Canonical feature list (27 features) expected by the trained model.
FEATURE_COLUMNS: List[str] = [
    # Goal-based features
    "home_rolling_goals_scored_5",
    "home_rolling_goals_conceded_5",
    "away_rolling_goals_scored_5",
    "away_rolling_goals_conceded_5",
    # xG-based features
    "home_rolling_xg_scored_5",
    "home_rolling_xg_conceded_5",
    "home_rolling_xg_diff_5",
    "away_rolling_xg_scored_5",
    "away_rolling_xg_conceded_5",
    "away_rolling_xg_diff_5",
    # Advanced match features
    "xg_total",
    "xg_diff",
    "xg_home_advantage",
    "xg_away_advantage",
    "shots_total",
    "shots_diff",
    "shots_home_ratio",
    "shots_away_ratio",
    "possession_diff",
    "corners_total",
    "corners_diff",
    "yellow_cards_total",
    "yellow_cards_diff",
    # Rolling differentials
    "rolling_xg_scored_5_diff",
    "rolling_xg_conceded_5_diff",
    "rolling_goals_scored_5_diff",
    "rolling_goals_conceded_5_diff",
]

