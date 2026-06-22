"""
nlp/preprocessing.py — Unified NLP preprocessing pipeline for LoanGuard AI.

Provides:
  - clean_text()        : lowercase, strip punctuation, normalize whitespace
  - lemmatize_text()    : POS-aware WordNet lemmatization with LRU cache
  - sentence_split()    : NLTK punkt tokenizer with regex fallback
  - remove_stopwords()  : removes stopwords, preserves risk keyword tokens
  - preprocess()        : unified pipeline
  - analyze_sentiment() : VADER + aggressive-tone + borrower-friendly scoring
  - extract_entities()  : regex-based NER for 9 entity types
  - TFIDFAnalyzer       : single-doc and corpus TF-IDF with bigrams
  - summarize()         : TextRank extractive summarization
"""

from __future__ import annotations

import re
import math
import string
import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NLTK bootstrap (graceful — regex fallbacks used if unavailable)
# ---------------------------------------------------------------------------
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords as nltk_stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.corpus import wordnet

    _NLTK_AVAILABLE = True
    _lemmatizer = WordNetLemmatizer()

    def _get_wordnet_pos(treebank_tag: str) -> str:
        """Map PennTreebank POS tag to WordNet POS."""
        if treebank_tag.startswith("J"):
            return wordnet.ADJ
        elif treebank_tag.startswith("V"):
            return wordnet.VERB
        elif treebank_tag.startswith("N"):
            return wordnet.NOUN
        elif treebank_tag.startswith("R"):
            return wordnet.ADV
        return wordnet.NOUN

except ImportError:
    _NLTK_AVAILABLE = False
    _lemmatizer = None
    logger.warning("NLTK not available — using regex fallbacks.")

# ---------------------------------------------------------------------------
# VADER bootstrap
# ---------------------------------------------------------------------------
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    _vader = SentimentIntensityAnalyzer()
    _VADER_AVAILABLE = True
except ImportError:
    _vader = None
    _VADER_AVAILABLE = False
    logger.warning("vaderSentiment not available — using word-count heuristic.")

# ---------------------------------------------------------------------------
# Stopwords
# ---------------------------------------------------------------------------
_KEEP_TOKENS = frozenset(
    ["at", "any", "of", "on", "in", "to", "no", "not", "all", "for", "by", "or"]
)
_ENGLISH_STOPWORDS: frozenset[str] = frozenset()

if _NLTK_AVAILABLE:
    try:
        _ENGLISH_STOPWORDS = frozenset(nltk_stopwords.words("english")) - _KEEP_TOKENS
    except LookupError:
        pass


# ===========================================================================
# Text cleaning
# ===========================================================================

def clean_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ===========================================================================
# Lemmatization — POS-aware with LRU cache
# ===========================================================================

@lru_cache(maxsize=4096)
def _lemmatize_word(word: str, pos: str) -> str:
    if _NLTK_AVAILABLE and _lemmatizer:
        return _lemmatizer.lemmatize(word, pos)
    return word


def lemmatize_text(text: str) -> str:
    """POS-aware WordNet lemmatization. Falls back to identity if NLTK unavailable."""
    if not _NLTK_AVAILABLE:
        return text
    try:
        tokens = word_tokenize(text)
        pos_tags = nltk.pos_tag(tokens)
        lemmatized = [
            _lemmatize_word(word, _get_wordnet_pos(tag)) for word, tag in pos_tags
        ]
        return " ".join(lemmatized)
    except Exception:
        return text


# ===========================================================================
# Sentence splitting
# ===========================================================================

_SENTENCE_ENDINGS = re.compile(r"(?<=[.!?])\s+")


def sentence_split(text: str) -> list[str]:
    """Split into sentences via NLTK punkt; fall back to regex."""
    if _NLTK_AVAILABLE:
        try:
            return sent_tokenize(text)
        except LookupError:
            pass
    # Regex fallback
    parts = _SENTENCE_ENDINGS.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


# ===========================================================================
# Stop-word removal
# ===========================================================================

def remove_stopwords(text: str, keep: frozenset[str] | None = None) -> str:
    """Remove stopwords, preserving keep tokens (defaults to _KEEP_TOKENS)."""
    preserve = keep if keep is not None else _KEEP_TOKENS
    words = text.split()
    filtered = [w for w in words if w.lower() not in _ENGLISH_STOPWORDS or w.lower() in preserve]
    return " ".join(filtered)


