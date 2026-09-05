"""channel_features.py testleri.

Bu modül, Python'un `hash()` fonksiyonunun süreçler arası kararsız olması
nedeniyle eklendi: kaydedilmiş River/RL modelleri yeniden başlatmadan sonra
farklı kanal kodları görüyor ve öğrenilenler bozuluyordu.
"""

from channel_features import KNOWN_CHANNELS, channel_code


def test_known_channels_are_in_unit_interval():
    for channel_id in KNOWN_CHANNELS:
        assert 0.0 <= channel_code(channel_id) < 1.0


def test_unknown_channels_are_in_unit_interval():
    for channel_id in ("BILINMEYEN", "X-999", ""):
        assert 0.0 <= channel_code(channel_id) < 1.0


def test_known_channels_get_distinct_codes():
    codes = {channel_code(c) for c in KNOWN_CHANNELS}
    assert len(codes) == len(KNOWN_CHANNELS)


def test_code_is_deterministic_across_calls():
    assert channel_code("T-1") == channel_code("T-1")
    assert channel_code("BILINMEYEN") == channel_code("BILINMEYEN")


def test_code_is_stable_against_hardcoded_expectations():
    """Sabit beklenen değerler — kod değişirse kaydedilmiş modeller geçersiz olur.

    Bu test kırılırsa river_learner._FEATURE_VERSION artırılmalıdır.
    """
    assert channel_code(KNOWN_CHANNELS[0]) == 0.0
    expected_step = 1.0 / len(KNOWN_CHANNELS)
    assert channel_code(KNOWN_CHANNELS[1]) == expected_step


def test_different_channels_do_not_collide():
    assert channel_code("T-1") != channel_code("T-2")
