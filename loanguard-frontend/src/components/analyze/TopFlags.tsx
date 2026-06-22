"use client";

import { useState } from "react";
import { Flag } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { severityFor } from "@/lib/severity";
import { explanationFor } from "@/lib/explanations";
import type { CategoryBreakdown } from "@/lib/schemas";
import { toast } from "sonner";

export function TopFlags({
  flags,
  categories,
}: {
  flags: string[];
  categories: CategoryBreakdown[];
}) {
  const [reported, setReported] = useState<Set<number>>(new Set());

  if (flags.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Key Findings</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-text-muted">
            No high-priority flags were found in this document — a good sign.
          </p>
        </CardContent>
      </Card>
    );
  }

  function handleReport(i: number) {
    setReported((prev) => new Set(prev).add(i));
    toast.success("Thanks — this finding has been noted for review.");
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Key Findings</CardTitle>
        <p className="text-xs text-text-muted mt-1">Top {flags.length} flag(s), ranked by relevance</p>
      </CardHeader>
      <CardContent>
        <ol className="space-y-4">
          {flags.map((flag, i) => {
            const { category, explanation } = explanationFor(flag, categories);
            const style = category ? severityFor(category.severity) : severityFor("INFO");
            return (
              <li key={i} className="flex gap-3 rounded-lg border border-border p-3.5">
                <span
                  className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
                  style={{ backgroundColor: style.dot }}
                >
                  {i + 1}
                </span>
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium text-text-primary">{flag}</span>
                    {category && (
                      <span className="text-xs text-text-muted">· {category.label}</span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-text-muted">
                    <span className="font-medium text-text-primary">What this means for you: </span>
                    {explanation}
                  </p>
                  <button
                    onClick={() => handleReport(i)}
                    disabled={reported.has(i)}
                    className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline disabled:text-text-muted disabled:no-underline"
                  >
                    <Flag size={12} />
                    {reported.has(i) ? "Reported" : "Report as incorrect"}
                  </button>
                </div>
              </li>
            );
          })}
        </ol>
      </CardContent>
    </Card>
  );
}
