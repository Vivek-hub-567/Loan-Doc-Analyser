"""
RAG-based explanation generator.

Takes the ML classifier's flagged keywords/categories, RETRIEVES relevant
knowledge base context (regulatory rules, legal definitions, predatory
patterns, fee explanations), and GENERATES a structured, plain-language
report — entirely offline, template-based. No LLM API call required.

This is the "G" in RAG, implemented via structured templates instead
of a generative LLM, since the project no longer uses Gemini.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from rag.retriever import RagRetriever

RISK_LEVEL_SEVERITY_RANK = {"low": 1, "info": 1, "medium": 2, "high": 3, "critical": 4}

OVERALL_MESSAGES = {
    "low_risk": (
        "This document appears relatively safe. Standard loan terms were detected "
        "with no major red flags. Still, read every clause carefully before signing."
    ),
    "medium_risk": (
        "This document carries moderate risk. Some fee or rate clauses need your "
        "attention before signing. None of the flags found are immediately dangerous, "
        "but you should clarify them with the lender in writing."
    ),
    "high_risk": (
        "This document is HIGH RISK. Several clauses give the lender unusual power "
        "over you or expose you to aggressive recovery action. Get a second opinion "
        "before signing."
    ),
    "predatory": (
        "WARNING — this document shows signs of PREDATORY lending. Multiple critical "
        "red flags were found. We strongly advise against signing this agreement "
        "without independent legal advice."
    ),
}


class RagExplainer:
    """
    Combines ML risk classification output with RAG-retrieved knowledge
    base context to produce a structured, borrower-facing explanation.
    """

    def __init__(self, retriever: RagRetriever | None = None):
        self.retriever = retriever or RagRetriever()
        if not self.retriever._ready:
            if self.retriever.index_exists():
                self.retriever.load_index()
            else:
                self.retriever.build_index()
                self.retriever.save_index()

    def explain(self, ml_result: dict) -> dict:
        """
        Main entry point. Takes LoanRiskClassifier.predict()-style output
        (risk_label, top_flags, category_breakdown) and returns a full
        RAG-augmented explanation report.
        """
        label = ml_result["risk_label"]
        score = ml_result["risk_score"]
        top_flags = ml_result.get("top_flags", [])
        breakdown = [c for c in ml_result.get("category_breakdown", []) if c["keyword_hits"] > 0]

        # ── RETRIEVE step ────────────────────────────────────────────
        retrieval = self.retriever.retrieve_for_keywords(top_flags, top_k_per_keyword=2)
        retrieved_docs = retrieval["retrieved_documents"]

        # ── AUGMENT + GENERATE step ──────────────────────────────────
        flagged_clauses = self._build_flagged_clauses(top_flags, retrieved_docs)
        action_plan = self._build_action_plan(label, flagged_clauses)
        regulatory_violations = self._extract_regulatory_violations(retrieved_docs)

        should_sign = label in ("low_risk", "medium_risk") and not any(
            d["risk_level"] == "critical" for d in retrieved_docs
        )

        return {
            "overall_summary": OVERALL_MESSAGES.get(label, OVERALL_MESSAGES["medium_risk"]),
            "risk_label": label,
            "risk_score": score,
            "flagged_clauses": flagged_clauses,
            "regulatory_violations": regulatory_violations,
            "borrower_action_plan": action_plan,
            "should_sign": should_sign,
            "sign_reasoning": self._sign_reasoning(label, regulatory_violations),
            "retrieved_sources": [
                {"title": d["title"], "source": d["source"], "relevance": d["relevance_score"]}
                for d in retrieved_docs
            ],
            "questions_to_ask_lender": self._generate_questions(breakdown),
            "_method": "rag_retrieval_template",
        }

    # ── Internal builders ───────────────────────────────────────────

    def _build_flagged_clauses(self, top_flags: list[str], retrieved_docs: list[dict]) -> list[dict]:
        """Pair each flagged keyword with its best-matching retrieved doc."""
        clauses = []
        used_docs = set()

        for kw in top_flags[:8]:
            # Find the best retrieved doc that was matched for this keyword
            match = next(
                (d for d in retrieved_docs if d.get("matched_keyword") == kw and d["doc_id"] not in used_docs),
                None,
            )
            if match is None:
                match = next((d for d in retrieved_docs if d["doc_id"] not in used_docs), None)

            if match:
                used_docs.add(match["doc_id"])
                clauses.append({
                    "clause_name": kw,
                    "explanation": match["content"],
                    "source": match["source"],
                    "severity": match["risk_level"],
                    "what_to_do": self._action_for_severity(match["risk_level"]),
                })
            else:
                clauses.append({
                    "clause_name": kw,
                    "explanation": f"The term '{kw}' was flagged as a risk indicator in this document.",
                    "source": "ML keyword analysis",
                    "severity": "medium",
                    "what_to_do": "Ask the lender to explain this clause in writing before signing.",
                })

        clauses.sort(key=lambda c: RISK_LEVEL_SEVERITY_RANK.get(c["severity"], 0), reverse=True)
        return clauses

    def _action_for_severity(self, severity: str) -> str:
        return {
            "critical": "Do not sign. Consult a financial advisor or file an RBI complaint if already signed.",
            "high": "Ask the lender to remove or clarify this clause in writing before signing.",
            "medium": "Negotiate this clause or ask for a clearer explanation before signing.",
            "low": "No action needed, but keep this in mind for your records.",
            "info": "Use this as a reference point when comparing loan offers.",
        }.get(severity, "Review this clause carefully before signing.")

    def _build_action_plan(self, label: str, flagged_clauses: list[dict]) -> list[str]:
        plan = ["Read the full loan agreement and Key Fact Statement (KFS) carefully."]

        has_critical = any(c["severity"] == "critical" for c in flagged_clauses)
        has_high = any(c["severity"] == "high" for c in flagged_clauses)

        if has_critical:
            plan.append("Do NOT sign this agreement until the critical issues below are resolved.")
            plan.append("Verify the lender's RBI registration at rbi.org.in/Scripts/BS_NBFCList.aspx.")
        if has_high:
            plan.append("Request written clarification for each high-risk clause before signing.")

        plan.append("Ask for the Key Fact Statement (KFS) if not already provided.")
        plan.append("Compare the APR (not just the interest rate) with at least 2 other lenders.")

        if label in ("high_risk", "predatory"):
            plan.append("Consult a financial advisor or legal expert before proceeding.")
            plan.append("If you suspect predatory practices, file a complaint at cms.rbi.org.in.")

        return plan

    def _extract_regulatory_violations(self, retrieved_docs: list[dict]) -> list[dict]:
        """Surface only the regulatory-category documents as explicit violations."""
        return [
            {
                "rule": d["title"],
                "source": d["source"],
                "description": d["content"],
                "severity": d["risk_level"],
            }
            for d in retrieved_docs
            if d["category"] == "regulatory"
        ]

    def _sign_reasoning(self, label: str, violations: list[dict]) -> str:
        if violations:
            rule_names = ", ".join(v["rule"] for v in violations[:2])
            return (
                f"This document appears to conflict with established regulatory guidance "
                f"including: {rule_names}. Address these before signing."
            )
        if label == "predatory":
            return "Multiple predatory lending patterns detected. Signing is not advised."
        if label == "high_risk":
            return "Significant power-imbalance or recovery-risk clauses present. Proceed with caution."
        if label == "medium_risk":
            return "Some clauses need clarification, but no critical violations were found."
        return "No major risk indicators found. Standard due diligence still recommended."

    def _generate_questions(self, breakdown: list[dict]) -> list[str]:
        questions = [
            "Can I get a copy of the Key Fact Statement (KFS) before signing?",
            "Is your company registered with the RBI? Can you share the registration number?",
            "What is the exact APR including all fees, not just the interest rate?",
        ]
        cat_ids = {c["category_id"] for c in breakdown}
        if "payment_fee" in cat_ids:
            questions.append("Can you itemize every fee that will be deducted before disbursal?")
        if "power_imbalance" in cat_ids:
            questions.append("Under what specific conditions can you change my loan terms?")
        if "privacy_risk" in cat_ids:
            questions.append("Why does your app need access to my contacts/SMS/location?")
        if "default_risk" in cat_ids:
            questions.append("What is the exact process and notice period before recovery action begins?")
        return questions[:6]
