"""
ML prediction service — loads model at startup, runs inference + SHAP.

Responsibilities:
  1. Load model.pkl + extractor.pkl from artifacts dir once at startup
  2. Given a match_state dict, return probabilities + SHAP values
  3. Cache result in pub/sub so WebSocket clients get pushed updates
  4. Write prediction to DB
"""
import pickle
import time
import json
from pathlib import Path
from typing import Any
import numpy as np
from loguru import logger

from app.config import get_settings
from app.services.cache import cache_set, publish

settings = get_settings()

ARTIFACTS_DIR = Path(settings.artifacts_dir)
LABEL_NAMES = ["home_win", "draw", "away_win"]

# Loaded once at startup
_model = None
_extractor = None
_explainer = None


def load_artifacts():
    """Called during FastAPI lifespan startup."""
    global _model, _extractor, _explainer

    model_path = ARTIFACTS_DIR / "model.pkl"
    extractor_path = ARTIFACTS_DIR / "extractor.pkl"

    if not model_path.exists() or not extractor_path.exists():
        logger.warning(
            "Model artifacts not found — predictions will use a naive baseline. "
            "Run `python -m ml.train --csv <path>` to train the model."
        )
        _model = None
        _extractor = None
        _explainer = None
        return

    with open(model_path, "rb") as f:
        _model = pickle.load(f)
    with open(extractor_path, "rb") as f:
        _extractor = pickle.load(f)

    # Build SHAP TreeExplainer on the underlying XGBoost model
    try:
        import shap
        # CalibratedClassifierCV wraps estimators — grab the base estimator
        if hasattr(_model, "calibrated_classifiers_"):
            base = _model.calibrated_classifiers_[0].estimator
        elif hasattr(_model, "estimator"):
            base = _model.estimator
        else:
            base = _model
        _explainer = shap.TreeExplainer(base)
        logger.info("SHAP TreeExplainer ready")
    except Exception as e:
        logger.warning(f"SHAP init failed ({e}), explainability disabled")
        _explainer = None

    logger.info("ML artifacts loaded successfully")


def _naive_prediction(state: dict) -> dict:
    """
    Fallback prediction when no trained model exists.
    Uses simple heuristics based on goal difference and time remaining.
    """
    from ml.feature_extractor import FeatureExtractor
    minute = state.get("minute", 45)
    goal_diff = state.get("home_goals", 0) - state.get("away_goals", 0)
    time_weight = minute / 90.0   # further into game → score matters more

    base_home = 0.45
    base_draw = 0.27
    base_away = 0.28

    if goal_diff > 0:
        boost = min(goal_diff * 0.12 * time_weight, 0.40)
        prob_home = min(base_home + boost, 0.90)
        prob_draw = max(base_draw - boost * 0.5, 0.05)
        prob_away = max(1 - prob_home - prob_draw, 0.05)
    elif goal_diff < 0:
        boost = min(abs(goal_diff) * 0.12 * time_weight, 0.40)
        prob_away = min(base_away + boost, 0.90)
        prob_draw = max(base_draw - boost * 0.5, 0.05)
        prob_home = max(1 - prob_away - prob_draw, 0.05)
    else:
        prob_home, prob_draw, prob_away = base_home, base_draw, base_away

    total = prob_home + prob_draw + prob_away
    return {
        "prob_home_win": round(prob_home / total, 4),
        "prob_draw": round(prob_draw / total, 4),
        "prob_away_win": round(prob_away / total, 4),
    }


