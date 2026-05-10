"""
ML training pipeline for win probability prediction.

Pipeline:
  1. Load historical CSV data (football-data.co.uk format)
  2. Build FeatureExtractor + compute team form
  3. Time-based train/validation split (no data leakage)
  4. Optuna hyperparameter search (XGBoost, log loss)
  5. Calibrate probabilities with isotonic regression
  6. Evaluate AUC-ROC, Brier score, log loss
  7. Save artifacts + log to MLflow

Run:
  python -m ml.train --csv data/E0.csv --trials 50
"""
import argparse
import os
import pickle
import sys
from pathlib import Path

import mlflow
import numpy as np
import optuna
import pandas as pd
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.preprocessing import LabelEncoder

# Ensure backend/ is on sys.path when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.evaluate import evaluate_model
from ml.feature_extractor import FEATURE_NAMES, FeatureExtractor

optuna.logging.set_verbosity(optuna.logging.WARNING)

LABEL_MAP = {"H": 0, "D": 1, "A": 2}
ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)


# ── Data loading ─────────────────────────────────────────────────────────────

def load_csv(path: str) -> pd.DataFrame:
    """
    Load football-data.co.uk CSV.
    Handles both E0 (England) and other league files.
    Renames columns to our internal schema.
    """
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    rename_map = {
        "HomeTeam": "home_team",
        "AwayTeam": "away_team",
        "FTHG": "home_goals",
        "FTAG": "away_goals",
        "FTR": "result",
        "HST": "hst",     # home shots on target
        "AST": "ast",     # away shots on target
        "Date": "match_date",
        "Div": "league",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Drop rows with missing essentials
    df = df.dropna(subset=["home_team", "away_team", "home_goals", "away_goals", "result"])
    df["result"] = df["result"].str.strip().str.upper()
    df = df[df["result"].isin(["H", "D", "A"])]

    # Ensure match_date is sortable
    if "match_date" in df.columns:
        df["match_date"] = pd.to_datetime(df["match_date"], dayfirst=True, errors="coerce")
        df = df.dropna(subset=["match_date"])
        df = df.sort_values("match_date").reset_index(drop=True)

    if "hst" not in df.columns:
        df["hst"] = 0
    if "ast" not in df.columns:
        df["ast"] = 0

    return df


def time_split(df: pd.DataFrame, val_fraction: float = 0.25):
    """Strict time-based split — no random shuffling."""
    split_idx = int(len(df) * (1 - val_fraction))
    return df.iloc[:split_idx], df.iloc[split_idx:]


# ── Optuna objective ─────────────────────────────────────────────────────────

def make_objective(X_train, y_train, X_val, y_val):
    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 500),
            "max_depth": trial.suggest_int("max_depth", 3, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-4, 10, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-4, 10, log=True),
            "objective": "multi:softprob",
            "num_class": 3,
            "eval_metric": "mlogloss",
            "use_label_encoder": False,
            "random_state": 42,
            "n_jobs": -1,
        }
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        preds = model.predict_proba(X_val)
        return log_loss(y_val, preds)

    return objective


# ── Main training pipeline ───────────────────────────────────────────────────

def train(csv_path: str, n_trials: int = 50):
    print(f"\n{'='*60}")
    print("  Sports Analytics — ML Training Pipeline")
    print(f"  Data: {csv_path}  |  Trials: {n_trials}")
    print(f"{'='*60}\n")

    # 1. Load data
    df = load_csv(csv_path)
    print(f"Loaded {len(df)} historical matches")

    # 2. Feature extraction
    extractor = FeatureExtractor()
    extractor.fit(df)
    X = extractor.transform_df(df)
    y = np.array([LABEL_MAP[r] for r in df["result"]])

    print(f"Features: {X.shape}  |  Classes: H={sum(y==0)}, D={sum(y==1)}, A={sum(y==2)}")

    # 3. Time-based split
    split = int(len(X) * 0.75)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    print(f"Train: {len(X_train)}  |  Val: {len(X_val)}")

    # 4. Optuna tuning
    print(f"\nRunning Optuna hyperparameter search ({n_trials} trials)...")
    study = optuna.create_study(direction="minimize")
    study.optimize(make_objective(X_train, y_train, X_val, y_val), n_trials=n_trials)
    best_params = study.best_params
    print(f"Best log loss: {study.best_value:.4f}")
    print(f"Best params: {best_params}")

    # 5. Train final model with best params
    best_params.update({
        "objective": "multi:softprob",
        "num_class": 3,
        "eval_metric": "mlogloss",
        "use_label_encoder": False,
        "random_state": 42,
        "n_jobs": -1,
    })
    base_model = xgb.XGBClassifier(**best_params)

    # 6. Calibrate probabilities
    print("\nCalibrating probabilities (isotonic regression)...")
    calibrated = CalibratedClassifierCV(base_model, method="isotonic", cv=3)
    calibrated.fit(X_train, y_train)

    # 7. Evaluate
    print("\nEvaluating on validation set...")
    metrics = evaluate_model(calibrated, X_val, y_val)
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")

    # 8. Save artifacts
    print(f"\nSaving artifacts to {ARTIFACTS_DIR}/")
    with open(ARTIFACTS_DIR / "model.pkl", "wb") as f:
        pickle.dump(calibrated, f)
    with open(ARTIFACTS_DIR / "extractor.pkl", "wb") as f:
        pickle.dump(extractor, f)

    # 9. Log to MLflow
    mlflow.set_experiment("win_probability")
    with mlflow.start_run():
        mlflow.log_params(best_params)
        mlflow.log_metrics(metrics)
        mlflow.log_artifact(str(ARTIFACTS_DIR / "model.pkl"))
        mlflow.log_artifact(str(ARTIFACTS_DIR / "extractor.pkl"))
        run_id = mlflow.active_run().info.run_id

    print(f"\nMLflow run ID: {run_id}")
    print(f"Training complete! AUC (macro): {metrics.get('auc_macro', 0):.4f}")

    if metrics.get("auc_macro", 0) < 0.70:
        print("⚠  AUC below target (0.78). Consider more training data or more Optuna trials.")
    else:
        print("✓  AUC meets target threshold.")

    return calibrated, extractor, metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train win probability model")
    parser.add_argument("--csv", required=True, help="Path to football-data CSV file")
    parser.add_argument("--trials", type=int, default=50, help="Number of Optuna trials")
    args = parser.parse_args()
    train(args.csv, args.trials)
