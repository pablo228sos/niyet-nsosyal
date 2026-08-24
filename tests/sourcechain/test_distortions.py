from sourcechain.distortion import distortion_lens
from sourcechain.alignment import align_claim
from sourcechain.mismatch import source_mismatch
from sourcechain.schemas import DistortionType, EvidenceRelation
from sourcechain.structured_checks import detect_distortions


def test_distortion_lens_finds_numeric_causality_certainty_and_temporal_shifts():
    result = distortion_lens(
        "Araştırma X'in Y'ye kesinlikle neden olduğunu ve 2025'te yüzde 40 arttığını kanıtladı.",
        "Araştırma X ile Y arasında ilişki olabileceğini ve 2024'te yüzde 20 arttığını bildirdi.",
    )
    assert DistortionType.NUMERIC_DISTORTION in result.distortions
    assert DistortionType.CAUSALITY_SHIFT in result.distortions
    assert DistortionType.CERTAINTY_SHIFT in result.distortions
    assert DistortionType.TEMPORAL_SHIFT in result.distortions


def test_source_mismatch_is_typed_and_unknown_is_not_reputation():
    mismatch = source_mismatch("WHO raporuna göre oran arttı.", publisher="Example Institute")
    assert mismatch is True
    assert source_mismatch("Rapora göre oran arttı.", publisher="Example Institute") is None
    assert source_mismatch("WHO raporuna göre oran arttı.", publisher="World Health Organization (WHO)") is False
    assert source_mismatch("According to Example Institute, X causes Y.", publisher="Example Institute") is False
    assert source_mismatch("According to SOURCE, X causes Y.", publisher="Example Institute") is True
    assert source_mismatch("TÜİK raporuna göre oran arttı.", publisher="Türkiye İstatistik Kurumu") is False


def test_association_is_supported_without_causality_invention():
    assert align_claim("X is associated with Y.", "X is associated with Y.") is EvidenceRelation.SUPPORTED


def test_association_to_causation_is_conflicting_and_flagged_in_english_and_turkish():
    english = detect_distortions("X causes Y.", "X is associated with Y.")
    turkish = detect_distortions("X, Y'ye neden olur.", "X ile Y ilişkilidir.")

    assert DistortionType.CAUSALITY_SHIFT in english
    assert DistortionType.CAUSALITY_SHIFT in turkish
    assert align_claim("X causes Y.", "X is associated with Y.") is EvidenceRelation.CONFLICTING


def test_hedged_increase_to_unqualified_increase_is_certainty_shift():
    distortions = detect_distortions("X increases Y.", "X may increase Y.")

    assert DistortionType.CERTAINTY_SHIFT in distortions
    assert align_claim("X increases Y.", "X may increase Y.") is EvidenceRelation.CONFLICTING


def test_numeric_change_and_negation_are_conflicts():
    assert DistortionType.NUMERIC_DISTORTION in detect_distortions(
        "The rate is 40%.", "The rate is 12%."
    )
    assert align_claim("The rate is 40%.", "The rate is 12%.") is EvidenceRelation.CONFLICTING
    assert align_claim("X increases Y.", "X does not increase Y.") is EvidenceRelation.CONFLICTING


def test_shared_stopwords_do_not_create_false_conflict():
    assert align_claim(
        "The medicine causes nausea.",
        "The weather may improve tomorrow.",
    ) is EvidenceRelation.INSUFFICIENT


def test_one_shared_entity_does_not_create_false_structured_conflict():
    assert align_claim(
        "Coffee causes severe climate damage.",
        "Coffee may improve short term attention.",
    ) is EvidenceRelation.INSUFFICIENT


def test_turkish_certainty_and_scope_shifts_are_detected():
    assert DistortionType.CERTAINTY_SHIFT in detect_distortions(
        "X, Y'yi artırır.", "X, Y'yi artırabilir."
    )
    assert DistortionType.SCOPE_SHIFT in detect_distortions(
        "Tüm katılımcılar yarar gördü.", "Bazı katılımcılar yarar bildirdi."
    )
