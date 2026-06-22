"use client";

import { motion } from "framer-motion";
import { Upload, ScanSearch, FileCheck2 } from "lucide-react";

const STEPS = [
  {
    icon: Upload,
    title: "Upload your agreement",
    description: "PDF, DOCX, or TXT — or paste the text directly. Max 5MB.",
  },
  {
    icon: ScanSearch,
    title: "AI scans for risk signals",
    description: "130+ keyword patterns across 8 risk categories, in seconds.",
  },
  {
    icon: FileCheck2,
    title: "Get a plain-language report",
    description: "Every flag comes with a clear explanation — and what to do next.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="px-4 py-16 sm:px-6 sm:py-24">
      <div className="mx-auto max-w-5xl">
        <h2 className="text-center font-display text-2xl font-bold text-text-primary sm:text-3xl">
          How it works
        </h2>

        <div className="relative mt-12 grid grid-cols-1 gap-8 sm:grid-cols-3">
          <div
            className="absolute left-[16.5%] right-[16.5%] top-7 hidden h-px bg-border sm:block"
            aria-hidden
          />
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.12 }}
                className="relative flex flex-col items-center text-center"
              >
                <div className="z-10 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-white shadow-md">
                  <Icon size={24} />
                </div>
                <h3 className="mt-4 font-display font-semibold text-text-primary">{step.title}</h3>
                <p className="mt-1 text-sm text-text-muted">{step.description}</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
