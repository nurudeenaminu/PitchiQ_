import pandas as pd
import numpy as np
from pathlib import Path
import json

from src.features.columns import FEATURE_COLUMNS
from src.domain.football import feature_build_leagues
from src.config import get_current_season, get_previous_season


def main() -> None:
    # Define leagues to process (shared canonical list)
    leagues = feature_build_leagues()
    
    # Get season from config instead of hardcoding
    current_season = get_current_season()
    previous_season = get_previous_season()
    
    all_dataframes = []
    
    for league_code, league_name in leagues:
        print(f"Processing {league_name}...")
        
        # Fetch base match data
        from src.ingestion.adapters.football_data import fetch_football_data
        from src.ingestion.adapters.understat import fetch_understat_data
        from src.ingestion.schemas import match_schema

        # Get basic match results
        try:
            base_df = fetch_football_data(previous_season, league_code)
        except Exception:
            base_df = pd.DataFrame()

        # Get enhanced data with xG from Understat & additional metrics from FBref
        # Use year from previous season (e.g., "2023" for 2324 season)
        year = "20" + previous_season[:2]
        xg_df = fetch_understat_data(year, league_name)
        from src.ingestion.adapters.fbref import fetch_fbref_data
        fbref_df = fetch_fbref_data(year, league_name)

        # Merge on row index as a fallback for synthetic sources
        if len(base_df) > 0 and len(xg_df) > 0:
            merged_df = _merge_match_data(base_df, xg_df, fbref_df)
        elif len(xg_df) > 0:
            merged_df = xg_df
        elif len(base_df) > 0:
            merged_df = base_df
        else:
            merged_df = fbref_df

        if len(merged_df) == 0:
            print(f"No data available for {league_name}, skipping...")
            continue

        validated = match_schema.validate(merged_df, lazy=True)
        df = validated.sort_values('date')
        
        all_dataframes.append(df)
    
    if not all_dataframes:
        print("No data available for any league")
        return
    
    # Combine all leagues
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    # Create features for both home and away perspectives
    home_features = _create_team_features(combined_df, is_home=True)
    away_features = _create_team_features(combined_df, is_home=False)

    # Merge home and away features
    final_df = pd.merge(
        combined_df,
        home_features.add_prefix('home_'),
        left_index=True,
        right_index=True,
        how='left'
    )
    final_df = pd.merge(
        final_df,
        away_features.add_prefix('away_'),
        left_index=True,
        right_index=True,
        how='left'
    )

    # Add advanced features (P7: Enhanced Features)
    final_df = _add_advanced_features(final_df)

    out_dir = Path('data/features')
    out_dir.mkdir(parents=True, exist_ok=True)
    final_df.to_parquet(out_dir / 'features_v2.parquet', index=False)
    print(f'Feature build completed: {final_df.shape}')

    # Persist a small build report for the dashboard/ops page.
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    report = {
        "rows": int(len(final_df)),
        "columns": int(final_df.shape[1]),
        "n_model_features": int(len(FEATURE_COLUMNS)),
        "null_rate": float(final_df.isna().mean().mean()) if len(final_df) else 0.0,
        "date_min": str(final_df["date"].min()) if "date" in final_df.columns and len(final_df) else None,
        "date_max": str(final_df["date"].max()) if "date" in final_df.columns and len(final_df) else None,
        "leagues": sorted(final_df["league"].dropna().astype(str).unique().tolist()) if "league" in final_df.columns else [],
        "timestamp_utc": pd.Timestamp.utcnow().isoformat(),
    }
    with open(reports_dir / "features_metrics.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def _merge_match_data(base_df: pd.DataFrame, xg_df: pd.DataFrame, fbref_df: pd.DataFrame) -> pd.DataFrame:
    """Merge football-data, Understat, and FBref by a stable match key (no index-alignment)."""
    merged = base_df.copy()

    def _merge_extras(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
        if right is None or right.empty:
            return left

        if 'match_id' in left.columns and 'match_id' in right.columns:
            join_cols = ['match_id']
        else:
            join_cols = None
            candidates = [
                ['date', 'home_team', 'away_team', 'league'],
                ['date', 'home_team', 'away_team'],
            ]
            for cols in candidates:
                if all(c in left.columns for c in cols) and all(c in right.columns for c in cols):
                    join_cols = cols
                    break

        if join_cols is None:
            return left

        left = left.copy()
        right = right.copy()
        if 'date' in join_cols:
            left['date'] = pd.to_datetime(left['date'], errors='coerce')
            right['date'] = pd.to_datetime(right['date'], errors='coerce')

        extras = [c for c in right.columns if c not in join_cols and c not in left.columns]
        if not extras:
            return left

        right_dedup = right[join_cols + extras].drop_duplicates(subset=join_cols, keep='last')
        return pd.merge(left, right_dedup, on=join_cols, how='left')

    merged = _merge_extras(merged, xg_df)
    merged = _merge_extras(merged, fbref_df)
    return merged


def _create_team_features(df: pd.DataFrame, is_home: bool) -> pd.DataFrame:
    """Create rolling features for a team perspective."""
    team_col = 'home_team' if is_home else 'away_team'
    goals_scored_col = 'home_goals' if is_home else 'away_goals'
    goals_conceded_col = 'away_goals' if is_home else 'home_goals'
    xg_scored_col = 'xg_home' if is_home else 'xg_away'
    xg_conceded_col = 'xg_away' if is_home else 'xg_home'
    shots_for_col = 'shots_home' if is_home else 'shots_away'
    shots_against_col = 'shots_away' if is_home else 'shots_home'
    corners_for_col = 'corners_home' if is_home else 'corners_away'
    corners_against_col = 'corners_away' if is_home else 'corners_home'
    yellow_for_col = 'yellow_cards_home' if is_home else 'yellow_cards_away'
    yellow_against_col = 'yellow_cards_away' if is_home else 'yellow_cards_home'
    possession_for_col = 'possession_home' if is_home else 'possession_away'

    group_cols = ['league', team_col] if 'league' in df.columns else [team_col]

    def _shifted_rolling_mean(series: pd.Series, window: int = 5) -> pd.Series:
        """Calculate rolling mean using only PAST matches (no data leakage).
        
        Uses shift(1) to ensure the current match is never included in the statistic.
        For match i, we calculate the mean of matches [i-window, i-1].
        """
        s = pd.to_numeric(series, errors='coerce')
        # CRITICAL: shift(1) moves everything down by 1 row, so row i gets stats from i-1 and earlier
        return s.shift(1).rolling(window, min_periods=1).mean()

    # Basic goal-based features (pre-match; use only past matches)
    rolling_goals_scored_5 = df.groupby(group_cols)[goals_scored_col].transform(_shifted_rolling_mean)
    rolling_goals_conceded_5 = df.groupby(group_cols)[goals_conceded_col].transform(_shifted_rolling_mean)

    # xG-based features (if available)
    if xg_scored_col in df.columns:
        rolling_xg_scored_5 = df.groupby(group_cols)[xg_scored_col].transform(_shifted_rolling_mean)
        rolling_xg_conceded_5 = df.groupby(group_cols)[xg_conceded_col].transform(_shifted_rolling_mean)
    else:
        rolling_xg_scored_5 = pd.Series([0.0] * len(df), index=df.index)
        rolling_xg_conceded_5 = pd.Series([0.0] * len(df), index=df.index)

    rolling_xg_diff_5 = rolling_xg_scored_5 - rolling_xg_conceded_5

    # Rolling match-stat features (pre-match; derived from past matches only)
    if shots_for_col in df.columns and shots_against_col in df.columns:
        rolling_shots_for_5 = df.groupby(group_cols)[shots_for_col].transform(_shifted_rolling_mean)
        rolling_shots_against_5 = df.groupby(group_cols)[shots_against_col].transform(_shifted_rolling_mean)
    else:
        rolling_shots_for_5 = pd.Series([0.0] * len(df), index=df.index)
        rolling_shots_against_5 = pd.Series([0.0] * len(df), index=df.index)

    if corners_for_col in df.columns and corners_against_col in df.columns:
        rolling_corners_for_5 = df.groupby(group_cols)[corners_for_col].transform(_shifted_rolling_mean)
        rolling_corners_against_5 = df.groupby(group_cols)[corners_against_col].transform(_shifted_rolling_mean)
    else:
        rolling_corners_for_5 = pd.Series([0.0] * len(df), index=df.index)
        rolling_corners_against_5 = pd.Series([0.0] * len(df), index=df.index)

    if yellow_for_col in df.columns and yellow_against_col in df.columns:
        rolling_yellow_for_5 = df.groupby(group_cols)[yellow_for_col].transform(_shifted_rolling_mean)
        rolling_yellow_against_5 = df.groupby(group_cols)[yellow_against_col].transform(_shifted_rolling_mean)
    else:
        rolling_yellow_for_5 = pd.Series([0.0] * len(df), index=df.index)
        rolling_yellow_against_5 = pd.Series([0.0] * len(df), index=df.index)

    if possession_for_col in df.columns:
        rolling_possession_for_5 = df.groupby(group_cols)[possession_for_col].transform(_shifted_rolling_mean)
    else:
        rolling_possession_for_5 = pd.Series([0.0] * len(df), index=df.index)

    # Combine features
    features = pd.DataFrame({
        'rolling_goals_scored_5': rolling_goals_scored_5,
        'rolling_goals_conceded_5': rolling_goals_conceded_5,
        'rolling_xg_scored_5': rolling_xg_scored_5,
        'rolling_xg_conceded_5': rolling_xg_conceded_5,
        'rolling_xg_diff_5': rolling_xg_diff_5,
        'rolling_shots_for_5': rolling_shots_for_5,
        'rolling_shots_against_5': rolling_shots_against_5,
        'rolling_corners_for_5': rolling_corners_for_5,
        'rolling_corners_against_5': rolling_corners_against_5,
        'rolling_yellow_cards_for_5': rolling_yellow_for_5,
        'rolling_yellow_cards_against_5': rolling_yellow_against_5,
        'rolling_possession_for_5': rolling_possession_for_5,
    }).fillna(0.0)

    return features


def _add_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add advanced features for P7: Enhanced Features.
    
    IMPORTANT: These features are derived from PRE-MATCH rolling statistics only.
    They do NOT use any information from the current match being predicted.
    All inputs are already shifted (from _create_team_features), ensuring no data leakage.
    """
    df = df.copy()

    # Derived match-level features from pre-match rolling stats (avoids leakage)
    home_xg_scored = df.get('home_rolling_xg_scored_5', 0.0)
    home_xg_conceded = df.get('home_rolling_xg_conceded_5', 0.0)
    away_xg_scored = df.get('away_rolling_xg_scored_5', 0.0)
    away_xg_conceded = df.get('away_rolling_xg_conceded_5', 0.0)

    home_xg_est = 0.5 * (home_xg_scored + away_xg_conceded)
    away_xg_est = 0.5 * (away_xg_scored + home_xg_conceded)
    df['xg_total'] = home_xg_est + away_xg_est
    df['xg_diff'] = home_xg_est - away_xg_est
    denom_xg = df['xg_total'].replace(0, np.nan)
    df['xg_home_advantage'] = (home_xg_est / denom_xg).fillna(0.5)
    df['xg_away_advantage'] = (away_xg_est / denom_xg).fillna(0.5)

    home_shots_for = df.get('home_rolling_shots_for_5', 0.0)
    home_shots_against = df.get('home_rolling_shots_against_5', 0.0)
    away_shots_for = df.get('away_rolling_shots_for_5', 0.0)
    away_shots_against = df.get('away_rolling_shots_against_5', 0.0)

    home_shots_est = 0.5 * (home_shots_for + away_shots_against)
    away_shots_est = 0.5 * (away_shots_for + home_shots_against)
    df['shots_total'] = home_shots_est + away_shots_est
    df['shots_diff'] = home_shots_est - away_shots_est
    denom_shots = df['shots_total'].replace(0, np.nan)
    df['shots_home_ratio'] = (home_shots_est / denom_shots).fillna(0.5)
    df['shots_away_ratio'] = (away_shots_est / denom_shots).fillna(0.5)

    df['possession_diff'] = df.get('home_rolling_possession_for_5', 0.0) - df.get('away_rolling_possession_for_5', 0.0)

    home_corners_for = df.get('home_rolling_corners_for_5', 0.0)
    home_corners_against = df.get('home_rolling_corners_against_5', 0.0)
    away_corners_for = df.get('away_rolling_corners_for_5', 0.0)
    away_corners_against = df.get('away_rolling_corners_against_5', 0.0)

    home_corners_est = 0.5 * (home_corners_for + away_corners_against)
    away_corners_est = 0.5 * (away_corners_for + home_corners_against)
    df['corners_total'] = home_corners_est + away_corners_est
    df['corners_diff'] = home_corners_est - away_corners_est

    home_yellow_for = df.get('home_rolling_yellow_cards_for_5', 0.0)
    home_yellow_against = df.get('home_rolling_yellow_cards_against_5', 0.0)
    away_yellow_for = df.get('away_rolling_yellow_cards_for_5', 0.0)
    away_yellow_against = df.get('away_rolling_yellow_cards_against_5', 0.0)

    home_yellow_est = 0.5 * (home_yellow_for + away_yellow_against)
    away_yellow_est = 0.5 * (away_yellow_for + home_yellow_against)
    df['yellow_cards_total'] = home_yellow_est + away_yellow_est
    df['yellow_cards_diff'] = home_yellow_est - away_yellow_est

    # Rolling differentials (recent form differences)
    rolling_cols = [
        'rolling_xg_scored_5', 'rolling_xg_conceded_5',
        'rolling_goals_scored_5', 'rolling_goals_conceded_5'
    ]

    for col in rolling_cols:
        home_col = f'home_{col}'
        away_col = f'away_{col}'
        if home_col in df.columns and away_col in df.columns:
            df[f'{col}_diff'] = df[home_col] - df[away_col]

    return df.fillna(0.0)


if __name__ == '__main__':
    main()
