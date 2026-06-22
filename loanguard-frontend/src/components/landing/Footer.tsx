import Link from "next/link";
import { LoanGuardWordmark } from "@/components/shared/ShieldLogo";

export function Footer() {
  return (
    <footer className="border-t border-border bg-card px-4 py-10 sm:px-6">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
        <LoanGuardWordmark />
        <p className="text-xs text-text-muted">
          Built to help Indian borrowers read the fine print. Not a substitute for legal advice.
        </p>
        <div className="flex gap-4 text-sm text-text-muted">
          <Link href="/dashboard/analyze" className="hover:text-primary">Analyze</Link>
          <Link href="/dashboard/history" className="hover:text-primary">History</Link>
        </div>
      </div>
    </footer>
  );
}
