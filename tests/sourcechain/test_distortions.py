from sourcechain.distortion import distortion_lens
from sourcechain.mismatch import source_mismatch
from sourcechain.schemas import DistortionType


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