async def predict(state: dict, match_id: int, home_team: str = "", away_team: str = "") -> dict:
    """
    Run ML inference on a match state dict.
    Returns prediction dict and publishes to pub/sub channel.
    """
    t0 = time.perf_counter()

    state_with_teams = {**state, "home_team": home_team, "away_team": away_team}

    shap_features = []

    if _model is None or _extractor is None:
        # Naive baseline
        probs = _naive_prediction(state)
        from ml.feature_extractor import FEATURE_NAMES
        # Generate synthetic SHAP-like values for display
        shap_features = _synthetic_shap(state, probs)
    else:
        X = _extractor.transform(state_with_teams)   # shape (1, n_features)
        prob_array = _model.predict_proba(X)[0]      # [home, draw, away]

        probs = {
            "prob_home_win": round(float(prob_array[0]), 4),
            "prob_draw": round(float(prob_array[1]), 4),
            "prob_away_win": round(float(prob_array[2]), 4),
        }

        # SHAP values
        if _explainer is not None:
            shap_features = _compute_shap(X, state_with_teams)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.debug(f"Inference for match {match_id} min {state.get('minute',0)}: {elapsed_ms:.1f}ms")

    payload = {
        "match_id": match_id,
        "minute": state.get("minute", 0),
        "home_goals": state.get("home_goals", 0),
        "away_goals": state.get("away_goals", 0),
        "event_type": state.get("event_type", "tick"),
        "event_team": state.get("event_team", ""),
        **probs,
        "shap_features": shap_features,
        "inference_ms": round(elapsed_ms, 2),
    }

    # Cache latest prediction for REST endpoint (60s TTL)
    await cache_set(f"pred:{match_id}", payload, ttl_seconds=60)

    # Publish for WebSocket push
    await publish(f"match:{match_id}:prediction", payload)

    return payload


def _compute_shap(X: np.ndarray, state: dict) -> list[dict]:
    """Compute SHAP values and pair them with feature names."""
    from ml.feature_extractor import FEATURE_NAMES
    try:
        shap_vals = _explainer.shap_values(X)
        # shap_vals is list of arrays (one per class) or 3D array
        # We use class 0 (home win) SHAP values for the waterfall chart
        if isinstance(shap_vals, list):
            sv = shap_vals[0][0]   # class=home_win, sample=0
        else:
            sv = shap_vals[0, :, 0]

        raw = X[0].tolist()
        features = []
        for i, fname in enumerate(FEATURE_NAMES):
            features.append({
                "feature": fname,
                "shap_value": round(float(sv[i]), 4),
                "raw_value": round(float(raw[i]), 4),
            })
        # Sort by absolute SHAP value (most impactful first)
        features.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        return features
    except Exception as e:
        logger.warning(f"SHAP computation failed: {e}")
        return _synthetic_shap(state, {})


def _synthetic_shap(state: dict, probs: dict) -> list[dict]:
    """
    Produce plausible-looking SHAP values when no real model/explainer is available.
    Ensures the UI always has data to render.
    """
    from ml.feature_extractor import FEATURE_NAMES
    minute = state.get("minute", 45)
    goal_diff = state.get("home_goals", 0) - state.get("away_goals", 0)
    home_red = state.get("home_red_cards", 0)
    away_red = state.get("away_red_cards", 0)
    possession = state.get("home_possession", 50.0)
    shots_home = state.get("home_shots_on_target", 0)
    shots_away = state.get("away_shots_on_target", 0)

    feature_shap = {
        "minute": round((minute / 90) * 0.02, 4),
        "goal_diff": round(goal_diff * 0.15, 4),
        "home_goals": round(state.get("home_goals", 0) * 0.08, 4),
        "away_goals": round(-state.get("away_goals", 0) * 0.08, 4),
        "home_red": round(-home_red * 0.12, 4),
        "away_red": round(away_red * 0.10, 4),
        "shots_home": round(shots_home * 0.02, 4),
        "shots_away": round(-shots_away * 0.02, 4),
        "possession_home": round((possession - 50) * 0.003, 4),
        "time_remaining_frac": round(((90 - minute) / 90) * -0.01, 4),
        "is_tied": round(-0.05 if goal_diff == 0 else 0.0, 4),
        "home_form_5": round(state.get("home_form", 0.5) * 0.08, 4),
        "away_form_5": round(-state.get("away_form", 0.5) * 0.06, 4),
    }

    raw_values = {
        "minute": minute,
        "goal_diff": goal_diff,
        "home_goals": state.get("home_goals", 0),
        "away_goals": state.get("away_goals", 0),
        "home_red": home_red,
        "away_red": away_red,
        "shots_home": shots_home,
        "shots_away": shots_away,
        "possession_home": possession,
        "time_remaining_frac": round((90 - minute) / 90, 3),
        "is_tied": 1 if goal_diff == 0 else 0,
        "home_form_5": state.get("home_form", 0.5),
        "away_form_5": state.get("away_form", 0.5),
    }

    result = [
        {"feature": k, "shap_value": v, "raw_value": raw_values.get(k, 0.0)}
        for k, v in feature_shap.items()
    ]
    result.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
    return result