# ===========================================================================
# Unified preprocess pipeline
# ===========================================================================

def preprocess(text: str) -> dict[str, Any]:
    """
    Full NLP pipeline.

    Returns:
        original, cleaned, lemmatized, sentences, sentence_count, word_count
    """
    cleaned = clean_text(text)
    lemmatized = lemmatize_text(cleaned)
    sentences = sentence_split(text)
    word_count = len(text.split())
    return {
        "original": text,
        "cleaned": cleaned,
        "lemmatized": lemmatized,
        "sentences": sentences,
        "sentence_count": len(sentences),
        "word_count": word_count,
    }


# ===========================================================================
# Sentiment Analysis
# ===========================================================================

_AGGRESSIVE_MARKERS = [
    "seize", "irrevocable", "without notice", "without prior notice",
    "liable for all", "recovery agent", "sole discretion", "mandatory arbitration",
    "asset seizure", "repossession", "legal action", "attach property",
    "accelerate", "entire outstanding", "full repayment immediately",
    "criminal action", "file a case", "collection agent", "penalise",
    "penalty on penalty", "unilaterally", "absolute discretion",
    "without reason", "at any time", "no cooling off",
]

_FRIENDLY_MARKERS = [
    "cooling-off", "cooling off period", "grievance redressal", "fair lending",
    "kfs", "key fact statement", "ombudsman", "rbi ombudsman",
    "borrower rights", "right to prepay", "no prepayment penalty",
    "transparent pricing", "full disclosure", "clear disclosure",
]

_AGGRESSIVE_CAP = 6  # denominator for aggressive_score


def analyze_sentiment(text: str) -> dict[str, Any]:
    """
    Returns VADER scores + custom aggressive / borrower-friendly scores.
    Falls back to word-count heuristic if VADER unavailable.
    """
    sentences = sentence_split(text)
    text_lower = text.lower()

    # --- Aggressive markers ---
    agg_hits = [m for m in _AGGRESSIVE_MARKERS if m in text_lower]
    aggressive_score = min(len(agg_hits) / _AGGRESSIVE_CAP, 1.0)

    # --- Friendly markers ---
    fri_hits = [m for m in _FRIENDLY_MARKERS if m in text_lower]
    friendly_score = min(len(fri_hits) / len(_FRIENDLY_MARKERS), 1.0)

    if _VADER_AVAILABLE and _vader:
        doc_scores = _vader.polarity_scores(text)
        compound = doc_scores["compound"]
        pos = round(doc_scores["pos"], 4)
        neg = round(doc_scores["neg"], 4)
        neu = round(doc_scores["neu"], 4)

        # Per-sentence scoring — surface 5 worst
        sent_scores = []
        for s in sentences:
            sc = _vader.polarity_scores(s)
            sent_scores.append({"sentence": s, "compound": round(sc["compound"], 4)})
        worst_clauses = sorted(sent_scores, key=lambda x: x["compound"])[:5]
    else:
        # Heuristic fallback
        negative_words = {"penalty", "seize", "liable", "default", "recovery", "legal"}
        tokens_lower = set(text_lower.split())
        neg_count = len(tokens_lower & negative_words)
        compound = -min(neg_count / 10, 1.0)
        pos, neg, neu = 0.0, round(abs(compound), 4), round(1 - abs(compound), 4)
        worst_clauses = []

    # --- Label ---
    # VADER's general-purpose lexicon doesn't understand loan-domain
    # vocabulary: words like "ombudsman", "grievance", "dispute", and
    # "default" can score as negative even inside a clearly borrower-
    # protective sentence (e.g. "Contact the ombudsman for disputes").
    # So a negative compound score alone should not declare THREATENING
    # if there's no actual aggressive-marker hit AND friendly markers are
    # present — domain-specific markers are more reliable here than the
    # generic lexicon. Only let compound override friendly signal when
    # genuine aggressive phrasing also fired.
    has_aggressive = aggressive_score > 0.0
    has_strong_friendly = len(fri_hits) >= 2

    if has_aggressive and (aggressive_score >= 0.4 or compound <= -0.3):
        label = "THREATENING"
    elif has_strong_friendly and not has_aggressive:
        label = "BORROWER_FRIENDLY"
    elif compound <= -0.3:
        label = "THREATENING"
    elif compound <= -0.1:
        label = "NEGATIVE"
    elif compound < 0.1:
        label = "NEUTRAL"
    elif len(fri_hits) >= 2:
        label = "BORROWER_FRIENDLY"
    else:
        label = "NEUTRAL_POSITIVE"

    return {
        "label": label,
        "compound_score": round(compound, 4),
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "aggressive_score": round(aggressive_score, 4),
        "aggressive_hits": agg_hits,
        "friendly_score": round(friendly_score, 4),
        "friendly_hits": fri_hits,
        "worst_clauses": worst_clauses,
    }


