import type { RiskLevel, SentimentLabel } from "@/lib/schemas";

export type SeverityKey = "CRITICAL" | "HIGH" | "MEDIUM" | "INFO";

interface SeverityStyle {
  label: string;
  text: string;
  bg: string;
  border: string;
  dot: string;
  underline: string;
}

/** Severity color map — consistent everywhere per design system. */
export const SEVERITY: Record<SeverityKey, SeverityStyle> = {
  CRITICAL: {
    label: "Critical",
    text: "text-danger",
    bg: "bg-red-50",
    border: "border-red-200",
    dot: "#DC2626",
    underline: "kw-critical",
  },
  HIGH: {
    label: "High",
    text: "text-warning",
    bg: "bg-amber-50",
    border: "border-amber-200",
    dot: "#D97706",
    underline: "kw-high",
  },
  MEDIUM: {
    label: "Medium",
    text: "text-info",
    bg: "bg-blue-50",
    border: "border-blue-200",
    dot: "#2563EB",
    underline: "kw-medium",
  },
  INFO: {
    label: "Info",
    text: "text-text-muted",
    bg: "bg-slate-50",
    border: "border-slate-200",
    dot: "#64748B",
    underline: "kw-info",
  },
};

export function severityFor(raw: string): SeverityStyle {
  const key = raw.toUpperCase() as SeverityKey;
  return SEVERITY[key] ?? SEVERITY.INFO;
}

interface RiskLevelStyle {
  label: RiskLevel;
  badgeBg: string;
  badgeText: string;
  gaugeColor: string;
}

/** Risk level badge colors. */
export const RISK_LEVEL: Record<RiskLevel, RiskLevelStyle> = {
  CRITICAL: {
    label: "CRITICAL",
    badgeBg: "bg-danger",
    badgeText: "text-white",
    gaugeColor: "#DC2626",
  },
  HIGH: {
    label: "HIGH",
    badgeBg: "bg-warning",
    badgeText: "text-[#0F172A]",
    gaugeColor: "#F97316",
  },
  MEDIUM: {
    label: "MEDIUM",
    badgeBg: "bg-info",
    badgeText: "text-white",
    gaugeColor: "#EAB308",
  },
  LOW: {
    label: "LOW",
    badgeBg: "bg-success",
    badgeText: "text-[#0F172A]",
    gaugeColor: "#16A34A",
  },
};

/** Gauge color purely by numeric score, per spec: green<30, yellow 30-60, orange 60-80, red>80 */
export function gaugeColorForScore(score: number): string {
  if (score > 80) return "#DC2626";
  if (score > 60) return "#F97316";
  if (score >= 30) return "#EAB308";
  return "#16A34A";
}

interface SentimentStyle {
  label: string;
  bg: string;
  text: string;
}

export const SENTIMENT_STYLE: Record<SentimentLabel, SentimentStyle> = {
  THREATENING: { label: "Threatening", bg: "bg-red-100", text: "text-danger" },
  NEGATIVE: { label: "Negative", bg: "bg-amber-100", text: "text-warning" },
  NEUTRAL: { label: "Neutral", bg: "bg-slate-100", text: "text-text-muted" },
  NEUTRAL_POSITIVE: { label: "Neutral / Positive", bg: "bg-blue-100", text: "text-info" },
  BORROWER_FRIENDLY: { label: "Borrower Friendly", bg: "bg-green-100", text: "text-success" },
};

/** "Should you sign?" verdict copy + color, derived from should_sign + risk_level */
export function signVerdict(shouldSign: boolean, riskLevel: RiskLevel) {
  if (shouldSign) {
    return { label: "Looks Safe", tone: "success" as const };
  }
  if (riskLevel === "CRITICAL") {
    return { label: "Do Not Sign", tone: "danger" as const };
  }
  return { label: "Review Carefully", tone: "warning" as const };
}
