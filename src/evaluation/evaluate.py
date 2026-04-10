import pandas as pd
import numpy as np
import os
from pathlib import Path
from sklearn.metrics import log_loss, f1_score, roc_auc_score, brier_score_loss, confusion_matrix, accuracy_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib
from sklearn.calibration import calibration_curve

try:
    import shap  # type: ignore
except Exception:  # pragma: no cover
    shap = None  # type: ignore

from src.features.columns import FEATURE_COLUMNS, TARGET_MAP


def _require_ml_extras() -> None:
    if shap is None:
        raise RuntimeError(
            "PitchIQ evaluation requires the optional 'ml' extra. Install it with 'poetry install --extras ml'."
        )


def _normalize_proba(y_pred_proba: np.ndarray) -> np.ndarray:
    """Ensure class probabilities are well-formed (rows sum to 1).

    Some models return float32 probabilities where row sums can drift slightly,
    which triggers noisy sklearn warnings (and breaks per-row log loss loops).
    """
    proba = np.asarray(y_pred_proba, dtype=np.float64)
    if proba.ndim != 2:
        raise ValueError(f"Expected 2D proba array, got shape={proba.shape}")

    row_sums = proba.sum(axis=1, keepdims=True)
    zero_rows = (row_sums.squeeze(axis=1) == 0)
    if np.any(zero_rows):
        proba[zero_rows] = 1.0 / proba.shape[1]
        row_sums = proba.sum(axis=1, keepdims=True)

    proba = proba / row_sums

    # Numerical guardrails: clip and renormalize so rows still sum to 1.
    proba = np.clip(proba, 1e-15, 1 - 1e-15)
    proba = proba / proba.sum(axis=1, keepdims=True)
    return proba


def load_model_and_data():
    # Load model from environment or default path
    _env_model_path = os.getenv("MODEL_PATH")
    model_path = Path(_env_model_path) if _env_model_path else Path('models/ensemble_v1.pkl')
    
    if not model_path.exists():
        print('Model not found, training...')
        from src.training.train import main as train_main
        train_main()
    model = joblib.load(model_path)

    # Load enhanced features from environment or default path
    _env_features_path = os.getenv("FEATURES_PATH")
    fpath = Path(_env_features_path) if _env_features_path else Path('data/features/features_v2.parquet')
    if not fpath.exists():
        from src.features.build_features import main as build_features
        build_features()
    df = pd.read_parquet(fpath)
    df = df.sort_values('date')

    # Encode target with a stable mapping (A=0, D=1, H=2)
    df["target"] = df["FTR"].map(TARGET_MAP)
    df = df.dropna(subset=["target"]).copy()
    df["target"] = df["target"].astype(int)

    features = FEATURE_COLUMNS
    X = df[features]
    y = df['target']

    # If no explicit test season, use last 20% of data as temporal test split
    if 'season' in df.columns and df['season'].isin(['2324']).any():
        test_mask = df['season'] == '2324'
        X_train, X_test = X[~test_mask], X[test_mask]
        y_train, y_test = y[~test_mask], y[test_mask]
    else:
        split_idx = int(len(df) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    df_test = df.loc[X_test.index].copy()
    return model, X_train, X_test, y_train, y_test, features, df_test


def _fit_eval_model(model, X_train: pd.DataFrame, y_train: pd.Series):
    """Train a fresh model copy on the train split to avoid evaluation leakage."""
    try:
        cls = model.__class__
        params = model.get_params(deep=True) if hasattr(model, "get_params") else {}
        eval_model = cls(**params)
        eval_model.fit(X_train, y_train)
        return eval_model
    except Exception as exc:
        print(f"Warning: could not retrain a fresh eval model ({exc}). Using the loaded model (may be optimistic).")
        return model


def compute_metrics(y_true, y_pred_proba):
    y_pred_proba = _normalize_proba(y_pred_proba)
    # Log loss
    logloss = log_loss(y_true, y_pred_proba)

    # Macro F1
    y_pred = np.argmax(y_pred_proba, axis=1)
    f1 = f1_score(y_true, y_pred, average='macro')

    acc = accuracy_score(y_true, y_pred)

    # ROC-AUC per class (one-vs-rest)
    roc_auc = {}
    for i in range(3):
        y_binary = (y_true == i).astype(int)
        roc_auc[f'class_{i}'] = roc_auc_score(y_binary, y_pred_proba[:, i])

    # Brier score per class
    brier = {}
    for i in range(3):
        y_binary = (y_true == i).astype(int)
        brier[f'class_{i}'] = brier_score_loss(y_binary, y_pred_proba[:, i])

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)

    return {
        'log_loss': logloss,
        'macro_f1': f1,
        'accuracy': acc,
        'roc_auc': roc_auc,
        'brier': brier,
        'confusion_matrix': cm
    }


