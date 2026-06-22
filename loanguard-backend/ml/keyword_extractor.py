"""
ml/keyword_extractor.py — 3-pass keyword extraction engine for LoanGuard AI.

Pass 1: Exact string match
Pass 2: Regex pattern match
Pass 3: spaCy NER (graceful fallback if model unavailable)

Returns risk score (0-100), risk level, and per-match metadata.
"""

from __future__ import annotations

import re
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# spaCy — optional
try:
    import spacy

    _nlp = spacy.load("en_core_web_sm")
    _SPACY_AVAILABLE = True
except Exception:
    _nlp = None
    _SPACY_AVAILABLE = False
    logger.info("spaCy model unavailable — NER pass disabled; using exact+regex only.")

# Severity → weight mapping
SEVERITY_WEIGHTS = {
    "CRITICAL": 25,
    "HIGH": 15,
    "MEDIUM": 8,
    "INFO": 2,
}

# Negation cues checked in a short word-window immediately before a keyword
# match. If found, the match is "protective" rather than "risky" — e.g.
# "without any prepayment penalty" should not score the same as
# "a prepayment penalty of 5% applies".
_NEGATION_CUES = [
    "no", "not", "without", "waived", "waiver of", "exempt from", "exempted from",
    "free of", "free from", "shall not", "will not", "won't", "cannot", "can not",
    "never", "nil", "zero", "does not apply", "do not apply", "not applicable",
    "not be charged", "not be levied", "not subject to",
]
_NEGATION_WINDOW_WORDS = 6  # how many words before the match to scan

# Phrases that are inherently borrower-protective regardless of context —
# their presence should reduce overall risk, not just be neutral, since
# they signal a compliant, transparent lender.
_PROTECTIVE_BONUS_KEYWORDS = {
    "cooling-off period", "cooling off period", "grievance redressal",
    "rbi ombudsman", "key fact statement", "no prepayment penalty",
    "right to prepay", "right to cancel", "notice period",
    "rbi digital lending guidelines",
}
_PROTECTIVE_BONUS_PER_HIT = 6  # points subtracted from raw_score per protective hit (capped)
_PROTECTIVE_BONUS_CAP = 18

_DEFAULT_CONFIG_PATH = Path(__file__).parent / "keywords_config.json"


