import { useMutation } from "@tanstack/react-query";
import { analyzeText, analyzeFile, LoanGuardApiError } from "@/lib/api";
import { useAnalysisStore } from "@/stores/analysisStore";
import type { AnalysisOptions } from "@/lib/schemas";
import { toast } from "sonner";

export function useAnalyzeText() {
  const addEntry = useAnalysisStore((s) => s.addEntry);

  return useMutation({
    mutationFn: ({ text, options }: { text: string; options: AnalysisOptions }) =>
      analyzeText(text, options),
    onSuccess: (result, variables) => {
      addEntry(result, variables.text);
    },
    onError: (error) => {
      const message =
        error instanceof LoanGuardApiError ? error.message : "Something went wrong during analysis.";
      toast.error(message);
    },
  });
}

export function useAnalyzeFile() {
  const addEntry = useAnalysisStore((s) => s.addEntry);

  return useMutation({
    mutationFn: (file: File) => analyzeFile(file),
    onSuccess: (result) => {
      addEntry(result);
    },
    onError: (error) => {
      const message =
        error instanceof LoanGuardApiError ? error.message : "Something went wrong during analysis.";
      toast.error(message);
    },
  });
}
