"""
ml/rag_explainer.py — TF-IDF Cosine Similarity RAG Explainer for LoanGuard AI.

Retrieves relevant regulatory documents from a local knowledge base and
generates a structured explanation report.
"""

from __future__ import annotations

import math
import re
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_KB_PATH = Path(__file__).parent.parent / "knowledge_base"


class RAGExplainer:
    """
    Offline TF-IDF cosine similarity retrieval over local knowledge base documents.
    Documents are loaded at init time and indexed.
    """

    def __init__(self, kb_path: str | Path = _DEFAULT_KB_PATH) -> None:
        self.kb_path = Path(kb_path)
        self._documents: list[dict[str, str]] = []
        self._doc_vectors: list[dict[str, float]] = []
        self._idf: dict[str, float] = {}
        self._loaded = False
        self._load_and_index()

    # ------------------------------------------------------------------
    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b[a-z]{2,}\b", text.lower())

    def _tf(self, tokens: list[str]) -> dict[str, float]:
        counts: dict[str, int] = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
        total = max(len(tokens), 1)
        return {t: c / total for t, c in counts.items()}

    def _cosine(self, v1: dict[str, float], v2: dict[str, float]) -> float:
        common = set(v1) & set(v2)
        if not common:
            return 0.0
        dot = sum(v1[t] * v2[t] for t in common)
        m1 = math.sqrt(sum(x * x for x in v1.values()))
        m2 = math.sqrt(sum(x * x for x in v2.values()))
        if m1 == 0 or m2 == 0:
            return 0.0
        return dot / (m1 * m2)

    # ------------------------------------------------------------------
    def _load_and_index(self) -> None:
        """Load all .txt and .md files from knowledge_base/ and build TF-IDF index."""
        if not self.kb_path.exists():
            logger.warning(f"Knowledge base path not found: {self.kb_path}")
            return

        docs = []
        for ext in ("*.txt", "*.md"):
            for fpath in sorted(self.kb_path.glob(ext)):
                try:
                    text = fpath.read_text(encoding="utf-8", errors="replace")
                    docs.append({"title": fpath.stem, "content": text, "path": str(fpath)})
                except Exception as e:
                    logger.warning(f"Could not read {fpath}: {e}")

        if not docs:
            logger.info("RAG knowledge base is empty — RAG explainer will return no results.")
            return

        self._documents = docs
        N = len(docs)
        df: dict[str, int] = {}
        tokenized_docs = []
        for doc in docs:
            tokens = self._tokenize(doc["content"])
            tokenized_docs.append(tokens)
            for t in set(tokens):
                df[t] = df.get(t, 0) + 1

        self._idf = {t: math.log((N + 1) / (d + 1)) + 1.0 for t, d in df.items()}

        for tokens in tokenized_docs:
            tf = self._tf(tokens)
            vec = {t: tf[t] * self._idf.get(t, 1.0) for t in tf}
            self._doc_vectors.append(vec)

        self._loaded = True
        logger.info(f"RAG: indexed {len(docs)} knowledge base documents.")

    # ------------------------------------------------------------------
    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.05,
    ) -> list[dict[str, Any]]:
        """Retrieve top-k relevant documents for a query."""
        if not self._loaded or not self._documents:
            return []

        tokens = self._tokenize(query)
        tf = self._tf(tokens)
        query_vec = {t: tf[t] * self._idf.get(t, 1.0) for t in tf}

        scores = [
            (i, self._cosine(query_vec, dv))
            for i, dv in enumerate(self._doc_vectors)
        ]
        scores.sort(key=lambda x: -x[1])

        results = []
        for idx, score in scores[:top_k]:
            if score < min_score:
                break
            doc = self._documents[idx]
            snippet = doc["content"][:300].strip()
            results.append(
                {
                    "title": doc["title"],
                    "snippet": snippet,
                    "score": round(score, 4),
                    "path": doc["path"],
                }
            )
        return results

    def retrieve_for_keywords(
        self,
        keywords: list[str],
        top_k: int = 3,
        min_score: float = 0.05,
    ) -> list[dict[str, Any]]:
        """Retrieve and deduplicate results for multiple keyword queries."""
        seen_titles: set[str] = set()
        all_results: list[dict[str, Any]] = []

        for kw in keywords:
            for r in self.retrieve(kw, top_k=2, min_score=min_score):
                if r["title"] not in seen_titles:
                    seen_titles.add(r["title"])
                    all_results.append(r)

        # Re-sort by score
        all_results.sort(key=lambda x: -x["score"])
        return all_results[:top_k]

    # ------------------------------------------------------------------
    def explain(
        self,
        top_flags: list[str],
        risk_level: str,
        category_breakdown: list[dict],
        sentiment_label: str,
    ) -> dict[str, Any]:
        """
        Generate a structured RAG explanation report.

        Returns:
            should_sign, overall_summary, flagged_clauses,
            regulatory_violations, borrower_action_plan,
            questions_to_ask_lender, retrieved_sources
        """
        sources = self.retrieve_for_keywords(top_flags[:5])

        # Determine should_sign
        should_sign = risk_level not in ("CRITICAL", "HIGH") and sentiment_label != "THREATENING"

        # Build flagged clauses from category breakdown
        flagged_clauses = [
            {
                "category": cat["label"],
                "severity": cat["severity"],
                "keywords": cat["matched_keywords"][:5],
                "explanation": _FLAG_EXPLANATIONS.get(
                    cat["category_id"],
                    "This clause may be unfavourable to the borrower."
                ),
            }
            for cat in category_breakdown
            if cat["keyword_hits"] > 0
        ]

        # Regulatory violations — surface only if MEDIUM+ severity
        reg_violations = [
            c for c in flagged_clauses
            if c["severity"] in ("critical", "high", "medium")
        ]

        # Borrower action plan
        action_plan = _build_action_plan(risk_level, category_breakdown)

        # Questions to ask lender
        questions = _build_questions(top_flags[:10])

        return {
            "should_sign": should_sign,
            "overall_summary": _build_summary(risk_level, sentiment_label, len(flagged_clauses)),
            "flagged_clauses": flagged_clauses,
            "regulatory_violations": reg_violations,
            "borrower_action_plan": action_plan,
            "questions_to_ask_lender": questions,
            "retrieved_sources": sources,
        }