def load_keywords_config(path: str | Path = _DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load the keywords configuration from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class KeywordExtractor:
    """
    3-pass keyword extractor over loan agreement text.
    Instantiated once at startup and reused per request.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.categories = config["categories"]
        self.version = config.get("version", "1.0.0")
        # Pre-compile regex patterns per category
        self._regex_patterns: dict[str, list[tuple[str, re.Pattern[str]]]] = {}
        for cat in self.categories:
            patterns = []
            for kw in cat["keywords"]:
                # Build word-boundary-aware pattern
                escaped = re.escape(kw)
                pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
                patterns.append((kw, pattern))
            self._regex_patterns[cat["id"]] = patterns

    # ------------------------------------------------------------------
    def extract(
        self,
        text: str,
        context_window: int = 100,
    ) -> dict[str, Any]:
        """
        Run 3-pass extraction on text.

        Returns:
            matches          : flat list of all keyword matches
            category_breakdown: aggregated per-category stats
            risk_score       : composite 0-100
            risk_level       : LOW / MEDIUM / HIGH / CRITICAL
            top_flags        : top 10 matched keywords by severity
        """
        text_lower = text.lower()
        matches: list[dict[str, Any]] = []
        seen_spans: list[tuple[int, int]] = []

        # ---- Pass 1 + 2: exact match & regex ----
        for cat in self.categories:
            cat_id = cat["id"]
            severity = cat["severity"]
            label = cat["label"]
            for kw, pattern in self._regex_patterns[cat_id]:
                for m in pattern.finditer(text):
                    start, end = m.start(), m.end()
                    if self._overlaps(start, end, seen_spans):
                        continue
                    ctx_start = max(0, start - context_window)
                    ctx_end = min(len(text), end + context_window)
                    context = text[ctx_start:ctx_end]
                    # Decide match_type: exact if full word, else regex
                    match_type = "exact" if m.group().lower() == kw.lower() else "regex"
                    confidence = 1.0 if match_type == "exact" else 0.85
                    is_negated = self._is_negated(text, start)
                    is_protective = self._is_protective_phrase(kw)
                    matches.append(
                        {
                            "keyword": kw,
                            "matched_text": m.group(),
                            "category": cat_id,
                            "label": label,
                            "severity": severity,
                            "start": start,
                            "end": end,
                            "context": context,
                            "match_type": match_type,
                            "confidence": confidence,
                            "is_negated": is_negated,
                            "is_protective": is_protective,
                        }
                    )
                    seen_spans.append((start, end))

        # ---- Pass 3: spaCy NER ----
        if _SPACY_AVAILABLE and _nlp:
            try:
                doc = _nlp(text[:100_000])  # spaCy limit
                for ent in doc.ents:
                    if ent.label_ in {"ORG", "MONEY", "PERCENT", "LAW"}:
                        start, end = ent.start_char, ent.end_char
                        if self._overlaps(start, end, seen_spans):
                            continue
                        ctx_start = max(0, start - context_window)
                        ctx_end = min(len(text), end + context_window)
                        matches.append(
                            {
                                "keyword": ent.text,
                                "matched_text": ent.text,
                                "category": "financial_entity_extraction",
                                "label": "Financial Entity",
                                "severity": "INFO",
                                "start": start,
                                "end": end,
                                "context": text[ctx_start:ctx_end],
                                "match_type": "ner",
                                "confidence": 0.75,
                                "is_negated": False,
                                "is_protective": False,
                            }
                        )
                        seen_spans.append((start, end))
            except Exception as e:
                logger.warning(f"spaCy NER pass failed: {e}")

        # ---- Category breakdown ----
        category_breakdown = self._build_breakdown(matches)

        # ---- Risk score ----
        risk_score, risk_level = self._compute_risk_score(matches, text)

        # ---- Top flags (sorted by severity weight, negated matches excluded) ----
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "INFO": 3}
        risky_for_flags = [m for m in matches if not m.get("is_negated")]
        sorted_matches = sorted(
            risky_for_flags, key=lambda x: severity_order.get(x["severity"], 9)
        )
        top_flags = list(
            dict.fromkeys(m["keyword"] for m in sorted_matches)
        )[:10]

        return {
            "matches": matches,
            "category_breakdown": category_breakdown,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "top_flags": top_flags,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
        return any(not (end <= s or start >= e) for s, e in spans)

    # ------------------------------------------------------------------
    @staticmethod
    def _is_negated(text: str, match_start: int) -> bool:
        """
        Look back up to _NEGATION_WINDOW_WORDS words before the match start
        for a negation cue. Returns True if the keyword appears to be
        negated/waived (i.e. protective rather than risky context).
        """
        preceding = text[:match_start]
        words = preceding.split()[-_NEGATION_WINDOW_WORDS:]
        window = " ".join(words).lower()
        return any(cue in window for cue in _NEGATION_CUES)

    # ------------------------------------------------------------------
    @staticmethod
    def _is_protective_phrase(keyword: str) -> bool:
        return keyword.lower() in _PROTECTIVE_BONUS_KEYWORDS

    # ------------------------------------------------------------------
    def _build_breakdown(self, matches: list[dict]) -> list[dict]:
        cat_map: dict[str, dict] = {}
        for cat in self.categories:
            cat_map[cat["id"]] = {
                "category_id": cat["id"],
                "label": cat["label"],
                "severity": cat["severity"].lower(),
                "risk_weight": SEVERITY_WEIGHTS.get(cat["severity"], 0),
                "keyword_hits": 0,
                "matched_keywords": [],
                "weighted_score": 0.0,
                "negated_hits": 0,
            }

        for m in matches:
            cid = m["category"]
            if cid not in cat_map:
                continue
            kw = m["keyword"]
            if m.get("is_negated"):
                # Track negated hits separately; don't count toward the
                # risk-bearing hit count shown to the user, since the clause
                # is protective ("no prepayment penalty"), not risky.
                cat_map[cid]["negated_hits"] += 1
                continue
            cat_map[cid]["keyword_hits"] += 1
            if kw not in cat_map[cid]["matched_keywords"]:
                cat_map[cid]["matched_keywords"].append(kw)

        for cid, entry in cat_map.items():
            entry["weighted_score"] = round(
                entry["keyword_hits"] * entry["risk_weight"], 2
            )

        # Return only categories with at least one hit, plus all in sorted order
        return sorted(
            [v for v in cat_map.values()],
            key=lambda x: -x["weighted_score"],
        )

    # ------------------------------------------------------------------
    def _compute_risk_score(
        self, matches: list[dict], text: str
    ) -> tuple[float, str]:
        # Only non-negated matches count as risk signal. A negated match
        # ("no prepayment penalty") is protective, not risky.
        risky_matches = [m for m in matches if not m.get("is_negated")]

        if not risky_matches:
            return 0.0, "LOW"

        raw_score = sum(
            SEVERITY_WEIGHTS.get(m["severity"], 0) for m in risky_matches
        )

        # Keyword density bonus (per 100 words) — only counts risky matches,
        # so a long, mostly-clean document isn't penalised just for length.
        word_count = max(len(text.split()), 1)
        density = len(risky_matches) / word_count * 100
        density_bonus = min(density * 2, 20)

        # Protective bonus: borrower-friendly phrases (cooling-off period,
        # grievance redressal, RBI Ombudsman, etc.) actively reduce risk,
        # since their presence signals a transparent, compliant lender.
        protective_hits = sum(1 for m in matches if m.get("is_protective"))
        protective_bonus = min(
            protective_hits * _PROTECTIVE_BONUS_PER_HIT, _PROTECTIVE_BONUS_CAP
        )

        score = raw_score + density_bonus - protective_bonus
        score = max(0.0, min(score, 100.0))

        # ---- Decision-aware level assignment ----
        # Severity should not be purely linear: a single genuine CRITICAL
        # signal (e.g. an advance-fee scam phrase, an acceleration clause)
        # must be able to push the verdict to CRITICAL/HIGH on its own,
        # even in a long document otherwise full of neutral boilerplate
        # that would dilute a pure linear average. Conversely, several
        # low-severity/INFO mentions alone should not manufacture a HIGH
        # or CRITICAL verdict.
        critical_hits = sum(1 for m in risky_matches if m["severity"] == "CRITICAL")
        high_hits = sum(1 for m in risky_matches if m["severity"] == "HIGH")

        if critical_hits >= 2 or score >= 75:
            level = "CRITICAL"
        elif critical_hits >= 1 or high_hits >= 2 or score >= 50:
            level = "HIGH"
        elif high_hits >= 1 or score >= 25:
            level = "MEDIUM"
        else:
            level = "LOW"

        return round(score, 2), level

    # ------------------------------------------------------------------
    def get_categories_info(self) -> list[dict]:
        """Return category metadata for the /categories endpoint."""
        return [
            {
                "id": cat["id"],
                "label": cat["label"],
                "severity": cat["severity"].lower(),
                "keyword_count": len(cat["keywords"]),
                "keywords": cat["keywords"],
            }
            for cat in self.categories
        ]
