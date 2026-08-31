from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("churn_api.supabase_service")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
# Server-side only. NEVER read/expose the service-role key on any
# frontend code path -- it lives exclusively in the backend's
# environment (Railway), never in NEXT_PUBLIC_* variables.
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("Supabase credentials not configured; persistence disabled.")
        return None
    try:
        from supabase import create_client

        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        return _client
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to initialize Supabase client: %s", exc)
        return None


def persist_prediction(
    customer_reference: Optional[str],
    prediction: str,
    churn_probability: float,
    risk_level: str,
    model_version: str,
) -> bool:
    """Best-effort persistence. A Supabase outage must never break the
    /predict endpoint's core response -- failures are logged and
    swallowed here, and the caller always returns the prediction to the
    user regardless of persistence outcome."""
    client = _get_client()
    if client is None:
        return False
    try:
        client.table("prediction_history").insert(
            {
                "customer_reference": customer_reference,
                "prediction": prediction,
                "churn_probability": churn_probability,
                "risk_level": risk_level,
                "model_version": model_version,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to persist prediction to Supabase: %s", exc)
        return False
