"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const COLORS: Record<string, string> = {
  Low: "#16a34a",
  Medium: "#d97706",
  High: "#dc2626",
};

export default function RiskDistributionChart({
  data,
}: {
  data: { risk_level: string; count: number }[];
}) {
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="risk_level" tickLine={false} axisLine={false} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
          <Tooltip />
          <Bar dataKey="count" radius={[6, 6, 0, 0]} fill="#4f46e5" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
