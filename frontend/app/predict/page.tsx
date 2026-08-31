import PredictionForm from "./PredictionForm";

export default function PredictPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Predict Churn</h1>
        <p className="mt-1 text-sm text-slate-600">
          Enter a customer&apos;s account details to score their churn risk and see the
          explanation behind the score.
        </p>
      </div>
      <PredictionForm />
    </div>
  );
}
