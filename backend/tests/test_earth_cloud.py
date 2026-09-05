from earth_cloud import EarthCloudSimulator


def test_low_precision_raises_threshold():
    derived = EarthCloudSimulator.suggest_threshold(
        {
            "sequence_evaluated": True,
            "sequence_indexed_readings": 200,
            "sequence_precision": 0.2,
            "sequence_recall": 0.9,
        }
    )
    assert derived["feedback_basis"] == "sequence"
    assert derived["threshold_suggestion"] > 55.0


def test_low_recall_lowers_threshold():
    derived = EarthCloudSimulator.suggest_threshold(
        {
            "sequence_evaluated": True,
            "sequence_indexed_readings": 200,
            "sequence_precision": 0.9,
            "sequence_recall": 0.2,
        }
    )
    assert derived["threshold_suggestion"] < 55.0


def test_suggestion_stays_in_band():
    derived = EarthCloudSimulator.suggest_threshold(
        {
            "evaluated_readings": 80,
            "precision": 0.0,
            "recall": 1.0,
        }
    )
    assert 40.0 <= derived["threshold_suggestion"] <= 70.0
    assert derived["feedback_basis"] == "point"


def test_payload_increments_round():
    earth = EarthCloudSimulator()
    a = earth.build_update_payload({"evaluated_readings": 80, "precision": 0.5, "recall": 0.5})
    b = earth.build_update_payload({"evaluated_readings": 80, "precision": 0.5, "recall": 0.5})
    assert b["federated_round"] == a["federated_round"] + 1
    assert a["threshold_suggestion"] == 55.0
