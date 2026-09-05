from sequence_metrics import collapse_indices_to_sequences, score_sequences


def test_collapse_consecutive_indices():
    assert collapse_indices_to_sequences([5, 6, 7, 20, 21, 40]) == [
        (5, 7),
        (20, 21),
        (40, 40),
    ]


def test_empty_indices():
    assert collapse_indices_to_sequences([]) == []


def test_hundman_overlap_true_sequence_is_tp():
    """Gerçek [10, 20] içine tek tahmin noktası düşerse dizi TP'dir."""
    scored = score_sequences(
        {"T-1": [15]},
        {"T-1": [(10, 20)]},
    )
    assert scored["sequence_true_positives"] == 1
    assert scored["sequence_false_negatives"] == 0
    assert scored["sequence_pred_true_positives"] == 1
    assert scored["sequence_false_positives"] == 0
    assert scored["sequence_recall"] == 1.0
    assert scored["sequence_precision"] == 1.0


def test_false_positive_predicted_sequence():
    scored = score_sequences(
        {"T-1": [1, 2, 3]},
        {"T-1": [(100, 110)]},
    )
    assert scored["sequence_false_positives"] == 1
    assert scored["sequence_false_negatives"] == 1
    assert scored["sequence_precision"] == 0.0
    assert scored["sequence_recall"] == 0.0


def test_channels_are_independent():
    scored = score_sequences(
        {"T-1": [15], "T-2": [1]},
        {"T-1": [(10, 20)], "T-2": [(50, 60)]},
    )
    assert scored["sequence_true_positives"] == 1
    assert scored["sequence_false_negatives"] == 1
    assert scored["sequence_false_positives"] == 1
