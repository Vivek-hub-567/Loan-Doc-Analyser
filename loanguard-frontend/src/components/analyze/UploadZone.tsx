"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { FileText, X } from "lucide-react";
import { ShieldLogo } from "@/components/shared/ShieldLogo";
import { Badge } from "@/components/ui/badge";
import { formatFileSize } from "@/lib/utils";
import { cn } from "@/lib/utils";

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

export function UploadZone({
  file,
  onFileSelect,
  onFileRemove,
}: {
  file: File | null;
  onFileSelect: (file: File) => void;
  onFileRemove: () => void;
}) {
  const onDrop = useCallback(
    (accepted: File[], rejected: import("react-dropzone").FileRejection[]) => {
      if (rejected.length > 0) {
        const reason = rejected[0].errors[0]?.message ?? "File could not be accepted.";
        import("sonner").then(({ toast }) => toast.error(reason));
        return;
      }
      if (accepted[0]) onFileSelect(accepted[0]);
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive, isDragAccept } = useDropzone({
    onDrop,
    maxFiles: 1,
    maxSize: MAX_FILE_SIZE_BYTES,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
  });

  if (file) {
    return (
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50">
            <FileText size={20} className="text-primary" />
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="truncate text-sm font-medium text-text-primary">{file.name}</p>
            <p className="text-xs text-text-muted">{formatFileSize(file.size)}</p>
          </div>
          <button
            onClick={onFileRemove}
            className="rounded-full p-1.5 text-text-muted hover:bg-slate-100 hover:text-text-primary"
            aria-label="Remove file"
          >
            <X size={16} />
          </button>
        </div>
        <Badge className="mt-3 bg-green-50 text-success border border-green-200">
          Ready to analyze
        </Badge>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors",
        isDragActive && isDragAccept && "border-primary bg-blue-50 animate-pulse-once",
        isDragActive && !isDragAccept && "border-danger bg-red-50",
        !isDragActive && "border-border bg-card hover:border-primary hover:bg-blue-50/50"
      )}
    >
      <input {...getInputProps()} />
      <ShieldLogo size={36} />
      <div>
        <p className="text-sm font-medium text-text-primary">
          Drop your loan agreement here, or click to browse
        </p>
        <p className="mt-1 text-xs text-text-muted">PDF, DOCX, or TXT · max 5MB</p>
      </div>
    </div>
  );
}
