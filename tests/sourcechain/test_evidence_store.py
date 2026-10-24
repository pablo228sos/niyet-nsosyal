from __future__ import annotations

from datetime import UTC, datetime
import pytest

from sourcechain.evidence import build_evidence_bundle
from sourcechain.evidence_store import (
    AuditRecord,
    BundleVersionRecord,
    ContributionRejectedError,
    ContributionStatus,
    EvidenceNotFoundError,
    EvidenceStoreError,
    HumanSourceContribution,
    ImmutableVersionConflictError,
    MemoryEvidenceStore,
    compute_bundle_hash,
)
from sourcechain.retrieval import ControlledEvidenceProvider, SourceDocument
from sourcechain.schemas import BundleStatus, EvidenceBundle, EvidenceRelation
from sourcechain.statement_classifier import analyze_post

NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=UTC)


def make_test_bundle(text: str = "Satışlar yüzde 20 arttı.") -> EvidenceBundle:
    analysis = analyze_post(text)
    provider = ControlledEvidenceProvider(())
    return build_evidence_bundle(analysis, provider, now=NOW)


def test_compute_bundle_hash_is_deterministic():
    bundle1 = make_test_bundle()
    bundle2 = make_test_bundle()
    hash1 = compute_bundle_hash(bundle1)
    hash2 = compute_bundle_hash(bundle2)

    assert hash1 == hash2
    assert len(hash1) == 64
    assert isinstance(hash1, str)


def test_save_and_retrieve_bundle():
    store = MemoryEvidenceStore()
    bundle = make_test_bundle()

    record = store.save_bundle(bundle, actor_id="analyst-1", audit_metadata={"source": "test"})

    assert record.bundle_id == bundle.bundle_id
    assert record.version == bundle.version
    assert record.bundle == bundle
    assert record.bundle_hash == compute_bundle_hash(bundle)

    latest = store.get_bundle(bundle.bundle_id)
    assert latest == bundle

    v1 = store.get_bundle(bundle.bundle_id, version=1)
    assert v1 == bundle

    assert store.get_bundle("nonexistent-bundle") is None
    assert store.get_bundle(bundle.bundle_id, version=999) is None


def test_save_bundle_is_idempotent_for_identical_content():
    store = MemoryEvidenceStore()
    bundle = make_test_bundle()

    rec1 = store.save_bundle(bundle)
    rec2 = store.save_bundle(bundle)

    assert rec1.bundle_hash == rec2.bundle_hash
    assert rec1 is rec2


def test_save_bundle_rejects_mutation_conflict():
    store = MemoryEvidenceStore()
    bundle = make_test_bundle()
    store.save_bundle(bundle)

    # Attempt to save a modified bundle under the exact same bundle_id and version
    mutated_bundle = EvidenceBundle(
        bundle_id=bundle.bundle_id,
        version=bundle.version,
        analysis=bundle.analysis,
        evidence=bundle.evidence,
        status=BundleStatus.CONFLICTING,  # changed status
        sufficient=bundle.sufficient,
        explanation="Mutated explanation",
        cited_evidence_ids=bundle.cited_evidence_ids,
        created_at=bundle.created_at,
    )

    with pytest.raises(ImmutableVersionConflictError) as exc_info:
        store.save_bundle(mutated_bundle)

    assert f"Cannot mutate bundle '{bundle.bundle_id}' version {bundle.version}" in str(exc_info.value)


def test_version_history_and_listing():
    store = MemoryEvidenceStore()
    bundle_v1 = make_test_bundle()
    store.save_bundle(bundle_v1)

    bundle_v2 = EvidenceBundle(
        bundle_id=bundle_v1.bundle_id,
        version=2,
        analysis=bundle_v1.analysis,
        evidence=bundle_v1.evidence,
        status=bundle_v1.status,
        sufficient=bundle_v1.sufficient,
        explanation="Updated version 2 explanation",
        cited_evidence_ids=bundle_v1.cited_evidence_ids,
        created_at=NOW,
    )
    store.save_bundle(bundle_v2)

    versions = store.list_versions(bundle_v1.bundle_id)
    assert len(versions) == 2
    assert [v.version for v in versions] == [1, 2]

    latest = store.get_bundle(bundle_v1.bundle_id)
    assert latest is not None
    assert latest.version == 2
    assert latest.explanation == "Updated version 2 explanation"

    stored_v1 = store.get_bundle(bundle_v1.bundle_id, version=1)
    assert stored_v1 is not None
    assert stored_v1.version == 1


