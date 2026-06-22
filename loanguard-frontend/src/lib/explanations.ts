import type { CategoryBreakdown } from "@/lib/schemas";

/**
 * The backend's top_flags is just list[str] — no per-flag explanation.
 * This builds plain-English context by matching each flag against the
 * category_breakdown's matched_keywords, so users see WHY a term matters,
 * not just the raw keyword.
 */

const CATEGORY_EXPLANATIONS: Record<string, string> = {
  hidden_fee_risk:
    "This may mean charges are added without being clearly listed upfront — always ask for the full Schedule of Charges before signing.",
  default_recovery_risk:
    "This clause could let the lender demand your entire outstanding loan immediately if you miss even one payment, not just the overdue amount.",
  legal_clause_detection:
    "This is a legal clause that limits your options or shifts responsibility onto you — worth understanding fully before agreeing.",
  financial_entity_extraction:
    "This is a financial figure or term mentioned in your agreement. It's flagged so you can quickly locate and verify all the numbers.",
  power_imbalance_risk:
    "This gives the lender broad, one-sided control over decisions that affect you — such terms can be used unfairly without your input.",
  privacy_data_risk:
    "This may allow the lender to access personal data on your phone beyond what's needed for the loan, which goes against RBI data-minimization rules.",
  regulatory_compliance:
    "This relates to a regulatory requirement digital lenders must follow under RBI guidelines — check if it's properly disclosed here.",
  predatory_lending_signals:
    "This is a known predatory lending pattern. RBI guidelines specifically prohibit this practice to protect borrowers.",
};

export function explanationFor(flag: string, categories: CategoryBreakdown[]): {
  category: CategoryBreakdown | null;
  explanation: string;
} {
  const match = categories.find((cat) =>
    cat.matched_keywords.some((kw) => kw.toLowerCase() === flag.toLowerCase())
  );
  if (!match) {
    return {
      category: null,
      explanation: "This term was flagged as part of LoanGuard's risk scan and may be worth a closer look.",
    };
  }
  return {
    category: match,
    explanation:
      CATEGORY_EXPLANATIONS[match.category_id] ??
      "This term was flagged as part of LoanGuard's risk scan and may be worth a closer look.",
  };
}
