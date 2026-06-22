import { z } from "zod";

// ---------------------------------------------------------------------------
// Request schemas — mirrors backend/schemas/request.py
// ---------------------------------------------------------------------------

export const AnalysisOptionsSchema = z.object({
  run_sentiment: z.boolean().default(true),
  run_ner: z.boolean().default(true),
  run_summary: z.boolean().default(true),
  run_tfidf: z.boolean().default(true),
  run_classifier: z.boolean().default(true),
  run_rag: z.boolean().default(false),
  summary_top_n: z.number().int().min(1).max(10).default(3),
  tfidf_top_n: z.number().int().min(1).max(50).default(15),
});
export type AnalysisOptions = z.infer<typeof AnalysisOptionsSchema>;

export const DEFAULT_ANALYSIS_OPTIONS: AnalysisOptions = {
  run_sentiment: true,
  run_ner: true,
  run_summary: true,
  run_tfidf: true,
  run_classifier: true,
  run_rag: false,
  summary_top_n: 3,
  tfidf_top_n: 15,
};

export const AnalyzeRequestSchema = z.object({
  text: z.string().min(1).max(50_000),
  options: AnalysisOptionsSchema,
});
export type AnalyzeRequest = z.infer<typeof AnalyzeRequestSchema>;

// ---------------------------------------------------------------------------
// Response schemas — mirrors backend/schemas/response.py
// ---------------------------------------------------------------------------

export const WorstClauseSchema = z.object({
  sentence: z.string(),
  compound: z.number(),
});

export const SentimentLabelSchema = z.enum([
  "THREATENING",
  "NEGATIVE",
  "NEUTRAL",
  "NEUTRAL_POSITIVE",
  "BORROWER_FRIENDLY",
]);
export type SentimentLabel = z.infer<typeof SentimentLabelSchema>;

export const SentimentResponseSchema = z.object({
  label: SentimentLabelSchema,
  compound_score: z.number(),
  positive: z.number(),
  negative: z.number(),
  neutral: z.number(),
  aggressive_score: z.number(),
  aggressive_hits: z.array(z.string()),
  friendly_score: z.number(),
  friendly_hits: z.array(z.string()),
  worst_clauses: z.array(WorstClauseSchema),
});
export type SentimentResponse = z.infer<typeof SentimentResponseSchema>;

export const EntityMatchSchema = z.object({
  text: z.string(),
  normalized: z.string(),
  start: z.number(),
  end: z.number(),
});
export type EntityMatch = z.infer<typeof EntityMatchSchema>;

export const EntitySummarySchema = z.object({
  total_entities: z.number(),
  money_mentions: z.number(),
  rate_mentions: z.number(),
  fee_mentions: z.number(),
  clause_types: z.array(z.string()).default([]),
  regulations: z.array(z.string()).default([]),
});

export const EntityResponseSchema = z.object({
  MONEY: z.array(EntityMatchSchema).default([]),
  RATE: z.array(EntityMatchSchema).default([]),
  FEE_AMOUNT: z.array(EntityMatchSchema).default([]),
  LOAN_AMOUNT: z.array(EntityMatchSchema).default([]),
  DURATION: z.array(EntityMatchSchema).default([]),
  DATE: z.array(EntityMatchSchema).default([]),
  ORG: z.array(EntityMatchSchema).default([]),
  CLAUSE_TYPE: z.array(EntityMatchSchema).default([]),
  REGULATION: z.array(EntityMatchSchema).default([]),
  summary: EntitySummarySchema,
});
export type EntityResponse = z.infer<typeof EntityResponseSchema>;

export const TFIDFTermSchema = z.object({
  term: z.string(),
  score: z.number(),
});
export type TFIDFTerm = z.infer<typeof TFIDFTermSchema>;

export const KeySentenceSchema = z.object({
  sentence: z.string(),
  score: z.number(),
  position: z.number(),
  rank: z.number(),
});

export const SummaryResponseSchema = z.object({
  text: z.string(),
  key_sentences: z.array(KeySentenceSchema),
  sentence_count: z.number(),
  compression_ratio: z.number(),
  method: z.enum(["textrank", "tfidf"]),
});
export type SummaryResponse = z.infer<typeof SummaryResponseSchema>;

export const SeveritySchema = z.enum(["CRITICAL", "HIGH", "MEDIUM", "INFO"]);
export type Severity = z.infer<typeof SeveritySchema>;

