import type { CategoryBreakdown } from "@/lib/schemas";

export interface HighlightSegment {
  text: string;
  severity: string | null; // null = plain text, no match
  category: string | null;
  matchedKeyword: string | null;
}

/**
 * Builds an array of text segments from raw source text, marking spans that
 * match any matched_keyword from category_breakdown. This is a client-side
 * reconstruction since the backend does not return character offsets for
 * keyword matches (only EntityMatch has start/end, and only for NER
 * entities). Matching is case-insensitive substring search, longest-keyword
 * first to avoid partial-overlap artifacts.
 */
export function buildHighlightSegments(
  sourceText: string,
  categories: CategoryBreakdown[]
): HighlightSegment[] {
  type KeywordEntry = { keyword: string; severity: string; category: string };

  const allKeywords: KeywordEntry[] = categories.flatMap((cat) =>
    cat.matched_keywords.map((kw) => ({ keyword: kw, severity: cat.severity, category: cat.label }))
  );

  // Longest keywords first so "penal interest on entire outstanding" doesn't
  // get fragmented by a shorter overlapping match like "penal interest".
  allKeywords.sort((a, b) => b.keyword.length - a.keyword.length);

  if (allKeywords.length === 0 || !sourceText) {
    return [{ text: sourceText, severity: null, category: null, matchedKeyword: null }];
  }

  // Build a single regex alternation, escaping each keyword.
  const escaped = allKeywords.map((k) => k.keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const pattern = new RegExp(`(${escaped.join("|")})`, "gi");

  const segments: HighlightSegment[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(sourceText)) !== null) {
    if (match.index > lastIndex) {
      segments.push({
        text: sourceText.slice(lastIndex, match.index),
        severity: null,
        category: null,
        matchedKeyword: null,
      });
    }
    const matchedText = match[0];
    const found = allKeywords.find((k) => k.keyword.toLowerCase() === matchedText.toLowerCase());
    segments.push({
      text: matchedText,
      severity: found?.severity ?? null,
      category: found?.category ?? null,
      matchedKeyword: found?.keyword ?? matchedText,
    });
    lastIndex = match.index + matchedText.length;
  }

  if (lastIndex < sourceText.length) {
    segments.push({
      text: sourceText.slice(lastIndex),
      severity: null,
      category: null,
      matchedKeyword: null,
    });
  }

  return segments;
}
