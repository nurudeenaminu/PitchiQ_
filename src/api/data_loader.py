"""Mock data loader for football data (offline/demo friendly).

This module intentionally uses in-repo fixtures instead of live API calls so
the dashboard/API can run in restricted environments.
"""
from datetime import datetime, timedelta
from typing import Dict, List

# Mock EPL table (example snapshot for UI/demo)
EPL_TABLE_2024_25 = [
    {"pos": 1, "team": "Liverpool", "p": 34, "w": 26, "d": 6, "l": 2, "gf": 82, "ga": 28, "pts": 84},
    {"pos": 2, "team": "Man City", "p": 34, "w": 24, "d": 7, "l": 3, "gf": 78, "ga": 32, "pts": 79},
    {"pos": 3, "team": "Arsenal", "p": 34, "w": 23, "d": 6, "l": 5, "gf": 76, "ga": 35, "pts": 75},
    {"pos": 4, "team": "Chelsea", "p": 34, "w": 21, "d": 5, "l": 8, "gf": 68, "ga": 42, "pts": 68},
    {"pos": 5, "team": "Aston Villa", "p": 34, "w": 19, "d": 8, "l": 7, "gf": 64, "ga": 45, "pts": 65},
    {"pos": 6, "team": "Tottenham", "p": 34, "w": 18, "d": 6, "l": 10, "gf": 62, "ga": 48, "pts": 60},
    {"pos": 7, "team": "Man United", "p": 34, "w": 16, "d": 5, "l": 13, "gf": 55, "ga": 52, "pts": 53},
    {"pos": 8, "team": "Newcastle", "p": 34, "w": 15, "d": 6, "l": 13, "gf": 52, "ga": 54, "pts": 51},
]

# Mock EPL top scorers (example snapshot for UI/demo)
EPL_TOP_SCORERS = [
    {"rank": 1, "player": "Mohamed Salah", "team": "Liverpool", "goals": 26, "assists": 9, "xg": 24.5},
    {"rank": 2, "player": "Erling Haaland", "team": "Man City", "goals": 24, "assists": 7, "xg": 23.2},
    {"rank": 3, "player": "Harry Kane", "team": "Bayern Munich", "goals": 0, "assists": 0, "xg": 0},  # Moved
    {"rank": 4, "player": "Bukayo Saka", "team": "Arsenal", "goals": 19, "assists": 8, "xg": 18.1},
    {"rank": 5, "player": "Ollie Watkins", "team": "Aston Villa", "goals": 17, "assists": 6, "xg": 16.3},
    {"rank": 6, "player": "Rodrygo Goes", "team": "Chelsea", "goals": 15, "assists": 4, "xg": 14.2},
    {"rank": 7, "player": "Son Heung-min", "team": "Tottenham", "goals": 14, "assists": 8, "xg": 13.5},
    {"rank": 8, "player": "Maddison", "team": "Tottenham", "goals": 13, "assists": 7, "xg": 12.8},
]

# Mock La Liga table (example snapshot for UI/demo)
LA_LIGA_TABLE = [
    {"pos": 1, "team": "Real Madrid", "p": 32, "w": 24, "d": 6, "l": 2, "gf": 78, "ga": 24, "pts": 78},
    {"pos": 2, "team": "Barcelona", "p": 32, "w": 23, "d": 5, "l": 4, "gf": 76, "ga": 28, "pts": 74},
    {"pos": 3, "team": "Atletico Madrid", "p": 32, "w": 20, "d": 7, "l": 5, "gf": 62, "ga": 32, "pts": 67},
    {"pos": 4, "team": "Villarreal", "p": 32, "w": 17, "d": 6, "l": 9, "gf": 58, "ga": 45, "pts": 57},
    {"pos": 5, "team": "Real Betis", "p": 32, "w": 15, "d": 5, "l": 12, "gf": 54, "ga": 52, "pts": 50},
    {"pos": 6, "team": "Real Sociedad", "p": 32, "w": 14, "d": 6, "l": 12, "gf": 50, "ga": 50, "pts": 48},
]

LA_LIGA_TOP_SCORERS = [
    {"rank": 1, "player": "Kylian Mbappe", "team": "Real Madrid", "goals": 28, "assists": 10, "xg": 26.8},
    {"rank": 2, "player": "Vinicius Junior", "team": "Real Madrid", "goals": 24, "assists": 8, "xg": 22.5},
    {"rank": 3, "player": "Robert Lewandowski", "team": "Barcelona", "goals": 22, "assists": 7, "xg": 21.3},
    {"rank": 4, "player": "Gavi", "team": "Barcelona", "goals": 18, "assists": 5, "xg": 17.2},
    {"rank": 5, "player": "Iago Aspas", "team": "Celta Vigo", "goals": 16, "assists": 4, "xg": 15.4},
]

