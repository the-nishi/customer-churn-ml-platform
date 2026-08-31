"""
evaluate.py
Runs threshold analysis on out-of-fold-style validation behavior, then
performs the ONE final evaluation against the untouched test set, and
saves the final inference pipeline + metadata artifact.
"""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone

import joblib
import numpy as np
import sklearn
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_predict, StratifiedKFold

from ml import config


def analyze_thresholds(pipeline, X_train, y_train) -> dict:
    """Threshold analysis using out-of-fold predictions on TRAINING data
    only (never the test set), so the chosen operating threshold is not
    optimized against data used for final evaluation."""
    cv = StratifiedKFold(n_splits=config.CV_FOLDS, shuffle=True, random_state=config.RANDOM_STATE)
    oof_proba = cross_val_predict(
        pipeline, X_train, y_train, cv=cv, method="predict_proba", n_jobs=-1
    )[:, 1]

    thresholds = np.round(np.arange(0.2, 0.71, 0.05), 2)
    rows = []
    for t in thresholds:
        preds = (oof_proba >= t).astype(int)
        rows.append(
            {
                "threshold": float(t),
                "precision": round(float(precision_score(y_train, preds, zero_division=0)), 4),
                "recall": round(float(recall_score(y_train, preds, zero_division=0)), 4),
                "f1": round(float(f1_score(y_train, preds, zero_division=0)), 4),
            }
        )

    # Business framing: missing a churner (false negative) is usually
    # costlier than a wasted retention offer (false positive), so we
    # bias slightly toward recall by picking the threshold that
    # maximizes F1 among thresholds with recall >= 0.6, falling back to
    # best-F1 overall if none qualify.
    qualifying = [r for r in rows if r["recall"] >= 0.6]
    pool = qualifying if qualifying else rows
    best = max(pool, key=lambda r: r["f1"])

    return {"threshold_grid": rows, "selected_threshold": best["threshold"], "selected_threshold_stats": best}


def final_test_evaluation(pipeline, X_test, y_test, threshold: float) -> dict:
    proba = pipeline.predict_proba(X_test)[:, 1]
    preds = (proba >= threshold).astype(int)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, preds)), 4),
        "precision": round(float(precision_score(y_test, preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, preds, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, preds, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
        "confusion_matrix": confusion_matrix(y_test, preds).tolist(),
        "classification_report": classification_report(y_test, preds, output_dict=True),
        "n_test_samples": int(len(y_test)),
    }
    return metrics


def run_evaluation() -> dict:
    state = joblib.load(config.ARTIFACT_DIR / "_training_state.joblib")
    pipeline = state["pipeline"]
    X_train, y_train = state["X_train"], state["y_train"]
    X_test, y_test = state["X_test"], state["y_test"]

    threshold_info = analyze_thresholds(pipeline, X_train, y_train)
    selected_threshold = threshold_info["selected_threshold"]

    # Refit tuned pipeline on the FULL training split (already done by
    # RandomizedSearchCV's refit=True during train.py, but pipeline
    # object here is the fitted best_estimator_, so it is already fit
    # on X_train/y_train -- no further fitting needed before test eval).
    test_metrics = final_test_evaluation(pipeline, X_test, y_test, selected_threshold)

    metadata = {
        "model_name": state["best_model_name"],
        "model_version": "1.0.0",
        "selected_threshold": selected_threshold,
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "features": state["features"],
        "test_metrics": test_metrics,
        "dataset_rows_used": int(len(X_train) + len(X_test)),
        "dataset_provenance": (
            "IBM Telco Customer Churn (github.com/IBM/telco-customer-churn-on-icp4d), "
            "253-row subset retrieved via automated fetch -- see ml/config.py for details"
        ),
        "library_versions": {
            "python": platform.python_version(),
            "scikit-learn": sklearn.__version__,
        },
    }

    joblib.dump(pipeline, config.MODEL_ARTIFACT_PATH)
    with open(config.METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    with open(config.RESULTS_DIR / "threshold_analysis.json", "w") as f:
        json.dump(threshold_info, f, indent=2, default=str)
    with open(config.RESULTS_DIR / "final_test_metrics.json", "w") as f:
        json.dump(test_metrics, f, indent=2, default=str)

    return {"threshold_info": threshold_info, "test_metrics": test_metrics, "metadata": metadata}


if __name__ == "__main__":
    out = run_evaluation()
    print(json.dumps(out, indent=2, default=str))
