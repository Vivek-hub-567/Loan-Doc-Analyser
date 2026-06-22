"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, AlertTriangle } from "lucide-react";
import { AnnotatedDocument } from "@/components/report/AnnotatedDocument";
import { ReportDownloads } from "@/components/report/ReportDownloads";
import { RiskScoreHero } from "@/components/analyze/RiskScoreHero";
import { SentimentPanel } from "@/components/analyze/SentimentPanel";
import { CategoryGrid } from "@/components/analyze/CategoryGrid";
import { EntityChips } from "@/components/analyze/EntityChips";
import { TopFlags } from "@/components/analyze/TopFlags";
import { SummaryCard } from "@/components/analyze/SummaryCard";
import { RAGResultCard } from "@/components/analyze/RAGResultCard";
import { useReport } from "@/hooks/useReports";
import { useAnalysisStore } from "@/stores/analysisStore";

export default function ReportPage() {
  const params = useParams<{ id: string }>();
  const docId = params.id;
  const { result, isLoading, isError } = useReport(docId);
  const cached = useAnalysisStore((s) => s.getEntry(docId));

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10 text-center text-sm text-text-muted">
        Loading report...
      </div>
    );
  }

  if (isError || !result) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="flex flex-col items-center gap-3 rounded-card border border-dashed border-border bg-card p-12 text-center">
          <AlertTriangle size={36} className="text-amber-400" />
          <div>
            <p className="font-display font-semibold text-text-primary">Report not found</p>
            <p className="mt-1 max-w-sm text-sm text-text-muted">
              This report isn&apos;t in your local history, and the backend&apos;s in-memory store may
              have reset since it was created. Reports are only reliably available in the browser
              that generated them.
            </p>
          </div>
          <Link href="/dashboard/analyze" className="text-sm font-medium text-primary hover:underline">
            Run a new analysis →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-10">
      <Link
        href="/dashboard/history"
        className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-text-muted hover:text-primary"
      >
        <ArrowLeft size={14} /> Back to history
      </Link>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[3fr_2fr]">
        {/* Left — annotated document */}
        <div>
          <h2 className="mb-3 font-display text-lg font-semibold text-text-primary">
            Annotated Document
          </h2>
          <AnnotatedDocument
            sourceText={cached?.sourceText ?? null}
            categories={result.category_breakdown}
          />
        </div>

        {/* Right — sticky report panel */}
        <div className="space-y-4 lg:sticky lg:top-6 lg:max-h-[calc(100vh-3rem)] lg:overflow-y-auto lg:pb-6">
          <RiskScoreHero result={result} />
          <ReportDownloads result={result} />
          {result.sentiment && <SentimentPanel sentiment={result.sentiment} />}
          {result.category_breakdown.length > 0 && (
            <CategoryGrid categories={result.category_breakdown} />
          )}
          {result.entities && <EntityChips entities={result.entities} />}
          <TopFlags flags={result.top_flags} categories={result.category_breakdown} />
          {result.summary && <SummaryCard summary={result.summary} />}
          {result.rag_result ? (
            <RAGResultCard rag={result.rag_result} />
          ) : (
            <p className="rounded-lg border border-dashed border-border bg-card p-4 text-xs text-text-muted">
              Borrower action plan and RBI guideline mapping are only generated when the AI Explainer
              (RAG) option is turned on before analysis.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
