"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { severityFor } from "@/lib/severity";
import type { CategoryBreakdown } from "@/lib/schemas";

export function CategoryGrid({ categories }: { categories: CategoryBreakdown[] }) {
  const [activeCategory, setActiveCategory] = useState<CategoryBreakdown | null>(null);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {categories.map((cat, i) => {
            const style = severityFor(cat.severity);
            const noHits = cat.keyword_hits === 0;
            return (
              <motion.button
                key={cat.category_id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                onClick={() => !noHits && setActiveCategory(cat)}
                className={`flex flex-col gap-2 rounded-lg border p-3.5 text-left transition-colors ${
                  noHits
                    ? "border-border bg-slate-50 opacity-70 cursor-default"
                    : `${style.border} ${style.bg} hover:shadow-card cursor-pointer`
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-text-primary">{cat.label}</span>
                  {!noHits && (
                    <Badge className={`${style.bg} ${style.text} border ${style.border}`}>
                      {style.label}
                    </Badge>
                  )}
                </div>
                {noHits ? (
                  <span className="text-xs font-medium text-success">No issues found ✓</span>
                ) : (
                  <>
                    <span className="text-xs text-text-muted">{cat.keyword_hits} keyword(s) matched</span>
                    <div className="flex flex-wrap gap-1.5">
                      {cat.matched_keywords.slice(0, 3).map((kw, idx) => (
                        <span
                          key={idx}
                          className="rounded-pill bg-white/70 px-2 py-0.5 text-xs text-text-primary border border-border"
                        >
                          {kw}
                        </span>
                      ))}
                    </div>
                  </>
                )}
              </motion.button>
            );
          })}
        </div>
      </CardContent>

      <AnimatePresence>
        {activeCategory && (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-black/30"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setActiveCategory(null)}
            />
            <motion.div
              className="fixed right-0 top-0 z-50 h-full w-full max-w-md overflow-y-auto bg-card shadow-modal sm:rounded-l-modal"
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "tween", duration: 0.25 }}
            >
              <div className="flex items-center justify-between border-b border-border p-5">
                <h3 className="font-display text-lg font-semibold">{activeCategory.label}</h3>
                <button
                  onClick={() => setActiveCategory(null)}
                  className="rounded-full p-1.5 hover:bg-slate-100"
                  aria-label="Close"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="p-5">
                <p className="mb-4 text-sm text-text-muted">
                  {activeCategory.keyword_hits} keyword(s) matched · risk weight {activeCategory.risk_weight} ·
                  weighted score {activeCategory.weighted_score.toFixed(1)}
                </p>
                <ul className="space-y-2">
                  {activeCategory.matched_keywords.map((kw, i) => (
                    <li
                      key={i}
                      className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text-primary"
                    >
                      {kw}
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </Card>
  );
}
