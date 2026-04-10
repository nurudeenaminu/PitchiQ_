"""Pytest configuration and fixtures for PitchIQ tests."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_match_data() -> pd.DataFrame:
    """Sample match data for testing."""
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10, freq='W'),
        'home_team': ['Liverpool', 'Arsenal', 'Chelsea', 'Man City', 'Tottenham'] * 2,
        'away_team': ['Arsenal', 'Chelsea', 'Man City', 'Tottenham', 'Liverpool'] * 2,
        'home_goals': [2, 1, 0, 3, 1, 2, 2, 1, 4, 0],
        'away_goals': [1, 1, 2, 0, 1, 0, 1, 3, 1, 0],
        'FTR': ['H', 'D', 'A', 'H', 'D', 'H', 'H', 'A', 'H', 'D'],
        'league': ['E0'] * 10,
        'xg_home': [1.8, 1.2, 0.9, 2.5, 1.1, 1.9, 2.1, 0.8, 3.2, 0.5],
        'xg_away': [1.1, 1.3, 1.8, 0.6, 1.0, 0.7, 1.2, 2.1, 0.9, 0.4],
    })


@pytest.fixture
def sample_features() -> pd.DataFrame:
    """Sample feature data for testing."""
    np.random.seed(42)
    n = 20
    return pd.DataFrame({
        'home_rolling_goals_scored_5': np.random.uniform(1, 3, n),
        'home_rolling_goals_conceded_5': np.random.uniform(0.5, 2, n),
        'away_rolling_goals_scored_5': np.random.uniform(1, 3, n),
        'away_rolling_goals_conceded_5': np.random.uniform(0.5, 2, n),
        'home_rolling_xg_scored_5': np.random.uniform(1, 2.5, n),
        'home_rolling_xg_conceded_5': np.random.uniform(0.5, 2, n),
        'home_rolling_xg_diff_5': np.random.uniform(-0.5, 1, n),
        'away_rolling_xg_scored_5': np.random.uniform(1, 2.5, n),
        'away_rolling_xg_conceded_5': np.random.uniform(0.5, 2, n),
        'away_rolling_xg_diff_5': np.random.uniform(-0.5, 1, n),
        'xg_total': np.random.uniform(2, 4, n),
        'xg_diff': np.random.uniform(-1, 1, n),
        'xg_home_advantage': np.random.uniform(0.4, 0.6, n),
        'xg_away_advantage': np.random.uniform(0.4, 0.6, n),
        'shots_total': np.random.uniform(20, 35, n),
        'shots_diff': np.random.uniform(-5, 5, n),
        'shots_home_ratio': np.random.uniform(0.4, 0.6, n),
        'shots_away_ratio': np.random.uniform(0.4, 0.6, n),
        'possession_diff': np.random.uniform(-10, 10, n),
        'corners_total': np.random.uniform(8, 15, n),
        'corners_diff': np.random.uniform(-3, 3, n),
        'yellow_cards_total': np.random.uniform(2, 6, n),
        'yellow_cards_diff': np.random.uniform(-2, 2, n),
        'rolling_xg_scored_5_diff': np.random.uniform(-0.5, 0.5, n),
        'rolling_xg_conceded_5_diff': np.random.uniform(-0.5, 0.5, n),
        'rolling_goals_scored_5_diff': np.random.uniform(-1, 1, n),
        'rolling_goals_conceded_5_diff': np.random.uniform(-1, 1, n),
    })
