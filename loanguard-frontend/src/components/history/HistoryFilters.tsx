"use client";

import { Search } from "lucide-react";
import type { RiskLevel } from "@/lib/schemas";

export interface HistoryFilterState {
  search: string;
  riskLevels: Set<RiskLevel>;
  sortBy: "date" | "score" | "name";
}

const ALL_LEVELS: RiskLevel[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];

export function HistoryFilters({
  filters,
  onChange,
}: {
  filters: HistoryFilterState;
  onChange: (filters: HistoryFilterState) => void;
}) {
  function toggleLevel(level: RiskLevel) {
    const next = new Set(filters.riskLevels);
    if (next.has(level)) next.delete(level);
    else next.add(level);
    onChange({ ...filters, riskLevels: next });
  }

  return (
    <div className="space-y-5">
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          placeholder="Search by file name or keyword"
          className="w-full rounded-lg border border-border bg-card py-2 pl-9 pr-3 text-sm placeholder:text-text-muted focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
      </div>

      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-text-muted">Risk level</p>
        <div className="space-y-1.5">
          {ALL_LEVELS.map((level) => (
            <label key={level} className="flex items-center gap-2 text-sm text-text-primary cursor-pointer">
              <input
                type="checkbox"
                checked={filters.riskLevels.has(level)}
                onChange={() => toggleLevel(level)}
                className="h-4 w-4 rounded accent-primary"
              />
              {level}
            </label>
          ))}
        </div>
      </div>

      <div>
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-text-muted">Sort by</p>
        <select
          value={filters.sortBy}
          onChange={(e) => onChange({ ...filters, sortBy: e.target.value as HistoryFilterState["sortBy"] })}
          className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm focus:border-primary focus:outline-none"
        >
          <option value="date">Date (newest)</option>
          <option value="score">Risk score (highest)</option>
          <option value="name">Name (A–Z)</option>
        </select>
      </div>
    </div>
  );
}