# ===========================================================================
# Named Entity Recognition — regex-based, fully offline
# ===========================================================================

# Priority order: higher index = lower priority (earlier patterns win on overlaps)
_ENTITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # LOAN_AMOUNT — contextual
    (
        "LOAN_AMOUNT",
        re.compile(
            r"(?:emi\s+of|sanctioned\s+amount\s+of|loan\s+amount\s+of|principal\s+of|disburs(?:e|al)\s+of)"
            r"\s*(?:₹|rs\.?|inr)\s*[\d,]+(?:\.\d+)?",
            re.IGNORECASE,
        ),
    ),
    # FEE_AMOUNT — contextual
    (
        "FEE_AMOUNT",
        re.compile(
            r"(?:processing\s+fee|late\s+fee|penal(?:ty|)\s+(?:charge|fee)|bounce\s+charge|"
            r"pre-?closure\s+(?:fee|charge)|foreclosure\s+charge)\s+of\s+"
            r"(?:(?:₹|rs\.?|inr)\s*[\d,]+(?:\.\d+)?|\d+(?:\.\d+)?\s*%)",
            re.IGNORECASE,
        ),
    ),
    # MONEY — ₹, Rs., INR, $
    (
        "MONEY",
        re.compile(
            r"(?:₹|rs\.?\s*|inr\s*|\$)\s*[\d,]+(?:\.\d+)?(?:\s*(?:lakhs?|lacs?|crores?|thousands?))?",
            re.IGNORECASE,
        ),
    ),
    # RATE — percentages per period
    (
        "RATE",
        re.compile(
            r"\d+(?:\.\d+)?\s*%(?:\s+p\.?a\.?|\s+per\s+(?:annum|month|year|day)|\s+per\s+cent\s+per\s+annum)?",
            re.IGNORECASE,
        ),
    ),
    # DURATION
    (
        "DURATION",
        re.compile(
            r"\d+\s*(?:days?|months?|years?|weeks?)",
            re.IGNORECASE,
        ),
    ),
    # DATE
    (
        "DATE",
        re.compile(
            r"(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
            r"\d{1,2}\s+(?:january|february|march|april|may|june|july|august|"
            r"september|october|november|december)\s+\d{4}|"
            r"(?:january|february|march|april|may|june|july|august|"
            r"september|october|november|december)\s+\d{4})",
            re.IGNORECASE,
        ),
    ),
    # ORG — lender names
    (
        "ORG",
        re.compile(
            r"[A-Z][A-Za-z\s&]+?(?:Pvt\.?\s*Ltd\.?|Private\s+Limited|NBFC|Bank|Finance|Financial\s+Services|"
            r"Capital|Credit|Fintech)",
        ),
    ),
    # CLAUSE_TYPE
    (
        "CLAUSE_TYPE",
        re.compile(
            r"(?:prepayment|arbitration|force\s+majeure|indemnification|acceleration|"
            r"cross\s+default|governing\s+law|jurisdiction)\s+clause",
            re.IGNORECASE,
        ),
    ),
    # REGULATION
    (
        "REGULATION",
        re.compile(
            r"\b(?:RBI|SEBI|SARFAESI|DPDP\s+Act|Indian\s+Contract\s+Act|FEMA|IBC|"
            r"DRT|NCLT|Competition\s+Act|NBFC\s+Regulations|RBI\s+Master\s+Direction)\b",
            re.IGNORECASE,
        ),
    ),
]

_PRIORITY_MAP = {name: i for i, (name, _) in enumerate(_ENTITY_PATTERNS)}


