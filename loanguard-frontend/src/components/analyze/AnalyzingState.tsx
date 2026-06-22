"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldLogo } from "@/components/shared/ShieldLogo";

const STATUS_MESSAGES = [
  "Preprocessing text...",
  "Running keyword extraction...",
  "Analyzing sentiment...",
  "Extracting named entities...",
  "Generating summary...",
  "Computing risk score...",
];

export function AnalyzingState() {
  const [messageIndex, setMessageIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const messageTimer = setInterval(() => {
      setMessageIndex((i) => Math.min(i + 1, STATUS_MESSAGES.length - 1));
    }, 900);
    const clockTimer = setInterval(() => setElapsed((e) => e + 0.1), 100);
    return () => {
      clearInterval(messageTimer);
      clearInterval(clockTimer);
    };
  }, []);

  return (
    <div className="relative flex flex-col items-center gap-5 overflow-hidden rounded-card border border-border bg-card p-10">
      <div className="relative h-28 w-20 rounded-md border-2 border-border bg-surface">
        <div className="absolute inset-x-0 top-0 h-0.5 animate-scanline bg-primary shadow-[0_0_8px_2px_rgba(27,79,216,0.6)]" />
        <div className="space-y-1.5 p-2">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-1 rounded-full bg-slate-200" style={{ width: `${70 + (i % 3) * 10}%` }} />
          ))}
        </div>
      </div>

      <ShieldLogo size={28} />

      <AnimatePresence mode="wait">
        <motion.p
          key={messageIndex}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          className="text-sm font-medium text-text-primary"
        >
          {STATUS_MESSAGES[messageIndex]}
        </motion.p>
      </AnimatePresence>

      <span className="text-xs tabular-nums text-text-muted">{elapsed.toFixed(1)}s</span>
    </div>
  );
}
