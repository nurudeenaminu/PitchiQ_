try:
    import pandera.pandas as pa
    from pandera.pandas import Column, DataFrameSchema
except ModuleNotFoundError:
    import pandera as pa
    from pandera import Column, DataFrameSchema

match_schema = DataFrameSchema(
    {
        'match_id': Column(pa.String, nullable=False),
        'date': Column(pa.DateTime, nullable=False),
        'season': Column(pa.String, nullable=False),
        'league': Column(pa.String, nullable=False),
        'home_team': Column(pa.String, nullable=False),
        'away_team': Column(pa.String, nullable=False),
        'home_goals': Column(pa.Int, nullable=False),
        'away_goals': Column(pa.Int, nullable=False),
        'xg_home': Column(pa.Float, nullable=True, required=False),
        'xg_away': Column(pa.Float, nullable=True, required=False),
        'referee': Column(pa.String, nullable=True, required=False),
        'matchweek': Column(pa.Float, nullable=True, required=False),
        'FTR': Column(pa.String, nullable=False),
        # Understat additional columns
        'shots_home': Column(pa.Float, nullable=True, required=False),
        'shots_away': Column(pa.Float, nullable=True, required=False),
        'shots_on_target_home': Column(pa.Float, nullable=True, required=False),
        'shots_on_target_away': Column(pa.Float, nullable=True, required=False),
        'corners_home': Column(pa.Float, nullable=True, required=False),
        'corners_away': Column(pa.Float, nullable=True, required=False),
        'fouls_home': Column(pa.Float, nullable=True, required=False),
        'fouls_away': Column(pa.Float, nullable=True, required=False),
        'yellow_cards_home': Column(pa.Float, nullable=True, required=False),
        'yellow_cards_away': Column(pa.Float, nullable=True, required=False),
        'red_cards_home': Column(pa.Float, nullable=True, required=False),
        'red_cards_away': Column(pa.Float, nullable=True, required=False),
    },
    strict=False,  # Allow extra columns
    coerce=True,
)
