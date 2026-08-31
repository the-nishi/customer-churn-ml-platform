import { getModelInfo } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ModelInfoPage() {
  let info;
  let error: string | null = null;
  try {
    info = await getModelInfo();
  } catch {
    error = "Could not reach the prediction backend to load model information.";
  }

  if (error || !info) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
        {error}
      </div>
    );
  }

  const testMetrics = info.test_metrics as Record<string, unknown>;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-900">Model Information</h1>

      <div className="grid gap-4 sm:grid-cols-2">
        <InfoRow label="Model" value={info.model_name} />
        <InfoRow label="Version" value={info.model_version} />
        <InfoRow label="Decision threshold" value={info.selected_threshold.toString()} />
        <InfoRow label="Trained" value={new Date(info.training_timestamp).toLocaleString()} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-3 text-sm font-semibold text-slate-800">Verified Test-Set Metrics</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
          {["accuracy", "precision", "recall", "f1", "roc_auc"].map((key) => (
            <div key={key}>
              <p className="text-xs uppercase text-slate-500">{key.replace("_", " ")}</p>
              <p className="text-lg font-semibold text-slate-900">
                {typeof testMetrics[key] === "number"
                  ? (testMetrics[key] as number).toFixed(3)
                  : "—"}
              </p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-xs text-slate-400">
          Computed once against an untouched test split, not re-optimized after the fact.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-3 text-sm font-semibold text-slate-800">Features Used</h2>
        <div className="flex flex-wrap gap-2">
          {info.features.map((f) => (
            <span key={f} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
              {f}
            </span>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
        <h2 className="mb-2 text-sm font-semibold text-slate-800">Dataset Provenance</h2>
        <p>{info.dataset_provenance}</p>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-medium text-slate-900">{value}</p>
    </div>
  );
}
