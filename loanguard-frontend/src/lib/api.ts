import axios, { AxiosError } from "axios";
import {
  AnalyzeResponseSchema,
  CategoriesResponseSchema,
  HealthResponseSchema,
  HistoryItemSchema,
  type AnalysisOptions,
  type AnalyzeResponse,
  type CategoriesResponse,
  type ErrorResponse,
  type HealthResponse,
  type HistoryItem,
} from "./schemas";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60_000,
});

/** Normalized error shape the UI can always rely on, regardless of failure mode. */
export class LoanGuardApiError extends Error {
  status: number;
  title: string;
  requestId: string;

  constructor(opts: {
    message: string;
    status: number;
    title: string;
    requestId?: string;
  }) {
    super(opts.message);
    this.status = opts.status;
    this.title = opts.title;
    this.requestId = opts.requestId ?? "";
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ErrorResponse>) => {
    if (error.response?.data && typeof error.response.data === "object") {
      const body = error.response.data;
      throw new LoanGuardApiError({
        message: body.detail || error.message,
        status: body.status || error.response.status,
        title: body.title || "Request Failed",
        requestId: body.request_id,
      });
    }
    if (error.code === "ECONNABORTED") {
      throw new LoanGuardApiError({
        message: "The analysis is taking longer than expected. Please try again.",
        status: 408,
        title: "Request Timed Out",
      });
    }
    if (!error.response) {
      throw new LoanGuardApiError({
        message:
          "Could not reach the LoanGuard server. Check that the backend is running on " +
          API_BASE_URL,
        status: 0,
        title: "Network Error",
      });
    }
    throw new LoanGuardApiError({
      message: error.message,
      status: error.response.status,
      title: "Request Failed",
    });
  }
);

// ---------------------------------------------------------------------------
// POST /analyze — text analysis
// ---------------------------------------------------------------------------
export async function analyzeText(
  text: string,
  options: AnalysisOptions
): Promise<AnalyzeResponse> {
  const { data } = await apiClient.post("/analyze", { text, options });
  return AnalyzeResponseSchema.parse(data);
}

// ---------------------------------------------------------------------------
// POST /analyze/file — file upload analysis (.pdf, .docx, .txt only — backend
// has no OCR/image support, so image upload is intentionally not offered)
// ---------------------------------------------------------------------------
export async function analyzeFile(file: File): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post("/analyze/file", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return AnalyzeResponseSchema.parse(data);
}

// ---------------------------------------------------------------------------
// GET /categories
// ---------------------------------------------------------------------------
export async function getCategories(): Promise<CategoriesResponse> {
  const { data } = await apiClient.get("/categories");
  return CategoriesResponseSchema.parse(data);
}

// ---------------------------------------------------------------------------
// GET /history/{doc_id}
// ---------------------------------------------------------------------------
export async function getHistoryItem(docId: string): Promise<HistoryItem> {
  const { data } = await apiClient.get(`/history/${docId}`);
  return HistoryItemSchema.parse(data);
}

// ---------------------------------------------------------------------------
// DELETE /history/{doc_id}
// ---------------------------------------------------------------------------
export async function deleteHistoryItem(
  docId: string
): Promise<{ deleted: boolean; doc_id: string }> {
  const { data } = await apiClient.delete(`/history/${docId}`);
  return data;
}

// ---------------------------------------------------------------------------
// GET /health
// ---------------------------------------------------------------------------
export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get("/health");
  return HealthResponseSchema.parse(data);
}
