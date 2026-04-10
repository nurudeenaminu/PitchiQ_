import pandas as pd
import numpy as np
from pathlib import Path
from contextlib import nullcontext
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import log_loss, f1_score, accuracy_score
from typing import Tuple

try:
    import mlflow  # type: ignore
    import mlflow.sklearn  # type: ignore
except Exception:  # pragma: no cover
    # Training can run without MLflow installed; logging is optional.
    mlflow = None  # type: ignore

from src.features.columns import FEATURE_COLUMNS, TARGET_MAP
import argparse
import os


def _mlflow_enabled() -> bool:
    """Return True when MLflow logging should be used."""
    if mlflow is None:
        return False
    return os.getenv("ENABLE_MLFLOW", "1") == "1"


def _mlflow_log_params(params: dict) -> None:
    """Best-effort MLflow params logging."""
    if not _mlflow_enabled():
        return
    try:
        mlflow.log_params(params)
    except Exception:
        pass


def _mlflow_log_metrics(metrics: dict) -> None:
    """Best-effort MLflow metrics logging."""
    if not _mlflow_enabled():
        return
    try:
        mlflow.log_metrics(metrics)
    except Exception:
        pass


def _mlflow_log_artifact(path: Path) -> None:
    """Best-effort MLflow artifact logging."""
    if not _mlflow_enabled() or not path.exists():
        return
    try:
        mlflow.log_artifact(str(path))
    except Exception:
        pass


def load_data():
    # Load enhanced features with xG data
    fpath = Path('data/features/features_v2.parquet')
    if not fpath.exists():
        from src.features.build_features import main as build_features
        build_features()
    df = pd.read_parquet(fpath)
    df = df.sort_values('date')

    # Encode target with a stable mapping (avoid LabelEncoder ordering surprises)
    # Convention used across API/eval: A=0, D=1, H=2
    df["target"] = df["FTR"].map(TARGET_MAP)
    df = df.dropna(subset=["target"]).copy()
    df["target"] = df["target"].astype(int)

    features = FEATURE_COLUMNS
    missing = [c for c in features if c not in df.columns]
    if missing:
        print(f"Warning: missing features filled with 0.0: {missing}")
    X = df.reindex(columns=features, fill_value=0.0)
    y = df['target']

    return X, y, df


def _temporal_split(
    X: pd.DataFrame, y: pd.Series, val_frac: float
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    if not (0.0 < val_frac < 1.0):
        raise ValueError("val_frac must be between 0 and 1")
    if len(X) != len(y):
        raise ValueError("X and y must have the same length")

    split_idx = int(len(X) * (1.0 - val_frac))
    split_idx = max(1, min(split_idx, len(X) - 1))
    return X.iloc[:split_idx], X.iloc[split_idx:], y.iloc[:split_idx], y.iloc[split_idx:]


def train_base_models(X, y):
    # Simple training without Optuna for now
    lr = LogisticRegression(C=0.1, max_iter=1000, random_state=42)
    lr.fit(X, y)

    xgb = XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.7,
        eval_metric='mlogloss',
        random_state=42,
    )
    xgb.fit(X, y)

    lgb = LGBMClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.7,
        metric='multi_logloss',
        random_state=42,
        verbose=-1,
    )
    lgb.fit(X, y)

    return [lr, xgb, lgb]


