"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Collapsible } from "@/components/ui/collapsible";
import { SENTIMENT_STYLE } from "@/lib/severity";
import type { SentimentResponse } from "@/lib/schemas";

export function SentimentPanel({ sentiment }: { sentiment: SentimentResponse }) {
  const style = SENTIMENT_STYLE[sentiment.label];
  // compound_score is typically -1..1 — map to 0-100% position
  const markerPct = Math.round(((sentiment.compound_score + 1) / 2) * 100);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Sentiment</CardTitle>
        <Badge className={`${style.bg} ${style.text} font-semibold`}>{style.label}</Badge>
      </CardHeader>
      <CardContent className="space-y-5">
        <div>
          <div className="flex justify-between text-xs text-text-muted mb-1.5">
            <span>Negative</span>
            <span>Positive</span>
          </div>
          <div className="relative h-2.5 rounded-pill bg-gradient-to-r from-red-400 via-slate-200 to-green-400">
            <div
              className="absolute top-1/2 h-4 w-4 -translate-y-1/2 -translate-x-1/2 rounded-full border-2 border-white bg-text-primary shadow"
              style={{ left: `${markerPct}%` }}
              title={`Compound score: ${sentiment.compound_score.toFixed(2)}`}
            />
          </div>
        </div>

        {sentiment.aggressive_hits.length > 0 && (
          <div>
            <p className="mb-1.5 text-xs font-medium text-text-muted">Aggressive language found</p>
            <div className="flex flex-wrap gap-1.5">
              {sentiment.aggressive_hits.map((hit, i) => (
                <Badge key={i} className="bg-red-50 text-danger border border-red-200">
                  {hit}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {sentiment.friendly_hits.length > 0 && (
          <div>
            <p className="mb-1.5 text-xs font-medium text-text-muted">Borrower-friendly language found</p>
            <div className="flex flex-wrap gap-1.5">
              {sentiment.friendly_hits.map((hit, i) => (
                <Badge key={i} className="bg-green-50 text-success border border-green-200">
                  {hit}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {sentiment.worst_clauses.length > 0 && (
          <Collapsible title="Most threatening clause">
            <div className="space-y-3">
              {sentiment.worst_clauses.map((clause, i) => (
                <blockquote
                  key={i}
                  className="border-l-2 border-danger bg-red-50/50 px-3 py-2 text-sm italic text-text-primary"
                >
                  &ldquo;{clause.sentence}&rdquo;
                  <span className="mt-1 block text-xs not-italic text-text-muted">
                    Compound score: {clause.compound.toFixed(2)}
                  </span>
                </blockquote>
              ))}
            </div>
          </Collapsible>
        )}
      </CardContent>
    </Card>
  );
}