# Mock Bundesliga table (example snapshot for UI/demo)
BUNDESLIGA_TABLE = [
    {"pos": 1, "team": "Bayern Munich", "p": 28, "w": 21, "d": 5, "l": 2, "gf": 68, "ga": 22, "pts": 68},
    {"pos": 2, "team": "Borussia Dortmund", "p": 28, "w": 19, "d": 4, "l": 5, "gf": 62, "ga": 32, "pts": 61},
    {"pos": 3, "team": "Bayer Leverkusen", "p": 28, "w": 17, "d": 5, "l": 6, "gf": 58, "ga": 36, "pts": 56},
    {"pos": 4, "team": "RB Leipzig", "p": 28, "w": 15, "d": 5, "l": 8, "gf": 54, "ga": 42, "pts": 50},
]

BUNDESLIGA_TOP_SCORERS = [
    {"rank": 1, "player": "Harry Kane", "team": "Bayern Munich", "goals": 28, "assists": 8, "xg": 26.5},
    {"rank": 2, "player": "Serge Gnabry", "team": "Bayern Munich", "goals": 18, "assists": 6, "xg": 17.2},
    {"rank": 3, "player": "Jamal Musiala", "team": "Bayern Munich", "goals": 15, "assists": 7, "xg": 14.8},
]

# Mock Serie A table (example snapshot for UI/demo)
SERIE_A_TABLE = [
    {"pos": 1, "team": "Napoli", "p": 30, "w": 23, "d": 5, "l": 2, "gf": 72, "ga": 26, "pts": 74},
    {"pos": 2, "team": "Inter", "p": 30, "w": 22, "d": 5, "l": 3, "gf": 70, "ga": 28, "pts": 71},
    {"pos": 3, "team": "Juventus", "p": 30, "w": 20, "d": 6, "l": 4, "gf": 65, "ga": 30, "pts": 66},
    {"pos": 4, "team": "AC Milan", "p": 30, "w": 18, "d": 5, "l": 7, "gf": 62, "ga": 38, "pts": 59},
]

SERIE_A_TOP_SCORERS = [
    {"rank": 1, "player": "Victor Osimhen", "team": "Napoli", "goals": 25, "assists": 5, "xg": 23.8},
    {"rank": 2, "player": "Lautaro Martinez", "team": "Inter", "goals": 22, "assists": 6, "xg": 21.2},
    {"rank": 3, "player": "Dusan Vlahovic", "team": "Juventus", "goals": 20, "assists": 3, "xg": 19.5},
]

# Mock Ligue 1 table (example snapshot for UI/demo)
LIGUE_1_TABLE = [
    {"pos": 1, "team": "PSG", "p": 32, "w": 24, "d": 6, "l": 2, "gf": 82, "ga": 22, "pts": 78},
    {"pos": 2, "team": "Marseille", "p": 32, "w": 20, "d": 5, "l": 7, "gf": 68, "ga": 38, "pts": 65},
    {"pos": 3, "team": "Lille", "p": 32, "w": 18, "d": 6, "l": 8, "gf": 62, "ga": 44, "pts": 60},
    {"pos": 4, "team": "Lyon", "p": 32, "w": 16, "d": 5, "l": 11, "gf": 56, "ga": 50, "pts": 53},
]

LIGUE_1_TOP_SCORERS = [
    {"rank": 1, "player": "Kylian Mbappe", "team": "PSG", "goals": 32, "assists": 12, "xg": 30.5},
    {"rank": 2, "player": "Pierre-Emerick Aubameyang", "team": "Marseille", "goals": 24, "assists": 6, "xg": 22.8},
    {"rank": 3, "player": "Ousmane Dembele", "team": "PSG", "goals": 21, "assists": 9, "xg": 19.5},
]

# Champions League Table (Knockout Stage)
UCL_TABLE = [
    {"pos": 1, "team": "Real Madrid", "p": 10, "w": 8, "d": 2, "l": 0, "gf": 28, "ga": 10, "pts": 26},
    {"pos": 2, "team": "Bayern Munich", "p": 10, "w": 7, "d": 2, "l": 1, "gf": 25, "ga": 12, "pts": 23},
    {"pos": 3, "team": "Liverpool", "p": 10, "w": 7, "d": 1, "l": 2, "gf": 24, "ga": 14, "pts": 22},
    {"pos": 4, "team": "Barcelona", "p": 10, "w": 6, "d": 2, "l": 2, "gf": 22, "ga": 15, "pts": 20},
    {"pos": 5, "team": "Man City", "p": 10, "w": 6, "d": 1, "l": 3, "gf": 21, "ga": 16, "pts": 19},
    {"pos": 6, "team": "Arsenal", "p": 10, "w": 5, "d": 2, "l": 3, "gf": 19, "ga": 18, "pts": 17},
    {"pos": 7, "team": "Inter", "p": 10, "w": 4, "d": 2, "l": 4, "gf": 16, "ga": 18, "pts": 14},
    {"pos": 8, "team": "PSG", "p": 10, "w": 3, "d": 1, "l": 6, "gf": 14, "ga": 22, "pts": 10},
]

