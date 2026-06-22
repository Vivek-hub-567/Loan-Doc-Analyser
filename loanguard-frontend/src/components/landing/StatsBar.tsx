const STATS = [
  { value: "130+", label: "Risk Keywords" },
  { value: "8", label: "Risk Categories" },
  { value: "DPDP & RBI", label: "Regulations Checked" },
  { value: "100%", label: "Offline Processing" },
];

export function StatsBar() {
  return (
    <section className="border-y border-border bg-card px-4 py-10 sm:px-6">
      <div className="mx-auto grid max-w-4xl grid-cols-2 gap-6 sm:grid-cols-4">
        {STATS.map((stat) => (
          <div key={stat.label} className="text-center">
            <p className="font-display text-2xl font-bold text-primary">{stat.value}</p>
            <p className="mt-1 text-xs text-text-muted">{stat.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
