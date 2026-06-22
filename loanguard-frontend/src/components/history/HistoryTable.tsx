"use client";

import Link from "next/link";
import { FileText, Trash2, Eye } from "lucide-react";
import { RiskLevelBadge } from "@/components/ui/badge";
import { SENTIMENT_STYLE, gaugeColorForScore } from "@/lib/severity";
import { formatDate, formatScore } from "@/lib/utils";
import { useDeleteHistoryItem } from "@/hooks/useHistory";
import type { HistoryEntry } from "@/stores/analysisStore";

function MiniGauge({ score }: { score: number }) {
  const color = gaugeColorForScore(score);
  const circumference = 2 * Math.PI * 14;
  const offset = circumference - (score / 100) * circumference;
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" className="shrink-0">
      <circle cx="18" cy="18" r="14" fill="none" stroke="#E2E8F0" strokeWidth="4" />
      <circle
        cx="18"
        cy="18"
        r="14"
        fill="none"
        stroke={color}
        strokeWidth="4"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 18 18)"
      />
      <text x="18" y="19" textAnchor="middle" dominantBaseline="middle" fontSize="9" fontWeight="700" fill={color}>
        {formatScore(score)}
      </text>
    </svg>
  );
}

export function HistoryTable({ entries }: { entries: HistoryEntry[] }) {
  const deleteMutation = useDeleteHistoryItem();

  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-card border border-dashed border-border bg-card p-12 text-center">
        <FileText size={40} className="text-slate-300" strokeWidth={1.5} />
        <div>
          <p className="font-display font-semibold text-text-primary">No analyses yet</p>
          <p className="mt-1 text-sm text-text-muted">Upload your first agreement to see it here.</p>
        </div>
        <Link
          href="/dashboard/analyze"
          className="mt-1 text-sm font-medium text-primary hover:underline"
        >
          Go to Analyze →
        </Link>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-card border border-border bg-card">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border bg-slate-50 text-xs uppercase tracking-wide text-text-muted">
            <th className="px-4 py-3 font-medium">Document</th>
            <th className="px-4 py-3 font-medium">Date</th>
            <th className="px-4 py-3 font-medium">Score</th>
            <th className="px-4 py-3 font-medium">Level</th>
            <th className="px-4 py-3 font-medium">Sentiment</th>
            <th className="px-4 py-3 font-medium">Top Flag</th>
            <th className="px-4 py-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.docId} className="border-b border-border last:border-0 hover:bg-slate-50/60">
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <FileText size={16} className="text-text-muted shrink-0" />
                  <span className="font-medium text-text-primary">
                    {entry.fileName ?? "Pasted text"}
                  </span>
                  {entry.fileType && (
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] uppercase text-text-muted">
                      {entry.fileType}
                    </span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 text-text-muted">{formatDate(entry.analyzedAt)}</td>
              <td className="px-4 py-3">
                <MiniGauge score={entry.riskScore} />
              </td>
              <td className="px-4 py-3">
                <RiskLevelBadge level={entry.riskLevel} />
              </td>
              <td className="px-4 py-3">
                {entry.sentimentLabel ? (
                  <span className={`text-xs font-medium ${SENTIMENT_STYLE[entry.sentimentLabel].text}`}>
                    {SENTIMENT_STYLE[entry.sentimentLabel].label}
                  </span>
                ) : (
                  <span className="text-xs text-text-muted">—</span>
                )}
              </td>
              <td className="max-w-[160px] truncate px-4 py-3 text-text-muted">
                {entry.topFlag ?? "—"}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center justify-end gap-2">
                  <Link
                    href={`/dashboard/report/${entry.docId}`}
                    className="rounded-lg p-1.5 text-text-muted hover:bg-blue-50 hover:text-primary"
                    aria-label="View report"
                  >
                    <Eye size={16} />
                  </Link>
                  <button
                    onClick={() => deleteMutation.mutate(entry.docId)}
                    disabled={deleteMutation.isPending}
                    className="rounded-lg p-1.5 text-text-muted hover:bg-red-50 hover:text-danger disabled:opacity-50"
                    aria-label="Delete analysis"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
