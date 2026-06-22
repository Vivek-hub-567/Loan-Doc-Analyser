export function CheckShieldIcon({ size = 20, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <circle cx="12" cy="12" r="11" fill="#16A34A" />
      <path d="M7.5 12.5L10.5 15.5L16.5 8.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function WarningTriangleIcon({ size = 20, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <path d="M12 3L22 20H2L12 3Z" fill="#D97706" />
      <rect x="11" y="9" width="2" height="6" rx="1" fill="white" />
      <rect x="11" y="16.5" width="2" height="2" rx="1" fill="white" />
    </svg>
  );
}

export function StopOctagonIcon({ size = 20, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className}>
      <path
        d="M8 2H16L22 8V16L16 22H8L2 16V8L8 2Z"
        fill="#DC2626"
      />
      <path d="M9 9L15 15M15 9L9 15" stroke="white" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
