"use client";

import { X } from "lucide-react";

const MIN_WORDS = 50;
const MAX_CHARS = 50_000;

export function TextInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  const wordCount = value.trim() ? value.trim().split(/\s+/).length : 0;
  const charCount = value.length;
  const charPct = Math.min((charCount / MAX_CHARS) * 100, 100);
  const belowMinimum = wordCount > 0 && wordCount < MIN_WORDS;

  return (
    <div>
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Paste your loan agreement text here..."
          maxLength={MAX_CHARS}
          className="min-h-[300px] w-full resize-y rounded-lg border border-border bg-card p-4 font-mono text-sm text-text-primary placeholder:text-text-muted focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
        {value.length > 0 && (
          <button
            onClick={() => onChange("")}
            className="absolute right-3 top-3 rounded-full bg-white p-1.5 text-text-muted shadow-sm hover:text-text-primary"
            aria-label="Clear text"
          >
            <X size={14} />
          </button>
        )}
      </div>

      <div className="mt-2 flex items-center justify-between text-xs">
        <span className={belowMinimum ? "font-medium text-warning" : "text-text-muted"}>
          {belowMinimum && `⚠ Minimum ${MIN_WORDS} words required — `}
          {wordCount.toLocaleString()} / 50,000 words
        </span>
        <span className="text-text-muted">{charCount.toLocaleString()} / {MAX_CHARS.toLocaleString()} chars</span>
      </div>
      <div className="mt-1 h-1 w-full rounded-pill bg-slate-200">
        <div
          className="h-1 rounded-pill bg-primary transition-all"
          style={{ width: `${charPct}%` }}
        />
      </div>
    </div>
  );
}
