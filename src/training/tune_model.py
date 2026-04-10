import pandas as pd
import numpy as np
from pathlib import Path
import optuna
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import log_loss, make_scorer
from xgboost import XGBClassifier
import joblib


def load_data():
    """Load enhanced features with xG and advanced metrics."""
    fpath = Path('data/features/features_v2.parquet')
    if not fpath.exists():
        from src.features.build_features import main as build_features
        build_features()
    df = pd.read_parquet(fpath)
    df = df.sort_values('date')

    # Encode target
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    df['target'] = le.fit_transform(df['FTR'])

    # Enhanced features
    features = [
        'home_rolling_goals_scored_5', 'home_rolling_goals_conceded_5',
        'away_rolling_goals_scored_5', 'away_rolling_goals_conceded_5',
        'home_rolling_xg_scored_5', 'home_rolling_xg_conceded_5', 'home_rolling_xg_diff_5',
        'away_rolling_xg_scored_5', 'away_rolling_xg_conceded_5', 'away_rolling_xg_diff_5',
        'xg_total', 'xg_diff', 'xg_home_advantage', 'xg_away_advantage',
        'shots_total', 'shots_diff', 'shots_home_ratio', 'shots_away_ratio',
        'possession_diff', 'corners_total', 'corners_diff',
        'yellow_cards_total', 'yellow_cards_diff',
        'rolling_xg_scored_5_diff', 'rolling_xg_conceded_5_diff',
        'rolling_goals_scored_5_diff', 'rolling_goals_conceded_5_diff',
    ]
    X = df[features]
    y = df['target']

    return X, y


def objective(trial):
    """Optuna objective function for XGB hyperparameter tuning."""
    X, y = load_data()

    # Define hyperparameter search space
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'gamma': trial.suggest_float('gamma', 0, 5),
        'reg_alpha': trial.suggest_float('reg_alpha', 0, 10),
        'reg_lambda': trial.suggest_float('reg_lambda', 0, 10),
        'eval_metric': 'mlogloss',
        'use_label_encoder': False,
    }

    # Time series cross-validation
    tscv = TimeSeriesSplit(n_splits=3)
    scores = []

    for train_idx, val_idx in tscv.split(X):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        model = XGBClassifier(**params, random_state=42)
        model.fit(X_train, y_train)

        preds = model.predict_proba(X_val)
        score = log_loss(y_val, preds)
        scores.append(score)

    return np.mean(scores)


def main():
    """Run Optuna hyperparameter optimization."""
    print("Starting Optuna hyperparameter optimization for XGB...")

    # Create study
    study = optuna.create_study(direction='minimize', study_name='pitchiq_xgb_tuning')

    # Run optimization
    study.optimize(objective, n_trials=50, timeout=600)  # 50 trials or 10 minutes

    print("Optimization completed!")
    print(f"Best log_loss: {study.best_value:.4f}")
    print(f"Best parameters: {study.best_params}")

    # Train final model with best parameters
    X, y = load_data()
    best_params = study.best_params.copy()
    best_params.update({
        'eval_metric': 'mlogloss',
        'use_label_encoder': False,
        'random_state': 42
    })

    final_model = XGBClassifier(**best_params)
    final_model.fit(X, y)

    # Save tuned model
    Path('models').mkdir(exist_ok=True)
    joblib.dump(final_model, 'models/xgb_tuned.pkl')
    print("Tuned model saved to models/xgb_tuned.pkl")

    # Save study results
    study.trials_dataframe().to_csv('reports/optuna_study.csv', index=False)
    print("Study results saved to reports/optuna_study.csv")


if __name__ == '__main__':
    main()