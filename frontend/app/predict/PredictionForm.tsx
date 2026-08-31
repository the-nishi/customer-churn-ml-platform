"use client";

import { useState } from "react";
import { ApiError, postPrediction, type CustomerFeatures, type PredictionResponse } from "@/lib/api";

const DEFAULTS: CustomerFeatures = {
  gender: "Female",
  SeniorCitizen: "No",
  Partner: "No",
  Dependents: "No",
  tenure: 12,
  PhoneService: "Yes",
  MultipleLines: "No",
  InternetService: "Fiber optic",
  OnlineSecurity: "No",
  OnlineBackup: "No",
  DeviceProtection: "No",
  TechSupport: "No",
  StreamingTV: "No",
  StreamingMovies: "No",
  Contract: "Month-to-month",
  PaperlessBilling: "Yes",
  PaymentMethod: "Electronic check",
  MonthlyCharges: 75,
  TotalCharges: 900,
  customer_reference: "",
};

const YES_NO = ["Yes", "No"] as const;
const YES_NO_PHONE = ["Yes", "No", "No phone service"] as const;
const YES_NO_INTERNET = ["Yes", "No", "No internet service"] as const;

const RISK_STYLES: Record<string, string> = {
  Low: "bg-risk-low/10 text-risk-low border-risk-low/30",
  Medium: "bg-risk-medium/10 text-risk-medium border-risk-medium/30",
  High: "bg-risk-high/10 text-risk-high border-risk-high/30",
};

function factorLabel(feature: string): string {
  return feature.replace(/^num__|^cat__/, "").replace(/_/g, " ");
}