def extract_entities(text: str) -> dict[str, Any]:
    """Offline regex-based NER with overlap resolution (earlier patterns win)."""
    occupied: list[tuple[int, int]] = []  # list of (start, end) spans already claimed

    entities: dict[str, list[dict[str, Any]]] = {
        name: [] for name, _ in _ENTITY_PATTERNS
    }

    def _overlaps(s: int, e: int) -> bool:
        return any(not (e <= os or s >= oe) for os, oe in occupied)

    for entity_type, pattern in _ENTITY_PATTERNS:
        for m in pattern.finditer(text):
            start, end = m.start(), m.end()
            if _overlaps(start, end):
                continue
            raw = m.group()
            normalized = _normalize_entity(entity_type, raw)
            entities[entity_type].append(
                {"text": raw, "normalized": normalized, "start": start, "end": end}
            )
            occupied.append((start, end))

    # Build summary
    money_mentions = len(entities["MONEY"]) + len(entities["LOAN_AMOUNT"])
    rate_mentions = len(entities["RATE"])
    fee_mentions = len(entities["FEE_AMOUNT"])
    clause_types = [e["text"] for e in entities["CLAUSE_TYPE"]]
    regulations = [e["normalized"] for e in entities["REGULATION"]]
    total_entities = sum(len(v) for v in entities.values())

    entities["summary"] = {
        "total_entities": total_entities,
        "money_mentions": money_mentions,
        "rate_mentions": rate_mentions,
        "fee_mentions": fee_mentions,
        "clause_types": clause_types,
        "regulations": regulations,
    }
    return entities


def _normalize_entity(entity_type: str, raw: str) -> str:
    """Normalize entity text based on its type."""
    if entity_type == "MONEY":
        cleaned = re.sub(r"(?:rs\.?\s*|inr\s*)", "", raw, flags=re.IGNORECASE).strip()
        if not cleaned.startswith("₹") and not cleaned.startswith("$"):
            cleaned = "₹" + cleaned
        return cleaned
    elif entity_type == "RATE":
        cleaned = re.sub(r"\s+", " ", raw).strip()
        if "%" not in cleaned:
            cleaned = cleaned.replace("per cent", "%")
        return cleaned
    elif entity_type == "REGULATION":
        return raw.upper().strip()
    return raw.strip()


# ===========================================================================
# TF-IDF Analyzer
# ===========================================================================


class TFIDFAnalyzer:
    """
    Single-document or corpus TF-IDF with bigrams.
    ngram_range=(1,2) captures 'penal interest', 'sole discretion', etc.
    """

    def __init__(self, ngram_range: tuple[int, int] = (1, 2)):
        self.ngram_range = ngram_range
        self._idf: dict[str, float] = {}
        self._fitted = False

    # ------------------------------------------------------------------
    def _tokenize(self, text: str) -> list[str]:
        words = re.findall(r"\b[a-z]{2,}\b", text.lower())
        tokens = list(words)
        if self.ngram_range[1] >= 2:
            bigrams = [f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1)]
            tokens += bigrams
        return tokens

    def _tf(self, tokens: list[str]) -> dict[str, float]:
        counts: dict[str, int] = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
        total = max(len(tokens), 1)
        return {t: c / total for t, c in counts.items()}

    # ------------------------------------------------------------------
    def fit(self, documents: list[str]) -> "TFIDFAnalyzer":
        """Fit IDF on corpus (or single doc)."""
        N = len(documents)
        df: dict[str, int] = {}
        for doc in documents:
            unique = set(self._tokenize(doc))
            for t in unique:
                df[t] = df.get(t, 0) + 1
        self._idf = {t: math.log((N + 1) / (d + 1)) + 1.0 for t, d in df.items()}
        self._fitted = True
        return self

    def fit_transform_single(self, text: str) -> dict[str, float]:
        """Fit + transform a single document on itself."""
        self.fit([text])
        tokens = self._tokenize(text)
        tf = self._tf(tokens)
        return {t: tf[t] * self._idf.get(t, 1.0) for t in tf}

    def top_terms(self, text: str, top_n: int = 15) -> list[dict[str, float]]:
        """Return top-N TF-IDF terms for a document."""
        scores = self.fit_transform_single(text)
        sorted_terms = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [{"term": t, "score": round(s, 6)} for t, s in sorted_terms[:top_n]]

    def rank_sentences(self, sentences: list[str]) -> list[dict]:
        """Score each sentence by sum of its TF-IDF weights."""
        if not self._fitted:
            all_text = " ".join(sentences)
            self.fit([all_text])
        results = []
        for i, sent in enumerate(sentences):
            tokens = self._tokenize(sent)
            tf = self._tf(tokens)
            score = sum(tf[t] * self._idf.get(t, 0.0) for t in tf)
            results.append({"sentence": sent, "score": round(score, 6), "position": i})
        ranked = sorted(results, key=lambda x: x["score"], reverse=True)
        for rank_idx, item in enumerate(ranked, 1):
            item["rank"] = rank_idx
        return sorted(results, key=lambda x: x["position"])


