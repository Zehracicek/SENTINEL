import numpy as np

from simulator import MSL_CHANNELS, NASADataLoader


def _loader_with_offset(test_len=100, se_len=80):
    loader = NASADataLoader()
    loader.channels["T-1"] = {
        "data": np.zeros((test_len, 1)),
        "meta": MSL_CHANNELS["T-1"],
        "length": test_len,
    }
    loader.smoothed_errors["T-1"] = np.arange(se_len, dtype=float)
    loader.y_hat["T-1"] = np.arange(se_len, dtype=float) + 0.5
    return loader


def test_smoothed_error_none_during_lookback():
    loader = _loader_with_offset()
    assert loader._get_smoothed_error("T-1", 0) is None
    assert loader._get_smoothed_error("T-1", 19) is None


def test_smoothed_error_aligns_after_offset():
    loader = _loader_with_offset()
    assert loader._get_smoothed_error("T-1", 20) == 0.0
    assert loader._get_smoothed_error("T-1", 21) == 1.0
    assert loader._get_smoothed_error("T-1", 99) == 79.0
    assert loader._get_smoothed_error("T-1", 100) is None


def test_prediction_uses_same_offset():
    loader = _loader_with_offset()
    assert loader._get_prediction("T-1", 20) == 0.5
    assert loader._get_prediction("T-1", 19) is None
