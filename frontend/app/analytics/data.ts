import "server-only";

// This module runs ONLY on the server (Next.js Server Component /
// Route Handler context). It is never bundled into client JS, so the
// service-role key never reaches the browser -- the frontend has no
// direct database credentials at all, matching spec section 23.

export interface PredictionRecord {
  id: number;
  customer_reference: string | null;
  prediction: string;
  churn_probability: number;
  risk_level: "Low" | "Medium" | "High";
  model_version: string;
  created_at: string;
}

export interface AnalyticsSummary {
  total: number;
  averageProbability: number;
  highRiskCount: number;
  riskDistribution: { risk_level: string; count: number }[];
  recent: PredictionRecord[];
}

export async function fetchAnalytics(): Promise<AnalyticsSummary | null> {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) return null;

  const res = await fetch(
    `${url}/rest/v1/prediction_history?select=*&order=created_at.desc&limit=200`,
    {
      headers: { apikey: key, Authorization: `Bearer ${key}` },
      cache: "no-store",
    }
  );
  if (!res.ok) return null;

  const rows = (await res.json()) as PredictionRecord[];
  const total = rows.length;
  const averageProbability =
    total > 0 ? rows.reduce((sum, r) => sum + Number(r.churn_probability), 0) / total : 0;
  const highRiskCount = rows.filter((r) => r.risk_level === "High").length;

  const counts: Record<string, number> = { Low: 0, Medium: 0, High: 0 };
  rows.forEach((r) => (counts[r.risk_level] = (counts[r.risk_level] ?? 0) + 1));
  const riskDistribution = Object.entries(counts).map(([risk_level, count]) => ({
    risk_level,
    count,
  }));

  return {
    total,
    averageProbability,
    highRiskCount,
    riskDistribution,
    recent: rows.slice(0, 10),
  };
}
