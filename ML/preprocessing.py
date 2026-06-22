import re
import math
import functools
from collections import defaultdict
from typing import Optional

import nltk
from nltk.corpus import wordnet, stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _VADER = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except ImportError:
    _VADER = None
    VADER_AVAILABLE = False

import numpy as np

_LEMMATIZER = WordNetLemmatizer()
_STOPWORDS: Optional[set] = None


def _ensure_nltk_data():
    for pkg, path in [
        ("wordnet",                        "corpora/wordnet"),
        ("omw-1.4",                        "corpora/omw-1.4"),
        ("averaged_perceptron_tagger_eng", "taggers/averaged_perceptron_tagger_eng"),
        ("punkt_tab",                      "tokenizers/punkt_tab"),
        ("stopwords",                      "corpora/stopwords"),
        ("vader_lexicon",                  "sentiment/vader_lexicon"),
    ]:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(pkg, quiet=True)


_ensure_nltk_data()


def _get_stopwords() -> set:
    global _STOPWORDS
    if _STOPWORDS is None:
        _STOPWORDS = set(stopwords.words("english"))
    return _STOPWORDS


def _wordnet_pos(tag: str) -> str:
    if tag.startswith("J"): return wordnet.ADJ
    if tag.startswith("V"): return wordnet.VERB
    if tag.startswith("N"): return wordnet.NOUN
    if tag.startswith("R"): return wordnet.ADV
    return wordnet.NOUN


@functools.lru_cache(maxsize=4096)
def lemmatize_text(text: str) -> str:
    tokens = word_tokenize(text.lower())
    tagged = nltk.pos_tag(tokens)
    return " ".join(
        _LEMMATIZER.lemmatize(tok, _wordnet_pos(tag)) for tok, tag in tagged
    )


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s\-₹%]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def remove_stopwords(text: str, keep: Optional[set] = None) -> str:
    sw   = _get_stopwords()
    keep = keep or set()
    tokens = word_tokenize(text)
    return " ".join(
        t for t in tokens
        if (t.lower() not in sw) or (t.lower() in keep) or (not t.isalpha())
    )


def sentence_split(text: str) -> list:
    try:
        sents = sent_tokenize(text.strip())
    except Exception:
        sents = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sents if s.strip()]


class TFIDFAnalyzer:
    def __init__(self, max_features: int = 500, ngram_range: tuple = (1, 2)):
        self._vectorizer = TfidfVectorizer(
            max_features = max_features,
            ngram_range  = ngram_range,
            sublinear_tf = True,
            min_df       = 1,
            stop_words   = "english",
        )
        self._is_fit = False

    def fit(self, texts: list) -> "TFIDFAnalyzer":
        self._vectorizer.fit([clean_text(t) for t in texts])
        self._is_fit = True
        return self

    def transform(self, text: str) -> np.ndarray:
        if not self._is_fit:
            raise RuntimeError("Call fit() first.")
        return self._vectorizer.transform([clean_text(text)]).toarray()[0]

    def top_terms(self, text: str, top_n: int = 15) -> list:
        if not self._is_fit:
            self.fit([text])
        vec   = self._vectorizer.transform([clean_text(text)]).toarray()[0]
        names = self._vectorizer.get_feature_names_out()
        pairs = sorted(zip(names, vec), key=lambda x: -x[1])
        return [{"term": t, "score": round(float(s), 4)} for t, s in pairs[:top_n] if s > 0]

    def rank_sentences(self, text: str, top_n: int = 5) -> list:
        sentences = sentence_split(text)
        if not sentences:
            return []
        vect = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
        try:
            matrix = vect.fit_transform([clean_text(s) for s in sentences])
        except ValueError:
            return [{"sentence": s, "score": 0.0, "position": i, "rank": i}
                    for i, s in enumerate(sentences[:top_n])]
        scores = np.asarray(matrix.sum(axis=1)).flatten()
        ranked = sorted(enumerate(zip(sentences, scores)), key=lambda x: -x[1][1])
        top = sorted(ranked[:top_n], key=lambda x: x[0])
        return [
            {"sentence": sent, "score": round(float(score), 4), "position": idx, "rank": rank}
            for rank, (idx, (sent, score)) in enumerate(top, 1)
        ]


_tfidf = TFIDFAnalyzer(max_features=500, ngram_range=(1, 2))


def tfidf_top_terms(text: str, top_n: int = 15) -> list:
    return TFIDFAnalyzer(max_features=500).top_terms(text, top_n)


