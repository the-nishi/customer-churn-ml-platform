import "server-only";

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
  riskDistribution: {
    risk_level: string;
    count: number;
  }[];
  recent: PredictionRecord[];
}

async function fetchAllPredictions(
  url: string,
  key: string
): Promise<PredictionRecord[]> {
  const allRows: PredictionRecord[] = [];

  const pageSize = 1000;
  let offset = 0;

  while (true) {
    const res = await fetch(
      `${url}/rest/v1/prediction_history?select=*&order=created_at.desc`,
      {
        headers: {
          apikey: key,
          Range: `${offset}-${offset + pageSize - 1}`,
        },
        cache: "no-store",
      }
    );

    if (!res.ok) {
      const errorText = await res.text();

      console.error(
        "Supabase analytics error:",
        res.status,
        errorText
      );

      throw new Error("Failed to fetch analytics data.");
    }

    const rows =
      (await res.json()) as PredictionRecord[];

    allRows.push(...rows);

    if (rows.length < pageSize) {
      break;
    }

    offset += pageSize;
  }

  return allRows;
}

export async function fetchAnalytics():
  Promise<AnalyticsSummary | null> {
  const url = process.env.SUPABASE_URL;
  const key =
    process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !key) {
    console.error(
      "Supabase analytics credentials are not configured."
    );

    return null;
  }

  try {
    const rows = await fetchAllPredictions(
      url,
      key
    );

    const total = rows.length;

    const averageProbability =
      total > 0
        ? rows.reduce(
            (sum, record) =>
              sum +
              Number(record.churn_probability),
            0
          ) / total
        : 0;

    const highRiskCount = rows.filter(
      (record) =>
        record.risk_level === "High"
    ).length;

    const counts: Record<string, number> = {
      Low: 0,
      Medium: 0,
      High: 0,
    };

    rows.forEach((record) => {
      counts[record.risk_level] =
        (counts[record.risk_level] ?? 0) + 1;
    });

    const riskDistribution =
      Object.entries(counts).map(
        ([risk_level, count]) => ({
          risk_level,
          count,
        })
      );

    return {
      total,
      averageProbability,
      highRiskCount,
      riskDistribution,

      // Only show latest 10 rows in
      // Recent Predictions section.
      recent: rows.slice(0, 10),
    };
  } catch (error) {
    console.error(
      "Failed to build analytics summary:",
      error
    );

    return null;
  }
}
