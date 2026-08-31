from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger("churn_api.prediction_service")

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "churn_pipeline.joblib"
METADATA_PATH = ARTIFACT_DIR / "metadata.json"

try:
    import shap

    _HAS_SHAP = True
except ImportError:
    _HAS_SHAP = False


class PredictionService:
    """Loads the trained pipeline + metadata once and serves predictions.

    Fails safe: if the artifact cannot be loaded, `is_ready` stays False
    and /health reports degraded rather than the process crashing, so a
    misconfigured deployment is diagnosable via /health instead of a
    silent 500 on every request.
    """

    def __init__(self) -> None:
        self.pipeline = None
        self.metadata: Optional[dict] = None
        self.is_ready = False
        self._load()

    def _load(self) -> None:
        try:
            self.pipeline = joblib.load(MODEL_PATH)
            with open(METADATA_PATH) as f:
                self.metadata = json.load(f)
            self.is_ready = True
            logger.info("Model artifact loaded: %s", self.metadata.get("model_name"))
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load model artifact: %s", exc)
            self.is_ready = False

    def _risk_level(self, probability: float) -> str:
        if probability < 0.33:
            return "Low"
        if probability < 0.66:
            return "Medium"
        return "High"

    def predict(self, features: dict) -> dict:
        if not self.is_ready:
            raise RuntimeError("Model is not loaded")

        feature_order = self.metadata["features"]
        row = pd.DataFrame([{k: features[k] for k in feature_order}])

        probability = float(self.pipeline.predict_proba(row)[0, 1])
        threshold = float(self.metadata["selected_threshold"])
        prediction = "Churn" if probability >= threshold else "No Churn"

        top_factors = self._local_factors(row)

        return {
            "prediction": prediction,
            "probability": round(probability, 4),
            "risk_level": self._risk_level(probability),
            "model_version": self.metadata["model_version"],
            "threshold_used": threshold,
            "top_factors": top_factors,
        }

    def _local_factors(self, row: pd.DataFrame, top_n: int = 5) -> list[dict]:
        model = self.pipeline.named_steps["model"]
        preprocessor = self.pipeline.named_steps["preprocessor"]
        feature_names = list(preprocessor.get_feature_names_out())
        X_t = preprocessor.transform(row)
        if hasattr(X_t, "toarray"):
            X_t = X_t.toarray()

        contribs = None
        if _HAS_SHAP:
            try:
                explainer = shap.LinearExplainer(model, X_t)
                contribs = np.asarray(explainer.shap_values(X_t)).ravel()
            except Exception:  # noqa: BLE001
                contribs = None

        if contribs is None and hasattr(model, "coef_"):
            contribs = model.coef_.ravel() * X_t.ravel()

        if contribs is None:
            return []

        ranked = sorted(zip(feature_names, contribs), key=lambda t: -abs(t[1]))[:top_n]
        return [
            {
                "feature": feat,
                "direction": "increases_risk" if val > 0 else "decreases_risk",
                "contribution": round(float(val), 4),
            }
            for feat, val in ranked
        ]


prediction_service = PredictionService()
