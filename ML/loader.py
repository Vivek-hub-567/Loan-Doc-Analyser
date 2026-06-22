"""
Knowledge base loader.
Aggregates all documents across regulatory, legal, consumer protection,
predatory pattern, fee explanation, and safe/unsafe comparison sources
into one flat list ready for RAG embedding + indexing.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from knowledge_base.regulatory.rbi_digital_lending_2022 import DOCUMENTS as RBI_DL_DOCS
from knowledge_base.regulatory.rbi_master_circular_sebi import DOCUMENTS as RBI_MC_SEBI_DOCS
from knowledge_base.legal_definitions.legal_terms import DOCUMENTS as LEGAL_DOCS
from knowledge_base.legal_definitions.legal_terms_extended import DOCUMENTS as LEGAL_EXT_DOCS
from knowledge_base.knowledge_docs import ALL_DOCUMENTS as OTHER_DOCS


def load_all_documents() -> list[dict]:
    """
    Returns the complete knowledge base as a flat list of document dicts.
    Each doc has: id, category, source, title, content, keywords, risk_level/violation_severity
    """
    all_docs = (
        RBI_DL_DOCS
        + RBI_MC_SEBI_DOCS
        + LEGAL_DOCS
        + LEGAL_EXT_DOCS
        + OTHER_DOCS
    )

    # Normalize risk_level / violation_severity into a single field
    for doc in all_docs:
        if "violation_severity" in doc and "risk_level" not in doc:
            doc["risk_level"] = doc["violation_severity"]

    return all_docs


def get_stats() -> dict:
    """Returns knowledge base composition stats."""
    docs = load_all_documents()
    by_category = {}
    for doc in docs:
        cat = doc["category"]
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "total_documents": len(docs),
        "by_category": by_category,
        "sources": sorted(set(d["source"] for d in docs)),
    }


if __name__ == "__main__":
    stats = get_stats()
    print("Knowledge Base Stats")
    print("=" * 40)
    print(f"Total documents: {stats['total_documents']}")
    print("\nBy category:")
    for cat, count in stats["by_category"].items():
        print(f"  {cat}: {count}")
    print(f"\nSources ({len(stats['sources'])}):")
    for s in stats["sources"]:
        print(f"  - {s}")
