import pandas as pd

from src.domain.football import try_football_data_code


def _normalize_season(season: str) -> str:
    season = str(season).strip()
    if len(season) == 4 and season.isdigit():
        # If already in football-data "YYZZ" format (e.g. 2324), keep as-is.
        yy = int(season[:2])
        zz = int(season[2:])
        if (yy + 1) % 100 == zz:
            return season

        start = int(season) % 100
        end = (int(season) + 1) % 100
        return f"{start:02d}{end:02d}"
    return season


def _normalize_league(league: str) -> str:
    league = str(league).strip()
    code = try_football_data_code(league)
    return code or league


def fetch_football_data(season: str, league: str = 'E0') -> pd.DataFrame:
    season = _normalize_season(season)
    league = _normalize_league(league)
    url = f'https://www.football-data.co.uk/mmz4281/{season}/{league}.csv'
    df = pd.read_csv(url, encoding='latin-1')
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df = df.rename(
        columns={
            'Date': 'date',
            'HomeTeam': 'home_team',
            'AwayTeam': 'away_team',
            'FTHG': 'home_goals',
            'FTAG': 'away_goals',
            'FTR': 'FTR',
        }
    )
    df = df[['date', 'home_team', 'away_team', 'home_goals', 'away_goals', 'FTR']].copy()
    df = df.dropna(subset=['date', 'home_team', 'away_team'])
    df['season'] = season
    df['league'] = league
    df['match_id'] = df.apply(
        lambda r: f"{r['date'].strftime('%Y%m%d')}_{r['home_team']}_{r['away_team']}_{league}", axis=1
    )
    return df
