"use client";

import { Collapsible } from "@/components/ui/collapsible";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import type { AnalysisOptions } from "@/lib/schemas";

export function AnalysisOptionsPanel({
  options,
  onChange,
}: {
  options: AnalysisOptions;
  onChange: (options: AnalysisOptions) => void;
}) {
  function set<K extends keyof AnalysisOptions>(key: K, value: AnalysisOptions[K]) {
    onChange({ ...options, [key]: value });
  }

  return (
    <Collapsible title="Advanced Options">
      <div className="divide-y divide-border">
        <Switch
          id="run_sentiment"
          label="Run Sentiment Analysis"
          description="Detects threatening or aggressive language"
          checked={options.run_sentiment}
          onCheckedChange={(v) => set("run_sentiment", v)}
        />
        <Switch
          id="run_ner"
          label="Run Named Entity Recognition"
          description="Extracts amounts, rates, fees, and regulations"
          checked={options.run_ner}
          onCheckedChange={(v) => set("run_ner", v)}
        />
        <Switch
          id="run_summary"
          label="Run Extractive Summary"
          description="Highlights the most important sentences"
          checked={options.run_summary}
          onCheckedChange={(v) => set("run_summary", v)}
        />
        <Switch
          id="run_tfidf"
          label="Run TF-IDF Terms"
          description="Surfaces the document's most distinctive terms"
          checked={options.run_tfidf}
          onCheckedChange={(v) => set("run_tfidf", v)}
        />
        <Switch
          id="run_classifier"
          label="Run Document Classifier"
          description="Predicts risk category per text chunk"
          checked={options.run_classifier}
          onCheckedChange={(v) => set("run_classifier", v)}
        />
        <Switch
          id="run_rag"
          label="Run AI Explainer (RAG)"
          description="Adds a should-you-sign verdict with RBI sources — slower"
          checked={options.run_rag}
          onCheckedChange={(v) => set("run_rag", v)}
        />
      </div>
      <div className="mt-3 space-y-1">
        <Slider
          id="summary_top_n"
          label="Summary sentences"
          value={options.summary_top_n}
          min={1}
          max={10}
          onChange={(v) => set("summary_top_n", v)}
        />
        <Slider
          id="tfidf_top_n"
          label="TF-IDF terms"
          value={options.tfidf_top_n}
          min={1}
          max={50}
          onChange={(v) => set("tfidf_top_n", v)}
        />
      </div>
    </Collapsible>
  );
}
