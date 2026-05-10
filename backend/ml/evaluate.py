"""
Model evaluation utilities.
Computes AUC-ROC (one-vs-rest), Brier score, and log loss.
"""
import numpy as np
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.preprocessing import label_binarize


def brier_score_multiclass(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Multi-class Brier score (mean over classes)."""
    n_classes = y_prob.shape[1]
    y_bin = label_binarize(y_true, classes=list(range(n_classes)))
    return float(np.mean(np.sum((y_prob - y_bin) ** 2, axis=1)))


def evaluate_model(model, X_val: np.ndarray, y_val: np.ndarray) -> dict:
    """Return dict of all evaluation metrics."""
    y_prob = model.predict_proba(X_val)

    auc_macro = roc_auc_score(y_val, y_prob, multi_class="ovr", average="macro")
    auc_home = roc_auc_score((y_val == 0).astype(int), y_prob[:, 0])
    auc_draw = roc_auc_score((y_val == 1).astype(int), y_prob[:, 1])
    auc_away = roc_auc_score((y_val == 2).astype(int), y_prob[:, 2])
    brier = brier_score_multiclass(y_val, y_prob)
    ll = log_loss(y_val, y_prob)

    return {
        "auc_macro": auc_macro,
        "auc_home": auc_home,
        "auc_draw": auc_draw,
        "auc_away": auc_away,
        "brier_score": brier,
        "log_loss": ll,
    }
