"use client";

import { motion } from "framer-motion";
import { Download, Share2 } from "lucide-react";
import { toast } from "sonner";
import { RiskGauge } from "./RiskGauge";
import { RiskLevelBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { signVerdict } from "@/lib/severity";
import { formatProcessingTime } from "@/lib/utils";
import { CheckShieldIcon, StopOctagonIcon, WarningTriangleIcon } from "@/components/shared/VerdictIcons";
import type { AnalyzeResponse } from "@/lib/schemas";

export function RiskScoreHero({ result }: { result: AnalyzeResponse }) {
  const verdict = signVerdict(result.should_sign, result.risk_level);

  const VerdictIcon =
    verdict.tone === "success"
      ? CheckShieldIcon
      : verdict.tone === "danger"
      ? StopOctagonIcon
      : WarningTriangleIcon;

  const verdictColor =
    verdict.tone === "success"
      ? "text-success"
      : verdict.tone === "danger"
      ? "text-danger"
      : "text-warning";

  function handleShare() {
    const url = `${window.location.origin}/dashboard/report/${result.doc_id}`;
    navigator.clipboard.writeText(url);
    toast.success("Report link copied to clipboard.");
  }

  function handleDownload() {
    toast.info("Generating PDF report...");
    // Hook point for a real PDF export call; kept client-side for now.
  }

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="p-6">
        <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col items-center gap-3 sm:flex-row sm:items-center sm:gap-6">
            <RiskGauge score={result.risk_score} size={160} />
            <div className="flex flex-col items-center gap-2 sm:items-start">
              <RiskLevelBadge level={result.risk_level} className="px-3 py-1 text-sm" />
              <div className={`flex items-center gap-2 font-display text-lg font-semibold ${verdictColor}`}>
                <VerdictIcon size={22} />
                {verdict.label}
              </div>
              <p className="text-xs text-text-muted">
                Analyzed in {formatProcessingTime(result.processing_time_ms)}
              </p>
            </div>
          </div>
          <div className="flex w-full gap-2 sm:w-auto">
            <Button variant="outline" size="md" className="flex-1 sm:flex-none" onClick={handleShare}>
              <Share2 size={16} /> Share
            </Button>
            <Button variant="primary" size="md" className="flex-1 sm:flex-none" onClick={handleDownload}>
              <Download size={16} /> Download PDF
            </Button>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