def train_stacked_model(oof_preds, y):
    meta = LogisticRegression(C=0.05, max_iter=1000, multi_class='multinomial')
    meta.fit(oof_preds, y)
    return meta


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--train-baselines",
        action="store_true",
        help="Train baseline models (LR/XGB/LGBM) for comparison. Default: off.",
    )
    p.add_argument(
        "--val-frac",
        type=float,
        default=0.2,
        help="Temporal holdout fraction used for reporting validation metrics. Default: 0.2.",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    run_ctx = nullcontext()
    if _mlflow_enabled():
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
        experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "pitchiq_training")
        try:
            if tracking_uri:
                mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(experiment_name)
            run_ctx = mlflow.start_run(run_name=f"train-{pd.Timestamp.utcnow():%Y%m%d-%H%M%S}")
        except Exception:
            run_ctx = nullcontext()

    with run_ctx:
        X, y, df = load_data()

        _mlflow_log_params(
            {
                "model_type": "XGBClassifier",
                "val_frac": float(args.val_frac),
                "train_baselines": bool(args.train_baselines or os.getenv("PITCHIQ_TRAIN_BASELINES") == "1"),
                "n_rows": int(len(X)),
                "n_features": int(X.shape[1]),
            }
        )

        # Baselines are optional; the main artifact is the tuned XGB below.
        # (Baseline training is fairly noisy and not required for serving.)
        if args.train_baselines or os.getenv("PITCHIQ_TRAIN_BASELINES") == "1":
            _ = train_base_models(X, y)

        # Use latest Optuna-tuned hyperparameters
        tuned_params = {
            'n_estimators': 111,
            'max_depth': 6,
            'learning_rate': 0.0453,
            'subsample': 0.7039,
            'colsample_bytree': 0.8101,
            'min_child_weight': 1,  # default
            'gamma': 1.8871,
            'reg_alpha': 0.8549,
            'reg_lambda': 4.3053,
            'eval_metric': 'mlogloss',
            'random_state': 42
        }
        xgb = XGBClassifier(**tuned_params)

        _mlflow_log_params({f"xgb_{k}": v for k, v in tuned_params.items()})

        # Report a simple temporal holdout metric (but still fit the final model on all data).
        X_tr, X_val, y_tr, y_val = _temporal_split(X, y, val_frac=float(args.val_frac))
        xgb.fit(X_tr, y_tr)
        val_probs = xgb.predict_proba(X_val)
        val_loss = log_loss(y_val, val_probs, labels=[0, 1, 2])
        val_pred = np.argmax(val_probs, axis=1)
        val_f1 = f1_score(y_val, val_pred, average="macro")
        val_acc = accuracy_score(y_val, val_pred)

        _mlflow_log_metrics(
            {
                "val_log_loss": float(val_loss),
                "val_macro_f1": float(val_f1),
                "val_accuracy": float(val_acc),
            }
        )

        print(f"Holdout metrics (val_frac={args.val_frac:.2f}): log_loss={val_loss:.4f} macro_f1={val_f1:.4f} acc={val_acc:.4f}")

        # Persist metrics for the dashboard (so UI can stay in sync with the pipeline).
        import json
        Path("reports").mkdir(exist_ok=True)
        training_metrics_path = Path("reports") / "training_metrics.json"
        with open(training_metrics_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "val_frac": float(args.val_frac),
                    "val_log_loss": float(val_loss),
                    "val_macro_f1": float(val_f1),
                    "val_accuracy": float(val_acc),
                    "n_rows": int(len(X)),
                    "n_features": int(X.shape[1]),
                    "timestamp_utc": pd.Timestamp.utcnow().isoformat(),
                },
                f,
                indent=2,
            )
        _mlflow_log_artifact(training_metrics_path)

        # Fit final model on full data for export
        xgb.fit(X, y)
        model_to_save = xgb

        # Log metrics (train set; mainly sanity-check)
        preds = model_to_save.predict_proba(X)
        loss = log_loss(y, preds, labels=[0, 1, 2])
        _mlflow_log_metrics({"train_log_loss": float(loss)})

        # Save model
        import joblib
        Path('models').mkdir(exist_ok=True)
        model_path = Path('models') / 'ensemble_v1.pkl'
        print(f'Saving model type: {type(model_to_save).__name__}')
        joblib.dump(model_to_save, model_path)

        if _mlflow_enabled():
            try:
                mlflow.sklearn.log_model(model_to_save, artifact_path="model")
            except Exception:
                pass
        _mlflow_log_artifact(model_path)

        print(f'Training completed. Log loss: {loss:.4f}')


if __name__ == '__main__':
    main()
