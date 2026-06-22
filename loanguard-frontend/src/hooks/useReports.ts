import { useQuery } from "@tanstack/react-query";
import { useAnalysisStore } from "@/stores/analysisStore";
import { getHistoryItem } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/schemas";

/**
 * Reports are looked up client-side first (the cached AnalyzeResponse saved
 * at analysis time). If not found locally — e.g. opened in a different
 * browser/session — we fall back to GET /history/{doc_id}, which only works
 * if the backend's in-memory store still has it (it resets on restart).
 */
export function useReport(docId: string) {
  const cached = useAnalysisStore((s) => s.getEntry(docId));

  const query = useQuery({
    queryKey: ["report", docId],
    queryFn: async (): Promise<AnalyzeResponse | null> => {
      const item = await getHistoryItem(docId);
      return item.result ?? null;
    },
    enabled: !cached,
    retry: false,
  });

  return {
    result: cached?.cachedResult ?? query.data ?? null,
    isLoading: !cached && query.isLoading,
    isError: !cached && query.isError,
    notFoundLocally: !cached,
  };
}
