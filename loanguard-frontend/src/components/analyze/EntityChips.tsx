"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { EntityResponse } from "@/lib/schemas";

const ENTITY_GROUPS: { key: keyof EntityResponse; label: string; chipClass: string }[] = [
  { key: "MONEY", label: "Money", chipClass: "bg-green-50 text-success border-green-200" },
  { key: "RATE", label: "Interest Rate", chipClass: "bg-blue-50 text-info border-blue-200" },
  { key: "FEE_AMOUNT", label: "Fees", chipClass: "bg-amber-50 text-warning border-amber-200" },
  { key: "LOAN_AMOUNT", label: "Loan Amount", chipClass: "bg-green-50 text-success border-green-200" },
  { key: "DURATION", label: "Duration", chipClass: "bg-slate-100 text-text-muted border-slate-200" },
  { key: "DATE", label: "Dates", chipClass: "bg-slate-100 text-text-muted border-slate-200" },
  { key: "ORG", label: "Organizations", chipClass: "bg-slate-100 text-text-muted border-slate-200" },
  { key: "REGULATION", label: "Regulations", chipClass: "bg-purple-50 text-purple-700 border-purple-200" },
];

export function EntityChips({ entities }: { entities: EntityResponse }) {
  const groupsWithData = ENTITY_GROUPS.filter((g) => {
    const list = entities[g.key];
    return Array.isArray(list) && list.length > 0;
  });

  if (groupsWithData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Named Entities</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-text-muted">No financial entities were detected in this document.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Named Entities</CardTitle>
        <p className="text-xs text-text-muted mt-1">
          {entities.summary.total_entities} entities detected — {entities.summary.money_mentions} money,{" "}
          {entities.summary.rate_mentions} rate, {entities.summary.fee_mentions} fee mentions
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {groupsWithData.map((group) => {
          const items = entities[group.key];
          if (!Array.isArray(items)) return null;
          return (
            <div key={group.key as string}>
              <p className="mb-1.5 text-xs font-medium text-text-muted">{group.label}</p>
              <div className="flex gap-1.5 overflow-x-auto scrollbar-thin pb-1">
                {items.map((item, i) => (
                  <span
                    key={i}
                    className={`shrink-0 whitespace-nowrap rounded-pill border px-2.5 py-1 text-xs font-medium ${group.chipClass}`}
                    title={item.normalized !== item.text ? item.normalized : undefined}
                  >
                    {item.text}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
