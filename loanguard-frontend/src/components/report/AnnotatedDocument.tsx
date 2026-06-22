"use client";

import { useMemo, useState } from "react";
import { ZoomIn, ZoomOut, FileX } from "lucide-react";
import { Tooltip } from "@/components/ui/tooltip";
import { Tabs } from "@/components/ui/tabs";
import { buildHighlightSegments } from "@/lib/highlight";
import { severityFor } from "@/lib/severity";
import { explanationFor } from "@/lib/explanations";
import type { CategoryBreakdown } from "@/lib/schemas";

type FilterMode = "all" | "critical" | "fees" | "privacy";

const FILTER_CATEGORY_MAP: Record<FilterMode, string[] | null> = {
  all: null,
  critical: [], // handled by severity check instead
  fees: ["hidden_fee_risk", "predatory_lending_signals"],
  privacy: ["privacy_data_risk"],
};

export function AnnotatedDocument({
  sourceText,
  categories,
}: {
  sourceText: string | null;
  categories: CategoryBreakdown[];
}) {
  const [filter, setFilter] = useState<FilterMode>("all");
  const [zoom, setZoom] = useState(1);

  const segments = useMemo(
    () => (sourceText ? buildHighlightSegments(sourceText, categories) : []),
    [sourceText, categories]
  );

  if (!sourceText) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-card border border-dashed border-border bg-card p-10 text-center">
        <FileX size={36} className="text-slate-300" strokeWidth={1.5} />
        <div>
          <p className="font-display font-semibold text-text-primary">Document text not available</p>
          <p className="mt-1 max-w-sm text-sm text-text-muted">
            File uploads aren&apos;t re-rendered here since the original text isn&apos;t kept after analysis.
            Matched keywords are still listed in the report panel.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-card border border-border bg-card">
      <div className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-2 border-b border-border bg-card/95 px-4 py-2.5 backdrop-blur">
        <Tabs
          value={filter}
          onChange={(v) => setFilter(v as FilterMode)}
          tabs={[
            { value: "all", label: "Show All" },
            { value: "critical", label: "Critical Only" },
            { value: "fees", label: "Fees Only" },
            { value: "privacy", label: "Privacy Only" },
          ]}
        />
        <div className="flex items-center gap-1">
          <button
            onClick={() => setZoom((z) => Math.max(0.85, z - 0.1))}
            className="rounded-lg p-1.5 text-text-muted hover:bg-slate-100"
            aria-label="Zoom out"
          >
            <ZoomOut size={16} />
          </button>
          <button
            onClick={() => setZoom((z) => Math.min(1.4, z + 0.1))}
            className="rounded-lg p-1.5 text-text-muted hover:bg-slate-100"
            aria-label="Zoom in"
          >
            <ZoomIn size={16} />
          </button>
        </div>
      </div>

      <div
        className="max-h-[600px] overflow-y-auto whitespace-pre-wrap p-5 leading-relaxed text-text-primary"
        style={{ fontSize: `${zoom}rem` }}
      >
        {segments.map((seg, i) => {
          if (!seg.severity) return <span key={i}>{seg.text}</span>;

          const isCriticalFilter = filter === "critical" && seg.severity.toUpperCase() !== "CRITICAL";
          const categoryFilterIds = FILTER_CATEGORY_MAP[filter];
          const matchedCategory = categories.find((c) => c.label === seg.category);
          const isCategoryFiltered =
            categoryFilterIds &&
            categoryFilterIds.length > 0 &&
            matchedCategory &&
            !categoryFilterIds.includes(matchedCategory.category_id);

          if (filter !== "all" && (isCriticalFilter || isCategoryFiltered)) {
            return <span key={i}>{seg.text}</span>;
          }

          const style = severityFor(seg.severity);
          const { explanation } = explanationFor(seg.matchedKeyword ?? "", categories);

          return (
            <Tooltip
              key={i}
              content={
                <div className="text-left">
                  <p className="font-semibold">{seg.matchedKeyword}</p>
                  <p className="opacity-80">{seg.category} · {style.label}</p>
                  <p className="mt-1 max-w-[220px] opacity-90">{explanation}</p>
                </div>
              }
            >
              <span className={`kw-underline ${style.underline}`}>{seg.text}</span>
            </Tooltip>
          );
        })}
      </div>
    </div>
  );
}
