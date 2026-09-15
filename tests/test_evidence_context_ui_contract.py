from api.human_help import _evidence_context


def test_evidence_context_preserves_exact_claim_text_for_each_passage():
    response = {
        "evidence_bundle": {
            "analysis": {
                "claims": [
                    {
                        "claim_id": "claim-1",
                        "text": "Industrial activities raised atmospheric carbon dioxide by 90% since 1750.",
                    }
                ]
            },
            "status": "CONFLICTING",
            "sufficient": True,
            "explanation": "bounded evidence",
            "evidence": [
                {
                    "claim_id": "claim-1",
                    "title": "Causes",
                    "source_url": "https://science.nasa.gov/climate-change/causes/",
                    "publisher": "NASA Science",
                    "publication_date": None,
                    "passage": (
                        "The industrial activities that our modern civilization depends upon "
                        "have raised atmospheric carbon dioxide levels by nearly 50% since 1750."
                    ),
                    "relation": "CONFLICTING",
                    "distortions": ["NUMERIC_DISTORTION"],
                }
            ],
        },
        "resolution": {"path": "BOTH"},
    }

    context = _evidence_context(response)

    assert context is not None
    item = context["evidence"][0]
    assert item["claim_text"] == response["evidence_bundle"]["analysis"]["claims"][0]["text"]
    assert item["passage"].endswith("nearly 50% since 1750.")
    assert item["distortions"] == ["NUMERIC_DISTORTION"]


def test_evidence_context_does_not_invent_claim_text_when_mapping_is_missing():
    response = {
        "evidence_bundle": {
            "analysis": {"claims": []},
            "status": "PARTIAL",
            "sufficient": True,
            "explanation": "bounded evidence",
            "evidence": [
                {
                    "claim_id": "unknown",
                    "title": "Stored source",
                    "source_url": "https://example.org/source",
                    "publisher": "Example",
                    "publication_date": None,
                    "passage": "Stored evidence passage.",
                    "relation": "PARTIALLY_SUPPORTED",
                    "distortions": [],
                }
            ],
        },
        "resolution": {"path": "EVIDENCE"},
    }

    context = _evidence_context(response)

    assert context is not None
    assert context["evidence"][0]["claim_text"] is None
