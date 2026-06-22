import { DashboardNav, MobileTopBar } from "@/components/shared/DashboardNav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardNav />
      <div className="flex flex-1 flex-col">
        <MobileTopBar />
        <main className="flex-1 pb-20 md:pb-0">{children}</main>
      </div>
    </div>
  );
}
