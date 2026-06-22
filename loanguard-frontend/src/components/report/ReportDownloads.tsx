"use client";

import { Download, FileJson, FileSpreadsheet } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import type { AnalyzeResponse } from "@/lib/schemas";

function downloadBlob(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ReportDownloads({ result }: { result: AnalyzeResponse }) {
  function handleJsonExport() {
    downloadBlob(
      JSON.stringify(result, null, 2),
      `loanguard-report-${result.doc_id.slice(0, 8)}.json`,
      "application/json"
    );
    toast.success("JSON report downloaded.");
  }

  function handleCsvExport() {
    const rows = [["Category", "Severity", "Keyword"]];
    result.category_breakdown.forEach((cat) => {
      cat.matched_keywords.forEach((kw) => {
        rows.push([cat.label, cat.severity, kw]);
      });
    });
    const csv = rows.map((r) => r.map((v) => `"${v.replace(/"/g, '""')}"`).join(",")).join("\n");
    downloadBlob(csv, `loanguard-keywords-${result.doc_id.slice(0, 8)}.csv`, "text/csv");
    toast.success("CSV of keywords downloaded.");
  }

  function handlePdfExport() {
    toast.info("PDF export requires a print-to-PDF step for now — opening print dialog.");
    window.print();
  }

  return (
    <div className="flex flex-wrap gap-2">
      <Button variant="outline" size="sm" onClick={handlePdfExport}>
        <Download size={14} /> PDF report
      </Button>
      <Button variant="outline" size="sm" onClick={handleJsonExport}>
        <FileJson size={14} /> JSON export
      </Button>
      <Button variant="outline" size="sm" onClick={handleCsvExport}>
        <FileSpreadsheet size={14} /> CSV of keywords
      </Button>
    </div>
  );
}
