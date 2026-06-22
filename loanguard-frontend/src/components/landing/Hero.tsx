"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, PlayCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ShieldLogo } from "@/components/shared/ShieldLogo";

function FloatingParticle({ delay, x, y, size }: { delay: number; x: string; y: string; size: number }) {
  return (
    <motion.div
      className="absolute rounded-full bg-primary/10"
      style={{ left: x, top: y, width: size, height: size }}
      animate={{ y: [0, -16, 0], opacity: [0.4, 0.8, 0.4] }}
      transition={{ duration: 6, repeat: Infinity, delay, ease: "easeInOut" }}
    />
  );
}

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-blue-50/60 to-surface px-4 pt-16 pb-20 sm:px-6 sm:pt-24">
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <FloatingParticle delay={0} x="8%" y="20%" size={10} />
        <FloatingParticle delay={1.2} x="85%" y="15%" size={14} />
        <FloatingParticle delay={0.6} x="15%" y="70%" size={8} />
        <FloatingParticle delay={1.8} x="80%" y="65%" size={12} />
        <FloatingParticle delay={2.4} x="50%" y="10%" size={6} />
      </div>

      <div className="relative mx-auto max-w-3xl text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="mx-auto mb-6 flex h-16 w-16 items-center justify-center"
        >
          <ShieldLogo size={56} animate />
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="font-display text-3xl font-bold tracking-tight text-text-primary sm:text-5xl"
        >
          Read Before You Sign.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mx-auto mt-4 max-w-xl text-base text-text-muted sm:text-lg"
        >
          LoanGuard AI scans your loan agreement in seconds and flags hidden fees,
          predatory clauses, and RBI violations — in plain language.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row"
        >
          <Link href="/dashboard/analyze">
            <Button size="lg">
              Analyze My Agreement <ArrowRight size={18} />
            </Button>
          </Link>
          <a href="#how-it-works">
            <Button variant="ghost" size="lg">
              <PlayCircle size={18} /> See How It Works
            </Button>
          </a>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="mt-8 text-xs font-medium text-text-muted"
        >
          Checks against 130+ risk signals · 8 risk categories · RBI Digital Lending Guidelines 2022–2025
        </motion.p>
      </div>
    </section>
  );
}
