"""
Tests for the ML preprocessing/artifact layer. These run with only
pandas/numpy/scikit-learn/joblib, so they execute in minimal
environments (unlike the FastAPI test suite, which needs fastapi
installed).

Run with: python3 -m pytest tests/test_ml_pipeline.py -v
(or, if pytest is unavailable, python3 tests/test_ml_pipeline.py runs
the same checks via the __main__ block using plain asserts.)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import pandas as pd

from ml import config
from ml.preprocessing import clean_raw, get_feature_columns, load_raw


def test_raw_data_loads():
    df = load_raw(str(config.RAW_DATA_PATH))
    assert len(df) > 0
    assert "Churn" in df.columns
    assert "customerID" in df.columns


def test_clean_raw_encodes_target_binary():
    df = clean_raw(load_raw(str(config.RAW_DATA_PATH)))
    assert set(df["Churn"].unique()) <= {0, 1}


def test_clean_raw_total_charges_numeric():
    df = clean_raw(load_raw(str(config.RAW_DATA_PATH)))
    assert pd.api.types.is_numeric_dtype(df["TotalCharges"])


def test_no_duplicate_customer_ids():
    df = load_raw(str(config.RAW_DATA_PATH))
    assert df["customerID"].duplicated().sum() == 0


def test_feature_columns_exclude_identifier_and_target():
    features = get_feature_columns()
    assert "customerID" not in features
    assert "Churn" not in features


def test_model_artifact_loads_and_predicts_valid_probability():
    assert config.MODEL_ARTIFACT_PATH.exists(), "Run ml/train.py and ml/evaluate.py first"
    pipeline = joblib.load(config.MODEL_ARTIFACT_PATH)

    df = clean_raw(load_raw(str(config.RAW_DATA_PATH)))
    features = get_feature_columns()
    sample = df[features].iloc[[0]]

    proba = pipeline.predict_proba(sample)[0, 1]
    assert 0.0 <= proba <= 1.0


def test_model_artifact_predicts_full_batch_without_error():
    pipeline = joblib.load(config.MODEL_ARTIFACT_PATH)
    df = clean_raw(load_raw(str(config.RAW_DATA_PATH)))
    features = get_feature_columns()
    probas = pipeline.predict_proba(df[features])[:, 1]
    assert len(probas) == len(df)
    assert ((probas >= 0) & (probas <= 1)).all()


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {t.__name__} -> {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