export const CategoryBreakdownSchema = z.object({
  category_id: z.string(),
  label: z.string(),
  severity: z.string(),
  keyword_hits: z.number(),
  matched_keywords: z.array(z.string()),
  risk_weight: z.number(),
  weighted_score: z.number(),
});
export type CategoryBreakdown = z.infer<typeof CategoryBreakdownSchema>;

export const ClassifierPredictionSchema = z.object({
  chunk: z.string(),
  predictions: z.record(z.string(), z.number()),
  top_label: z.string(),
});
export type ClassifierPrediction = z.infer<typeof ClassifierPredictionSchema>;

export const RAGSourceSchema = z.object({
  title: z.string(),
  snippet: z.string(),
  score: z.number(),
});

export const FlaggedClauseSchema = z.object({
  category: z.string(),
  severity: z.string(),
  keywords: z.array(z.string()),
  explanation: z.string(),
});
export type FlaggedClause = z.infer<typeof FlaggedClauseSchema>;

export const RAGResultSchema = z.object({
  should_sign: z.boolean(),
  overall_summary: z.string(),
  flagged_clauses: z.array(FlaggedClauseSchema),
  regulatory_violations: z.array(FlaggedClauseSchema),
  borrower_action_plan: z.array(z.string()),
  questions_to_ask_lender: z.array(z.string()),
  retrieved_sources: z.array(RAGSourceSchema),
});
export type RAGResult = z.infer<typeof RAGResultSchema>;

export const RiskLevelSchema = z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]);
export type RiskLevel = z.infer<typeof RiskLevelSchema>;

export const AnalyzeResponseSchema = z.object({
  doc_id: z.string(),
  risk_score: z.number(),
  risk_level: RiskLevelSchema,
  should_sign: z.boolean(),
  processing_time_ms: z.number(),
  word_count: z.number(),
  sentence_count: z.number(),
  sentiment: SentimentResponseSchema.nullable().optional(),
  entities: EntityResponseSchema.nullable().optional(),
  category_breakdown: z.array(CategoryBreakdownSchema).default([]),
  top_flags: z.array(z.string()).default([]),
  tfidf_terms: z.array(TFIDFTermSchema).nullable().optional(),
  summary: SummaryResponseSchema.nullable().optional(),
  classifier_predictions: z.array(ClassifierPredictionSchema).nullable().optional(),
  rag_result: RAGResultSchema.nullable().optional(),
  file_name: z.string().nullable().optional(),
  file_type: z.string().nullable().optional(),
  page_count: z.number().nullable().optional(),
});
export type AnalyzeResponse = z.infer<typeof AnalyzeResponseSchema>;

export const BatchResponseSchema = z.object({
  batch_id: z.string(),
  status: z.enum(["processing", "completed", "failed"]),
  document_count: z.number(),
  message: z.string(),
});
export type BatchResponse = z.infer<typeof BatchResponseSchema>;

export const CategoryInfoSchema = z.object({
  id: z.string(),
  label: z.string(),
  severity: z.string(),
  keyword_count: z.number(),
  keywords: z.array(z.string()),
});
export type CategoryInfo = z.infer<typeof CategoryInfoSchema>;

export const CategoriesResponseSchema = z.object({
  categories: z.array(CategoryInfoSchema),
  total_keywords: z.number(),
  version: z.string(),
});
export type CategoriesResponse = z.infer<typeof CategoriesResponseSchema>;

export const HealthResponseSchema = z.object({
  status: z.enum(["healthy", "degraded", "unhealthy"]),
  model_loaded: z.boolean(),
  vader_available: z.boolean(),
  nltk_data_ready: z.boolean(),
  uptime_seconds: z.number(),
  version: z.string(),
});
export type HealthResponse = z.infer<typeof HealthResponseSchema>;

export const HistoryItemSchema = z.object({
  doc_id: z.string(),
  status: z.enum(["processing", "completed", "failed"]),
  result: AnalyzeResponseSchema.nullable().optional(),
});
export type HistoryItem = z.infer<typeof HistoryItemSchema>;

export const ErrorResponseSchema = z.object({
  type: z.string(),
  title: z.string(),
  status: z.number(),
  detail: z.string(),
  instance: z.string(),
  request_id: z.string().default(""),
});
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
