import pandas as pd
import numpy as np
import hashlib
from typing import Dict, List, Optional

from src.domain.football import football_data_code, league_name, teams_for_league


def fetch_understat_data(season: str, league: str = 'EPL') -> pd.DataFrame:
    """
    Fetch match data from Understat API.

    For now, generates realistic synthetic data that matches Understat's xG distributions
    until proper API access is established.

    Args:
        season: Season year (e.g., '2023')
        league: League name ('EPL', 'La liga', 'Bundesliga', 'Serie A', 'Ligue 1')

    Returns:
        DataFrame with match data including xG statistics
    """
    league = league_name(league)
    print(f"Using synthetic Understat data for {league} {season} (API integration pending)")

    # For now, generate synthetic data based on football-data.co.uk results
    # This provides realistic xG values that correlate with actual match outcomes

    try:
        # Try to get base data from football-data.co.uk
        from .football_data import fetch_football_data

        league_code = football_data_code(league) or 'E0'
        base_df = fetch_football_data(season, league_code)

        if len(base_df) == 0:
            return _generate_synthetic_matches(season, league)

        # Add realistic xG data based on match outcomes
        enhanced_df = _add_synthetic_xg(base_df, league)

        return enhanced_df

    except Exception as e:
        print(f"Error with football-data base: {e}, using pure synthetic data")
        return _generate_synthetic_matches(season, league)