_AGGRESSIVE_MARKERS = {
    "seize", "seizure", "repossess", "foreclose", "garnish", "harass",
    "coerce", "coercive", "threaten", "intimidate", "demand", "immediate",
    "irrevocable", "absolute", "unconditional", "sole discretion",
    "without notice", "at any time", "non-negotiable", "mandatory",
    "liable for all", "recovery agent", "legal action", "criminal complaint",
}

_BORROWER_POSITIVE = {
    "right to cancel", "cooling-off", "grievance redressal", "ombudsman",
    "fair lending", "no prepayment penalty", "transparent", "disclosed",
    "key fact statement", "kfs",
}


def analyze_sentiment(text: str) -> dict:
    lower = text.lower()

    if VADER_AVAILABLE:
        doc_scores = _VADER.polarity_scores(text)
    else:
        pos_words = {"fair", "transparent", "right", "option", "waive", "protect"}
        neg_words = {"penalty", "seize", "default", "coerce", "liable", "immediate"}
        words  = set(lower.split())
        pos_ct = len(words & pos_words)
        neg_ct = len(words & neg_words)
        total  = max(1, pos_ct + neg_ct)
        compound = (pos_ct - neg_ct) / total
        doc_scores = {
            "neg": neg_ct / total, "neu": 0.5,
            "pos": pos_ct / total, "compound": compound,
        }

    aggressive_hits  = [m for m in _AGGRESSIVE_MARKERS if m in lower]
    aggressive_score = min(1.0, len(aggressive_hits) / 6)
    friendly_hits    = [m for m in _BORROWER_POSITIVE if m in lower]
    friendly_score   = min(1.0, len(friendly_hits) / 4)

    sentences   = sentence_split(text)
    sent_scores = []
    for s in sentences:
        sc = _VADER.polarity_scores(s)["compound"] if VADER_AVAILABLE else doc_scores["compound"]
        sent_scores.append({"sentence": s[:120], "compound": round(sc, 3)})
    sent_scores.sort(key=lambda x: x["compound"])
    worst_sentences = sent_scores[:5]

    compound = doc_scores["compound"]
    if aggressive_score >= 0.4 or compound <= -0.3:
        sentiment_label = "THREATENING"
    elif compound <= -0.05:
        sentiment_label = "NEGATIVE"
    elif compound >= 0.15 and friendly_score >= 0.3:
        sentiment_label = "BORROWER_FRIENDLY"
    elif compound >= 0.05:
        sentiment_label = "NEUTRAL_POSITIVE"
    else:
        sentiment_label = "NEUTRAL"

    return {
        "sentiment_label":  sentiment_label,
        "compound_score":   round(compound, 4),
        "positive":         round(doc_scores["pos"], 3),
        "negative":         round(doc_scores["neg"], 3),
        "neutral":          round(doc_scores["neu"], 3),
        "aggressive_score": round(aggressive_score, 3),
        "aggressive_hits":  aggressive_hits[:10],
        "friendly_score":   round(friendly_score, 3),
        "friendly_hits":    friendly_hits,
        "worst_sentences":  worst_sentences,
        "vader_available":  VADER_AVAILABLE,
    }


_NER_PATTERNS = {
    "MONEY": re.compile(
        r"(?:₹|rs\.?\s*|inr\s*|\$)\s*[\d,]+(?:\.\d{1,2})?(?:\s*(?:lakh|crore|thousand|k|l|cr))?",
        re.IGNORECASE,
    ),
    "RATE": re.compile(
        r"\b\d{1,3}(?:\.\d{1,2})?\s*(?:%|percent)\s*(?:per\s+annum|p\.a\.|monthly|per\s+month|per\s+day|daily)?",
        re.IGNORECASE,
    ),
    "DURATION": re.compile(
        r"\b\d+\s*(?:day|month|year|week)s?\b",
        re.IGNORECASE,
    ),
    "DATE": re.compile(
        r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:january|february|march|april|may|june|"
        r"july|august|september|october|november|december)(?:\s+\d{4})?|"
        r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\b",
        re.IGNORECASE,
    ),
    "LOAN_AMOUNT": re.compile(
        r"(?:loan\s+amount|sanctioned\s+amount|principal\s+amount|"
        r"disbursed\s+amount|emi|installment)\s+(?:of\s+)?(?:₹|rs\.?\s*|inr\s*)[\d,]+",
        re.IGNORECASE,
    ),
    "FEE_AMOUNT": re.compile(
        r"(?:processing\s+fee|origination\s+fee|late\s+fee|penal\s+(?:interest|charges?)|"
        r"bounce\s+charge|pre-?closure\s+fee|documentation\s+fee|convenience\s+fee)"
        r"\s+(?:of\s+)?(?:₹|rs\.?\s*|inr\s*)?[\d,]+(?:\.\d{1,2})?(?:\s*%)?",
        re.IGNORECASE,
    ),
    "ORG": re.compile(
        r"\b[A-Z][A-Za-z\s&]{2,40}(?:Pvt\.?\s*Ltd\.?|Ltd\.?|LLP|NBFC|Bank|Finance|Fintech|"
        r"Capital|Credit|Services|Technologies)\b",
    ),
    "CLAUSE_TYPE": re.compile(
        r"\b(?:prepayment clause|penalty clause|arbitration clause|indemnity clause|"
        r"force majeure|governing law|severability clause|termination clause|"
        r"waiver clause|acceleration clause|cross-default clause|entire agreement)\b",
        re.IGNORECASE,
    ),
    "REGULATION": re.compile(
        r"\b(?:RBI|SEBI|NBFC|IRDAI|PMLA|FEMA|SARFAESI|CERSAI|IBC|"
        r"Consumer\s+Protection\s+Act|DPDP\s+Act|Arbitration\s+(?:and\s+Conciliation\s+)?Act|"
        r"Transfer\s+of\s+Property\s+Act|Indian\s+Contract\s+Act)\b",
        re.IGNORECASE,
    ),
}


