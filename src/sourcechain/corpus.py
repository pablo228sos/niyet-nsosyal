from __future__ import annotations

from datetime import UTC, datetime

from .retrieval import SourceDocument


def demo_documents() -> tuple[SourceDocument, ...]:
    """Small, verified corpus for deterministic product demonstrations.

    Every passage is a short excerpt from the linked primary/official page and
    is stored with explicit provenance so the demo never depends on live web
    retrieval. The corpus is intentionally bounded: it demonstrates evidence
    relationships and failure behavior, not comprehensive web search or truth
    verification.
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
        SourceDocument(
            source_url="https://www.who.int/news-room/fact-sheets/detail/physical-activity",
            canonical_url="https://www.who.int/news-room/fact-sheets/detail/physical-activity",
            title="Physical activity",
            publisher="World Health Organization",
            publication_date="2024-06-26",
            text=(
                "Regular physical activity provides significant physical and mental health benefits."
            ),
            retrieved_at=datetime(2026, 9, 15, tzinfo=UTC),
            origin_cluster_id="who-physical-activity-2024",
        ),
        SourceDocument(
            source_url="https://science.nasa.gov/climate-change/causes/",
            canonical_url="https://science.nasa.gov/climate-change/causes/",
            title="Causes - NASA Science",
            publisher="NASA",
            publication_date=None,
            text=(
                "The industrial activities that our modern civilization depends upon have raised "
                "atmospheric carbon dioxide levels by nearly 50% since 1750."
            ),
            retrieved_at=datetime(2026, 9, 15, tzinfo=UTC),
            origin_cluster_id="nasa-climate-causes-co2",
        ),
    )
