"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";
import type { HistoryEntry } from "@/stores/analysisStore";

export function RiskChart({ entries }: { entries: HistoryEntry[] }) {
  if (entries.length < 2) return null;

  const chartData = [...entries]
    .reverse()
    .map((e) => ({ date: formatDate(e.analyzedAt), score: e.riskScore }));

  const recent = entries.slice(0, 5);
  const avgScore = Math.round(recent.reduce((sum, e) => sum + e.riskScore, 0) / recent.length);
  const avgLevel = avgScore > 80 ? "CRITICAL" : avgScore > 60 ? "HIGH" : avgScore >= 30 ? "MEDIUM" : "LOW";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Risk Score Over Time</CardTitle>
        <p className="mt-1 text-xs text-text-muted">
          Your last {recent.length} agreement(s) averaged a risk score of {avgScore} ({avgLevel})
        </p>
      </CardHeader>
      <CardContent>
        <div className="h-48 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#E2E8F0" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748B" }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#64748B" }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: "1px solid #E2E8F0", fontSize: 12 }}
              />
              <Line type="monotone" dataKey="score" stroke="#1B4FD8" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