def _add_synthetic_xg(df: pd.DataFrame, league: str) -> pd.DataFrame:
    """
    Add realistic xG values based on match outcomes and league characteristics.
    """
    league = league_name(league)

    # League-specific xG averages (approximate real values)
    league_xg_avg = {
        'EPL': 1.35,
        'La Liga': 1.25,
        'Bundesliga': 1.45,
        'Serie A': 1.30,
        'Ligue 1': 1.40,
    }

    avg_xg = league_xg_avg.get(league, 1.35)

    rng = np.random.default_rng(42)  # For reproducibility

    xg_home = []
    xg_away = []
    shots_home = []
    shots_away = []
    shots_on_target_home = []
    shots_on_target_away = []
    corners_home = []
    corners_away = []
    fouls_home = []
    fouls_away = []
    yellow_cards_home = []
    yellow_cards_away = []
    red_cards_home = []
    red_cards_away = []
    possession_home = []
    possession_away = []

    for _, row in df.iterrows():
        home_goals = row['home_goals']
        away_goals = row['away_goals']

        # Base xG from league average with some randomness
        base_home = rng.normal(avg_xg, 0.3)
        base_away = rng.normal(avg_xg, 0.3)

        # Adjust based on actual goals (xG should correlate with goals)
        home_xg = max(0.1, base_home + (home_goals - away_goals) * 0.2 + rng.normal(0, 0.2))
        away_xg = max(0.1, base_away + (away_goals - home_goals) * 0.2 + rng.normal(0, 0.2))

        # Home advantage
        home_xg *= 1.1

        xg_home.append(round(home_xg, 2))
        xg_away.append(round(away_xg, 2))

        # Match stats loosely correlated with xG (synthetic)
        sh = int(max(1, rng.poisson(7 + home_xg * 5)))
        sa = int(max(1, rng.poisson(7 + away_xg * 5)))
        p_shot_home = float(np.clip(0.28 + 0.08 * (home_xg - 1.2), 0.18, 0.55))
        p_shot_away = float(np.clip(0.28 + 0.08 * (away_xg - 1.2), 0.18, 0.55))
        sot_h = int(rng.binomial(sh, p_shot_home))
        sot_a = int(rng.binomial(sa, p_shot_away))

        ch = int(max(0, rng.poisson(2 + sh * 0.2)))
        ca = int(max(0, rng.poisson(2 + sa * 0.2)))

        xg_diff = home_xg - away_xg
        fh = int(max(0, rng.poisson(10 + abs(xg_diff) * 2)))
        fa = int(max(0, rng.poisson(10 + abs(xg_diff) * 2)))

        yh = int(max(0, rng.poisson(1.2 + fh / 18)))
        ya = int(max(0, rng.poisson(1.3 + fa / 18)))
        rh = int(rng.binomial(1, 0.03 + min(0.02, yh * 0.002)))
        ra = int(rng.binomial(1, 0.03 + min(0.02, ya * 0.002)))

        base_pos = 52 + 10 * (xg_diff / (home_xg + away_xg + 0.25)) + rng.normal(0, 4)
        pos_h = float(np.clip(base_pos, 30, 70))
        pos_a = float(100 - pos_h)

        shots_home.append(sh)
        shots_away.append(sa)
        shots_on_target_home.append(sot_h)
        shots_on_target_away.append(sot_a)
        corners_home.append(ch)
        corners_away.append(ca)
        fouls_home.append(fh)
        fouls_away.append(fa)
        yellow_cards_home.append(yh)
        yellow_cards_away.append(ya)
        red_cards_home.append(rh)
        red_cards_away.append(ra)
        possession_home.append(round(pos_h, 1))
        possession_away.append(round(pos_a, 1))

    df = df.copy()
    df['xg_home'] = xg_home
    df['xg_away'] = xg_away
    df['shots_home'] = shots_home
    df['shots_away'] = shots_away
    df['shots_on_target_home'] = shots_on_target_home
    df['shots_on_target_away'] = shots_on_target_away
    df['corners_home'] = corners_home
    df['corners_away'] = corners_away
    df['fouls_home'] = fouls_home
    df['fouls_away'] = fouls_away
    df['yellow_cards_home'] = yellow_cards_home
    df['yellow_cards_away'] = yellow_cards_away
    df['red_cards_home'] = red_cards_home
    df['red_cards_away'] = red_cards_away
    df['possession_home'] = possession_home
    df['possession_away'] = possession_away

    # Add matchweek (synthetic)
    df['matchweek'] = ((df['date'] - df['date'].min()).dt.days // 7) + 1

    return df


def _generate_synthetic_matches(season: str, league: str) -> pd.DataFrame:
    """
    Generate completely synthetic match data with realistic xG distributions.
    """
    league = league_name(league)
    print(f"Generating synthetic {league} {season} data...")

    teams = teams_for_league(league)[:20]
    if not teams:
        teams = teams_for_league("EPL")[:20]

    matches = []
    match_id = 0

    seed = int.from_bytes(hashlib.md5(f"{season}-{league}".encode("utf-8")).digest()[:4], "little")
    rng = np.random.default_rng(seed)

    # Add persistent team strengths so rolling-form features are learnable.
    # This keeps the demo model from being "pure noise" in offline mode.
    league_xg_avg = {
        'EPL': 1.35,
        'La Liga': 1.25,
        'Bundesliga': 1.45,
        'Serie A': 1.30,
        'Ligue 1': 1.40,
    }
    base_xg = float(league_xg_avg.get(league, 1.35))

    # Log-space strengths (attack up, defense down) to keep xG positive and stable.
    team_attack = {t: float(rng.normal(0.0, 0.28)) for t in teams}
    team_defense = {t: float(rng.normal(0.0, 0.28)) for t in teams}
    # Extra persistent skill factors so goals aren't *only* a noisy function of xG.
    # This makes rolling goals + rolling xG jointly informative (more realistic and learnable).
    team_finishing = {t: float(rng.normal(0.0, 0.20)) for t in teams}
    team_goalkeeping = {t: float(rng.normal(0.0, 0.20)) for t in teams}
    home_adv = 0.12  # log-space home advantage

    # Generate round-robin matches
    for week in range(1, 39):  # 38 weeks
        # Shuffle teams for each week
        week_teams = teams.copy()
        rng.shuffle(week_teams)

        # Create 10 matches per week
        for i in range(0, len(week_teams), 2):
            if i + 1 < len(week_teams):
                home_team = week_teams[i]
                away_team = week_teams[i + 1]

                # Generate realistic match data (ensure positive xG)
                mu_home = np.log(base_xg) + team_attack[home_team] - team_defense[away_team] + home_adv
                mu_away = np.log(base_xg) + team_attack[away_team] - team_defense[home_team]
                home_mean = float(np.exp(mu_home))
                away_mean = float(np.exp(mu_away))

                home_xg = float(np.clip(rng.normal(home_mean, 0.25 * home_mean), 0.1, 4.5))
                away_xg = float(np.clip(rng.normal(away_mean, 0.25 * away_mean), 0.1, 4.5))

                # Generate goals from xG with persistent finishing/goalkeeping effects.
                # This helps avoid a "pure xG = goals" toy world while staying deterministic per team.
                conv = 0.8
                home_lambda = float(
                    max(0.05, home_xg * conv * np.exp(team_finishing[home_team] - team_goalkeeping[away_team]))
                )
                away_lambda = float(
                    max(0.05, away_xg * conv * np.exp(team_finishing[away_team] - team_goalkeeping[home_team]))
                )
                home_goals = int(rng.poisson(home_lambda))
                away_goals = int(rng.poisson(away_lambda))

                # Determine result
                if home_goals > away_goals:
                    ftr = 'H'
                elif away_goals > home_goals:
                    ftr = 'A'
                else:
                    ftr = 'D'

                # Generate proper date (spread matches across the season)
                month = ((week - 1) // 4) + 8  # Start from August (month 8)
                if month > 12:
                    month = month - 12 + 1  # Wrap to January next year
                day = int(rng.integers(1, 28))
                year = int(season) if month >= 8 else int(season) + 1

                sh = int(max(1, rng.poisson(7 + home_xg * 5)))
                sa = int(max(1, rng.poisson(7 + away_xg * 5)))
                p_shot_home = float(np.clip(0.28 + 0.08 * (home_xg - 1.2), 0.18, 0.55))
                p_shot_away = float(np.clip(0.28 + 0.08 * (away_xg - 1.2), 0.18, 0.55))
                sot_h = int(rng.binomial(sh, p_shot_home))
                sot_a = int(rng.binomial(sa, p_shot_away))

                ch = int(max(0, rng.poisson(2 + sh * 0.2)))
                ca = int(max(0, rng.poisson(2 + sa * 0.2)))

                xg_diff = home_xg - away_xg
                fh = int(max(0, rng.poisson(10 + abs(xg_diff) * 2)))
                fa = int(max(0, rng.poisson(10 + abs(xg_diff) * 2)))

                yh = int(max(0, rng.poisson(1.2 + fh / 18)))
                ya = int(max(0, rng.poisson(1.3 + fa / 18)))
                rh = int(rng.binomial(1, 0.03 + min(0.02, yh * 0.002)))
                ra = int(rng.binomial(1, 0.03 + min(0.02, ya * 0.002)))

                base_pos = 52 + 10 * (xg_diff / (home_xg + away_xg + 0.25)) + rng.normal(0, 4)
                pos_h = float(np.clip(base_pos, 30, 70))
                pos_a = float(100 - pos_h)

                match_data = {
                    'match_id': f"{season}_{league}_{match_id}",
                    'date': pd.Timestamp(f'{year}-{month:02d}-{day:02d}'),
                    'season': season,
                    'league': league,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_goals': home_goals,
                    'away_goals': away_goals,
                    'xg_home': round(home_xg, 2),
                    'xg_away': round(away_xg, 2),
                    'shots_home': sh,
                    'shots_away': sa,
                    'shots_on_target_home': sot_h,
                    'shots_on_target_away': sot_a,
                    'corners_home': ch,
                    'corners_away': ca,
                    'fouls_home': fh,
                    'fouls_away': fa,
                    'yellow_cards_home': yh,
                    'yellow_cards_away': ya,
                    'red_cards_home': rh,
                    'red_cards_away': ra,
                    'possession_home': round(pos_h, 1),
                    'possession_away': round(pos_a, 1),
                    'FTR': ftr,
                    'matchweek': week
                }

                matches.append(match_data)
                match_id += 1

    df = pd.DataFrame(matches)
    return df


def _calculate_ftr(home_goals: str, away_goals: str) -> str:
    """Calculate Full Time Result from goals"""
    try:
        h_goals = int(home_goals) if home_goals else 0
        a_goals = int(away_goals) if away_goals else 0

        if h_goals > a_goals:
            return 'H'
        elif a_goals > h_goals:
            return 'A'
        else:
            return 'D'
    except (ValueError, TypeError):
        return 'D'  # Default to draw if parsing fails


def fetch_understat_team_stats(season: str, league: str = 'EPL') -> pd.DataFrame:
    """
    Fetch team statistics from Understat.

    Returns team-level stats like xG, xGA, etc.
    """
    # Placeholder for future implementation
    return pd.DataFrame()


def fetch_understat_player_stats(season: str, league: str = 'EPL') -> pd.DataFrame:
    """
    Fetch player statistics from Understat.

    Returns player-level stats like xG, xA, shots, etc.
    """
    # Placeholder for future implementation
    return pd.DataFrame()
