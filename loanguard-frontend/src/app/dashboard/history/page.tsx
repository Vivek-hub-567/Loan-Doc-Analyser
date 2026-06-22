"use client";

import { useMemo, useState } from "react";
import { Filter, X } from "lucide-react";
import { HistoryTable } from "@/components/history/HistoryTable";
import { HistoryFilters, type HistoryFilterState } from "@/components/history/HistoryFilters";
import { RiskChart } from "@/components/history/RiskChart";
import { Button } from "@/components/ui/button";
import { useHistory } from "@/hooks/useHistory";
import type { RiskLevel } from "@/lib/schemas";

export default function HistoryPage() {
  const allEntries = useHistory();
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [filters, setFilters] = useState<HistoryFilterState>({
    search: "",
    riskLevels: new Set<RiskLevel>(),
    sortBy: "date",
  });

  const filtered = useMemo(() => {
    let result = [...allEntries];

    if (filters.search.trim()) {
      const q = filters.search.toLowerCase();
      result = result.filter(
        (e) =>
          (e.fileName ?? "pasted text").toLowerCase().includes(q) ||
          (e.topFlag ?? "").toLowerCase().includes(q)
      );
    }

    if (filters.riskLevels.size > 0) {
      result = result.filter((e) => filters.riskLevels.has(e.riskLevel));
    }

    if (filters.sortBy === "score") {
      result.sort((a, b) => b.riskScore - a.riskScore);
    } else if (filters.sortBy === "name") {
      result.sort((a, b) => (a.fileName ?? "").localeCompare(b.fileName ?? ""));
    } else {
      result.sort((a, b) => new Date(b.analyzedAt).getTime() - new Date(a.analyzedAt).getTime());
    }

    return result;
  }, [allEntries, filters]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-xl font-bold text-text-primary sm:text-2xl">History</h1>
          <p className="mt-1 text-sm text-text-muted">
            {allEntries.length} analysis{allEntries.length !== 1 ? "es" : ""} saved in this browser.
          </p>
        </div>
        <Button variant="outline" size="sm" className="md:hidden" onClick={() => setFiltersOpen(true)}>
          <Filter size={14} /> Filters
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[220px_1fr]">
        <aside className="hidden lg:block">
          <HistoryFilters filters={filters} onChange={setFilters} />
        </aside>

        <div className="space-y-6">
          <RiskChart entries={allEntries} />
          <HistoryTable entries={filtered} />
        </div>
      </div>

      {filtersOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div className="absolute inset-0 bg-black/30" onClick={() => setFiltersOpen(false)} />
          <div className="relative ml-auto h-full w-72 overflow-y-auto bg-card p-5 shadow-modal">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-display font-semibold">Filters</h2>
              <button onClick={() => setFiltersOpen(false)} aria-label="Close filters">
                <X size={18} />
              </button>
            </div>
            <HistoryFilters filters={filters} onChange={setFilters} />
          </div>
        </div>
      )}
    </div>
  );
}