# ===========================================================================
# TextRank Extractive Summarization
# ===========================================================================

def _cosine_similarity(v1: dict[str, float], v2: dict[str, float]) -> float:
    common = set(v1) & set(v2)
    if not common:
        return 0.0
    dot = sum(v1[t] * v2[t] for t in common)
    mag1 = math.sqrt(sum(x * x for x in v1.values()))
    mag2 = math.sqrt(sum(x * x for x in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


def _pagerank(
    matrix: list[list[float]],
    damping: float = 0.85,
    iterations: int = 30,
) -> list[float]:
    n = len(matrix)
    scores = [1.0 / n] * n
    for _ in range(iterations):
        new_scores = []
        for i in range(n):
            col_sum = sum(matrix[j][i] for j in range(n))
            rank = (1 - damping) / n + damping * col_sum
            new_scores.append(rank)
        total = sum(new_scores) or 1.0
        scores = [s / total for s in new_scores]
    return scores


def summarize(text: str, top_n: int = 3) -> dict[str, Any]:
    """
    TextRank extractive summarization.
    Falls back to TF-IDF weight-sum when <2 sentences.
    Returns summary in original reading order.
    """
    sentences = sentence_split(text)
    sentence_count = len(sentences)
    method = "textrank"

    if sentence_count < 2:
        # Fallback
        method = "tfidf"
        analyzer = TFIDFAnalyzer()
        ranked = analyzer.rank_sentences(sentences)
        top_k = min(top_n, sentence_count)
        key_sentences = sorted(ranked[:top_k], key=lambda x: x["position"])
        summary_text = " ".join(s["sentence"] for s in key_sentences)
        compression = round(len(summary_text) / max(len(text), 1), 4)
        return {
            "text": summary_text,
            "key_sentences": key_sentences,
            "sentence_count": sentence_count,
            "compression_ratio": compression,
            "method": method,
        }

    # Build TF-IDF vectors per sentence
    analyzer = TFIDFAnalyzer()
    vectors: list[dict[str, float]] = []
    for sent in sentences:
        scores = analyzer.fit_transform_single(sent)
        vectors.append(scores)
        analyzer = TFIDFAnalyzer()  # fresh per sentence for single-doc mode

    # Rebuild with corpus IDF
    corpus_analyzer = TFIDFAnalyzer()
    corpus_analyzer.fit(sentences)
    tfidf_vectors: list[dict[str, float]] = []
    for sent in sentences:
        tokens = corpus_analyzer._tokenize(sent)
        tf = corpus_analyzer._tf(tokens)
        vec = {t: tf[t] * corpus_analyzer._idf.get(t, 0.0) for t in tf}
        tfidf_vectors.append(vec)

    # Build similarity matrix
    n = len(sentences)
    sim_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        row_sum = 0.0
        for j in range(n):
            if i != j:
                sim = _cosine_similarity(tfidf_vectors[i], tfidf_vectors[j])
                sim_matrix[i][j] = sim
                row_sum += sim
        # Row-normalize
        if row_sum > 0:
            for j in range(n):
                sim_matrix[i][j] /= row_sum

    pr_scores = _pagerank(sim_matrix)
    ranked_sents = sorted(
        enumerate(sentences), key=lambda x: pr_scores[x[0]], reverse=True
    )

    top_k = min(top_n, sentence_count)
    top_indices = sorted([idx for idx, _ in ranked_sents[:top_k]])

    key_sentences = [
        {
            "sentence": sentences[i],
            "score": round(pr_scores[i], 6),
            "position": i,
            "rank": next(
                (r + 1 for r, (idx, _) in enumerate(ranked_sents) if idx == i), 999
            ),
        }
        for i in top_indices
    ]
    summary_text = " ".join(s["sentence"] for s in key_sentences)
    compression = round(len(summary_text) / max(len(text), 1), 4)

    return {
        "text": summary_text,
        "key_sentences": key_sentences,
        "sentence_count": sentence_count,
        "compression_ratio": compression,
        "method": method,
    }
