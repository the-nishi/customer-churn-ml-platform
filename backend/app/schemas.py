from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class CustomerFeatures(BaseModel):
    gender: Literal["Male", "Female"]
    SeniorCitizen: Literal["Yes", "No"]
    Partner: Literal["Yes", "No"]
    Dependents: Literal["Yes", "No"]
    tenure: int = Field(ge=0, le=100, description="Months as a customer")
    PhoneService: Literal["Yes", "No"]
    MultipleLines: Literal["Yes", "No", "No phone service"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: Literal["Yes", "No", "No internet service"]
    OnlineBackup: Literal["Yes", "No", "No internet service"]
    DeviceProtection: Literal["Yes", "No", "No internet service"]
    TechSupport: Literal["Yes", "No", "No internet service"]
    StreamingTV: Literal["Yes", "No", "No internet service"]
    StreamingMovies: Literal["Yes", "No", "No internet service"]
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: Literal["Yes", "No"]
    PaymentMethod: Literal[
        "Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"
    ]
    MonthlyCharges: float = Field(ge=0, le=1000)
    TotalCharges: float = Field(ge=0, le=100000)
    customer_reference: Optional[str] = Field(
        default=None, description="Optional label to identify this customer in prediction history"
    )


class ExplanationFactor(BaseModel):
    feature: str
    direction: Literal["increases_risk", "decreases_risk"]
    contribution: float


class PredictionResponse(BaseModel):
    prediction: Literal["Churn", "No Churn"]
    probability: float
    risk_level: Literal["Low", "Medium", "High"]
    model_version: str
    threshold_used: float
    top_factors: list[ExplanationFactor]


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    selected_threshold: float
    training_timestamp: str
    features: list[str]
    test_metrics: dict
    dataset_provenance: str


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    model_loaded: bool
    model_version: Optional[str] = None
