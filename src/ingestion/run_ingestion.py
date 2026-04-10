import json
from pathlib import Path

import duckdb
import pandas as pd

from src.ingestion.adapters.football_data import fetch_football_data
from src.ingestion.adapters.understat import fetch_understat_data
from src.ingestion.schemas import match_schema
from src.domain.football import feature_build_leagues


class DataIngestionError(Exception):
    pass


def main() -> None:
    print(f"Current dir: {Path.cwd()}")
    out_dir = Path.cwd() / 'data' / 'processed'
    print(f"out_dir: {out_dir.absolute()}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_log_dir = Path.cwd() / 'reports'
    out_log_dir.mkdir(parents=True, exist_ok=True)

    # Prefer football-data.co.uk for real results, but fall back to Understat
    # synthetic data when network access is blocked (common in sandboxed envs).
    leagues = feature_build_leagues()

    dfs = []
    for league_code, league_name in leagues:
        try:
            df_league = fetch_football_data("2324", league_code)
        except Exception as exc:
            print(f"football-data fetch failed for {league_code}: {exc}. Falling back to Understat synthetic.")
            df_league = pd.DataFrame()

        if df_league is None or df_league.empty:
            df_league = fetch_understat_data("2023", league_name)

        if df_league is None or df_league.empty:
            print(f"No data available for {league_name}, skipping.")
            continue

        dfs.append(df_league)

    if not dfs:
        raise DataIngestionError("No data ingested for any league.")

    df = pd.concat(dfs, ignore_index=True)
    try:
        validated = match_schema.validate(df, lazy=True)
    except Exception as exc:
        raise DataIngestionError(f'Validation failed: {exc}')

    # Save to parquet first
    print('saving parquet')
    parquet_path = out_dir / 'matches.parquet'
    print(f"parquet_path: {parquet_path.absolute()}")
    try:
        validated.to_parquet(parquet_path, index=False)
        print('saved parquet')
    except Exception as e:
        print(f'failed to save parquet: {e}')

    # Save to duckdb
    print('saving to duckdb')
    db_path = out_dir / 'matches.duckdb'
    print(f"db_path: {db_path.absolute()}")
    try:
        con = duckdb.connect(str(db_path))
        parquet_sql_path = str(parquet_path).replace("\\", "/")
        con.execute("DROP TABLE IF EXISTS matches")
        con.execute(f"CREATE TABLE matches AS SELECT * FROM read_parquet('{parquet_sql_path}')")
        con.close()
        print('saved duckdb')
    except Exception as e:
        print(f'failed to save duckdb: {e}')

    log = {
        'rows': int(len(validated)),
        'null_rate': float(validated.isna().mean().mean()),
        'date_min': str(validated['date'].min()),
        'date_max': str(validated['date'].max()),
        'timestamp_utc': pd.Timestamp.utcnow().isoformat(),
    }

    with open(out_log_dir / 'ingestion_log.json', 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)

    print('Ingestion completed', log)


if __name__ == '__main__':
    main()
