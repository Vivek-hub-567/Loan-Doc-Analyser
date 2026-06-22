"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import { Tabs } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { UploadZone } from "@/components/analyze/UploadZone";
import { TextInput } from "@/components/analyze/TextInput";
import { AnalysisOptionsPanel } from "@/components/analyze/AnalysisOptionsPanel";
import { AnalyzingState } from "@/components/analyze/AnalyzingState";
import { EmptyResultsState } from "@/components/analyze/EmptyResultsState";
import { RiskScoreHero } from "@/components/analyze/RiskScoreHero";
import { SentimentPanel } from "@/components/analyze/SentimentPanel";
import { CategoryGrid } from "@/components/analyze/CategoryGrid";
import { EntityChips } from "@/components/analyze/EntityChips";
import { TopFlags } from "@/components/analyze/TopFlags";
import { SummaryCard } from "@/components/analyze/SummaryCard";
import { RAGResultCard } from "@/components/analyze/RAGResultCard";
import { useAnalyzeText, useAnalyzeFile } from "@/hooks/useAnalyze";
import { DEFAULT_ANALYSIS_OPTIONS, type AnalysisOptions } from "@/lib/schemas";

const MIN_WORDS = 50;

export default function AnalyzePage() {
  const [activeTab, setActiveTab] = useState("upload");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [options, setOptions] = useState<AnalysisOptions>(DEFAULT_ANALYSIS_OPTIONS);

  const analyzeTextMutation = useAnalyzeText();
  const analyzeFileMutation = useAnalyzeFile();

  const isAnalyzing = analyzeTextMutation.isPending || analyzeFileMutation.isPending;
  const result = analyzeTextMutation.data ?? analyzeFileMutation.data;

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const canSubmit =
    activeTab === "upload" ? file !== null : wordCount >= MIN_WORDS;

  function handleAnalyze() {
    if (activeTab === "upload" && file) {
      analyzeFileMutation.mutate(file);
    } else if (activeTab === "paste" && wordCount >= MIN_WORDS) {
      analyzeTextMutation.mutate({ text, options });
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-10">
      <div className="mb-6">
        <h1 className="font-display text-xl font-bold text-text-primary sm:text-2xl">
          Analyze your agreement
        </h1>
        <p className="mt-1 text-sm text-text-muted">
          Upload a PDF/DOCX/TXT file, or paste the text directly.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Left column — Input */}
        <div className="space-y-4">
          <Tabs
            value={activeTab}
            onChange={setActiveTab}
            tabs={[
              { value: "upload", label: "Upload File" },
              { value: "paste", label: "Paste Text" },
            ]}
          />

          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
            >
              {activeTab === "upload" ? (
                <UploadZone file={file} onFileSelect={setFile} onFileRemove={() => setFile(null)} />
              ) : (
                <TextInput value={text} onChange={setText} />
              )}
            </motion.div>
          </AnimatePresence>

          {activeTab === "paste" && (
            <AnalysisOptionsPanel options={options} onChange={setOptions} />
          )}

          <Button
            size="lg"
            className="w-full"
            disabled={!canSubmit || isAnalyzing}
            onClick={handleAnalyze}
          >
            <ShieldCheck size={18} />
            {isAnalyzing ? "Scanning document..." : "Analyze Agreement"}
          </Button>
          {activeTab === "upload" && (
            <p className="text-center text-xs text-text-muted">
              File uploads always run the full pipeline with default options.
            </p>
          )}
        </div>

        {/* Right column — Results */}
        <div className="space-y-4">
          {isAnalyzing && <AnalyzingState />}
          {!isAnalyzing && !result && <EmptyResultsState />}
          {!isAnalyzing && result && (
            <motion.div
              initial="hidden"
              animate="visible"
              variants={{
                visible: { transition: { staggerChildren: 0.05 } },
              }}
              className="space-y-4"
            >
              <RiskScoreHero result={result} />
              {result.sentiment && <SentimentPanel sentiment={result.sentiment} />}
              {result.category_breakdown.length > 0 && (
                <CategoryGrid categories={result.category_breakdown} />
              )}
              {result.entities && <EntityChips entities={result.entities} />}
              <TopFlags flags={result.top_flags} categories={result.category_breakdown} />
              {result.summary && <SummaryCard summary={result.summary} />}
              {result.rag_result && <RAGResultCard rag={result.rag_result} />}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
