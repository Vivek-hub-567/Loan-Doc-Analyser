import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AnalyzeResponse, RiskLevel, SentimentLabel } from "@/lib/schemas";

/**
 * The backend only exposes GET/DELETE /history/{doc_id} — there is no
 * "list all" endpoint. To power a History page at all, the frontend keeps
 * its own lightweight index of every analysis run in this browser, in
 * localStorage. The full AnalyzeResponse is cached too, so opening a past
 * report doesn't require the backend to still have it in memory (its
 * DatabaseService is in-memory only and resets on every server restart).
 */
export interface HistoryEntry {
  docId: string;
  analyzedAt: string; // ISO timestamp, client-set
  fileName: string | null;
  fileType: string | null;
  riskScore: number;
  riskLevel: RiskLevel;
  sentimentLabel: SentimentLabel | null;
  topFlag: string | null;
  cachedResult: AnalyzeResponse;
  /**
   * The original text that was submitted for analysis (pasted text, or
   * text extracted client-side isn't available for file uploads — only
   * pasted-text submissions can populate this). Used to render an annotated
   * document view, since the backend doesn't echo back source text or
   * keyword character offsets in category_breakdown.
   */
  sourceText: string | null;
}

interface AnalysisState {
  history: HistoryEntry[];
  addEntry: (result: AnalyzeResponse, sourceText?: string | null) => void;
  removeEntry: (docId: string) => void;
  getEntry: (docId: string) => HistoryEntry | undefined;
  clearAll: () => void;
}

export const useAnalysisStore = create<AnalysisState>()(
  persist(
    (set, get) => ({
      history: [],
      addEntry: (result, sourceText = null) => {
        const entry: HistoryEntry = {
          docId: result.doc_id,
          analyzedAt: new Date().toISOString(),
          fileName: result.file_name ?? null,
          fileType: result.file_type ?? null,
          riskScore: result.risk_score,
          riskLevel: result.risk_level,
          sentimentLabel: result.sentiment?.label ?? null,
          topFlag: result.top_flags?.[0] ?? null,
          cachedResult: result,
          sourceText,
        };
        set((state) => ({
          history: [entry, ...state.history.filter((h) => h.docId !== result.doc_id)],
        }));
      },
      removeEntry: (docId) => {
        set((state) => ({
          history: state.history.filter((h) => h.docId !== docId),
        }));
      },
      getEntry: (docId) => get().history.find((h) => h.docId === docId),
      clearAll: () => set({ history: [] }),
    }),
    { name: "loanguard-history" }
  )
);