def test_submit_human_source_validation():
    # Empty field validation
    with pytest.raises(ValueError, match="contribution_id, claim_id, and contributor_id are required"):
        HumanSourceContribution(
            contribution_id="",
            claim_id="cl-1",
            source_url="https://example.org",
            canonical_url="https://example.org",
            title="Title",
            publisher="Pub",
            text="Evidence text",
            contributor_id="user-1",
            rationale="Rationale",
            submitted_at=NOW,
        )

    # Invalid URL scheme
    with pytest.raises(ValueError, match="source URLs must use valid http or https scheme"):
        HumanSourceContribution(
            contribution_id="contrib-1",
            claim_id="cl-1",
            source_url="ftp://example.org/doc",
            canonical_url="https://example.org/doc",
            title="Title",
            publisher="Pub",
            text="Evidence text",
            contributor_id="user-1",
            rationale="Rationale",
            submitted_at=NOW,
        )

    # Empty text
    with pytest.raises(ValueError, match="contribution text is required"):
        HumanSourceContribution(
            contribution_id="contrib-1",
            claim_id="cl-1",
            source_url="https://example.org/doc",
            canonical_url="https://example.org/doc",
            title="Title",
            publisher="Pub",
            text="   ",
            contributor_id="user-1",
            rationale="Rationale",
            submitted_at=NOW,
        )


def test_submit_and_list_human_sources():
    store = MemoryEvidenceStore()

    c1 = HumanSourceContribution(
        contribution_id="c-1",
        claim_id="claim-100",
        source_url="https://reuters.com/article1",
        canonical_url="https://reuters.com/article1",
        title="Reuters Report",
        publisher="Reuters",
        text="Sales increased 20% according to company filings.",
        contributor_id="researcher-1",
        rationale="Verified primary filing source",
        submitted_at=NOW,
    )

    c2 = HumanSourceContribution(
        contribution_id="c-2",
        claim_id="claim-200",
        source_url="https://apnews.com/article2",
        canonical_url="https://apnews.com/article2",
        title="AP Report",
        publisher="AP",
        text="Weather report indicates sunshine tomorrow.",
        contributor_id="researcher-2",
        rationale="Official meteorological statement",
        submitted_at=NOW,
    )

    store.submit_human_source(c1)
    store.submit_human_source(c2)

    assert store.get_contribution("c-1") == c1
    assert store.get_contribution("c-999") is None

    all_contribs = store.list_contributions()
    assert len(all_contribs) == 2

    by_claim = store.list_contributions(claim_id="claim-100")
    assert len(by_claim) == 1
    assert by_claim[0].contribution_id == "c-1"

    pending = store.list_contributions(status=ContributionStatus.PENDING)
    assert len(pending) == 2


def test_ingest_human_contribution_success():
    store = MemoryEvidenceStore()
    bundle = make_test_bundle("Satışlar yüzde 20 arttı.")
    store.save_bundle(bundle)

    claim_id = bundle.analysis.claims[0].claim_id

    contrib = HumanSourceContribution(
        contribution_id="contrib-valid-1",
        claim_id=claim_id,
        source_url="https://example.org/press-release",
        canonical_url="https://example.org/press-release",
        title="Official Press Release",
        publisher="Example Corp",
        text="Denetlenen mali sonuçlara göre satışlar yüzde 20 arttı ve rekor kırdı.",
        contributor_id="auditor-alice",
        rationale="Direct link to audited earnings release",
        submitted_at=NOW,
    )
    store.submit_human_source(contrib)

    new_bundle, item = store.ingest_human_contribution(
        contribution_id="contrib-valid-1",
        bundle_id=bundle.bundle_id,
        actor_id="moderator-bob",
        now=NOW,
    )

    # Ingestion creates version 2
    assert new_bundle.version == 2
    assert new_bundle.bundle_id == bundle.bundle_id
    assert len(new_bundle.evidence) == 1
    assert item.claim_id == claim_id
    assert item.relation in {EvidenceRelation.SUPPORTED, EvidenceRelation.PARTIALLY_SUPPORTED}
    assert item.metadata["source_type"] == "human_submitted"
    assert item.metadata["contributor_id"] == "auditor-alice"

    # Status updated in store
    updated_contrib = store.get_contribution("contrib-valid-1")
    assert updated_contrib is not None
    assert updated_contrib.status is ContributionStatus.INGESTED
    assert updated_contrib.ingested_evidence_id == item.evidence_id

    # Trying to re-ingest raises ContributionRejectedError
    with pytest.raises(ContributionRejectedError, match="has already been ingested"):
        store.ingest_human_contribution(
            contribution_id="contrib-valid-1",
            bundle_id=bundle.bundle_id,
            actor_id="moderator-bob",
        )


