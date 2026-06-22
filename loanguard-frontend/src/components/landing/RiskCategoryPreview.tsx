"use client";

import {
  Banknote,
  AlertOctagon,
  Scale,
  Calculator,
  Crown,
  Lock,
  Landmark,
  ShieldAlert,
  type LucideIcon,
} from "lucide-react";
import { useCategories } from "@/hooks/useCategories";
import { severityFor } from "@/lib/severity";

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  hidden_fee_risk: Banknote,
  default_recovery_risk: AlertOctagon,
  legal_clause_detection: Scale,
  financial_entity_extraction: Calculator,
  power_imbalance_risk: Crown,
  privacy_data_risk: Lock,
  regulatory_compliance: Landmark,
  predatory_lending_signals: ShieldAlert,
};

// Static fallback mirrors the real backend keywords_config.json categories,
// shown if the API is unreachable so the landing page never breaks.
const FALLBACK_CATEGORIES = [
  { id: "hidden_fee_risk", label: "Hidden Fee Risk", severity: "HIGH", keywords: ["penal charges", "GST extra", "processing fee"] },
  { id: "default_recovery_risk", label: "Default Recovery Risk", severity: "CRITICAL", keywords: ["acceleration clause", "entire outstanding"] },
  { id: "legal_clause_detection", label: "Legal Clause Detection", severity: "MEDIUM", keywords: ["force majeure", "indemnification clause"] },
  { id: "financial_entity_extraction", label: "Financial Entity", severity: "INFO", keywords: ["EMI", "principal amount"] },
  { id: "power_imbalance_risk", label: "Power Imbalance Risk", severity: "HIGH", keywords: ["sole discretion", "lender's discretion"] },
  { id: "privacy_data_risk", label: "Privacy & Data Risk", severity: "HIGH", keywords: ["SMS access", "contact access"] },
  { id: "regulatory_compliance", label: "Regulatory Compliance", severity: "MEDIUM", keywords: ["NBFC", "RBI guidelines"] },
  { id: "predatory_lending_signals", label: "Predatory Lending Signal", severity: "CRITICAL", keywords: ["upfront deduction"] },
];

export function RiskCategoryPreview() {
  const { data, isLoading } = useCategories();

  const categories = data?.categories ?? FALLBACK_CATEGORIES;

  return (
    <section className="px-4 py-16 sm:px-6 sm:py-24">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-center font-display text-2xl font-bold text-text-primary sm:text-3xl">
          8 risk categories, checked every time
        </h2>
        <p className="mx-auto mt-2 max-w-lg text-center text-sm text-text-muted">
          {data ? `${data.total_keywords}+ keyword patterns` : "130+ keyword patterns"} across these
          categories, built from real digital lending complaints and RBI guidance.
        </p>

        <div className="mt-10 flex gap-4 overflow-x-auto scrollbar-thin pb-2 sm:grid sm:grid-cols-4 sm:overflow-visible">
          {categories.map((cat) => {
            const Icon = CATEGORY_ICONS[cat.id] ?? ShieldAlert;
            const style = severityFor(cat.severity);
            return (
              <div
                key={cat.id}
                className={`group relative w-56 shrink-0 rounded-card border p-4 transition-shadow hover:shadow-card sm:w-auto ${style.border} bg-card`}
              >
                <div
                  className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg"
                  style={{ backgroundColor: `${style.dot}1A` }}
                >
                  <Icon size={20} style={{ color: style.dot }} />
                </div>
                <h3 className="font-display text-sm font-semibold text-text-primary">{cat.label}</h3>
                <div className="mt-2 flex flex-wrap gap-1">
                  {cat.keywords.slice(0, 2).map((kw, i) => (
                    <span key={i} className="rounded-pill bg-slate-100 px-2 py-0.5 text-[11px] text-text-muted">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
        {isLoading && (
          <p className="mt-3 text-center text-xs text-text-muted">Loading live categories…</p>
        )}
      </div>
    </section>
  );
}
