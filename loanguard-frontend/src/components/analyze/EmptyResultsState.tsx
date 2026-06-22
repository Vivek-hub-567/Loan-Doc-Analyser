import { ShieldQuestion } from "lucide-react";

export function EmptyResultsState() {
  return (
    <div className="flex flex-col items-center gap-6 rounded-card border border-dashed border-border bg-card p-10 text-center">
      <ShieldQuestion size={48} className="text-slate-300" strokeWidth={1.5} />
      <div>
        <p className="font-display font-semibold text-text-primary">Your risk report will appear here</p>
        <p className="mt-1 text-sm text-text-muted">Upload or paste a loan agreement to get started.</p>
      </div>

      <div className="w-full max-w-sm space-y-2 opacity-40 blur-[1px]" aria-hidden>
        {[
          { label: "Upfront fee deduction", severity: "bg-red-100" },
          { label: "Penal charges on full amount", severity: "bg-amber-100" },
          { label: "SMS access permission", severity: "bg-blue-100" },
        ].map((item, i) => (
          <div key={i} className="flex items-center gap-3 rounded-lg border border-border bg-surface p-3 text-left">
            <span className={`h-2 w-2 rounded-full ${item.severity}`} />
            <span className="text-sm text-text-muted">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
