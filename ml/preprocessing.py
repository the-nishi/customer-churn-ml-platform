"""
preprocessing.py
Leakage-safe preprocessing pipeline for the Customer Churn dataset.

Design notes:
- customerID is dropped: it is a unique identifier with no predictive
  signal and including it risks the model memorizing rows instead of
  learning generalizable patterns.
- TotalCharges is shipped as a string in the raw IBM file and contains
  blank values for customers with tenure == 0 (brand-new customers who
  have not been billed yet). These are coerced to NaN and imputed.
- All transformations are fit ONLY on training data via sklearn's
  Pipeline/ColumnTransformer, then applied to validation/test data,
  which prevents leakage from those splits into preprocessing statistics.
"""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ID_COLUMN = "customerID"
TARGET_COLUMN = "Churn"

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]

CATEGORICAL_FEATURES = [
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]


def load_raw(path: str) -> pd.DataFrame:
    """Load the raw IBM Telco Customer Churn CSV."""
    df = pd.read_csv(path)
    return df


def clean_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Type-fix known quirks of the raw IBM file without leaking any
    train/test-specific statistics (this step is deterministic and
    dataset-structure-based, not statistic-based, so it is safe to run
    before splitting)."""
    df = df.copy()

    # TotalCharges arrives as an object dtype with blank strings for
    # customers whose tenure == 0 (new customers, not yet billed).
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    # SeniorCitizen arrives as 0/1 int; treat as categorical (it is a
    # binary demographic flag, not a magnitude).
    df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"}).astype(str)

    # Normalize target to a binary string for stratification, encoded
    # numerically just before model fitting.
    df[TARGET_COLUMN] = df[TARGET_COLUMN].map({"Yes": 1, "No": 0}).astype(int)

    return df


def get_feature_columns() -> list[str]:
    return NUMERIC_FEATURES + CATEGORICAL_FEATURES


def build_preprocessor() -> ColumnTransformer:
    """Build the ColumnTransformer used inside every model Pipeline.

    Fit exclusively on the training fold in each CV split / final fit,
    never on validation or test data.
    """
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return preprocessor
