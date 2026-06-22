"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileSearch, History } from "lucide-react";
import { cn } from "@/lib/utils";
import { LoanGuardWordmark, ShieldLogo } from "@/components/shared/ShieldLogo";

const NAV_ITEMS = [
  { href: "/dashboard/analyze", label: "Analyze", icon: FileSearch },
  { href: "/dashboard/history", label: "History", icon: History },
];

export function DashboardNav() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:w-60 md:flex-col md:border-r md:border-border md:bg-card md:py-6 md:px-4">
        <Link href="/" className="mb-8 px-2">
          <LoanGuardWordmark />
        </Link>
        <nav className="flex flex-1 flex-col gap-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-blue-50 text-primary"
                    : "text-text-muted hover:bg-slate-50 hover:text-text-primary"
                )}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-border pt-4 px-2">
          <p className="text-xs text-text-muted">
            100% offline processing.
            <br />
            Your documents are never stored beyond this session.
          </p>
        </div>
      </aside>

      {/* Mobile bottom tab bar */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 flex border-t border-border bg-card md:hidden">
        {NAV_ITEMS.map((item) => {
          const active = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-1 flex-col items-center gap-1 py-2.5 text-xs font-medium",
                active ? "text-primary" : "text-text-muted"
              )}
            >
              <Icon size={20} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}

export function MobileTopBar() {
  return (
    <header className="flex items-center justify-between border-b border-border bg-card px-4 py-3 md:hidden">
      <div className="flex items-center gap-2">
        <ShieldLogo size={24} />
        <span className="font-display text-base font-bold text-text-primary">
          LoanGuard <span className="text-primary">AI</span>
        </span>
      </div>
    </header>
  );
}
