"""
train.py
Trains and compares 6 classification algorithms using stratified CV on a
leakage-safe preprocessing pipeline, then hyperparameter-tunes the best
candidate and selects a final model.

Library availability handling:
  - Prefers xgboost.XGBClassifier for the "boosting" model slot.
    Falls back to sklearn.GradientBoostingClassifier if xgboost is not
    installed in the current environment (logged clearly either way).
  - Prefers imbalanced-learn's Pipeline + SMOTE for the imbalance
    strategy. Falls back to class_weight="balanced" where SMOTE is
    unavailable.
This lets the SAME script run in a minimal offline environment and in
a fully-provisioned one (e.g. Railway with requirements.txt installed),
producing a real, reproducible result in both cases.
"""

from __future__ import annotations

import json
import time
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedKFold,
    cross_validate,
    train_test_split,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from ml import config
from ml.preprocessing import (
    TARGET_COLUMN,
    build_preprocessor,
    clean_raw,
    get_feature_columns,
    load_raw,
)

warnings.filterwarnings("ignore")

try:
    from xgboost import XGBClassifier

    _HAS_XGBOOST = True
except ImportError:
    _HAS_XGBOOST = False

try:
    from imblearn.over_sampling import SMOTE
    from imblearn.pipeline import Pipeline as ImbPipeline

    _HAS_IMBLEARN = True
except ImportError:
    _HAS_IMBLEARN = False


def get_candidate_models() -> dict:
    models = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=config.RANDOM_STATE
        ),
        "knn": KNeighborsClassifier(n_neighbors=15),
        "svm": SVC(
            probability=True, class_weight="balanced", random_state=config.RANDOM_STATE
        ),
        "decision_tree": DecisionTreeClassifier(
            class_weight="balanced", random_state=config.RANDOM_STATE, max_depth=6
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced",
            random_state=config.RANDOM_STATE,
            n_jobs=-1,
        ),
    }
    if _HAS_XGBOOST:
        models["xgboost"] = XGBClassifier(
            n_estimators=300,
            eval_metric="logloss",
            random_state=config.RANDOM_STATE,
        )
        boosting_key = "xgboost"
    else:
        models["gradient_boosting_fallback"] = GradientBoostingClassifier(
            n_estimators=300, random_state=config.RANDOM_STATE
        )
        boosting_key = "gradient_boosting_fallback"
    return models, boosting_key


def make_pipeline(estimator) -> Pipeline:
    preprocessor = build_preprocessor()
    if _HAS_IMBLEARN:
        return ImbPipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("smote", SMOTE(random_state=config.RANDOM_STATE)),
                ("model", estimator),
            ]
        )
    return Pipeline(steps=[("preprocessor", preprocessor), ("model", estimator)])


def run_training() -> dict:
    df = clean_raw(load_raw(str(config.RAW_DATA_PATH)))
    features = get_feature_columns()
    X = df[features]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.TEST_SIZE,
        stratify=y,
        random_state=config.RANDOM_STATE,
    )

    cv = StratifiedKFold(
        n_splits=config.CV_FOLDS, shuffle=True, random_state=config.RANDOM_STATE
    )
    scoring = ["roc_auc", "f1", "recall", "precision", "accuracy"]

    models, boosting_key = get_candidate_models()
    comparison = {}

    for name, estimator in models.items():
        pipe = make_pipeline(estimator)
        t0 = time.time()
        cv_results = cross_validate(
            pipe, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1
        )
        elapsed = time.time() - t0
        comparison[name] = {
            metric: {
                "mean": round(float(np.mean(cv_results[f"test_{metric}"])), 4),
                "std": round(float(np.std(cv_results[f"test_{metric}"])), 4),
            }
            for metric in scoring
        }
        comparison[name]["fit_time_seconds"] = round(elapsed, 2)

    # Select best candidate by mean CV ROC-AUC (a threshold-independent
    # ranking metric appropriate for an imbalanced binary target).
    best_name = max(comparison, key=lambda k: comparison[k]["roc_auc"]["mean"])

    # --- Hyperparameter tuning of the best candidate ---
    param_distributions = {
        "logistic_regression": {"model__C": [0.01, 0.1, 1, 10]},
        "knn": {"model__n_neighbors": [5, 11, 15, 21, 31]},
        "svm": {"model__C": [0.1, 1, 10], "model__kernel": ["rbf", "linear"]},
        "decision_tree": {"model__max_depth": [3, 4, 5, 6, 8, None]},
        "random_forest": {
            "model__n_estimators": [200, 300, 500],
            "model__max_depth": [None, 6, 10],
        },
        "xgboost": {
            "model__n_estimators": [200, 300, 500],
            "model__max_depth": [3, 4, 6],
            "model__learning_rate": [0.03, 0.1, 0.2],
        },
        "gradient_boosting_fallback": {
            "model__n_estimators": [200, 300, 500],
            "model__max_depth": [2, 3, 4],
            "model__learning_rate": [0.03, 0.1, 0.2],
        },
    }

    best_pipe = make_pipeline(models[best_name])
    search = RandomizedSearchCV(
        best_pipe,
        param_distributions=param_distributions.get(best_name, {}),
        n_iter=8,
        scoring="roc_auc",
        cv=cv,
        random_state=config.RANDOM_STATE,
        n_jobs=-1,
    )
    search.fit(X_train, y_train)
    tuned_pipeline = search.best_estimator_

    result = {
        "comparison": comparison,
        "best_model_by_cv_roc_auc": best_name,
        "boosting_model_used": boosting_key,
        "xgboost_available": _HAS_XGBOOST,
        "imblearn_available": _HAS_IMBLEARN,
        "best_params": search.best_params_,
        "best_cv_roc_auc": round(float(search.best_score_), 4),
    }

    with open(config.RESULTS_DIR / "model_comparison.json", "w") as f:
        json.dump(result, f, indent=2, default=str)

    # Persist split + tuned pipeline for the evaluate/explain stages.
    joblib.dump(
        {
            "pipeline": tuned_pipeline,
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
            "features": features,
            "best_model_name": best_name,
        },
        config.ARTIFACT_DIR / "_training_state.joblib",
    )

    return result


if __name__ == "__main__":
    res = run_training()
    print(json.dumps(res, indent=2, default=str))