export default function PredictionForm() {
  const [form, setForm] = useState<CustomerFeatures>(DEFAULTS);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function update<K extends keyof CustomerFeatures>(key: K, value: CustomerFeatures[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await postPrediction(form);
      setResult(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Could not reach the prediction service. Is the backend running?");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <form onSubmit={handleSubmit} className="space-y-6 rounded-xl border border-slate-200 bg-white p-6">
        <div className="grid grid-cols-2 gap-4">
          <Field label="Customer reference (optional)">
            <input
              className="input"
              value={form.customer_reference}
              onChange={(e) => update("customer_reference", e.target.value)}
              placeholder="e.g. internal CRM ID"
            />
          </Field>
          <Field label="Tenure (months)">
            <input
              type="number"
              min={0}
              max={100}
              className="input"
              value={form.tenure}
              onChange={(e) => update("tenure", Number(e.target.value))}
            />
          </Field>

          <Select label="Gender" value={form.gender} options={["Female", "Male"]} onChange={(v) => update("gender", v as CustomerFeatures["gender"])} />
          <Select label="Senior citizen" value={form.SeniorCitizen} options={YES_NO} onChange={(v) => update("SeniorCitizen", v as CustomerFeatures["SeniorCitizen"])} />
          <Select label="Has partner" value={form.Partner} options={YES_NO} onChange={(v) => update("Partner", v as CustomerFeatures["Partner"])} />
          <Select label="Has dependents" value={form.Dependents} options={YES_NO} onChange={(v) => update("Dependents", v as CustomerFeatures["Dependents"])} />

          <Select label="Phone service" value={form.PhoneService} options={YES_NO} onChange={(v) => update("PhoneService", v as CustomerFeatures["PhoneService"])} />
          <Select label="Multiple lines" value={form.MultipleLines} options={YES_NO_PHONE} onChange={(v) => update("MultipleLines", v as CustomerFeatures["MultipleLines"])} />
          <Select label="Internet service" value={form.InternetService} options={["DSL", "Fiber optic", "No"]} onChange={(v) => update("InternetService", v as CustomerFeatures["InternetService"])} />
          <Select label="Contract" value={form.Contract} options={["Month-to-month", "One year", "Two year"]} onChange={(v) => update("Contract", v as CustomerFeatures["Contract"])} />

          <Select label="Online security" value={form.OnlineSecurity} options={YES_NO_INTERNET} onChange={(v) => update("OnlineSecurity", v as CustomerFeatures["OnlineSecurity"])} />
          <Select label="Online backup" value={form.OnlineBackup} options={YES_NO_INTERNET} onChange={(v) => update("OnlineBackup", v as CustomerFeatures["OnlineBackup"])} />
          <Select label="Device protection" value={form.DeviceProtection} options={YES_NO_INTERNET} onChange={(v) => update("DeviceProtection", v as CustomerFeatures["DeviceProtection"])} />
          <Select label="Tech support" value={form.TechSupport} options={YES_NO_INTERNET} onChange={(v) => update("TechSupport", v as CustomerFeatures["TechSupport"])} />
          <Select label="Streaming TV" value={form.StreamingTV} options={YES_NO_INTERNET} onChange={(v) => update("StreamingTV", v as CustomerFeatures["StreamingTV"])} />
          <Select label="Streaming movies" value={form.StreamingMovies} options={YES_NO_INTERNET} onChange={(v) => update("StreamingMovies", v as CustomerFeatures["StreamingMovies"])} />

          <Select label="Paperless billing" value={form.PaperlessBilling} options={YES_NO} onChange={(v) => update("PaperlessBilling", v as CustomerFeatures["PaperlessBilling"])} />
          <Select
            label="Payment method"
            value={form.PaymentMethod}
            options={["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]}
            onChange={(v) => update("PaymentMethod", v as CustomerFeatures["PaymentMethod"])}
          />

          <Field label="Monthly charges ($)">
            <input
              type="number"
              step="0.01"
              min={0}
              className="input"
              value={form.MonthlyCharges}
              onChange={(e) => update("MonthlyCharges", Number(e.target.value))}
            />
          </Field>
          <Field label="Total charges ($)">
            <input
              type="number"
              step="0.01"
              min={0}
              className="input"
              value={form.TotalCharges}
              onChange={(e) => update("TotalCharges", Number(e.target.value))}
            />
          </Field>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? "Scoring…" : "Predict churn risk"}
        </button>

        {error && (
          <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
        )}
      </form>

      <div>
        {!result && !error && (
          <div className="flex h-full items-center justify-center rounded-xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">
            Fill out the form and submit to see the churn risk prediction and explanation here.
          </div>
        )}

        {result && (
          <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-6">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Customer Churn Risk</p>
              <p className="mt-1 text-4xl font-bold text-slate-900">
                {(result.probability * 100).toFixed(1)}%
              </p>
              <span
                className={`mt-2 inline-block rounded-full border px-3 py-1 text-xs font-semibold ${RISK_STYLES[result.risk_level]}`}
              >
                {result.risk_level.toUpperCase()} RISK — {result.prediction === "Churn" ? "Likely to Churn" : "Likely to Stay"}
              </span>
            </div>

            <div>
              <p className="text-sm font-semibold text-slate-800">Main model factors for this prediction</p>
              <ul className="mt-2 space-y-1.5 text-sm">
                {result.top_factors.map((f) => (
                  <li key={f.feature} className="flex items-center gap-2">
                    <span className={f.direction === "increases_risk" ? "text-risk-high" : "text-risk-low"}>
                      {f.direction === "increases_risk" ? "↑" : "↓"}
                    </span>
                    <span className="text-slate-700">{factorLabel(f.feature)}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-slate-400">
                These are statistical associations learned by the model, not proven causes of
                churn for this specific customer.
              </p>
            </div>

            <p className="text-xs text-slate-400">
              Model version {result.model_version} · decision threshold {result.threshold_used}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-slate-700">{label}</span>
      {children}
    </label>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: readonly string[];
  onChange: (v: string) => void;
}) {
  return (
    <Field label={label}>
      <select className="input" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </Field>
  );
}
