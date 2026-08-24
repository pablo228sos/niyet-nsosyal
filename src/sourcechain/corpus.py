from __future__ import annotations

from datetime import UTC, datetime

from .retrieval import SourceDocument


def demo_documents() -> tuple[SourceDocument, ...]:
    """Small, verified corpus for the deterministic product demonstration.

    The passage is a short excerpt from the linked PubMed abstract. Keeping the
    corpus in code makes the provenance inspectable and avoids network access at
    request time. It is demonstration evidence, not comprehensive web search.
    """

    return (
        SourceDocument(
            source_url="https://pubmed.ncbi.nlm.nih.gov/26572796/",
            canonical_url="https://pubmed.ncbi.nlm.nih.gov/26572796/",
            title="Association of Coffee Consumption With Total and Cause-Specific Mortality in 3 Large Prospective Cohorts",
            publisher="Circulation",
            publication_date="2015-12-15",
            text=(
                "Higher consumption of total coffee, caffeinated coffee, and "
                "decaffeinated coffee was associated with lower risk of total mortality."
            ),
            retrieved_at=datetime(2026, 8, 24, tzinfo=UTC),
            origin_cluster_id="pubmed-26572796",
        ),
    )