def test_ingest_human_contribution_rejects_missing_claim():
    store = MemoryEvidenceStore()
    bundle = make_test_bundle("Satışlar yüzde 20 arttı.")
    store.save_bundle(bundle)

    contrib = HumanSourceContribution(
        contribution_id="contrib-wrong-claim",
        claim_id="nonexistent-claim-id",
        source_url="https://example.org/press-release",
        canonical_url="https://example.org/press-release",
        title="Official Press Release",
        publisher="Example Corp",
        text="Satışlar yüzde 20 arttı.",
        contributor_id="auditor-alice",
        rationale="Audit release",
        submitted_at=NOW,
    )
    store.submit_human_source(contrib)

    with pytest.raises(ContributionRejectedError, match="not present in bundle"):
        store.ingest_human_contribution(
            contribution_id="contrib-wrong-claim",
            bundle_id=bundle.bundle_id,
            actor_id="mod-1",
        )

    updated = store.get_contribution("contrib-wrong-claim")
    assert updated is not None
    assert updated.status is ContributionStatus.REJECTED
    assert "not present in bundle" in (updated.rejection_reason or "")


def test_ingest_human_contribution_rejects_unaligned_text():
    store = MemoryEvidenceStore()
    bundle = make_test_bundle("Satışlar yüzde 20 arttı.")
    store.save_bundle(bundle)

    claim_id = bundle.analysis.claims[0].claim_id

    contrib = HumanSourceContribution(
        contribution_id="contrib-irrelevant",
        claim_id=claim_id,
        source_url="https://example.org/weather",
        canonical_url="https://example.org/weather",
        title="Weather Report",
        publisher="Meteo",
        text="Yarın hava güneşli ve sıcaklık 25 derece olacak.",
        contributor_id="spammer",
        rationale="Totally unrelated article",
        submitted_at=NOW,
    )
    store.submit_human_source(contrib)

    with pytest.raises(ContributionRejectedError, match="No passage aligned"):
        store.ingest_human_contribution(
            contribution_id="contrib-irrelevant",
            bundle_id=bundle.bundle_id,
            actor_id="mod-1",
        )

    updated = store.get_contribution("contrib-irrelevant")
    assert updated is not None
    assert updated.status is ContributionStatus.REJECTED
    assert "No passage aligned" in (updated.rejection_reason or "")


def test_ingest_human_contribution_missing_entities():
    store = MemoryEvidenceStore()
    bundle = make_test_bundle()
    store.save_bundle(bundle)

    with pytest.raises(EvidenceNotFoundError, match="Contribution 'missing-c' not found"):
        store.ingest_human_contribution("missing-c", bundle.bundle_id, actor_id="admin")

    contrib = HumanSourceContribution(
        contribution_id="contrib-c1",
        claim_id=bundle.analysis.claims[0].claim_id,
        source_url="https://example.org/doc",
        canonical_url="https://example.org/doc",
        title="Doc",
        publisher="Pub",
        text="Satışlar yüzde 20 arttı.",
        contributor_id="user-1",
        rationale="Rationale",
        submitted_at=NOW,
    )
    store.submit_human_source(contrib)

    with pytest.raises(EvidenceNotFoundError, match="Bundle 'missing-b' not found"):
        store.ingest_human_contribution("contrib-c1", "missing-b", actor_id="admin")


def test_dict_serialization_roundtrip():
    bundle = make_test_bundle()
    record = BundleVersionRecord(
        bundle_id=bundle.bundle_id,
        version=bundle.version,
        bundle=bundle,
        bundle_hash=compute_bundle_hash(bundle),
        created_at=NOW,
        audit_metadata={"env": "prod"},
        document_hashes=("hash1", "hash2"),
    )
    data = record.to_dict()
    restored = BundleVersionRecord.from_dict(data)

    assert restored.bundle_id == record.bundle_id
    assert restored.version == record.version
    assert restored.bundle_hash == record.bundle_hash
    assert restored.audit_metadata == record.audit_metadata
    assert restored.document_hashes == record.document_hashes

    contrib = HumanSourceContribution(
        contribution_id="c-test",
        claim_id="cl-test",
        source_url="https://example.org/src",
        canonical_url="https://example.org/src",
        title="Test Title",
        publisher="Test Pub",
        text="Test content body",
        contributor_id="user-test",
        rationale="Good rationale",
        submitted_at=NOW,
        status=ContributionStatus.INGESTED,
        ingested_evidence_id="ev-123",
    )
    c_data = contrib.to_dict()
    restored_c = HumanSourceContribution.from_dict(c_data)

    assert restored_c.contribution_id == contrib.contribution_id
    assert restored_c.status == contrib.status
    assert restored_c.ingested_evidence_id == contrib.ingested_evidence_id
    assert restored_c.document_hash == contrib.document_hash


def test_audit_trail_logging():
    store = MemoryEvidenceStore()
    bundle = make_test_bundle()
    store.save_bundle(bundle, actor_id="admin-1")

    trail = store.get_audit_trail(bundle.bundle_id)
    assert len(trail) >= 1
    assert trail[0].bundle_id == bundle.bundle_id
    assert trail[0].action == "SAVE_BUNDLE"
    assert trail[0].actor_id == "admin-1"

    audit_dict = trail[0].to_dict()
    assert audit_dict["action"] == "SAVE_BUNDLE"
    assert audit_dict["actor_id"] == "admin-1"