UCL_TOP_SCORERS = [
    {"rank": 1, "player": "Kylian Mbappe", "team": "Real Madrid", "goals": 12, "assists": 4, "xg": 11.2},
    {"rank": 2, "player": "Harry Kane", "team": "Bayern Munich", "goals": 11, "assists": 2, "xg": 10.5},
    {"rank": 3, "player": "Mohamed Salah", "team": "Liverpool", "goals": 10, "assists": 3, "xg": 9.8},
    {"rank": 4, "player": "Vinicius Junior", "team": "Real Madrid", "goals": 9, "assists": 4, "xg": 8.6},
    {"rank": 5, "player": "Robert Lewandowski", "team": "Barcelona", "goals": 8, "assists": 2, "xg": 7.9},
]


def get_league_table(league: str) -> List[Dict]:
    """Get mock league table data."""
    league_map = {
        "epl": EPL_TABLE_2024_25,
        "EPL": EPL_TABLE_2024_25,
        "laliga": LA_LIGA_TABLE,
        "La Liga": LA_LIGA_TABLE,
        "bundesliga": BUNDESLIGA_TABLE,
        "Bundesliga": BUNDESLIGA_TABLE,
        "seriea": SERIE_A_TABLE,
        "Serie A": SERIE_A_TABLE,
        "ligue1": LIGUE_1_TABLE,
        "Ligue 1": LIGUE_1_TABLE,
        "ucl": UCL_TABLE,
        "Champions League": UCL_TABLE,
        "UCL": UCL_TABLE,
    }
    return league_map.get(league, [])


def get_top_scorers(league: str) -> List[Dict]:
    """Get mock top scorers data."""
    league_map = {
        "epl": EPL_TOP_SCORERS,
        "EPL": EPL_TOP_SCORERS,
        "laliga": LA_LIGA_TOP_SCORERS,
        "La Liga": LA_LIGA_TOP_SCORERS,
        "bundesliga": BUNDESLIGA_TOP_SCORERS,
        "Bundesliga": BUNDESLIGA_TOP_SCORERS,
        "seriea": SERIE_A_TOP_SCORERS,
        "Serie A": SERIE_A_TOP_SCORERS,
        "ligue1": LIGUE_1_TOP_SCORERS,
        "Ligue 1": LIGUE_1_TOP_SCORERS,
        "ucl": UCL_TOP_SCORERS,
        "Champions League": UCL_TOP_SCORERS,
        "UCL": UCL_TOP_SCORERS,
    }
    return league_map.get(league, [])


def get_live_matches() -> List[Dict]:
    """Get recent matches (mock)."""
    return [
        {
            "league": "EPL",
            "home_team": "Liverpool",
            "away_team": "Arsenal",
            "home_goals": 2,
            "away_goals": 1,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "COMPLETED"
        },
        {
            "league": "La Liga",
            "home_team": "Real Madrid",
            "away_team": "Barcelona",
            "home_goals": 3,
            "away_goals": 2,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "COMPLETED"
        },
        {
            "league": "Champions League",
            "home_team": "Real Madrid",
            "away_team": "Bayern Munich",
            "home_goals": 2,
            "away_goals": 0,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "COMPLETED"
        },
        {
            "league": "Ligue 1",
            "home_team": "PSG",
            "away_team": "Marseille",
            "home_goals": 3,
            "away_goals": 1,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "status": "COMPLETED"
        },
    ]


def get_featured_predictions() -> List[Dict]:
    """Get featured high-confidence predictions from upcoming matches (mock)."""
    return [
        {
            "match_id": "featured_1",
            "home_team": "Real Madrid",
            "away_team": "Man City",
            "league": "Champions League",
            "date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "kickoff_time": "20:00",
            "home_win_prob": 0.45,
            "draw_prob": 0.28,
            "away_win_prob": 0.27,
            "confidence": "HIGH"
        },
        {
            "match_id": "featured_2",
            "home_team": "Liverpool",
            "away_team": "Chelsea",
            "league": "EPL",
            "date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "kickoff_time": "15:00",
            "home_win_prob": 0.52,
            "draw_prob": 0.25,
            "away_win_prob": 0.23,
            "confidence": "HIGH"
        },
        {
            "match_id": "featured_3",
            "home_team": "PSG",
            "away_team": "Lille",
            "league": "Ligue 1",
            "date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "kickoff_time": "19:00",
            "home_win_prob": 0.68,
            "draw_prob": 0.18,
            "away_win_prob": 0.14,
            "confidence": "HIGH"
        },
    ]