def extract_entities(text: str) -> dict:
    results: dict = {}
    seen_spans: set = set()

    for label, pattern in _NER_PATTERNS.items():
        hits = []
        for m in pattern.finditer(text):
            span = (m.start(), m.end())
            if any(not (span[1] <= s[0] or span[0] >= s[1]) for s in seen_spans):
                continue
            seen_spans.add(span)
            raw = m.group().strip()
            hits.append({
                "text":       raw,
                "start":      m.start(),
                "end":        m.end(),
                "normalized": _normalize_entity(label, raw),
            })
        if hits:
            results[label] = hits

    results["_summary"] = {
        "total_entities":    sum(len(v) for k, v in results.items() if not k.startswith("_")),
        "entity_types_found": [k for k in results if not k.startswith("_")],
        "money_mentions":    len(results.get("MONEY", [])),
        "rate_mentions":     len(results.get("RATE", [])),
        "fee_mentions":      len(results.get("FEE_AMOUNT", [])),
        "clause_types":      [e["text"] for e in results.get("CLAUSE_TYPE", [])],
        "regulations":       [e["text"] for e in results.get("REGULATION", [])],
    }
    return results


def _normalize_entity(label: str, raw: str) -> str:
    raw = raw.strip()
    if label in {"MONEY", "LOAN_AMOUNT", "FEE_AMOUNT"}:
        raw = re.sub(r"(?i)rs\.?\s*|inr\s*", "₹", raw)
        raw = re.sub(r"\s+", "", raw)
    elif label == "RATE":
        raw = re.sub(r"(?i)\s*percent\s*", "%", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
    elif label == "REGULATION":
        raw = raw.upper()
    return raw


def _build_similarity_matrix(sentences: list) -> np.ndarray:
    if len(sentences) < 2:
        return np.array([[1.0]])
    vect = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", min_df=1)
    try:
        matrix = vect.fit_transform([clean_text(s) for s in sentences])
    except ValueError:
        return np.eye(len(sentences))
    sim = cosine_similarity(matrix, matrix)
    np.fill_diagonal(sim, 0)
    return sim


def _textrank(sim_matrix: np.ndarray, damping: float = 0.85, iterations: int = 30) -> np.ndarray:
    n = sim_matrix.shape[0]
    if n == 1:
        return np.array([1.0])
    row_sums = sim_matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    norm   = sim_matrix / row_sums
    scores = np.ones(n) / n
    for _ in range(iterations):
        scores = (1 - damping) / n + damping * norm.T @ scores
    return scores


def summarize(text: str, top_n: int = 3, method: str = "textrank") -> dict:
    sentences = sentence_split(text)
    if not sentences:
        return {"summary": "", "key_sentences": [], "sentence_count": 0, "compression_ratio": 0.0}

    top_n = min(top_n, len(sentences))

    if method == "textrank" and len(sentences) >= 2:
        scores = _textrank(_build_similarity_matrix(sentences))
    else:
        vect = TfidfVectorizer(stop_words="english")
        try:
            matrix = vect.fit_transform([clean_text(s) for s in sentences])
            scores = np.asarray(matrix.sum(axis=1)).flatten()
        except ValueError:
            scores = np.ones(len(sentences))

    ranked_idx         = np.argsort(scores)[::-1][:top_n]
    ranked_idx_ordered = sorted(ranked_idx)

    key_sentences = [
        {
            "sentence": sentences[i],
            "score":    round(float(scores[i]), 4),
            "position": i,
            "rank":     int(np.where(ranked_idx == i)[0][0]) + 1 if i in ranked_idx else top_n + 1,
        }
        for i in ranked_idx_ordered
    ]

    return {
        "summary":           " ".join(s["sentence"] for s in key_sentences),
        "key_sentences":     key_sentences,
        "sentence_count":    len(sentences),
        "compression_ratio": round(top_n / max(1, len(sentences)), 3),
        "method":            method,
    }


def preprocess(
    text: str,
    *,
    lemmatize:     bool = True,
    run_sentiment: bool = True,
    run_ner:       bool = True,
    run_summary:   bool = True,
    run_tfidf:     bool = True,
    summary_top_n: int  = 3,
    tfidf_top_n:   int  = 15,
) -> dict:
    cleaned    = clean_text(text)
    lemmatized = lemmatize_text(cleaned) if lemmatize else cleaned
    sentences  = sentence_split(text)

    result = {
        "original":       text,
        "cleaned":        cleaned,
        "lemmatized":     lemmatized,
        "sentences":      sentences,
        "sentence_count": max(1, len(sentences)),
        "word_count":     len(cleaned.split()),
    }

    if run_tfidf:
        result["tfidf_terms"] = tfidf_top_terms(text, top_n=tfidf_top_n)
    if run_sentiment:
        result["sentiment"] = analyze_sentiment(text)
    if run_ner:
        result["entities"] = extract_entities(text)
    if run_summary:
        result["summary"] = summarize(text, top_n=summary_top_n)

    return result


def print_analysis(result: dict) -> None:
    BOLD  = "\033[1m"
    CYAN  = "\033[96m"
    YELLOW= "\033[93m"
    RED   = "\033[91m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

    print(f"\n{'='*62}")
    print(f"{BOLD}NLP ANALYSIS REPORT{RESET}")
    print(f"{'='*62}")
    print(f"Words: {result['word_count']}  |  Sentences: {result['sentence_count']}")

    if "sentiment" in result:
        s     = result["sentiment"]
        label = s["sentiment_label"]
        color = RED if label == "THREATENING" else (GREEN if "FRIENDLY" in label else YELLOW)
        print(f"\n{BOLD}── Sentiment ──{RESET}")
        print(f"  Label      : {color}{BOLD}{label}{RESET}")
        print(f"  Compound   : {s['compound_score']:+.3f}  (neg {s['negative']:.2f} / pos {s['positive']:.2f})")
        print(f"  Aggressive : {s['aggressive_score']:.2f}  hits: {', '.join(s['aggressive_hits'][:5]) or 'none'}")
        print(f"  Friendly   : {s['friendly_score']:.2f}  hits: {', '.join(s['friendly_hits'][:3]) or 'none'}")
        if s["worst_sentences"]:
            print(f"  Worst clause: \"{s['worst_sentences'][0]['sentence'][:90]}...\"")

    if "entities" in result:
        e  = result["entities"]
        sm = e.get("_summary", {})
        print(f"\n{BOLD}── Named Entities ──{RESET}")
        print(f"  Total found : {sm.get('total_entities', 0)}")
        for etype in ["MONEY", "RATE", "FEE_AMOUNT", "LOAN_AMOUNT", "DURATION", "REGULATION", "CLAUSE_TYPE", "ORG"]:
            hits = e.get(etype, [])
            if hits:
                vals = [h["normalized"] for h in hits[:4]]
                print(f"  {CYAN}{etype:<14}{RESET}: {', '.join(vals)}" + (" ..." if len(hits) > 4 else ""))

    if "tfidf_terms" in result:
        terms = result["tfidf_terms"][:8]
        print(f"\n{BOLD}── Top TF-IDF Terms ──{RESET}")
        for t in terms:
            bar = "▓" * int(t["score"] * 30)
            print(f"  {t['term']:<28} {bar} {t['score']:.3f}")

    if "summary" in result:
        sm    = result["summary"]
        ratio = sm.get("compression_ratio", 0)
        print(f"\n{BOLD}── Extractive Summary  ({sm['sentence_count']} → {len(sm['key_sentences'])} sentences, {ratio:.0%} kept) ──{RESET}")
        for i, ks in enumerate(sm["key_sentences"], 1):
            print(f"\n  [{i}] (score {ks['score']:.3f})")
            print(f"      {ks['sentence'][:200]}")

    print(f"\n{'='*62}\n")