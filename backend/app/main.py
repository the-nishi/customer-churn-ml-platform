from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    CustomerFeatures,
    HealthResponse,
    ModelInfoResponse,
    PredictionResponse,
)
from app.services.prediction_service import prediction_service
from app.services.supabase_service import persist_prediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("churn_api")

app = FastAPI(
    title="Customer Churn Prediction API",
    description="Explainable ML API for predicting customer churn risk on the IBM Telco Customer Churn schema.",
    version="1.0.0",
)

# CORS: restrict to the deployed frontend origin(s) in production via
# the FRONTEND_ORIGINS env var (comma-separated). Defaults to
# permissive localhost origins for local development only.
_origins_env = os.environ.get("FRONTEND_ORIGINS", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if prediction_service.is_ready else "degraded",
        model_loaded=prediction_service.is_ready,
        model_version=(prediction_service.metadata or {}).get("model_version") if prediction_service.is_ready else None,
    )


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    if not prediction_service.is_ready:
        raise HTTPException(status_code=503, detail="Model is not currently loaded.")
    meta = prediction_service.metadata
    return ModelInfoResponse(
        model_name=meta["model_name"],
        model_version=meta["model_version"],
        selected_threshold=meta["selected_threshold"],
        training_timestamp=meta["training_timestamp"],
        features=meta["features"],
        test_metrics=meta["test_metrics"],
        dataset_provenance=meta["dataset_provenance"],
    )


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: CustomerFeatures) -> PredictionResponse:
    if not prediction_service.is_ready:
        raise HTTPException(status_code=503, detail="Model is not currently loaded.")

    try:
        features = payload.model_dump(exclude={"customer_reference"})
        result = prediction_service.predict(features)
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=f"Missing required feature: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Prediction failed due to an internal error.") from exc

    persist_prediction(
        customer_reference=payload.customer_reference,
        prediction=result["prediction"],
        churn_probability=result["probability"],
        risk_level=result["risk_level"],
        model_version=result["model_version"],
    )

    return PredictionResponse(**result)
    @app.post("/predict-batch")
def predict_batch(customers: list[CustomerFeatures]):
    if not prediction_service.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Model is not currently loaded."
        )

    if not customers:
        raise HTTPException(
            status_code=400,
            detail="No customer data provided."
        )

    if len(customers) > 500:
        raise HTTPException(
            status_code=400,
            detail="Maximum 500 customers allowed per batch."
        )

    results = []

    for payload in customers:
        try:
            features = payload.model_dump(
                exclude={"customer_reference"}
            )

            result = prediction_service.predict(features)

            persist_prediction(
                customer_reference=payload.customer_reference,
                prediction=result["prediction"],
                churn_probability=result["probability"],
                risk_level=result["risk_level"],
                model_version=result["model_version"],
            )

            results.append({
                "customer_reference": payload.customer_reference,
                "prediction": result["prediction"],
                "probability": result["probability"],
                "risk_level": result["risk_level"],
                "model_version": result["model_version"],
            })

        except Exception as exc:
            logger.exception(
                "Batch prediction failed for customer %s",
                payload.customer_reference,
            )

            results.append({
                "customer_reference": payload.customer_reference,
                "error": str(exc),
            })

    return {
        "total": len(customers),
        "results": results,
    }
