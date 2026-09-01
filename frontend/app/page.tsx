import Link from "next/link";

const FEATURES = [
  {
    title: "Predict Churn",
    body: "Score an individual customer and see the probability, risk tier, and top contributing factors.",
    href: "/predict",
  },
  {
    title: "Batch Prediction",
    body: "Upload a CSV file containing multiple customer records and generate churn predictions in batch.",
    href: "/batch",
  },
  {
    title: "Analytics Dashboard",
    body: "Review aggregate prediction history: volume, average risk, and the risk distribution over time.",
    href: "/analytics",
  },
  {
    title: "Model Information",
    body: "Inspect which model is in production, its verified test metrics, and dataset provenance.",
    href: "/model",
  },
];

export default function OverviewPage() {
  return (
    <div className="space-y-12">
      <section>
        <h1 className="text-3xl font-bold text-slate-900">
          Customer Churn Prediction &amp; Explainable ML
        </h1>

        <p className="mt-3 max-w-2xl text-slate-600">
          A production-style platform for scoring telecom customer churn risk,
          backed by a leakage-safe scikit-learn pipeline, served through a
          FastAPI backend, and explained with per-prediction feature
          contributions rather than a black-box score alone.
        </p>
      </section>

      <section className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <Link
            key={f.href}
            href={f.href}
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-md"
          >
            <h2 className="text-base font-semibold text-slate-900">
              {f.title}
            </h2>

            <p className="mt-2 text-sm text-slate-600">
              {f.body}
            </p>
          </Link>
        ))}
      </section>

      <section className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
        <strong>Business problem: </strong>
        Acquiring a new subscriber costs materially more than retaining an
        existing one. This platform flags at-risk customers early enough for a
        retention team to act, and explains <em>why</em> each customer is
        flagged so outreach can be targeted (e.g. a contract upgrade offer for
        a month-to-month customer, rather than a generic discount).
      </section>
    </div>
  );
}