# ---------------------------------------------------------------------------
# Helper text generators
# ---------------------------------------------------------------------------

_FLAG_EXPLANATIONS = {
    "hidden_fee_risk": (
        "This agreement contains hidden fee clauses that may not be clearly disclosed. "
        "Under RBI guidelines, all fees must be disclosed upfront in the Key Fact Statement (KFS)."
    ),
    "default_recovery_risk": (
        "Aggressive default recovery clauses detected. The lender may seize assets or accelerate "
        "the loan without adequate borrower protections. SARFAESI proceedings require a 60-day notice."
    ),
    "legal_clause_detection": (
        "Complex legal clauses including mandatory arbitration or force majeure may limit the "
        "borrower's ability to seek judicial remedies."
    ),
    "power_imbalance_risk": (
        "Clauses granting the lender unilateral or sole discretion powers create significant power "
        "imbalance. RBI guidelines require fair treatment of borrowers."
    ),
    "privacy_data_risk": (
        "This agreement requests access to personal device data (contacts, SMS, location) that may "
        "violate the DPDP Act, 2023. Consent must be specific and revocable."
    ),
    "regulatory_compliance": (
        "The agreement may not fully comply with RBI's digital lending guidelines including "
        "direct disbursement, KFS requirements, and grievance redressal mechanisms."
    ),
    "predatory_lending_signals": (
        "Strong predatory lending signals detected including upfront deductions, hidden charges, "
        "and forced insurance bundling — common tactics in predatory digital lending."
    ),
    "financial_entity_extraction": (
        "Financial terms including interest rates, fees, and loan amounts have been identified. "
        "Verify all figures match what was communicated during the loan application."
    ),
}


