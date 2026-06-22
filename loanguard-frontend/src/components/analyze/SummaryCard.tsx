"use client";

import { Copy } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { SummaryResponse } from "@/lib/schemas";

export function SummaryCard({ summary }: { summary: SummaryResponse }) {
  const compressionPct = Math.round(summary.compression_ratio * 100);

  function handleCopy() {
    navigator.clipboard.writeText(summary.text);
    toast.success("Summary copied to clipboard.");
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>AI Summary</CardTitle>
        <Badge className="bg-blue-50 text-primary border border-blue-200">
          {summary.sentence_count} sentences → {summary.key_sentences.length} key ({compressionPct}%)
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <ol className="space-y-3">
          {summary.key_sentences.map((s) => (
            <li key={s.rank} className="flex gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-50 text-xs font-bold text-primary">
                {s.rank}
              </span>
              <div className="flex-1">
                <p className="text-sm text-text-primary">{s.sentence}</p>
                <div className="mt-1 h-1 w-full max-w-[120px] rounded-pill bg-slate-200">
                  <div
                    className="h-1 rounded-pill bg-primary"
                    style={{ width: `${Math.round(s.score * 100)}%` }}
                  />
                </div>
              </div>
            </li>
          ))}
        </ol>
        <Button variant="outline" size="sm" onClick={handleCopy}>
          <Copy size={14} /> Copy summary
        </Button>
      </CardContent>
    </Card>
  );
}
