"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { severityFor } from "@/lib/severity";
import type { RAGResult } from "@/lib/schemas";

export function RAGResultCard({ rag }: { rag: RAGResult }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Explainer</CardTitle>
        <p className="mt-1 text-sm text-text-muted">{rag.overall_summary}</p>
      </CardHeader>
      <CardContent className="space-y-5">
        {rag.flagged_clauses.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-text-muted">Flagged clauses</p>
            <ul className="space-y-2">
              {rag.flagged_clauses.map((clause, i) => {
                const style = severityFor(clause.severity);
                return (
                  <li key={i} className={`rounded-lg border p-3 ${style.border} ${style.bg}`}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-text-primary">{clause.category}</span>
                      <Badge className={`${style.bg} ${style.text} border ${style.border}`}>
                        {style.label}
                      </Badge>
                    </div>
                    <p className="mt-1 text-sm text-text-muted">{clause.explanation}</p>
                    {clause.keywords.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {clause.keywords.map((kw, j) => (
                          <span key={j} className="rounded-pill bg-white/70 border border-border px-2 py-0.5 text-xs text-text-primary">
                            {kw}
                          </span>
                        ))}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {rag.regulatory_violations.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-text-muted">RBI guideline concerns</p>
            <ul className="space-y-2">
              {rag.regulatory_violations.map((v, i) => (
                <li key={i} className="rounded-lg border border-purple-200 bg-purple-50 p-3">
                  <span className="text-sm font-medium text-text-primary">{v.category}</span>
                  <p className="mt-1 text-sm text-text-muted">{v.explanation}</p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {rag.borrower_action_plan.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-text-muted">Before you sign, do these things</p>
            <ol className="space-y-1.5">
              {rag.borrower_action_plan.map((step, i) => (
                <li key={i} className="flex gap-2 text-sm text-text-primary">
                  <span className="font-semibold text-primary">{i + 1}.</span>
                  {step}
                </li>
              ))}
            </ol>
          </div>
        )}

        {rag.questions_to_ask_lender.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-text-muted">Questions to ask your lender</p>
            <ul className="space-y-1.5">
              {rag.questions_to_ask_lender.map((q, i) => (
                <li key={i} className="flex gap-2 text-sm text-text-primary">
                  <span className="text-primary">•</span>
                  {q}
                </li>
              ))}
            </ul>
          </div>
        )}

        {rag.retrieved_sources.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-text-muted">Sources consulted</p>
            <ul className="space-y-1">
              {rag.retrieved_sources.map((s, i) => (
                <li key={i} className="text-xs text-text-muted">
                  <span className="font-medium text-text-primary">{s.title}</span> — {s.snippet}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