def _build_summary(risk_level: str, sentiment: str, n_flags: int) -> str:
    if risk_level == "CRITICAL":
        return (
            f"This loan agreement carries CRITICAL risk with {n_flags} flagged clause(s). "
            "Multiple predatory clauses and aggressive recovery terms were detected. "
            "We strongly recommend NOT signing this agreement without legal consultation."
        )
    elif risk_level == "HIGH":
        return (
            f"This loan agreement carries HIGH risk with {n_flags} flagged clause(s). "
            "Several unfavourable terms including power imbalance and hidden fee clauses were found. "
            "We recommend seeking clarification from the lender and consulting a legal advisor."
        )
    elif risk_level == "MEDIUM":
        return (
            f"This loan agreement carries MEDIUM risk with {n_flags} flagged clause(s). "
            "Some standard clauses may be unfavourable. Review the flagged items carefully before signing."
        )
    else:
        return (
            f"This loan agreement appears to carry LOW risk with {n_flags} flagged clause(s). "
            "Review the terms carefully and ensure all figures match the loan offer communicated to you."
        )


def _build_action_plan(risk_level: str, breakdown: list[dict]) -> list[str]:
    actions = []
    if risk_level in ("CRITICAL", "HIGH"):
        actions.append("Do NOT sign this agreement without consulting a legal advisor or financial counsellor.")
        actions.append("File a complaint with the RBI Ombudsman if lender refuses to modify unfair terms.")

    cat_ids = {c["category_id"] for c in breakdown if c["keyword_hits"] > 0}

    if "hidden_fee_risk" in cat_ids:
        actions.append("Request an itemised fee schedule and verify it matches the Key Fact Statement (KFS).")
    if "predatory_lending_signals" in cat_ids:
        actions.append("Demand the net disbursement amount in writing before signing.")
    if "privacy_data_risk" in cat_ids:
        actions.append("Revoke unnecessary app permissions after loan disbursement.")
        actions.append("Report excessive data collection to the Data Protection Board of India.")
    if "power_imbalance_risk" in cat_ids:
        actions.append("Negotiate to remove or limit 'sole discretion' and 'without notice' clauses.")
    if "default_recovery_risk" in cat_ids:
        actions.append("Understand the default definition and ensure you can meet repayment obligations.")
    if "regulatory_compliance" in cat_ids:
        actions.append("Ask the lender to provide the Key Fact Statement (KFS) as required by RBI.")

    actions.append("Keep a copy of all signed documents and communications with the lender.")
    return actions


def _build_questions(top_flags: list[str]) -> list[str]:
    base_questions = [
        "What is the Annual Percentage Rate (APR) including all fees and charges?",
        "Can you provide the Key Fact Statement (KFS) as required by RBI guidelines?",
        "What is the net amount I will receive after all deductions?",
        "Are there any charges not mentioned in the agreement?",
        "What is the exact process and notice period before recovery action is taken?",
        "Can I prepay the loan without any penalty?",
        "What data permissions does the app require and can I revoke them?",
        "Who is the grievance redressal officer and how do I contact them?",
    ]
    flag_questions: list[str] = []
    if any("insurance" in f.lower() for f in top_flags):
        flag_questions.append("Is the insurance bundled with my loan mandatory or optional?")
    if any("arbitration" in f.lower() for f in top_flags):
        flag_questions.append("Why is mandatory arbitration required instead of court proceedings?")
    if any("upfront" in f.lower() or "deduction" in f.lower() for f in top_flags):
        flag_questions.append("Why are fees deducted upfront rather than added to the loan amount?")

    return (flag_questions + base_questions)[:8]
