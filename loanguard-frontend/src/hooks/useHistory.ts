import { useMutation } from "@tanstack/react-query";
import { useAnalysisStore } from "@/stores/analysisStore";
import { deleteHistoryItem, LoanGuardApiError } from "@/lib/api";
import { toast } from "sonner";

/**
 * History is sourced entirely from the client-side Zustand store, since the
 * backend has no GET /history (list-all) endpoint — only GET/DELETE by
 * doc_id against an in-memory store that resets on server restart. Deleting
 * also calls the backend best-effort, but always removes locally regardless
 * of whether the backend still has the record.
 */
export function useHistory() {
  return useAnalysisStore((s) => s.history);
}

export function useDeleteHistoryItem() {
  const removeEntry = useAnalysisStore((s) => s.removeEntry);

  return useMutation({
    mutationFn: async (docId: string) => {
      try {
        await deleteHistoryItem(docId);
      } catch (error) {
        // Backend may have already lost this record (in-memory store reset).
        // That's fine — we still remove it from the local index.
        if (!(error instanceof LoanGuardApiError && error.status === 404)) {
          throw error;
        }
      }
      return docId;
    },
    onSuccess: (docId) => {
      removeEntry(docId);
      toast.success("Analysis deleted.");
    },
    onError: () => {
      toast.error("Could not delete this analysis. Please try again.");
    },
  });
}
