"""
Backend API tests. Requires the backend/requirements.txt to be
installed (fastapi, httpx). NOT executable in an environment without
network access to install those packages -- see the project README's
"Known Limitations" section for how this was verified vs. shipped.

Run with: cd backend && python3 -m pytest tests/test_api.py -v
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "gender": "Female",
    "SeniorCitizen": "No",
    "Partner": "Yes",
    "Dependents": "No",
    "tenure": 12,
    "PhoneService": "Yes",
    "MultipleLines": "No",
    "InternetService": "Fiber optic",
    "OnlineSecurity": "No",
    "OnlineBackup": "No",
    "DeviceProtection": "No",
    "TechSupport": "No",
    "StreamingTV": "Yes",
    "StreamingMovies": "Yes",
    "Contract": "Month-to-month",
    "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check",
    "MonthlyCharges": 89.5,
    "TotalCharges": 1074.0,
}


def test_health_endpoint_returns_200():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert "model_loaded" in body


def test_model_info_endpoint_shape():
    resp = client.get("/model-info")
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        body = resp.json()
        for key in ["model_name", "model_version", "selected_threshold", "test_metrics"]:
            assert key in body


def test_predict_valid_payload_returns_prediction():
    resp = client.post("/predict", json=VALID_PAYLOAD)
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        body = resp.json()
        assert body["prediction"] in ("Churn", "No Churn")
        assert 0.0 <= body["probability"] <= 1.0
        assert body["risk_level"] in ("Low", "Medium", "High")
        assert isinstance(body["top_factors"], list)


def test_predict_rejects_malformed_payload():
    bad_payload = dict(VALID_PAYLOAD)
    bad_payload["Contract"] = "Not-A-Real-Contract-Type"
    resp = client.post("/predict", json=bad_payload)
    assert resp.status_code == 422


def test_predict_rejects_missing_field():
    incomplete = dict(VALID_PAYLOAD)
    del incomplete["tenure"]
    resp = client.post("/predict", json=incomplete)
    assert resp.status_code == 422


def test_predict_rejects_out_of_range_tenure():
    bad_payload = dict(VALID_PAYLOAD)
    bad_payload["tenure"] = -5
    resp = client.post("/predict", json=bad_payload)
    assert resp.status_code == 422
