"""Data leakage validation script - run after building features."""
import pandas as pd
import numpy as np
from pathlib import Path


def validate_feature_store_temporal_order():
    """Validate that feature store maintains temporal order and has no leakage."""
    features_path = Path("data/features/features_v2.parquet")
    
    if not features_path.exists():
        print("⚠️  Feature store not found at data/features/features_v2.parquet")
        print("   Run: python -m src.features.build_features")
        return False
    
    print("=" * 70)
    print("  DATA LEAKAGE VALIDATION")
    print("=" * 70)
    print()
    
    df = pd.read_parquet(features_path)
    print(f"📊 Loaded {len(df)} matches from feature store")
    print()
    
    all_good = True
    
    # Check 1: Temporal ordering
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        
        # Check per league
        for league in df['league'].unique():
            league_df = df[df['league'] == league].copy()
            dates_sorted = league_df['date'].is_monotonic_increasing
            
            if not dates_sorted:
                print(f"❌ CRITICAL: {league} is not temporally sorted!")
                print("   This WILL cause data leakage in rolling windows.")
                all_good = False
            else:
                print(f"✅ {league:15} - Temporally sorted")
    
    print()
    
    # Check 2: First matches should have zero/NaN rolling stats
    print("Checking early-season stats (should be 0 or NaN)...")
    for team_col in ['home_team', 'away_team']:
        prefix = 'home_' if team_col == 'home_team' else 'away_'
        rolling_col = f'{prefix}rolling_goals_scored_5'
        
        if rolling_col in df.columns:
            first_matches = df.groupby(team_col).head(1)
            non_zero = (first_matches[rolling_col] > 0).sum()
            
            if non_zero > len(first_matches) * 0.1:  # Allow some tolerance
                print(f"⚠️  WARNING: {non_zero}/{len(first_matches)} first matches have non-zero {rolling_col}")
                print("   Expected: Most should be 0 (no history yet)")
                all_good = False
            else:
                print(f"✅ {rolling_col:40} - First matches correctly have no history")
    
    print()
    
    # Check 3: Validate shift worked (spot check)
    print("Spot-checking rolling window calculations...")
    if 'home_team' in df.columns and 'home_goals' in df.columns:
        # Pick a team with many matches
        team_counts = df['home_team'].value_counts()
        if len(team_counts) > 0:
            test_team = team_counts.index[0]
            team_df = df[df['home_team'] == test_team].sort_values('date').reset_index(drop=True)
            
            if len(team_df) >= 10:
                # Match 5 should have rolling avg of matches 0-4
                row_5 = team_df.iloc[5]
                actual_avg = team_df.iloc[0:5]['home_goals'].mean()
                rolling_avg = row_5.get('home_rolling_goals_scored_5', None)
                
                if rolling_avg is not None and not pd.isna(rolling_avg):
                    diff = abs(actual_avg - rolling_avg)
                    if diff < 0.01:
                        print(f"✅ Rolling calculation verified for {test_team}")
                        print(f"   Expected: {actual_avg:.2f}, Got: {rolling_avg:.2f}")
                    else:
                        print(f"❌ Rolling calculation mismatch for {test_team}")
                        print(f"   Expected avg of matches 0-4: {actual_avg:.2f}")
                        print(f"   Got: {rolling_avg:.2f}")
                        all_good = False
    
    print()
    print("=" * 70)
    if all_good:
        print("✅ NO DATA LEAKAGE DETECTED - Feature engineering is safe!")
    else:
        print("❌ POTENTIAL ISSUES FOUND - Review above warnings")
    print("=" * 70)
    print()
    
    return all_good


if __name__ == '__main__':
    result = validate_feature_store_temporal_order()
    exit(0 if result else 1)
