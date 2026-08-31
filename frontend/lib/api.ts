const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CustomerFeatures {
  gender: "Male" | "Female";
  SeniorCitizen: "Yes" | "No";
  Partner: "Yes" | "No";
  Dependents: "Yes" | "No";
  tenure: number;
  PhoneService: "Yes" | "No";
  MultipleLines: "Yes" | "No" | "No phone service";
  InternetService: "DSL" | "Fiber optic" | "No";
  OnlineSecurity: "Yes" | "No" | "No internet service";
  OnlineBackup: "Yes" | "No" | "No internet service";
  DeviceProtection: "Yes" | "No" | "No internet service";
  TechSupport: "Yes" | "No" | "No internet service";
  StreamingTV: "Yes" | "No" | "No internet service";
  StreamingMovies: "Yes" | "No" | "No internet service";
  Contract: "Month-to-month" | "One year" | "Two year";
  PaperlessBilling: "Yes" | "No";
  PaymentMethod:
    | "Electronic check"
    | "Mailed check"
    | "Bank transfer (automatic)"
    | "Credit card (automatic)";
  MonthlyCharges: number;
  TotalCharges: number;
  customer_reference?: string;
}

export interface ExplanationFactor {
  feature: string;
  direction: "increases_risk" | "decreases_risk";
  contribution: number;
}

export interface PredictionResponse {
  prediction: "Churn" | "No Churn";
  probability: number;
  risk_level: "Low" | "Medium" | "High";
  model_version: string;
  threshold_used: number;
  top_factors: ExplanationFactor[];
}

export interface ModelInfoResponse {
  model_name: string;
  model_version: string;
  selected_threshold: number;
  training_timestamp: string;
  features: string[];
  test_metrics: Record<string, unknown>;
  dataset_provenance: string;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      // ignore parse errors, fall back to statusText
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export async function getHealth() {
  const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
  return handle<{ status: string; model_loaded: boolean; model_version?: string }>(res);
}

export async function getModelInfo() {
  const res = await fetch(`${API_URL}/model-info`, { cache: "no-store" });
  return handle<ModelInfoResponse>(res);
}

export async function postPrediction(payload: CustomerFeatures) {
  const res = await fetch(`${API_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle<PredictionResponse>(res);
}