def plot_calibration(y_true, y_pred_proba, class_names=['Away', 'Draw', 'Home']):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for i, ax in enumerate(axes):
        prob_true, prob_pred = calibration_curve((y_true == i).astype(int), y_pred_proba[:, i], n_bins=10)
        ax.plot(prob_pred, prob_true, marker='o', label='Model')
        ax.plot([0, 1], [0, 1], linestyle='--', label='Perfectly calibrated')
        ax.set_title(f'{class_names[i]} Win Calibration')
        ax.set_xlabel('Predicted probability')
        ax.set_ylabel('Empirical probability')
        ax.legend()
    plt.tight_layout()
    Path('reports').mkdir(exist_ok=True)
    plt.savefig('reports/calibration_curves.png')
    plt.close()


def shap_analysis(model, X_test, features):
    if shap is None:
        print("SHAP is not installed; skipping SHAP analysis. Install the optional 'ml' extra to enable it.")
        return

    Path('reports').mkdir(exist_ok=True)
    # Handle both stacking and direct XGBoost models
    if hasattr(model, 'estimators_') and len(model.estimators_) > 1:
        xgb_model = model.estimators_[1]
    elif hasattr(model, 'get_booster') or model.__class__.__name__ in ['XGBClassifier', 'XGBRegressor']:
        xgb_model = model
    else:
        print('SHAP analysis: Unsupported model type, skipping')
        return

    explainer = shap.TreeExplainer(xgb_model)
    shap_values = explainer.shap_values(X_test)

    # Normalize SHAP return shapes across versions:
    # - list[class] -> (n_samples, n_features)
    # - ndarray -> (n_samples, n_features, n_classes)
    if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        shap_values_list = [shap_values[:, :, i] for i in range(shap_values.shape[2])]
    elif isinstance(shap_values, list):
        shap_values_list = shap_values
    else:
        shap_values_list = [shap_values]

    # Summary plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values_list, X_test, feature_names=features, show=False)
    plt.savefig('reports/shap_summary.png')
    plt.close()

    # Waterfall for first prediction
    class_idx = int(np.argmax(model.predict_proba(X_test.iloc[[0]]), axis=1)[0])
    values = shap_values_list[class_idx][0]
    base_value = explainer.expected_value[class_idx] if isinstance(explainer.expected_value, list) else explainer.expected_value
    exp = shap.Explanation(
        values=values,
        base_values=base_value,
        data=X_test.iloc[0].values,
        feature_names=features,
    )

    plt.figure()
    shap.plots.waterfall(exp, show=False)
    plt.savefig('reports/shap_waterfall.png')
    plt.close()


def failure_mode_analysis(y_true, y_pred_proba, df_test):
    y_pred_proba = _normalize_proba(y_pred_proba)
    y_pred = np.argmax(y_pred_proba, axis=1)

    # Per-row multiclass log loss is the negative log prob of the true class.
    y_true_arr = np.asarray(y_true, dtype=int)
    idx = np.arange(len(y_true_arr))
    losses = (-np.log(y_pred_proba[idx, y_true_arr])).tolist()

    df_test = df_test.copy()
    df_test['log_loss'] = losses
    df_test['pred_class'] = y_pred

    # Top 10 worst predictions
    worst = df_test.nlargest(10, 'log_loss')[['date', 'home_team', 'away_team', 'FTR', 'pred_class', 'log_loss']]

    return worst


def main() -> None:
    model, X_train, X_test, y_train, y_test, features, df_test = load_model_and_data()

    if len(X_test) == 0:
        print('No test data found for season 2324')
        return

    # Predictions (fit a fresh model on train split to avoid leakage)
    eval_model = _fit_eval_model(model, X_train, y_train)
    y_pred_proba = eval_model.predict_proba(X_test)

    # Metrics
    metrics = compute_metrics(y_test, y_pred_proba)
    print('Evaluation Metrics:')
    for k, v in metrics.items():
        if isinstance(v, dict):
            print(f'  {k}: {v}')
        elif k == 'confusion_matrix':
            print(f'  {k}:\n{v}')
        else:
            print(f'  {k}: {v:.4f}')

    # Calibration
    plot_calibration(y_test, y_pred_proba)

    # SHAP
    try:
        shap_analysis(eval_model, X_test, features)
    except Exception as e:
        print(f'SHAP analysis failed: {e}, skipping')

    # Failure modes
    failures = failure_mode_analysis(y_test, y_pred_proba, df_test)
    failures.to_csv('reports/failure_modes.csv', index=False)

    # Save metrics
    import json
    with open('reports/evaluation_metrics.json', 'w') as f:
        serializable = {}
        for k, v in metrics.items():
            if isinstance(v, np.ndarray):
                serializable[k] = v.tolist()
            else:
                serializable[k] = v
        serializable["n_train_rows"] = int(len(X_train))
        serializable["n_test_rows"] = int(len(X_test))
        serializable["timestamp_utc"] = pd.Timestamp.utcnow().isoformat()
        json.dump(serializable, f, indent=2)

    print('Evaluation completed. Reports saved to reports/')


if __name__ == '__main__':
    main()
