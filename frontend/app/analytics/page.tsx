import { fetchAnalytics } from "./data";
import RiskDistributionChart from "./RiskDistributionChart";

export const dynamic = "force-dynamic";

export default async function AnalyticsPage() {
  const analytics = await fetchAnalytics();

  if (!analytics) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
        Analytics data is unavailable — the server-side Supabase credentials
        (SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY) are not configured for this
        deployment. Once predictions have been made through /predict, they will
        appear here.
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-900">Analytics Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Total Predictions" value={analytics.total.toString()} />
        <StatCard
          label="Average Churn Probability"
          value={`${(analytics.averageProbability * 100).toFixed(1)}%`}
        />
        <StatCard label="High-Risk Customers" value={analytics.highRiskCount.toString()} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-4 text-sm font-semibold text-slate-800">Risk Distribution</h2>
        <RiskDistributionChart data={analytics.riskDistribution} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="mb-4 text-sm font-semibold text-slate-800">Recent Predictions</h2>
        {analytics.recent.length === 0 ? (
          <p className="text-sm text-slate-500">No predictions recorded yet.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr>
                <th className="py-2">Reference</th>
                <th className="py-2">Prediction</th>
                <th className="py-2">Probability</th>
                <th className="py-2">Risk</th>
                <th className="py-2">When</th>
              </tr>
            </thead>
            <tbody>
              {analytics.recent.map((r) => (
                <tr key={r.id} className="border-t border-slate-100">
                  <td className="py-2">{r.customer_reference ?? "—"}</td>
                  <td className="py-2">{r.prediction}</td>
                  <td className="py-2">{(Number(r.churn_probability) * 100).toFixed(1)}%</td>
                  <td className="py-2">{r.risk_level}</td>
                  <td className="py-2 text-slate-500">{new Date(r.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}
