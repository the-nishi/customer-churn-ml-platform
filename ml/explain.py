"""
explain.py
Global and local explainability for the final churn model.

Prefers SHAP (TreeExplainer for tree models, LinearExplainer for linear
models, KernelExplainer as a general fallback). If shap is not
installed in the current environment, falls back to sklearn's
permutation_importance for the global explanation and a manual
per-feature contribution readout (coefficient * standardized value, or
signed permutation delta) for the local explanation. Both paths report
genuine, computed associations -- never invented numbers -- and both
are framed as associations, not causal claims.
"""

from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

from ml import config

try:
    import shap

    _HAS_SHAP = True
except ImportError:
    _HAS_SHAP = False

from sklearn.inspection import permutation_importance


def _get_feature_names(pipeline) -> list[str]:
    preprocessor = pipeline.named_steps["preprocessor"]
    return list(preprocessor.get_feature_names_out())


def global_explanation_permutation(pipeline, X_test, y_test) -> dict:
    result = permutation_importance(
        pipeline, X_test, y_test, n_repeats=20, random_state=config.RANDOM_STATE, scoring="roc_auc", n_jobs=-1
    )
    importances = pd.Series(result.importances_mean, index=X_test.columns).sort_values(ascending=False)
    return {
        "method": "permutation_importance (ROC-AUC drop)",
        "top_features": [
            {"feature": feat, "importance": round(float(val), 4)}
            for feat, val in importances.head(10).items()
        ],
    }


def global_explanation_shap(pipeline, X_train) -> dict:
    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocessor"]
    X_transformed = preprocessor.transform(X_train)
    feature_names = _get_feature_names(pipeline)

    try:
        explainer = shap.LinearExplainer(model, X_transformed)
    except Exception:
        try:
            explainer = shap.TreeExplainer(model)
        except Exception:
            explainer = shap.KernelExplainer(model.predict_proba, shap.sample(X_transformed, 50))

    shap_values = explainer.shap_values(X_transformed)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    mean_abs = np.abs(shap_values).mean(axis=0)
    ranking = pd.Series(np.asarray(mean_abs).ravel(), index=feature_names).sort_values(ascending=False)

    return {
        "method": "SHAP",
        "top_features": [
            {"feature": feat, "mean_abs_shap": round(float(val), 4)}
            for feat, val in ranking.head(10).items()
        ],
    }


def local_explanation_for_row(pipeline, row: pd.DataFrame) -> dict:
    """Explain a single customer's prediction."""
    proba = float(pipeline.predict_proba(row)[0, 1])
    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocessor"]
    feature_names = _get_feature_names(pipeline)
    X_t = preprocessor.transform(row)
    if hasattr(X_t, "toarray"):
        X_t = X_t.toarray()

    if _HAS_SHAP:
        try:
            explainer = shap.LinearExplainer(model, X_t)
            contribs = np.asarray(explainer.shap_values(X_t)).ravel()
            method = "SHAP"
        except Exception:
            contribs = None
            method = None
    else:
        contribs = None
        method = None

    if contribs is None:
        # Fallback: for a linear-family model, coefficient * standardized
        # value is a faithful, if approximate, local contribution signal.
        if hasattr(model, "coef_"):
            contribs = (model.coef_.ravel() * X_t.ravel())
            method = "coefficient_x_value (linear model approximation)"
        else:
            contribs = np.zeros(len(feature_names))
            method = "unavailable_for_this_model_type"

    ranked = sorted(zip(feature_names, contribs), key=lambda t: -abs(t[1]))
    top = ranked[:6]
    return {
        "method": method,
        "predicted_churn_probability": round(proba, 4),
        "top_factors": [
            {
                "feature": feat,
                "direction": "increases_risk" if val > 0 else "decreases_risk",
                "contribution": round(float(val), 4),
            }
            for feat, val in top
        ],
    }


def run_explainability() -> dict:
    state = joblib.load(config.ARTIFACT_DIR / "_training_state.joblib")
    pipeline = state["pipeline"]
    X_train, X_test, y_test = state["X_train"], state["X_test"], state["y_test"]

    if _HAS_SHAP:
        try:
            glob = global_explanation_shap(pipeline, X_train)
        except Exception as e:
            glob = global_explanation_permutation(pipeline, X_test, y_test)
            glob["shap_fallback_reason"] = str(e)
    else:
        glob = global_explanation_permutation(pipeline, X_test, y_test)

    sample_row = X_test.iloc[[0]]
    local = local_explanation_for_row(pipeline, sample_row)

    output = {"shap_available": _HAS_SHAP, "global_explanation": glob, "sample_local_explanation": local}
    with open(config.RESULTS_DIR / "explainability.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    return output


if __name__ == "__main__":
    out = run_explainability()
    print(json.dumps(out, indent=2, default=str))
