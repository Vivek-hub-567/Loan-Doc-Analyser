import { cn } from "@/lib/utils";

export function ShieldLogo({
  className,
  size = 28,
  animate = false,
}: {
  className?: string;
  size?: number;
  animate?: boolean;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 36"
      fill="none"
      className={cn(animate && "animate-pulse-once", className)}
      aria-hidden
    >
      <path
        d="M16 1.5L29.5 6.5V16.8C29.5 25.5 23.8 31.6 16 34.5C8.2 31.6 2.5 25.5 2.5 16.8V6.5L16 1.5Z"
        fill="#1B4FD8"
      />
      <path
        d="M10.5 17.5L14.5 21.5L21.5 13.5"
        stroke="white"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function LoanGuardWordmark({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2", className)}>
      <ShieldLogo size={26} />
      <span className="font-display text-lg font-bold text-text-primary">
        LoanGuard <span className="text-primary">AI</span>
      </span>
    </span>
  );
}
