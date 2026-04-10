import pandas as pd
import numpy as np
from .football_data import fetch_football_data


def fetch_fbref_data(season: str, league: str) -> pd.DataFrame:
    """Fetch/derive additional match stats from FBref or synthetic fallback"""
    try:
        # TODO: replace with async real FBref scraping/API when possible
        base_df = fetch_football_data(season, league)

        if base_df.empty:
            return _generate_synthetic_fbref(season, league)

        # Basic synthetic estimate using base match results
        df = base_df.copy()
        np.random.seed(42)
        df['shots_home'] = np.random.poisson(12, size=len(df))
        df['shots_away'] = np.random.poisson(10, size=len(df))
        df['possession_home'] = np.clip(np.random.normal(52, 8, size=len(df)), 30, 70)
        df['possession_away'] = 100 - df['possession_home']
        df['corners_home'] = np.random.poisson(5, size=len(df))
        df['corners_away'] = np.random.poisson(4, size=len(df))
        df['yellow_cards_home'] = np.random.poisson(1.5, size=len(df)).astype(int)
        df['yellow_cards_away'] = np.random.poisson(1.5, size=len(df)).astype(int)

        df['league'] = league
        df['season'] = season
        return df

    except Exception as e:
        print(f"FBref adapter error: {e}, using synthetic fallback")
        return _generate_synthetic_fbref(season, league)


def _generate_synthetic_fbref(season: str, league: str) -> pd.DataFrame:
    teams = [f"Team{i}" for i in range(1, 21)]
    rows = []
    for i in range(380):
        home, away = np.random.choice(teams, 2, replace=False)
        shots_home = np.random.poisson(12)
        shots_away = np.random.poisson(10)
        possession_home = float(np.clip(np.random.normal(52, 8), 30, 70))
        possession_away = 100 - possession_home
        rows.append({
            'season': season,
            'league': league,
            'home_team': home,
            'away_team': away,
            'shots_home': shots_home,
            'shots_away': shots_away,
            'possession_home': possession_home,
            'possession_away': possession_away,
            'corners_home': np.random.poisson(5),
            'corners_away': np.random.poisson(4),
            'yellow_cards_home': int(np.random.poisson(1.5)),
            'yellow_cards_away': int(np.random.poisson(1.5)),
        })
    return pd.DataFrame(rows)
