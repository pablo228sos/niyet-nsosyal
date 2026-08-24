import pytest

from experiments.evaluate_matching_draft import (
    lexical_similarity_matrix,
    load_data,
    retrieval_metrics,
)


def test_reviewed_lexical_retrieval_metrics_are_frozen():
    benchmark, queries, responders = load_data()
    similarities = lexical_similarity_matrix(queries, responders)

    assert benchmark["version"] == "v1-reviewed"
    assert benchmark["review_status"] == "reviewed"
    assert len(queries) == 32
    assert len(responders) == 8
    assert retrieval_metrics(queries, responders, similarities) == pytest.approx(
        (0.46875, 0.84375, 0.8450020583980385),
        abs=1e-12,
    )
