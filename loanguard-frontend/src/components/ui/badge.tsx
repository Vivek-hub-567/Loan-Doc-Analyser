import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { RISK_LEVEL, SEVERITY, type SeverityKey } from "@/lib/severity";
import type { RiskLevel } from "@/lib/schemas";

export function Badge({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-pill px-2.5 py-0.5 text-xs font-medium",
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

export function RiskLevelBadge({
  level,
  className,
}: {
  level: RiskLevel;
  className?: string;
}) {
  const style = RISK_LEVEL[level];
  return (
    <Badge className={cn(style.badgeBg, style.badgeText, "font-semibold tracking-wide", className)}>
      {style.label}
    </Badge>
  );
}

export function SeverityBadge({
  severity,
  className,
}: {
  severity: string;
  className?: string;
}) {
  const key = severity.toUpperCase() as SeverityKey;
  const style = SEVERITY[key] ?? SEVERITY.INFO;
  return (
    <Badge className={cn(style.bg, style.text, "border", style.border, className)}>
      <span
        className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: style.dot }}
        aria-hidden
      />
      {style.label}
    </Badge>
  );
}
